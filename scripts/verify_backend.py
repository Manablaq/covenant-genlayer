#!/usr/bin/env python3
"""Deterministic repository checks for the Covenant backend release gates.

This verifier is deliberately read-only unless ``--output`` is supplied. It
does not connect to a chain, sign transactions, submit writes, or infer live
finality from local files.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "contracts" / "covenant_authorization.py"
MANDATES = ROOT / "contracts" / "covenant_mandates.py"
MANIFEST = ROOT / "deployments" / "release-manifest.json"
RUNTIME_PATCH = ROOT / "runtime" / "patches" / "genvm-v0.2.16-no-redirect.patch"
RUNTIME_README = ROOT / "runtime" / "README.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_node(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def call_count(node: ast.AST, attribute: str) -> int:
    return sum(
        1
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == attribute
    )


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    authorization_source = AUTHORIZATION.read_text(encoding="utf-8")
    mandates_source = MANDATES.read_text(encoding="utf-8")
    runtime_patch = RUNTIME_PATCH.read_text(encoding="utf-8")
    runtime_readme = RUNTIME_README.read_text(encoding="utf-8")
    authorization_tree = ast.parse(authorization_source)
    mandates_tree = ast.parse(mandates_source)

    assert "MAX_EVIDENCE_BODY_BYTES = 8192" in mandates_source
    assert "max_evidence_body_bytes" in mandates_source
    assert "get_max_evidence_body_bytes" in authorization_source
    assert "REPAIR_EVIDENCE_BODY_TOO_LARGE" in authorization_source
    assert "hashlib.sha256(body).digest()" in authorization_source
    assert "gl.vm.run_nondet_unsafe" in authorization_source
    assert "receipt_consumed" in authorization_source
    assert "nonce_used" in authorization_source

    for name in (
        "_authority_reason",
        "_freshness_reason",
        "_evidence_policy_reason",
        "_run_semantic_consensus",
    ):
        assert call_count(function_node(authorization_tree, name), "view") == 0

    assert "criteria = policy.semantic_criteria" in authorization_source
    assert "self._validate_mandate_policy(policy)" in authorization_source
    assert "if len(body) > int(policy.max_evidence_body_bytes):" in authorization_source
    assert "387e1a66e920cb2dfadcdce40ab2d28da02efd1e" in runtime_readme
    assert "reqwest::redirect::Policy::none()" in runtime_patch

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "UNRELEASED"
    assert manifest["source_hashes"]["covenant_mandates.py"] == sha256(MANDATES)
    assert manifest["source_hashes"]["covenant_authorization.py"] == sha256(AUTHORIZATION)

    result = {
        "status": "PASS",
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "source_hashes": {
            "covenant_mandates.py": sha256(MANDATES),
            "covenant_authorization.py": sha256(AUTHORIZATION),
        },
        "runtime_patch_sha256": sha256(RUNTIME_PATCH),
        "policy_reads_in_evidence_helpers": 0,
        "evidence_body_limit_bytes": 8192,
        "manifest_status": manifest["status"],
    }

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(encoded, end="")
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
