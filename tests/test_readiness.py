import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/"src"), str(ROOT/"experiments")]
from run_local import FAULTS, fixture, mutate
from resai.core import digest, readiness, refine
from resai.mcp import read
from resai.pipeline import load_engine, verify_inputs, verify_correspondence, validate_site_config


class ReadinessTests(unittest.TestCase):
    def test_mutations_and_clean_control(self):
        engine = load_engine()
        for fault in FAULTS:
            with self.subTest(fault=fault):
                plan, evidence, graph = fixture()
                mutate(fault, plan, evidence, graph)
                ok = readiness(plan, evidence, 10010)["ready"] and not engine.validate(engine.resolve(graph, False))
                self.assertEqual(ok, fault == "clean")

    def test_repair_invalidates_evidence_and_preserves_science(self):
        plan, evidence, graph = fixture()
        mutate("oom", plan, evidence, graph)
        updated = refine(plan, evidence)
        self.assertEqual(updated["scientific"], plan["scientific"])
        self.assertEqual(updated["execution"]["batch_size"], 4)
        self.assertFalse(readiness(updated, evidence, 10010)["ready"])
        plan["scientific"]["batch_invariant"] = False
        self.assertIsNone(refine(plan, evidence))

    def test_unknown_fault_has_no_repair(self):
        plan, evidence, _ = fixture()
        evidence["attempts"][-1]["fault"] = "unknown"
        self.assertIsNone(refine(plan, evidence))

    def test_reordered_bundle_cannot_hide_recent_failure(self):
        plan, evidence, _ = fixture()
        failed = copy.deepcopy(evidence["attempts"][-1])
        failed.update(attempt_id="new-failure", timestamp=10005, status="failed")
        evidence["attempts"].insert(0, failed)
        self.assertFalse(readiness(plan, evidence, 10010)["ready"])

    def test_refinement_stops_at_budget(self):
        plan, evidence, graph = fixture()
        mutate("oom", plan, evidence, graph)
        evidence["attempts"][-1]["gpu_seconds"] = plan["budget_gpu_seconds"]
        self.assertIsNone(refine(plan, evidence))

    def test_missing_telemetry_blocks(self):
        plan, _, _ = fixture()
        self.assertFalse(readiness(plan, {"attempts": []}, 10010)["ready"])

    def test_nonfinite_and_negative_accounting(self):
        for value in (-1, float("nan"), float("inf")):
            plan, evidence, _ = fixture()
            evidence["attempts"][0]["gpu_seconds"] = value
            # JSON canonicalization rejects nonfinite evidence (fail closed).
            try:
                self.assertFalse(readiness(plan, evidence, 10010)["ready"])
            except ValueError:
                pass

    def test_path_escape(self):
        with self.assertRaises(ValueError):
            read("../outside.json")

    def test_unbound_pipeline_rejected(self):
        plan, _, _ = fixture()
        self.assertIn("missing_input_hashes", verify_inputs(plan))

    def test_resource_plan_cannot_authorize_different_shape(self):
        plan, _, graph = fixture()
        plan["execution"].update(partition="site-default")
        graph["vars"] = {"BATCH_SIZE": "8"}
        graph["resai_scientific"] = plan["scientific"]
        graph["stages"][0]["resources"]["time"] = "00:15:00"
        plan["execution"]["graph_hash"] = digest(graph)
        self.assertEqual(verify_correspondence(plan, graph), [])
        graph["stages"][0]["resources"]["gpus"] = "fixture:64"
        plan["execution"]["graph_hash"] = digest(graph)
        self.assertIn("resource_mapping:setup", verify_correspondence(plan, graph))
        graph["stages"][0]["resources"]["gpus"] = "fixture:1"
        graph["stages"][0]["sbatch_extra"] = ["--gpus=64"]
        plan["execution"]["graph_hash"] = digest(graph)
        self.assertIn("resource_override:setup", verify_correspondence(plan, graph))

    def test_invalid_policy_is_structured_block(self):
        for key, value in (("max_attempts", True), ("budget_gpu_seconds", float("nan")), ("memory_limit", 1.1)):
            plan, evidence, _ = fixture()
            plan[key] = value
            self.assertFalse(readiness(plan, evidence, 10010)["ready"])

    def test_windows_site_value_corruption_blocks(self):
        self.assertEqual(validate_site_config({"WORK": "/scratch/run"}), [])
        self.assertEqual(validate_site_config({"WORK": "/scratch/run\r"}), ["control_character_in_site_config:WORK"])

    def test_mcp_lifecycle(self):
        messages = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "assess_readiness", "arguments": {"plan": "../escape", "evidence": "../escape"}}}]
        proc = subprocess.run([sys.executable, "-m", "resai.mcp"], input="\n".join(map(json.dumps, messages))+"\n", text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        responses = list(map(json.loads, proc.stdout.splitlines()))
        self.assertEqual(len(responses), 3)
        self.assertEqual(len(responses[1]["result"]["tools"]), 3)
        self.assertIn("error", responses[2])


if __name__ == "__main__":
    unittest.main()
