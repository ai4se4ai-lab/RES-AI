import argparse
import json
from pathlib import Path
from .core import discover, readiness, refine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["discover", "gate", "refine"])
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.command == "discover":
        result = discover()
    else:
        if not args.plan or not args.evidence:
            parser.error("gate/refine require --plan and --evidence")
        plan, evidence = [json.loads(p.read_text()) for p in (args.plan, args.evidence)]
        result = readiness(plan, evidence) if args.command == "gate" else refine(plan, evidence)
    print(json.dumps(result, indent=2))
    return 2 if args.command == "gate" and not result["ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
