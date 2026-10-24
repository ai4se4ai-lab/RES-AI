"""Small real CUDA smoke probe; synthetic tensors, not an agent benchmark."""
import argparse
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from resai.core import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rep", type=int, required=True)
    parser.add_argument("--mode", choices=["clean", "corrupt_output", "missing_checkpoint", "runtime_failure"], required=True)
    args = parser.parse_args()
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; no CPU fallback")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    torch.manual_seed(args.rep)
    torch.cuda.reset_peak_memory_stats()
    passed = ["imports"]
    status, fault, valid = "ok", None, False
    model = torch.nn.Sequential(torch.nn.Linear(512, 1024), torch.nn.ReLU(), torch.nn.Linear(1024, 64)).cuda().eval()
    passed.append("model_init")
    checkpoint = args.out.with_suffix(".pt")
    try:
        with torch.inference_mode():
            x = torch.randn(128, 512, device="cuda")
            y = model(x)
            torch.cuda.synchronize()
            passed.append("boundary_input")
            if args.mode == "runtime_failure":
                raise RuntimeError("injected runtime failure after CUDA execution")
            observed = y.cpu().tolist()
            if args.mode == "corrupt_output":
                observed = observed[:-1]
            valid = len(observed) == 128 and all(len(row) == 64 for row in observed)
            if valid:
                passed.append("output")
            if args.mode != "missing_checkpoint":
                torch.save(model.state_dict(), checkpoint)
                restored = torch.load(checkpoint, map_location="cuda", weights_only=True)
                clone = torch.nn.Sequential(torch.nn.Linear(512, 1024), torch.nn.ReLU(), torch.nn.Linear(1024, 64)).cuda().eval()
                clone.load_state_dict(restored)
                if torch.equal(y, clone(x)):
                    passed.append("checkpoint")
                checkpoint.unlink()
    except RuntimeError as exc:
        status, fault = "failed", str(exc)
    torch.cuda.synchronize()
    seconds = time.perf_counter()-start
    props = torch.cuda.get_device_properties(0)
    row = {"attempt_id": f"{os.environ.get('SLURM_JOB_ID', 'local')}-{args.mode}-{args.rep}",
           "timestamp": time.time(), "status": status, "fault": fault,
           "passed_probes": passed, "output_valid": valid, "output_exists": True,
           "peak_memory_fraction": torch.cuda.max_memory_allocated()/props.total_memory,
           "gpu_seconds": seconds, "accelerator_instances": 1,
           "device": props.name, "device_total_bytes": props.total_memory,
           "torch": torch.__version__, "cuda": torch.version.cuda, "hostname": socket.gethostname(),
           "mode": args.mode, "rep": args.rep, "job_id": os.environ.get("SLURM_JOB_ID"),
           "note": "gpu_seconds is probe process time on one allocated instance; Slurm billed time reported separately"}
    args.out.write_text(json.dumps(row, indent=2)+"\n")
    print(json.dumps(row))


if __name__ == "__main__":
    main()
