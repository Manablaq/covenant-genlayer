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

    assert "MAX_EVIDENCE_BODY_BYTES=8192" in mandates_source
    assert "MAX_POLICY_COLLECTION_ITEMS=8" in mandates_source
    assert "MAX_EVIDENCE_RECORDS=8" in mandates_source
    assert "MAX_POLICY_COLLECTION_ITEMS=8" in authorization_source
    assert "MAX_EVIDENCE_RECORDS=8" in authorization_source
    assert "_safe_https_reference" in mandates_source
    assert "def _sr(" in authorization_source
    assert "# pyright: reportUnknownMemberType=false" in mandates_source
    assert "# pyright: reportUnknownMemberType=false" in authorization_source
    assert "max_evidence_body_bytes" in mandates_source
    assert "get_max_evidence_body_bytes" in authorization_source
    assert "REPAIR_EVIDENCE_BODY_TOO_LARGE" in authorization_source
    assert "hashlib.sha256(bb).digest()" in authorization_source
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

    assert "policy.n" in authorization_source
    assert "def _vp(" in authorization_source
    assert "self._vp(policy)" in authorization_source
    assert "len(bb)>int(policy.m)" in authorization_source
    assert "387e1a66e920cb2dfadcdce40ab2d28da02efd1e" in runtime_readme
    assert "reqwest::redirect::Policy::none()" in runtime_patch

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "UNRELEASED"
    production = manifest["production_deployment"]
    assert production["status"] == "UNRELEASED"
    current = manifest["current_candidate"]
    assert current["live_source_parity"] is True
    assert current["source_commit"] == "78280f3e82e056424342b3233f420332d6e2a71f"
    assert current["parity_scope"] == "supported local runtime only; not public/Bradbury"
    assert current["source_hashes"]["covenant_mandates.py"] == sha256(MANDATES)
    assert current["source_hashes"]["covenant_authorization.py"] == sha256(AUTHORIZATION)

    checkpoint = manifest["current_local_runtime_checkpoint"]
    assert checkpoint["status"] == "PARTIAL_CURRENT_SOURCE_LIVE_PROOF"
    assert checkpoint["source_commit"] == current["source_commit"]
    assert checkpoint["chain_id"] == 61999
    assert checkpoint["validator_count"] == 5
    assert checkpoint["deployed_addresses"]["mandates"] == "0xdFEce9C4ae3124B8de273B75227F6DC1DE30297C"
    assert checkpoint["deployed_addresses"]["authorization"] == "0xEBb2863137Dff7e96886090D303373E8Ec9CF5B8"
    assert checkpoint["mandate"]["mandate_id"] == "0xcc8506d1809fc4664c5f9287816f8c51198c250fe995cc505c340d4b12de8ab7"
    assert checkpoint["mandate"]["version"] == 1
    assert checkpoint["mandate"]["state_parity"] == "PASS"
    phase6d = checkpoint["phase6d_approval_create_request"]
    assert phase6d["status"] == "STOP_BEFORE_SIGNING_FRESHNESS_OBSERVATION_AGE_EXCEEDED"
    assert phase6d["submission_count"] == 0
    assert phase6d["chain_write_performed"] is False
    assert phase6d["request_created"] is False
    assert phase6d["observation_age_seconds"] == 1352
    assert phase6d["max_observation_age_seconds"] == 900
    fresh = checkpoint["phase6d_r1_fresh_approval_preparation"]
    assert fresh["status"] == "PASS_UNSIGNED_ONLY"
    assert fresh["preparation_now"] == 1790491733
    assert fresh["evm_nonce"] == 39
    assert fresh["covenant_request_nonce"] == 1
    assert fresh["fresh_unsigned_fingerprint"] == "45b1b67bd5bf328119646411e4b55f4731997d6e92f08d9ddab5e811a36ae838"
    assert fresh["old_stopped_fingerprint_reused"] is False
    assert fresh["freshness_at_preparation"] == "PASS"
    assert fresh["submission_count"] == 0
    assert fresh["signing_performed"] is False
    assert fresh["submission_performed"] is False
    assert fresh["chain_write_performed"] is False
    boundary = checkpoint["proof_boundary"]
    assert boundary["current_source_deployment_parity"] is True
    assert boundary["current_mandate_created"] is True
    assert boundary["current_approval_request_created"] is False
    assert boundary["production_or_bradbury_release"] is False

    historical = manifest["historical_local_live_proof"]
    assert historical["status"] == "HISTORICAL_ONLY_NOT_CURRENT_SOURCE_PARITY"
    runtime = manifest["runtime_provenance"]
    assert runtime["local_proof_only"] is True
    assert runtime["genvm_source_commit"] == "387e1a66e920cb2dfadcdce40ab2d28da02efd1e"
    assert runtime["runtime_patch_sha256"] == sha256(RUNTIME_PATCH)
    assert runtime["runtime_configuration_sha256"] == "b3499f5307c7eb1f181cc7944f8d9383ec9ad9dd3cad1aba1d94589ed263fa28"
    assert runtime["mounted_components"] == ["jsonrpc", "consensus-worker"]

    result = {
        "status": "PASS",
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "source_hashes": {
            "covenant_mandates.py": sha256(MANDATES),
            "covenant_authorization.py": sha256(AUTHORIZATION),
        },
        "runtime_patch_sha256": sha256(RUNTIME_PATCH),
        "runtime_binary_sha256": manifest["runtime_provenance"]["runtime_binary_sha256"],
        "policy_reads_in_evidence_helpers": 0,
        "evidence_body_limit_bytes": 8192,
        "manifest_status": manifest["status"],
        "current_live_source_parity": current["live_source_parity"],
        "production_deployment_status": production["status"],
    }

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(encoded, end="")
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
