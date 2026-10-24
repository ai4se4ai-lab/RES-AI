"""Pinned, local-only Ollama transport for the MapCoder deployment pilot."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request


class OllamaModel:
    def __init__(self, science, out, calls):
        self.science, self.out, self.calls = science, out, calls
        self.url = os.environ.get("OLLAMA_API", "http://127.0.0.1:18939")
        if self.url != "http://127.0.0.1:18939":
            raise ValueError("only the job-local Ollama endpoint is supported")

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.url+path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.load(response)

    def check_identity(self):
        version = self.request("/api/version")
        if version["version"] != self.science["ollama_version"]:
            raise ValueError("Ollama version differs from the declared plan")
        manifest = Path(self.science["model_path"])
        actual = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if actual != self.science["model_revision"]:
            raise ValueError("Ollama manifest identity changed")
        tags = self.request("/api/tags")["models"]
        (self.out/"backend.json").write_text(json.dumps({
            "version": version, "tags": tags,
            "manifest_sha256": actual, "science": self.science,
        }, indent=2)+"\n")
        if not any(m["name"] == self.science["model"] and
                   m["digest"].removeprefix("sha256:") == self.science["model_api_digest"] for m in tags):
            raise ValueError("Ollama server is not serving the pinned model")

    def warmup(self):
        # Empty prompt loads the model without generating an answer.
        self.request("/api/generate", {"model": self.science["model"],
                     "prompt": "", "stream": False, "keep_alive": "10m",
                     "options": {"num_ctx": self.science["max_input_tokens"]+
                                  self.science["max_new_tokens"], "num_gpu": 999}})
        running = self.request("/api/ps")["models"]
        (self.out/"loaded-model.json").write_text(json.dumps(running, indent=2)+"\n")
        if not any(m["name"] == self.science["model"] and m.get("size_vram", 0) > 0
                   and m["size_vram"] >= 0.95*m["size"]
                   for m in running):
            raise RuntimeError("model did not load fully into GPU memory")

    def prompt(self, messages):
        response = self.request("/api/chat", {
            "model": self.science["model"], "messages": messages,
            "think": self.science["thinking"], "stream": False,
            "keep_alive": "10m", "options": {"temperature": 0, "seed": 0,
                "num_predict": self.science["max_new_tokens"],
                "num_ctx": self.science["max_input_tokens"]+self.science["max_new_tokens"],
                "num_gpu": 999},
        })
        self.calls.append({"messages": messages, "response": response})
        (self.out/"calls.json").write_text(json.dumps(self.calls, indent=2)+"\n")
        if not response.get("done") or response.get("done_reason") == "length":
            raise RuntimeError("incomplete or truncated Ollama generation")
        inputs, outputs = response["prompt_eval_count"], response["eval_count"]
        if not isinstance(inputs, int) or not 0 <= inputs <= self.science["max_input_tokens"]:
            raise RuntimeError("declared input envelope exceeded")
        if not isinstance(outputs, int) or not 0 <= outputs <= self.science["max_new_tokens"]:
            raise RuntimeError("declared output envelope exceeded")
        text = response["message"]["content"]
        if not text.strip():
            raise RuntimeError("Ollama returned an empty answer")
        return text, inputs, outputs
