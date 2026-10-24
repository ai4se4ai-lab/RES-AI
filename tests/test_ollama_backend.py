import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("ollama_backend", Path(__file__).resolve().parents[1]/"experiments/mapcoder/ollama_backend.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OllamaTransportTests(unittest.TestCase):
    def test_manifest_bytes_and_api_digest_are_bound_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            manifest = out/"manifest.json"
            manifest.write_text('{"schemaVersion":2}')
            science = {"model": "qwen3.8:27b", "model_path": str(manifest),
                "model_revision": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "model_api_digest": "a"*64, "ollama_version": "0.40.10"}
            model = module.OllamaModel(science, out, [])
            tags = [{"name": science["model"], "digest": "a"*64}]
            model.request = lambda path: {"version": "0.40.10"} if path == "/api/version" else {"models": tags}
            model.check_identity()
            tags[0]["digest"] = "b"*64
            with self.assertRaisesRegex(ValueError, "pinned model"):
                model.check_identity()
            manifest.write_text('{}')
            with self.assertRaisesRegex(ValueError, "manifest identity"):
                model.check_identity()

    def test_response_contract_and_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            model = module.OllamaModel({"model": "qwen3.8:27b", "thinking": False,
                "max_input_tokens": 12, "max_new_tokens": 4}, Path(directory), calls)
            response = {"done": True, "done_reason": "stop", "prompt_eval_count": 10,
                        "eval_count": 3, "message": {"content": "answer"}}
            requests = []
            def request(path, body):
                requests.append(body)
                return dict(response)
            model.request = request
            self.assertEqual(model.prompt([{"role": "user", "content": "test"}]), ("answer", 10, 3))
            self.assertEqual(requests[0]["options"]["temperature"], 0)
            self.assertFalse(requests[0]["think"])
            response["done_reason"] = "length"
            with self.assertRaisesRegex(RuntimeError, "truncated"):
                model.prompt([])
            response["done_reason"] = "stop"
            response["prompt_eval_count"] = 13
            with self.assertRaisesRegex(RuntimeError, "envelope"):
                model.prompt([])
            response["prompt_eval_count"] = 10
            response["eval_count"] = 5
            with self.assertRaisesRegex(RuntimeError, "output envelope"):
                model.prompt([])
            self.assertEqual(len(calls), 4)  # Failed responses remain in the trace.

    def test_cpu_fallback_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            model = module.OllamaModel({"model": "qwen3.8:27b", "max_input_tokens": 12,
                "max_new_tokens": 4}, Path(directory), [])
            model.request = lambda path, body=None: {"models": [{"name": "qwen3.8:27b", "size_vram": 0}]}
            with self.assertRaisesRegex(RuntimeError, "GPU memory"):
                model.warmup()


if __name__ == "__main__":
    unittest.main()
