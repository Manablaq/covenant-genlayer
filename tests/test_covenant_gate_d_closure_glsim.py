import hashlib
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ["COVENANT_REPO"]).resolve()
TESTS = REPO / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

BASE_TEST = TESTS / "test_covenant_authorization_glsim.py"
EXPECTED_BASE_TEST_SHA = "eaa9fef2af837fd1e442d9f29b194d85a677385ea4c1f082063c26dba6968aa5"

assert hashlib.sha256(BASE_TEST.read_bytes()).hexdigest() == EXPECTED_BASE_TEST_SHA

import test_covenant_authorization_glsim as base

assert base.SDK == "v0.2.16"
assert base.sdk_loader.setup_sdk_paths is base._pinned_setup_sdk_paths
assert base.direct_loader._calldata_roundtrip_args is base._typed_calldata_roundtrip_args


def _force_clear_mock_state(vm):
    vm._web_mocks.clear()
    vm._llm_mocks.clear()
    vm._web_mocks_hit.clear()
    vm._llm_mocks_hit.clear()


def _safe_close(ctx):
    active_test_exception = sys.exc_info()[0] is not None
    strict_cleanup_error = None

    try:
        ctx.engine.vm.clear_mocks()
    except BaseException as exc:
        strict_cleanup_error = exc
        _force_clear_mock_state(ctx.engine.vm)

    try:
        ctx.engine.vm.clear_validators()
        ctx.engine.deactivate()
    finally:
        base._ACTIVE_EVIDENCE_INPUT = None
        base._ACTIVE_EVIDENCE_FIELDS = None

    assert base.sdk_loader.setup_sdk_paths is base._pinned_setup_sdk_paths
    assert base.direct_loader._calldata_roundtrip_args is base._typed_calldata_roundtrip_args
    assert "genlayer" not in sys.modules
    assert not any("/v0.6.0-rc5/" in path for path in sys.path)
    assert not any(".cache/gltest-direct/extracted/" in path for path in sys.path)

    if strict_cleanup_error is not None and not active_test_exception:
        raise strict_cleanup_error


def _register_evidence_and_llm(ctx, evidence, bodies, llm):
    for index, item in enumerate(evidence):
        key = ("a", "b", "c")[index]
        ctx.engine.vm.mock_web(
            re.escape(item.immutable_reference),
            {
                "status": 200,
                "body": bodies[key],
                "method": "GET",
            },
        )
    ctx.engine.vm.mock_llm(
        r"COVENANT V1 AUTHORIZATION DECISION",
        llm,
    )


def _publish_v2_with_changed_max_value(ctx):
    zero = ctx.Address(bytes(20))

    next_args = [
        ctx.u256(2_000_000),
        ctx.u256(3600),
        ctx.u256(600),
        [hashlib.sha256(b"PAYMENT").digest()],
        [hashlib.sha256(base.TARGET).digest()],
        [hashlib.sha256(base.RECIPIENT).digest()],
        "AUTHORIZE only when verified evidence proves the exact payment is permitted.",
        ctx.u256(1),
        ctx.u256(2),
        ctx.u256(3600),
        ctx.u256(900),
        ctx.u256(1800),
        ctx.u256(8),
        [ctx.u256(1), ctx.u256(2), ctx.u256(2)],
        ctx.authority_ids,
        ctx.publishers,
        ctx.prefixes,
        ctx.u256(0),
        zero,
        ctx.u256(2),
    ]

    return ctx.engine.call_method(
        ctx.mandates_address,
        "publish_next_version",
        args=[ctx.mandate_id, *next_args],
        sender=ctx.issuer.as_hex,
    )


def test_c02_forged_leader_consequential_result_is_rejected_by_validator():
    ctx = base.new_context()
    try:
        evidence, bodies = base.make_evidence(ctx)
        request_id = base.create_request(
            ctx,
            nonce=6201,
            evidence=evidence,
        )

        base.set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[request_id],
        )
        assert base.state_of(ctx, request_id) == base.STATE_AUTHORIZED
        assert len(ctx.engine.vm._captured_validators) == 1

        action_intent = ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_intent",
            args=[request_id],
        )
        correct_result = ctx.auth_module._decision_result(
            request_id,
            action_intent,
            ctx.auth_module.DECISION_AUTHORIZE,
            ctx.auth_module.REPAIR_NONE,
        )
        forged_result = ctx.auth_module._decision_result(
            bytes.fromhex("aa" * 32),
            action_intent,
            ctx.auth_module.DECISION_AUTHORIZE,
            ctx.auth_module.REPAIR_NONE,
        )

        assert forged_result != correct_result

        ctx.engine.vm.clear_mocks()
        assert len(ctx.engine.vm._captured_validators) == 1
        _register_evidence_and_llm(ctx, evidence, bodies, "AUTHORIZE")

        assert ctx.engine.vm.run_validator(leader_result=forged_result) is False

        print("FORGED_LEADER_RESULT_OVERRIDE_USED=YES")
        print("FORGED_LEADER_REQUEST_ID_MISMATCH=YES")
        print("VALIDATOR_REJECTED_FORGED_CONSEQUENTIAL_RESULT=PASS")
    finally:
        _safe_close(ctx)


def test_c03_publish_v2_then_frozen_v1_request_remains_valid_after_v1_deactivation():
    ctx = base.new_context()
    try:
        evidence, bodies = base.make_evidence(ctx)

        frozen_v1_request = base.create_request(
            ctx,
            nonce=6202,
            evidence=evidence,
        )
        assert base.state_of(ctx, frozen_v1_request) == base.STATE_PENDING

        v1_commitment_before = ctx.engine.call_method(
            ctx.mandates_address,
            "get_mandate_commitment",
            args=[ctx.mandate_id, ctx.u256(1)],
        )

        version = _publish_v2_with_changed_max_value(ctx)
        assert int(version) == 2
        assert int(
            ctx.engine.call_method(
                ctx.mandates_address,
                "get_latest_version",
                args=[ctx.mandate_id],
            )
        ) == 2

        v1_commitment_after = ctx.engine.call_method(
            ctx.mandates_address,
            "get_mandate_commitment",
            args=[ctx.mandate_id, ctx.u256(1)],
        )
        v2_commitment = ctx.engine.call_method(
            ctx.mandates_address,
            "get_mandate_commitment",
            args=[ctx.mandate_id, ctx.u256(2)],
        )

        assert v1_commitment_after == v1_commitment_before
        assert v2_commitment != v1_commitment_before

        ctx.engine.call_method(
            ctx.mandates_address,
            "set_version_eligible",
            args=[ctx.mandate_id, ctx.u256(1), False],
            sender=ctx.issuer.as_hex,
        )

        assert not ctx.engine.call_method(
            ctx.mandates_address,
            "is_version_eligible",
            args=[ctx.mandate_id, ctx.u256(1)],
        )

        with pytest.raises(Exception):
            base.create_request(
                ctx,
                nonce=6203,
                evidence=evidence,
            )

        base.set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[frozen_v1_request],
        )
        assert base.state_of(ctx, frozen_v1_request) == base.STATE_AUTHORIZED

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_subject",
            args=[frozen_v1_request],
        )
        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_intent",
            args=[frozen_v1_request],
        )

        print("PUBLISHED_V2=PASS")
        print("V1_COMMITMENT_IMMUTABLE_AFTER_V2=PASS")
        print("NEW_V1_REQUEST_BLOCKED_AFTER_DEACTIVATION=PASS")
        print("FROZEN_V1_REQUEST_AUTHORIZED_AFTER_V2_AND_DEACTIVATION=PASS")
    finally:
        _safe_close(ctx)
