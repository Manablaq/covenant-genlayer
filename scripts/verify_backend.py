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
RUNTIME_REMEDIATION_PATCH = (
    ROOT
    / "runtime"
    / "patches"
    / "genvm-v0.6.0-rc8-configurable-web-redirects.patch"
)
RUNTIME_README = ROOT / "runtime" / "README.md"
CURRENT_PROOF = ROOT / "docs" / "CURRENT_SOURCE_LIVE_PROOF_2026-09-27.json"
CURRENT_BRADBURY_PROOF = ROOT / "docs" / "CURRENT_SOURCE_BRADBURY_LIVE_PROOF_2026-09-29.json"
CURRENT_REDIRECT_PROOF = ROOT / "docs" / "CURRENT_SOURCE_REDIRECT_PROBE_2026-09-27.json"
CURRENT_CONSENSUS_PROOF = ROOT / "docs" / "CURRENT_SOURCE_BRADBURY_REPAIRED_EVALUATION_CONSENSUS_2026-09-29.json"
FRESH_EVALUATION_PROOF = ROOT / "docs" / "CURRENT_SOURCE_BRADBURY_FRESH_EVALUATION_CONSENSUS_2026-09-29.json"
LOCAL_GATE_G_PROOF = ROOT / "docs" / "CURRENT_SOURCE_LOCAL_GATE_G_2026-10-01.json"
LOCAL_GATE_F_PROOF = ROOT / "docs" / "CURRENT_SOURCE_LOCAL_GATE_F_2026-10-02.json"
STUDIO_NEXT_PREFLIGHT = ROOT / "docs" / "STUDIO_NEXT_READ_ONLY_PREFLIGHT_2026-10-02.json"


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


