"""Archive a pilot's raw data, declared source, assessment, and Slurm accounting."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--jobs", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root/"src"))
    from resai.pipeline import load_engine
    hpc = root/"hpc/mapcoder"
    engine = load_engine(hpc)
    logs = hpc/"logs"/args.run_id
    results = engine.results_dir(args.run_id, engine.cluster(args.run_id))
    assessment = logs/"assessment"
    assessment.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(root/"src"))
    with (assessment/"assessment-console.txt").open("w") as stream:
        rc = subprocess.run([sys.executable, str(root/"experiments/mapcoder/assess.py"),
            "--results", str(results), "--out", str(assessment)], cwd=root,
            stdout=stream, stderr=subprocess.STDOUT, env=env).returncode
    if (assessment/"evidence.json").exists():
        with (assessment/"admission-after.txt").open("w") as stream:
            subprocess.run([sys.executable, "-m", "resai.pipeline", "--hpc-dir", str(hpc),
                "--plan", str(root/"experiments/mapcoder/plan.json"), "--evidence",
                str(assessment/"evidence.json")], cwd=root, env=env,
                stdout=stream, stderr=subprocess.STDOUT)
    with (assessment/"sacct.psv").open("w") as stream:
        subprocess.run(["sacct", "-j", args.jobs, "--parsable2",
            "--format=JobID,JobName,State,Submit,Start,End,ElapsedRaw,AllocTRES,ExitCode"],
            stdout=stream, check=True)
    (assessment/"results-path.txt").write_text(str(results)+"\n")
    source = logs/"executed_source"
    plan = json.loads((root/"experiments/mapcoder/plan.json").read_text())
    names = set(plan["inputs"]) | {"experiments/mapcoder/plan.json",
        "experiments/mapcoder/assess.py", "experiments/mapcoder/archive_run.py"}
    for name in sorted(names):
        path = root/name
        if path.is_file():
            dest = source/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    archive = logs.parent/(args.run_id+"-complete.tar.gz")
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(logs, arcname="logs")
        if results.exists():
            bundle.add(results, arcname="results")
        bundle.add(assessment, arcname="assessment")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix+".sha256").write_text(checksum+"  "+archive.name+"\n")
    print(json.dumps({"archive": str(archive), "sha256": checksum,
                     "assessment_exit_code": rc, "results": str(results)}))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
