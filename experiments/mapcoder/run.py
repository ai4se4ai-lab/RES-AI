"""One genuine MapCoder task with a local cached model and evidence emission."""
import argparse
import contextlib
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
from resai.core import digest
from resai.pipeline import verify_inputs, verify_correspondence, load_engine, validate_site_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rep", type=int, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    args.out = args.out / f"attempt-{os.environ.get('SLURM_JOB_ID','local')}-{args.rep}-{time.time_ns()}"
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    passed, status, fault, solved = [], "failed", None, None
    calls = []
    evidence = {"attempt_id": f"{os.environ.get('SLURM_JOB_ID','local')}-mapcoder-{args.rep}",
                "plan_hash": digest(plan), "passed_probes": passed, "output_valid": False,
                "rep": args.rep, "job_id": os.environ.get("SLURM_JOB_ID"),
                "array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID"), "array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID")}
    try:
        errors = verify_inputs(plan, root=ROOT, hpc_relative="hpc/mapcoder")
        engine = load_engine(ROOT/"hpc/mapcoder")
        graph = engine.resolve(engine.load_experiments(ROOT/"hpc/mapcoder/config/experiments.json"), False)
        errors += verify_correspondence(plan, graph) + validate_site_config(engine.cluster())
        if errors:
            raise RuntimeError("invalid preflight: "+", ".join(errors))
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA required")
        torch.cuda.reset_peak_memory_stats()
        torch.manual_seed(0)
        sys.path.insert(0, str(ROOT/"experiments/vendor/mapcoder/src"))
        from promptings.MapCoder import MapCoder
        from datasets.HumanEvalDataset import HumanDataset
        from results.Results import Results
        import evaluations.func_evaluate as functional
        passed.append("imports")
        # Preserve original test assertions but execute generated programs in
        # bounded subprocesses with a deliberately narrow capability set.
        def bounded_exec(fn, arguments, timeout):
            if fn is not exec:
                raise ValueError("unsupported evaluator operation")
            proc = subprocess.run([sys.executable, str(ROOT/"experiments/mapcoder/safe_exec.py")],
                input=json.dumps({"code": arguments[0]}), text=True, capture_output=True,
                timeout=timeout+2, cwd=args.out, env={"PATH": os.environ.get("PATH", "")})
            if proc.returncode:
                raise RuntimeError(proc.stderr[-1500:])
        functional.function_with_timeout = bounded_exec
        science = plan["scientific"]
        model_dir = science["model_path"]
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.bfloat16,
                    local_files_only=True, attn_implementation="sdpa").to("cuda").eval()
        passed.append("model_init")
        class LocalModel:
            def prompt(self, processed_input):
                tokens = tokenizer.apply_chat_template(processed_input, tokenize=True,
                    add_generation_prompt=True, return_tensors="pt").to("cuda")
                if tokens.shape[1] > science["max_input_tokens"]:
                    raise RuntimeError("declared input envelope exceeded")
                with torch.inference_mode():
                    output = model.generate(tokens, max_new_tokens=science["max_new_tokens"], do_sample=False,
                        pad_token_id=tokenizer.eos_token_id, use_cache=True)
                text = tokenizer.decode(output[0, tokens.shape[1]:], skip_special_tokens=True)
                calls.append({"messages": processed_input, "response": text,
                              "input_tokens": tokens.shape[1], "output_tokens": output.shape[1]-tokens.shape[1]})
                (args.out/"calls.json").write_text(json.dumps(calls, indent=2))
                return text, tokens.shape[1], output.shape[1]-tokens.shape[1]
        data = HumanDataset(path=str(ROOT/"experiments/mapcoder/task.jsonl"))
        results = Results(str(args.out/"task-results.jsonl"))
        strategy = MapCoder(model=LocalModel(), data=data, language="Python3", pass_at_k=1,
                            results=results, verbose=True, k=science["k"], t=science["t"])
        with (args.out/"strategy.log").open("w") as log, contextlib.redirect_stdout(log):
            strategy.run()
        if not calls:
            raise RuntimeError("fresh attempt did not execute inference")
        passed.append("task_execution")
        records = [json.loads(line) for line in (args.out/"task-results.jsonl").read_text().splitlines()]
        if len(records) != 1 or records[0]["task_id"] != "HumanEval/0" or not isinstance(records[0]["is_solved"], bool):
            raise RuntimeError("output schema/count mismatch")
        passed.append("output_schema")
        # Reload persisted results into fresh strategy/Results objects.
        prior = len(calls)
        results = Results(str(args.out/"task-results.jsonl"))
        strategy = MapCoder(model=LocalModel(), data=data, language="Python3", pass_at_k=1,
                            results=results, verbose=True, k=science["k"], t=science["t"])
        with (args.out/"resume.log").open("w") as log, contextlib.redirect_stdout(log):
            strategy.run()
        if len(calls) != prior:
            raise RuntimeError("resume unexpectedly repeated inference")
        passed.append("resume")
        evidence["output_valid"] = True
        solved, status = records[0]["is_solved"], "ok"
    except Exception as exc:
        import traceback
        fault = type(exc).__name__+": "+str(exc)
        (args.out/"failure.log").write_text(traceback.format_exc())
    finally:
        evidence.update(status=status, fault=fault, scientific_task_solved=solved, timestamp=time.time(),
            gpu_seconds=time.perf_counter()-start, calls=len(calls))
        try:
            import torch
            props = torch.cuda.get_device_properties(0)
            evidence.update(peak_memory_fraction=torch.cuda.max_memory_allocated()/props.total_memory,
                            device=props.name, total_memory_bytes=props.total_memory,
                            torch=torch.__version__, cuda=torch.version.cuda)
        except Exception:
            evidence["peak_memory_fraction"] = 2
        (args.out/"evidence.json").write_text(json.dumps(evidence, indent=2)+"\n")
        print(json.dumps(evidence, indent=2))
    # Record genuine deployment failure in the ledger; afterany still collects.
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
