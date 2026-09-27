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
CURRENT_PROOF = ROOT / "docs" / "CURRENT_SOURCE_LIVE_PROOF_2026-09-27.json"
CURRENT_REDIRECT_PROOF = ROOT / "docs" / "CURRENT_SOURCE_REDIRECT_PROBE_2026-09-27.json"


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
    assert current["source_commit"] == "40417500c938ae59de4fded587e3bfefd562e07c"
    assert current["deployed_addresses"]["mandates"] == "0x4817FA4E770B1bE4633BD938991bcdB97EAA8E19"
    assert current["deployed_addresses"]["authorization"] == "0xCe751D8399639157268a55F12e6f2aB081d49c72"
    assert current["parity_scope"] == "redesigned repository source bytes match both current local deployments; all current-source local behavioral gates are finalized"
    assert current["source_hashes"]["covenant_mandates.py"] == sha256(MANDATES)
    assert current["source_hashes"]["covenant_authorization.py"] == sha256(AUTHORIZATION)
    redesign = manifest["bradbury_deployment_attempts"]["redesign_candidate_estimate"]
    assert redesign["source_sha256"] == sha256(MANDATES)
    assert redesign["eth_estimateGas"] < redesign["observed_submission_ceiling"]
    assert redesign["signing_performed"] is False
    assert redesign["submission_performed"] is False
    bradbury = manifest["bradbury_deployment_attempts"]["finalized_mandates_deployment"]
    assert bradbury["status"] == "FINALIZED"
    assert bradbury["status_code"] == 7
    assert bradbury["consensus_result"] == "AGREE"
    assert bradbury["execution_result"] == "FINISHED_WITH_RETURN"
    assert bradbury["source_parity"] is True
    assert bradbury["deployment_submissions"] == 1
    assert bradbury["replacement_or_resend"] is False
    auth_attempt = manifest["bradbury_deployment_attempts"]["authorization_deployment_attempt"]
    assert auth_attempt["status"] == "REJECTED_PRE_ACCEPTANCE"
    assert auth_attempt["gas_estimate"] >= auth_attempt["observed_submission_ceiling"]
    assert auth_attempt["accepted_transaction"] is None
    assert auth_attempt["nonce_consumed"] is False

    checkpoint = manifest["current_local_runtime_checkpoint"]
    assert checkpoint["status"] == "CURRENT_SOURCE_LOCAL_RUNTIME_CLOSURE"
    assert checkpoint["source_commit"] == "40417500c938ae59de4fded587e3bfefd562e07c"
    assert checkpoint["chain_id"] == 61999
    assert checkpoint["validator_count"] == 5
    assert checkpoint["deployed_addresses"]["mandates"] == "0x4817FA4E770B1bE4633BD938991bcdB97EAA8E19"
    assert checkpoint["deployed_addresses"]["authorization"] == "0xCe751D8399639157268a55F12e6f2aB081d49c72"
    proofs = checkpoint["live_proofs"]
    assert proofs["approval"]["terminal_state"] == "AUTHORIZED"
    assert proofs["rejection"]["terminal_state"] == "DENIED"
    assert proofs["repair_replacement"]["terminal_state"] == "AUTHORIZED"
    assert proofs["timeout_recovery"]["terminal_state"] == "EXPIRED"
    assert proofs["receipt_consumption"]["terminal_state"] == "CONSUMED"
    assert proofs["redirect_provenance"]["status"] == "PASS_LOCAL_CURRENT_RUNTIME"
    boundary = checkpoint["proof_boundary"]
    assert boundary["current_source_deployment_parity"] is True
    assert boundary["current_mandate_created"] is True
    assert boundary["current_approval_request_created"] is True
    assert boundary["current_approval_evaluated"] is True
    assert boundary["current_rejection_proven"] is True
    assert boundary["current_repair_replacement_proven"] is True
    assert boundary["current_timeout_recovery_proven"] is True
    assert boundary["current_receipt_consumption_proven"] is True
    assert boundary["current_redirect_provenance_proven"] is True
    assert boundary["production_or_bradbury_release"] is False

    current_proof = json.loads(CURRENT_PROOF.read_text(encoding="utf-8"))
    current_redirect = json.loads(CURRENT_REDIRECT_PROOF.read_text(encoding="utf-8"))
    assert current_proof["status"] == "CURRENT_SOURCE_LOCAL_RUNTIME_CLOSURE"
    assert current_proof["proof_boundary"]["production_or_bradbury_release"] is False
    assert current_redirect["status"] == "PASS_LOCAL_CURRENT_RUNTIME"
    assert current_redirect["decoded_result"] == "status=302;location=b'/final'"
    historical = manifest["historical_pre_redesign_local_runtime_checkpoint"]
    assert historical["status"] == "PRE_REDESIGN_HISTORICAL_LOCAL_RUNTIME_CLOSURE"
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
