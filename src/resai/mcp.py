"""Minimal MCP stdio JSON-RPC server; workspace-scoped read-only tool surface.

No arbitrary commands or submission tool: production remains the operator's
use-hpc command. This is a research prototype, not a hardened multi-user service.
"""
import json
import sys
from pathlib import Path
from .core import discover, readiness, refine

ROOT = Path.cwd().resolve()
TOOLS = [
    {"name": "cluster_snapshot", "description": "Read scheduler inventory; unavailable measurements remain unknown", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    *[{"name": name, "description": desc, "inputSchema": {"type": "object", "properties": {"plan": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["plan", "evidence"], "additionalProperties": False}}
      for name, desc in [("assess_readiness", "Evaluate exact-plan smoke evidence"), ("propose_refinement", "Propose batch reduction only when scientific contract permits")]]]


def read(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("path outside workspace")
    return json.loads(path.read_text())


def handle(message):
    method = message["method"]
    if method == "initialize":
        return {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "resai", "version": "0.1.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = message["params"]
        name, args = params["name"], params.get("arguments", {})
        if name == "cluster_snapshot":
            result = discover()
        elif name in ("assess_readiness", "propose_refinement"):
            fn = readiness if name == "assess_readiness" else refine
            result = fn(read(args["plan"]), read(args["evidence"]))
        else:
            raise ValueError("unknown tool")
        return {"content": [{"type": "text", "text": json.dumps(result)}], "isError": False}
    raise ValueError("unsupported method")


def main():
    for line in sys.stdin:
        msg = None
        try:
            msg = json.loads(line)
            if "id" not in msg:
                continue
            response = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(msg, dict) else None,
                        "error": {"code": -32602, "message": str(exc)}}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