def assert_protocol_success(record: dict, label: str) -> None:
    """Apply GenLayer's protocol success rule without inventing unanimity."""

    assert record["status"] == "FINALIZED", f"{label} is not FINALIZED"
    assert record["consensus_result"] == "AGREE", f"{label} is not accepted"
    assert (
        record["execution_result"] == "FINISHED_WITH_RETURN"
    ), f"{label} did not finish successfully"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    authorization_source = AUTHORIZATION.read_text(encoding="utf-8")
    mandates_source = MANDATES.read_text(encoding="utf-8")
    runtime_patch = RUNTIME_PATCH.read_text(encoding="utf-8")
    runtime_remediation_patch = RUNTIME_REMEDIATION_PATCH.read_text(encoding="utf-8")
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
    assert "_hs(bb).digest()" in authorization_source
    assert "gl.vm.run_nondet_unsafe" in authorization_source
    assert "receipt_consumed" in authorization_source
    assert "nonce_used" in authorization_source

    for name in (
        "_au",
        "_fr",
        "_ep",
        "_sc",
    ):
        assert call_count(function_node(authorization_tree, name), "view") == 0

    assert "p0.n" in authorization_source
    assert "def _vp(" in authorization_source
    assert "self._vp(p0)" in authorization_source
    assert "len(bb)>int(p0.m)" in authorization_source
    assert "387e1a66e920cb2dfadcdce40ab2d28da02efd1e" in runtime_readme
    assert "reqwest::redirect::Policy::none()" in runtime_patch
    assert "619dfad4bae51c191ef66c3e8cac6ed996961858" in runtime_readme
    assert "follow_redirects" in runtime_remediation_patch
    assert "reqwest::redirect::Policy::none()" in runtime_remediation_patch
    assert "signer_client" in runtime_remediation_patch
    assert (
        "test_unfiltered_client_can_expose_redirect_without_fetching_target"
        in runtime_remediation_patch
    )
    assert (
        "test_unfiltered_client_preserves_default_redirect_following"
        in runtime_remediation_patch
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 16
    assert manifest["status"] == "UNRELEASED"
    production = manifest["production_deployment"]
    assert production["status"] == "UNRELEASED"
    current = manifest["current_candidate"]
    assert current["live_source_parity"] is True
    assert current["source_commit"] == "6da89ec6e75cd9e8f1aee2be93a539020129c7f2"
    assert current["deployed_addresses"]["mandates"] == "0xd4C0945533C959b094967781815e31ecd0C345F7"
    assert current["deployed_addresses"]["authorization"] == "0x1e55a34a91b227a1fdc27bd7ce675a7f01dc30a2"
    assert current["parity_scope"] == "current contract source hashes match the exact Bradbury bytecode at the current deployment addresses"
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
    compact_preflight = manifest["bradbury_deployment_attempts"]["authorization_compact_candidate_preflight"]
    assert compact_preflight["source_sha256"] == "1fbeb9cd2223632fabd73dabaca63379c019939c779bbc730e825f4f03fe7e94"
    assert compact_preflight["eth_estimateGas"] >= compact_preflight["observed_submission_ceiling"]
    assert compact_preflight["signing_performed"] is False
    assert compact_preflight["submission_performed"] is False
    failed_attempt = manifest["bradbury_deployment_attempts"]["authorization_compact_candidate_deployment_attempt"]
    assert failed_attempt["source_sha256"] == "8df817d76ff0ff5abd5adcfdefb97765261a7cce7bc704ffb44c2e1f28c27238"
    assert failed_attempt["status"] == "GENLAYER_EXECUTION_FAILED"
    assert failed_attempt["genvm_result_code"] == 2
    assert failed_attempt["error"] == "invalid_contract"
    assert failed_attempt["deployment_address"] is None
    assert failed_attempt["source_parity"] is False
    assert failed_attempt["deployment_submissions"] == 1
    assert failed_attempt["replacement_or_resend"] is False
    accepted_attempt = manifest["bradbury_deployment_attempts"]["authorization_format_fix_deployment_attempt"]
    assert accepted_attempt["source_sha256"] == "306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c1"
    assert accepted_attempt["status"] == "FINALIZED"
    assert accepted_attempt["gas_estimate"] < accepted_attempt["observed_submission_ceiling"]
    assert accepted_attempt["tx_execution_result"] == "FINISHED_WITH_RETURN"
    assert accepted_attempt["genvm_trace_result_code"] == 0
    assert accepted_attempt["deployment_address"] == "0x8c1c7169756287a30bceeb28caee4991b5566076"
    assert accepted_attempt["source_parity"] is True
    assert accepted_attempt["finalization_submissions"] == 1
    assert accepted_attempt["finalization_required"] is False
    typed_attempt = manifest["bradbury_deployment_attempts"]["authorization_strict_typing_deployment"]
    assert typed_attempt["source_sha256"] == sha256(AUTHORIZATION)
    assert typed_attempt["source_commit"] == current["source_commit"]
    assert typed_attempt["status"] == "FINALIZED"
    assert typed_attempt["internal_status_code"] == 7
    assert typed_attempt["consensus_result"] == "AGREE"
    assert typed_attempt["tx_execution_result"] == "FINISHED_WITH_RETURN"
    assert typed_attempt["deployment_address"] == current["deployed_addresses"]["authorization"]
    assert typed_attempt["source_parity"] is True
    assert typed_attempt["deployment_submissions"] == 1
    assert typed_attempt["finalization_submissions"] == 1
    assert typed_attempt["replacement_or_resend"] is False

    checkpoint = manifest["current_local_runtime_checkpoint"]
    local_gate_g = json.loads(LOCAL_GATE_G_PROOF.read_text(encoding="utf-8"))
    assert checkpoint["status"] == "CURRENT_SOURCE_LOCAL_GATE_G_CLOSED"
    assert checkpoint["evidence"] == "docs/CURRENT_SOURCE_LOCAL_GATE_G_2026-10-01.json"
    assert checkpoint["source_commit"] == current["source_commit"]
    assert checkpoint["reviewed_repository_head"] == "285d0407b5493cdb8240bed7c19ffc2716160d54"
    assert checkpoint["reviewed_repository_tree"] == "333bc606754f08d5678fcec1528a71cce6d88d19"
    assert checkpoint["chain_id"] == 61999
    assert checkpoint["validator_count"] == 5
    assert checkpoint["genvm_version"] == "v0.2.16"
    assert checkpoint["source_hashes"]["covenant_mandates.py"] == sha256(MANDATES)
    assert checkpoint["source_hashes"]["covenant_authorization.py"] == sha256(AUTHORIZATION)
    assert checkpoint["source_bytes"]["covenant_mandates.py"] == len(MANDATES.read_bytes())
    assert checkpoint["source_bytes"]["covenant_authorization.py"] == len(AUTHORIZATION.read_bytes())
    assert checkpoint["deployed_addresses"]["mandates"] == "0xaD8B37Eb0263Ea525BEe0767e5e512E320c71656"
    assert checkpoint["deployed_addresses"]["authorization"] == "0x562FA7DD960338B41C456b60564F964F571A1764"
    assert checkpoint["transactions"]["mandates_deployment"] == "0xbc65aa5dd8b0a3079ad17b9481c85ef20f89a9547e626a9b17adc1105aebde07"
    assert checkpoint["transactions"]["authorization_deployment"] == "0x3880d77e219dbfbe1527512fe5434bc15d4fc6f048463d344f1bb020516d961d"
    assert checkpoint["authorized_candidates"]["mandates"]["nonce"] == 75
    assert checkpoint["authorized_candidates"]["authorization"]["nonce"] == 76
    assert checkpoint["authorized_candidates"]["authorization"]["constructor_mandates_address"] == checkpoint["deployed_addresses"]["mandates"]
    assert checkpoint["finality"]["mandates"]["status"] == "FINALIZED"
    assert checkpoint["finality"]["mandates"]["consensus_result"] == "AGREE"
    assert checkpoint["finality"]["mandates"]["execution_result"] == "FINISHED_WITH_RETURN"
    assert checkpoint["finality"]["mandates"]["source_parity"] is True
    assert checkpoint["finality"]["mandates"]["submission_count"] == 1
    assert checkpoint["finality"]["authorization"]["status"] == "FINALIZED"
    assert checkpoint["finality"]["authorization"]["consensus_result"] == "AGREE"
    assert checkpoint["finality"]["authorization"]["execution_result"] == "FINISHED_WITH_RETURN"
    assert checkpoint["finality"]["authorization"]["source_parity"] is True
    assert checkpoint["finality"]["authorization"]["submission_count"] == 1
    assert checkpoint["authorization_mandates_binding"] is True
    assert checkpoint["exactly_one_order1_write"] is True
    assert checkpoint["exactly_one_order2_write"] is True
    assert checkpoint["additional_order2_chain_writes"] == 0
    assert checkpoint["bradbury_writes_in_gate_g_order2"] == 0
    assert checkpoint["post_finality_sender_nonce"] == {"latest": 77, "pending": 77}
    assert checkpoint["gate_g_complete"] is True
    boundary = checkpoint["proof_boundary"]
    assert boundary["current_source_deployment_parity"] is True
    assert boundary["current_source_authorization_mandates_binding"] is True
    assert boundary["current_mandate_created"] is False
    assert boundary["current_approval_request_created"] is False
    assert boundary["current_approval_evaluated"] is False
    assert boundary["current_rejection_proven"] is False
    assert boundary["current_repair_replacement_proven"] is False
    assert boundary["current_timeout_recovery_proven"] is False
    assert boundary["current_receipt_consumption_proven"] is False
    assert boundary["current_redirect_provenance_proven"] is False
    assert boundary["production_or_bradbury_release"] is False
    assert local_gate_g["status"] == "GATE_G_CLOSED"
    assert local_gate_g["repository"]["reviewed_parent_head"] == checkpoint["reviewed_repository_head"]
    assert local_gate_g["repository"]["reviewed_parent_tree"] == checkpoint["reviewed_repository_tree"]
    assert local_gate_g["source"]["mandates"]["sha256"] == sha256(MANDATES)
    assert local_gate_g["source"]["authorization"]["sha256"] == sha256(AUTHORIZATION)
    assert local_gate_g["source"]["mandates"]["schema_sha256"] == checkpoint["schema_hashes"]["covenant_mandates.py"]
    assert local_gate_g["source"]["authorization"]["schema_sha256"] == checkpoint["schema_hashes"]["covenant_authorization.py"]
    assert local_gate_g["order1_mandates"]["transaction"] == checkpoint["transactions"]["mandates_deployment"]
    assert local_gate_g["order1_mandates"]["address"] == checkpoint["deployed_addresses"]["mandates"]
    assert local_gate_g["order2_authorization"]["transaction"] == checkpoint["transactions"]["authorization_deployment"]
    assert local_gate_g["order2_authorization"]["address"] == checkpoint["deployed_addresses"]["authorization"]
    assert local_gate_g["order2_authorization"]["constructor_mandates_address"] == checkpoint["deployed_addresses"]["mandates"]
    assert local_gate_g["order2_authorization"]["mandates_binding"] is True

    local_gate_f = json.loads(LOCAL_GATE_F_PROOF.read_text(encoding="utf-8"))
    gate_f_checkpoint = manifest["current_source_local_gate_f"]
    assert gate_f_checkpoint["status"] == "CURRENT_SOURCE_LOCAL_GATE_F_CLOSED"
    assert gate_f_checkpoint["evidence"] == "docs/CURRENT_SOURCE_LOCAL_GATE_F_2026-10-02.json"
    assert gate_f_checkpoint["documentation"] == "docs/CURRENT_SOURCE_LOCAL_GATE_F_2026-10-02.md"
    assert gate_f_checkpoint["source_commit"] == local_gate_f["repository"]["source_commit"]
    assert gate_f_checkpoint["chain_id"] == 61999
    assert gate_f_checkpoint["validator_count"] == 5
    assert gate_f_checkpoint["genvm_version"] == "v0.2.16"
    assert gate_f_checkpoint["source_hashes"] == {
        "covenant_authorization.py": sha256(AUTHORIZATION),
        "covenant_mandates.py": sha256(MANDATES),
    }
    assert gate_f_checkpoint["deployed_addresses"] == {
        "mandates": local_gate_f["deployments"]["mandates"]["address"],
        "authorization": local_gate_f["deployments"]["authorization"]["address"],
    }
    assert local_gate_f["schema"] == "covenant-current-source-local-gate-f-v1"
    assert local_gate_f["status"] == "GATE_F_CLOSED_LOCAL_ONLY"
    assert local_gate_f["source"]["covenant_mandates.py"]["sha256"] == sha256(MANDATES)
    assert local_gate_f["source"]["covenant_authorization.py"]["sha256"] == sha256(AUTHORIZATION)
    assert local_gate_f["deployments"]["authorization"]["mandates_binding"] is True
    assert local_gate_f["cases"]["approval_and_receipt"]["terminal_state"] == "AUTHORIZED"
    assert local_gate_f["cases"]["independent_rejection"]["terminal_state"] == "DENIED"
    assert local_gate_f["cases"]["repair_replacement"]["repaired_state"] == "AUTHORIZED"
    assert local_gate_f["cases"]["source_failure_repair"]["terminal_state"] == "AUTHORIZED"
    assert local_gate_f["cases"]["restart_recovery"]["same_original_transaction_finalized"] is True
    assert local_gate_f["cases"]["restart_recovery"]["additional_submission_count"] == 0
    assert local_gate_f["cases"]["restart_recovery"]["automatic_resend_or_replacement"] is False
    assert local_gate_f["cases"]["expiry"]["terminal_state"] == "EXPIRED"
    assert local_gate_f["cases"]["receipt_consumption"]["receipt_consumed_once"] is True
    assert local_gate_f["cases"]["receipt_consumption"]["wrong_consumer_rejected"] is True
    assert local_gate_f["cases"]["receipt_consumption"]["mutated_action_intent_rejected"] is True
    assert local_gate_f["cases"]["receipt_consumption"]["replay_rejected"] is True
    assert local_gate_f["transaction_policy"] == {
        "all_transactions_submitted_once": True,
        "automatic_resend_or_replacement": False,
        "raw_request_response_persisted_before_decode": True,
        "finality_required": True,
    }
    assert gate_f_checkpoint["authorization_mandates_binding"] is True
    assert gate_f_checkpoint["behavioral_cases"] == {
        "approval": "AUTHORIZED",
        "independent_rejection": "DENIED",
        "repair_replacement": "AUTHORIZED",
        "source_failure_repair": "AUTHORIZED",
        "restart_recovery": "AUTHORIZED",
        "expiry": "EXPIRED",
        "receipt_consumption": "CONSUMED",
        "wrong_consumer_rejection": True,
        "mutated_action_intent_rejection": True,
        "replay_rejection": True,
    }
    assert gate_f_checkpoint["transaction_policy"] == local_gate_f["transaction_policy"]
    assert gate_f_checkpoint["proof_boundary"]["current_source_local_behavioral_gate_f_complete"] is True
    assert gate_f_checkpoint["proof_boundary"]["current_source_bradbury_behavioral_gate_i_complete"] is False
    assert gate_f_checkpoint["proof_boundary"]["current_source_redirect_provenance"] is False
    assert gate_f_checkpoint["proof_boundary"]["target_network_runtime_provenance"] is False
    assert gate_f_checkpoint["proof_boundary"]["gate_j_complete"] is False
    assert gate_f_checkpoint["proof_boundary"]["production_or_bradbury_release"] is False
    assert local_gate_f["boundary"]["current_source_local_behavioral_gate_f_complete"] is True
    assert local_gate_f["boundary"]["current_source_bradbury_behavioral_gate_i_complete"] is False
    assert local_gate_f["boundary"]["effective_origin_proven"] is False
    assert local_gate_f["boundary"]["target_network_runtime_provenance"] is False
    assert local_gate_f["boundary"]["gate_j_complete"] is False
    assert local_gate_f["boundary"]["production_or_bradbury_release"] is False

    current_proof = json.loads(CURRENT_PROOF.read_text(encoding="utf-8"))
    current_bradbury = json.loads(CURRENT_BRADBURY_PROOF.read_text(encoding="utf-8"))
    current_redirect = json.loads(CURRENT_REDIRECT_PROOF.read_text(encoding="utf-8"))
    current_consensus = json.loads(CURRENT_CONSENSUS_PROOF.read_text(encoding="utf-8"))
    fresh_evaluation = json.loads(FRESH_EVALUATION_PROOF.read_text(encoding="utf-8"))
    assert current_proof["status"] == "HISTORICAL_PRE_COMPACT_SOURCE_LOCAL_RUNTIME_CLOSURE"
    assert current_proof["proof_boundary"]["current_source_deployment_parity"] is False
    assert current_proof["proof_boundary"]["production_or_bradbury_release"] is False
    assert current_bradbury["source_hashes"]["contracts/covenant_mandates.py"] == sha256(MANDATES)
    assert current_bradbury["source_hashes"]["contracts/covenant_authorization.py"] == sha256(AUTHORIZATION)
    assert current_bradbury["deployments"]["mandates"]["source_parity"] is True
    assert current_bradbury["deployments"]["authorization"]["source_parity"] is True
    assert current_bradbury["deployments"]["authorization"]["address"] == current["deployed_addresses"]["authorization"]
    assert current_bradbury["behavioral_evidence_source_hash"] == "306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c1"
    assert current_bradbury["behavioral_evidence_deployment_address"] == "0x8c1c7169756287a30bceeb28caee4991b5566076"
    assert current_bradbury["behavioral_evidence_matches_current_deployment"] is False
    assert current_bradbury["configuration"]["authorization_mandates_binding"] is True
    assert current_bradbury["behavioral_proofs"]["approval_and_consumption"]["terminal_state"] == "CONSUMED"
    assert current_bradbury["behavioral_proofs"]["independent_rejection"]["terminal_state"] == "DENIED"
    repaired = current_bradbury["behavioral_proofs"]["repair_replacement"]
    assert repaired["replacement_status"] == "FINALIZED"
    assert repaired["evaluation_status"] == "FINALIZED"
    assert repaired["terminal_state"] == "AUTHORIZED"
    assert repaired["evidence_revision"] == 1
    assert repaired["repair_deadline_unchanged"] is True
    assert repaired["validator_votes"] == "AQQBAQE="
    assert repaired["validator_votes_decoded"] == [1, 4, 1, 1, 1]
    assert repaired["validator_dissenting_index"] == 1
    assert repaired["validator_dissenting_address"] == "0x9d998ad7c7f9cc448a4dbdf49edd7cadbe3d57b6"
    assert repaired["validator_result_hashes_equal"] is False
    assert repaired["unanimity_gate_blocker"] is False
    assert repaired["validator_dissent_preserved"] is True
    assert repaired["tribunal_handling"] == "separate_from_transaction_outcome"
    assert current_consensus["transaction_id"] == repaired["evaluate_internal_transaction"]
    assert current_consensus["validator_votes_decoded"] == repaired["validator_votes_decoded"]
    assert current_consensus["validator_result_hashes_equal"] is False
    assert_protocol_success(current_consensus, "repaired evaluation")
    assert current_consensus["release_interpretation"]["unanimity_gate_blocker"] is False
    assert current_consensus["release_interpretation"]["project_gate_i_blocker"] is True
    assert fresh_evaluation["evaluation_transaction_id"] == "0x1c7bac1e7b42545425c17bfe76b36cfddf01d6ae4c68abac7978865af7b0031c"
    assert fresh_evaluation["evaluation"]["status"] == "FINALIZED"
    assert fresh_evaluation["evaluation"]["consensus_result"] == "AGREE"
    assert fresh_evaluation["evaluation"]["execution_result"] == "FINISHED_WITH_RETURN"
    assert fresh_evaluation["evaluation"]["terminal_state"] == "AUTHORIZED"
    assert fresh_evaluation["evaluation"]["receipt_id"] == "0x3fd417b1bac107e2204d9256e9c9889bc7cd61fe4eb7d4d20ccb0e8b7260635e"
    assert fresh_evaluation["evaluation"]["validator_votes_decoded"] == [1, 3, 4, 1, 1]
    assert fresh_evaluation["evaluation"]["validator_vote_names"] == ["AGREE", "TIMEOUT", "DETERMINISTIC_VIOLATION", "AGREE", "AGREE"]
    assert fresh_evaluation["evaluation"]["validator_result_hashes_equal"] is False
    assert_protocol_success(fresh_evaluation["evaluation"], "fresh predecessor evaluation")
    assert fresh_evaluation["evaluation"]["unanimity_gate_blocker"] is False
    assert fresh_evaluation["evaluation"]["validator_dissent_preserved"] is True
    assert fresh_evaluation["evaluation"]["tribunal_handling"] == "separate_from_transaction_outcome"
    assert fresh_evaluation["evaluation"]["project_gate_i_blocker"] is True
    assert fresh_evaluation["source_hash"] == "306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c1"
    assert fresh_evaluation["deployment_address"] == "0x8c1c7169756287a30bceeb28caee4991b5566076"
    assert fresh_evaluation["proven_against_current_deployment"] is False
    fresh_proof = current_bradbury["behavioral_proofs"]["fresh_predecessor_source_evaluation"]
    assert fresh_proof["evaluate_internal_transaction"] == fresh_evaluation["evaluation_transaction_id"]
    assert fresh_proof["terminal_state"] == "AUTHORIZED"
    assert fresh_proof["validator_votes_decoded"] == fresh_evaluation["evaluation"]["validator_votes_decoded"]
    assert fresh_proof["validator_result_hashes_equal"] is False
    assert fresh_proof["unanimity_gate_blocker"] is False
    assert fresh_proof["validator_dissent_preserved"] is True
    assert fresh_proof["source_hash"] == fresh_evaluation["source_hash"]
    assert fresh_proof["deployment_address"] == fresh_evaluation["deployment_address"]
    assert fresh_proof["proven_against_current_deployment"] is False
    assert manifest["current_bradbury_live_proof"]["behavioral_gate_i_complete"] is False
    assert manifest["current_bradbury_live_proof"]["protocol_consensus"]["acceptance_rule"] == "MAJORITY"
    assert manifest["current_bradbury_live_proof"]["protocol_consensus"]["unanimity_gate_blocker"] is False
    assert manifest["current_bradbury_live_proof"]["fresh_predecessor_source_evaluation"]["terminal_state"] == "AUTHORIZED"
    assert manifest["current_bradbury_live_proof"]["fresh_predecessor_source_evaluation"]["validator_result_hashes_equal"] is False
    if manifest["status"] == "RELEASED" or production["status"] == "RELEASED":
        raise AssertionError("release status cannot be enabled while Gate I/J remain open")
    boundary = current_bradbury["proof_boundary"]
    assert boundary["current_repair_replacement_proven"] is False
    assert boundary["current_timeout_recovery_proven"] is False
    assert boundary["current_replay_rejection_proven"] is False
    assert boundary["current_wrong_consumer_rejection_proven"] is False
    assert current_bradbury["redirect_effective_origin"]["status"] == "UNPROVEN_BRADBURY_EFFECTIVE_ORIGIN"
    assert current_bradbury["proof_boundary"]["production_or_bradbury_release"] is False
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
    remediation = manifest["runtime_remediation_candidate"]
    assert remediation["status"] == "PATCH_VERIFIED_LOCAL_NOT_DEPLOYED"
    assert remediation["upstream_commit"] == "619dfad4bae51c191ef66c3e8cac6ed996961858"
    assert remediation["upstream_tag"] == "v0.6.0-rc8"
    assert remediation["patch"] == (
        "runtime/patches/genvm-v0.6.0-rc8-configurable-web-redirects.patch"
    )
    assert remediation["patch_sha256"] == sha256(RUNTIME_REMEDIATION_PATCH)
    assert remediation["configuration"] == {
        "key": "follow_redirects",
        "default": True,
        "covenant_required_value": False,
    }
    assert remediation["scope"]["filtered_web_requests_configurable"] is True
    assert remediation["scope"]["allowlisted_web_requests_configurable"] is True
    assert remediation["scope"]["signer_client_isolated"] is True
    assert remediation["scope"]["llm_provider_behavior_preserved"] is True
    assert remediation["scope"]["contract_features_removed"] is False
    assert remediation["local_verification"]["clean_checkout_apply_check"] is True
    assert remediation["local_verification"]["cargo_fmt_check"] is True
    assert remediation["local_verification"]["redirect_tests_passed"] == 3
    assert remediation["local_verification"]["redirect_tests_failed"] == 0
    assert remediation["local_verification"]["providers_test_binary_compiled"] is True
    assert remediation["local_verification"]["signing_server_test_binary_compiled"] is True
    assert remediation["local_verification"]["full_test_suite_claimed"] is False
    studio_next = json.loads(STUDIO_NEXT_PREFLIGHT.read_text(encoding="utf-8"))
    assert studio_next["endpoint"] == "https://studio-dev.genlayer.com/api"
    assert studio_next["signing_performed"] is False
    assert studio_next["submission_performed"] is False
    assert studio_next["rpc"]["eth_chainId"] == {"hex": "0xf22d", "decimal": 61997}
    assert studio_next["rpc"]["sim_countValidators"] == 16
    assert studio_next["tooling"]["inspected_rc_cli"] == "0.40.0-rc.3"
    assert studio_next["tooling"]["inspected_rc_has_studio_dev_profile"] is True
    assert studio_next["runtime_redirect_behavior_proven"] is False
    assert remediation["studio_next"]["evidence"] == (
        "docs/STUDIO_NEXT_READ_ONLY_PREFLIGHT_2026-10-02.json"
    )
    assert remediation["studio_next"]["chain_id"] == 61997
    assert remediation["studio_next"]["validator_count"] == 16
    assert remediation["studio_next"]["patched_runtime_deployed"] is False
    assert remediation["studio_next"]["redirect_behavior_proven"] is False
    assert remediation["bradbury"]["patched_runtime_deployed"] is False
    assert remediation["bradbury"]["redirect_behavior_proven"] is False

    result = {
        "status": "PASS",
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "source_hashes": {
            "covenant_mandates.py": sha256(MANDATES),
            "covenant_authorization.py": sha256(AUTHORIZATION),
        },
        "runtime_patch_sha256": sha256(RUNTIME_PATCH),
        "runtime_remediation_patch_sha256": sha256(RUNTIME_REMEDIATION_PATCH),
        "runtime_binary_sha256": manifest["runtime_provenance"]["runtime_binary_sha256"],
        "studio_next_chain_id": studio_next["rpc"]["eth_chainId"]["decimal"],
        "studio_next_validator_count": studio_next["rpc"]["sim_countValidators"],
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
