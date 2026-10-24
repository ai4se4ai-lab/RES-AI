"""Narrow evaluator for the selected scalar/list HumanEval task, not a sandbox.

No file/network/import capabilities are exposed to generated code. A subprocess
adds a wall-time limit. Unsupported syntax is rejected rather than broadened.
"""
import ast
import builtins
import json
import resource
import sys
import typing


def main():
    code = json.loads(sys.stdin.read())["code"]
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if not isinstance(node, ast.ImportFrom) or node.module != "typing":
                raise ValueError("unsupported import")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.ClassDef, ast.With, ast.AsyncWith)):
            raise ValueError("unsupported syntax")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("private attribute blocked")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("private name blocked")
    tree.body = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    names = "abs all any bool dict enumerate float int isinstance len list map max min range reversed round set sorted str sum tuple zip AssertionError Exception TypeError ValueError".split()
    namespace = {"__builtins__": {name: getattr(builtins, name) for name in names},
                 "List": typing.List, "Tuple": typing.Tuple, "Dict": typing.Dict, "Set": typing.Set}
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    exec(compile(tree, "<generated>", "exec"), namespace)


if __name__ == "__main__":
    main()
