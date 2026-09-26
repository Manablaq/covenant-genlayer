import hashlib
import importlib
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1] if "COVENANT_REPO" not in __import__("os").environ else Path(__import__("os").environ["COVENANT_REPO"]).resolve()
TESTS = REPO / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

base = importlib.import_module("test_covenant_authorization_glsim")

EXPECTED_BASE_AUTH_TEST_SHA = "d45b82f3923b8fd30d03b1070251310d887d5a658fb6829ff5c7314bd700d61e"
BASE_TEST_PATH = TESTS / "test_covenant_authorization_glsim.py"

assert hashlib.sha256(BASE_TEST_PATH.read_bytes()).hexdigest() == EXPECTED_BASE_AUTH_TEST_SHA
assert base.SDK == "v0.2.16"
assert base.sdk_loader.setup_sdk_paths is base._pinned_setup_sdk_paths
assert base.direct_loader._calldata_roundtrip_args is base._typed_calldata_roundtrip_args

# Harden the imported V5 GLSim helper for adversarial tests.
# strict_mocks turns unused mocks into RuntimeWarning. If such a warning happens
# while another test exception is already propagating, teardown must still
# deactivate the VM and evict the pinned SDK modules before preserving the
# original failure. This is test-only; production contracts and installed
# genlayer-test files are untouched.
_ORIGINAL_BASE_CLOSE_CONTEXT = base.close_context

def _force_clear_mock_state(vm):
    vm._web_mocks.clear()
    vm._llm_mocks.clear()
    vm._web_mocks_hit.clear()
    vm._llm_mocks_hit.clear()

def _adversarial_safe_close_context(ctx):
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
    assert not any("/v0.6.0-rc5/" in p for p in sys.path)
    assert not any(".cache/gltest-direct/extracted/" in p for p in sys.path)

    if strict_cleanup_error is not None:
        if active_test_exception:
            print(
                "ADVERSARIAL_TEARDOWN_PRESERVED_PRIMARY_EXCEPTION="
                + type(strict_cleanup_error).__name__
            )
        else:
            raise strict_cleanup_error

base.close_context = _adversarial_safe_close_context
print("ADVERSARIAL_EXCEPTION_SAFE_TEARDOWN=ENABLED")

STATE_PENDING = base.STATE_PENDING
STATE_REPAIR_REQUIRED = base.STATE_REPAIR_REQUIRED
STATE_AUTHORIZED = base.STATE_AUTHORIZED
STATE_DENIED = base.STATE_DENIED
STATE_EXPIRED = base.STATE_EXPIRED

REPAIR_NONE = base.REPAIR_NONE
REPAIR_EVIDENCE_STALE = base.REPAIR_EVIDENCE_STALE
REPAIR_EVIDENCE_AUTHORITY_INVALID = base.REPAIR_EVIDENCE_AUTHORITY_INVALID
REPAIR_CORROBORATION_MISSING = base.REPAIR_CORROBORATION_MISSING

NOW = base.NOW
TARGET = base.TARGET
RECIPIENT = base.RECIPIENT
PAYLOAD = base.PAYLOAD


def clone_evidence(ctx, item, **changes):
    values = {
        name: getattr(item, name)
        for name in item.__dataclass_fields__
    }
    values.update(changes)
    return ctx.EvidenceInput(**values)


def create_request_custom(
    ctx,
    *,
    nonce,
    evidence=None,
    agent=None,
    mandate_id=None,
    mandate_version=None,
    mandate_commitment=None,
    action_type="PAYMENT",
    target=TARGET,
    recipient=RECIPIENT,
    value=250000,
    payload=PAYLOAD,
    consumer=None,
    expires_at=NOW + 1800,
    sender=None,
):
    if evidence is None:
        evidence, _ = base.make_evidence(ctx)
    if agent is None:
        agent = ctx.agent
    if mandate_id is None:
        mandate_id = ctx.mandate_id
    if mandate_version is None:
        mandate_version = ctx.mandate_version
    if mandate_commitment is None:
        mandate_commitment = ctx.mandate_commitment
    if consumer is None:
        consumer = ctx.consumer
    if sender is None:
        sender = agent.as_hex

    return ctx.engine.call_method(
        ctx.authorization_address,
        "create_request",
        args=[
            agent,
            mandate_id,
            mandate_version,
            mandate_commitment,
            action_type,
            target,
            recipient,
            ctx.u256(value),
            payload,
            consumer,
            ctx.u256(nonce),
            ctx.u256(expires_at),
            evidence,
        ],
        sender=sender,
    )


def nonce_used(ctx, nonce):
    return bool(
        ctx.engine.call_method(
            ctx.authorization_address,
            "is_nonce_used",
            args=[ctx.agent, ctx.u256(nonce)],
        )
    )


def authorize(ctx, nonce):
    evidence, bodies = base.make_evidence(ctx)
    request_id = create_request_custom(ctx, nonce=nonce, evidence=evidence)
    base.set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
    ctx.engine.call_method(
        ctx.authorization_address,
        "evaluate_request",
        args=[request_id],
    )
    assert base.state_of(ctx, request_id) == STATE_AUTHORIZED
    receipt = ctx.engine.call_method(
        ctx.authorization_address,
        "get_request_receipt_id",
        args=[request_id],
    )
    intent = ctx.engine.call_method(
        ctx.authorization_address,
        "get_request_action_intent",
        args=[request_id],
    )
    return request_id, receipt, intent


def test_a01_publisher_name_mismatch_enters_authority_repair():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        evidence[0] = clone_evidence(
            ctx,
            evidence[0],
            publisher_name="Altered Authority A",
        )
        request_id = create_request_custom(ctx, nonce=101, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_EVIDENCE_AUTHORITY_INVALID
    finally:
        base.close_context(ctx)


def test_a02_role_mismatch_enters_authority_repair():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        evidence[0] = clone_evidence(
            ctx,
            evidence[0],
            role=ctx.u256(2),
        )
        request_id = create_request_custom(ctx, nonce=102, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_EVIDENCE_AUTHORITY_INVALID
    finally:
        base.close_context(ctx)


def test_a03_future_observation_is_stale():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        evidence[0] = clone_evidence(
            ctx,
            evidence[0],
            observed_at=ctx.u256(NOW + 1),
        )
        request_id = create_request_custom(ctx, nonce=103, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_EVIDENCE_STALE
    finally:
        base.close_context(ctx)


def test_a04_evidence_expiry_equality_is_stale():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        evidence[0] = clone_evidence(
            ctx,
            evidence[0],
            expires_at=ctx.u256(NOW),
        )
        request_id = create_request_custom(ctx, nonce=104, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_EVIDENCE_STALE
    finally:
        base.close_context(ctx)


def test_a05_publish_observe_gap_over_bound_is_stale():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        evidence[0] = clone_evidence(
            ctx,
            evidence[0],
            published_at=ctx.u256(NOW - 2000),
            observed_at=ctx.u256(NOW - 100),
        )
        request_id = create_request_custom(ctx, nonce=105, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_EVIDENCE_STALE
    finally:
        base.close_context(ctx)


def test_a06_wrong_mandate_commitment_rejects_before_nonce_reservation():
    ctx = base.new_context()
    try:
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=106,
                mandate_commitment=bytes.fromhex("99" * 32),
            )
        assert not nonce_used(ctx, 106)
    finally:
        base.close_context(ctx)


def test_a07_nonexistent_mandate_version_rejects_before_nonce_reservation():
    ctx = base.new_context()
    try:
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=107,
                mandate_version=ctx.u256(2),
            )
        assert not nonce_used(ctx, 107)
    finally:
        base.close_context(ctx)


def test_a08_unapproved_target_is_denied_at_creation():
    ctx = base.new_context()
    try:
        request_id = create_request_custom(
            ctx,
            nonce=108,
            target=b"contract://attacker/1",
        )
        assert base.state_of(ctx, request_id) == STATE_DENIED
        assert base.repair_of(ctx, request_id) == REPAIR_NONE
    finally:
        base.close_context(ctx)


def test_a09_unapproved_recipient_is_denied_at_creation():
    ctx = base.new_context()
    try:
        request_id = create_request_custom(
            ctx,
            nonce=109,
            recipient=bytes.fromhex("88" * 20),
        )
        assert base.state_of(ctx, request_id) == STATE_DENIED
    finally:
        base.close_context(ctx)


def test_a10_unapproved_action_type_is_denied_at_creation():
    ctx = base.new_context()
    try:
        request_id = create_request_custom(
            ctx,
            nonce=110,
            action_type="TRANSFER",
        )
        assert base.state_of(ctx, request_id) == STATE_DENIED
    finally:
        base.close_context(ctx)


def test_a11_wrong_replacement_caller_preserves_repair_state_and_revision():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx, missing_c=True)
        request_id = create_request_custom(ctx, nonce=111, evidence=evidence)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert base.repair_of(ctx, request_id) == REPAIR_CORROBORATION_MISSING

        revision_before = int(
            ctx.engine.call_method(
                ctx.authorization_address,
                "get_request_evidence_revision",
                args=[request_id],
            )
        )
        replacement, _ = base.make_evidence(
            ctx,
            a_body=b"replacement evidence for wrong-caller test",
        )
        wrong = ctx.Address(bytes.fromhex("88" * 20))
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "replace_evidence",
                args=[request_id, replacement],
                sender=wrong.as_hex,
            )

        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert int(
            ctx.engine.call_method(
                ctx.authorization_address,
                "get_request_evidence_revision",
                args=[request_id],
            )
        ) == revision_before
    finally:
        base.close_context(ctx)


def test_a12_identical_replacement_rejects_without_revision_increment():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx, missing_c=True)
        request_id = create_request_custom(ctx, nonce=112, evidence=evidence)
        old_intent = ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_intent",
            args=[request_id],
        )
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "replace_evidence",
                args=[request_id, evidence],
                sender=ctx.agent.as_hex,
            )
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert int(
            ctx.engine.call_method(
                ctx.authorization_address,
                "get_request_evidence_revision",
                args=[request_id],
            )
        ) == 0
        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_intent",
            args=[request_id],
        ) == old_intent
    finally:
        base.close_context(ctx)


def test_a13_replacement_at_repair_deadline_rejects_then_permissionless_expiry():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx, missing_c=True)
        request_id = create_request_custom(ctx, nonce=113, evidence=evidence)
        deadline = int(
            ctx.engine.call_method(
                ctx.authorization_address,
                "get_request_repair_deadline",
                args=[request_id],
            )
        )
        assert deadline == NOW + 600

        base.set_time(ctx, "2030-01-01T00:10:00Z")
        replacement, _ = base.make_evidence(
            ctx,
            a_body=b"late replacement",
        )
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "replace_evidence",
                args=[request_id, replacement],
                sender=ctx.agent.as_hex,
            )

        permissionless = ctx.Address(bytes.fromhex("88" * 20))
        ctx.engine.call_method(
            ctx.authorization_address,
            "expire_request",
            args=[request_id],
            sender=permissionless.as_hex,
        )
        assert base.state_of(ctx, request_id) == STATE_EXPIRED
    finally:
        base.close_context(ctx)


def test_a14_human_approval_wrong_action_subject_rejects():
    ctx = base.new_context(human_mode=1)
    try:
        request_id = create_request_custom(ctx, nonce=114)
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "submit_human_approval",
                args=[request_id, bytes.fromhex("aa" * 32)],
                sender=ctx.human.as_hex,
            )
        assert base.state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert not ctx.engine.call_method(
            ctx.authorization_address,
            "is_request_human_approved",
            args=[request_id],
        )
    finally:
        base.close_context(ctx)


def test_a15_second_human_approval_attempt_rejects():
    ctx = base.new_context(human_mode=1)
    try:
        request_id = create_request_custom(ctx, nonce=115)
        subject = ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_action_subject",
            args=[request_id],
        )
        ctx.engine.call_method(
            ctx.authorization_address,
            "submit_human_approval",
            args=[request_id, subject],
            sender=ctx.human.as_hex,
        )
        assert base.state_of(ctx, request_id) == STATE_PENDING
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "submit_human_approval",
                args=[request_id, subject],
                sender=ctx.human.as_hex,
            )
        assert base.state_of(ctx, request_id) == STATE_PENDING
    finally:
        base.close_context(ctx)


def test_a16_wrong_receipt_id_cannot_consume_authorization():
    ctx = base.new_context()
    try:
        request_id, receipt, intent = authorize(ctx, 116)
        assert receipt != bytes.fromhex("aa" * 32)
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "consume_receipt",
                args=[request_id, bytes.fromhex("aa" * 32), intent],
                sender=ctx.consumer.as_hex,
            )
        assert base.state_of(ctx, request_id) == STATE_AUTHORIZED
        assert not ctx.engine.call_method(
            ctx.authorization_address,
            "is_receipt_consumed",
            args=[request_id],
        )
    finally:
        base.close_context(ctx)


def test_a17_wrong_action_intent_cannot_consume_authorization():
    ctx = base.new_context()
    try:
        request_id, receipt, intent = authorize(ctx, 117)
        assert intent != bytes.fromhex("bb" * 32)
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "consume_receipt",
                args=[request_id, receipt, bytes.fromhex("bb" * 32)],
                sender=ctx.consumer.as_hex,
            )
        assert base.state_of(ctx, request_id) == STATE_AUTHORIZED
        assert not ctx.engine.call_method(
            ctx.authorization_address,
            "is_receipt_consumed",
            args=[request_id],
        )
    finally:
        base.close_context(ctx)


def test_a18_pending_request_cannot_expire_before_expiry():
    ctx = base.new_context()
    try:
        request_id = create_request_custom(ctx, nonce=118)
        assert base.state_of(ctx, request_id) == STATE_PENDING
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "expire_request",
                args=[request_id],
            )
        assert base.state_of(ctx, request_id) == STATE_PENDING
    finally:
        base.close_context(ctx)


def test_a19_authorized_request_cannot_expire_before_expiry():
    ctx = base.new_context()
    try:
        request_id, _, _ = authorize(ctx, 119)
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "expire_request",
                args=[request_id],
            )
        assert base.state_of(ctx, request_id) == STATE_AUTHORIZED
    finally:
        base.close_context(ctx)


def test_a20_leader_deny_validator_authorize_disagreement_is_detected():
    ctx = base.new_context()
    try:
        evidence, bodies = base.make_evidence(ctx)
        request_id = create_request_custom(ctx, nonce=120, evidence=evidence)

        # Leader sees DENY. base.set_mocks() is safe here because there is no
        # captured validator yet.
        base.set_mocks(ctx, evidence, bodies, llm="DENY")
        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[request_id],
        )
        assert base.state_of(ctx, request_id) == STATE_DENIED
        assert len(ctx.engine.vm._captured_validators) == 1

        # IMPORTANT: preserve the captured validator. The GenLayer Direct Mode
        # docs require swapping mocks with clear_mocks(), then run_validator().
        # Do not call base.set_mocks() here because it calls clear_validators().
        ctx.engine.vm.clear_mocks()
        assert len(ctx.engine.vm._captured_validators) == 1

        for index, item in enumerate(evidence):
            body_key = ("a", "b", "c")[index]
            ctx.engine.vm.mock_web(
                re.escape(item.immutable_reference),
                {
                    "status": 200,
                    "body": bodies[body_key],
                    "method": "GET",
                },
            )
        ctx.engine.vm.mock_llm(
            r"COVENANT V1 AUTHORIZATION DECISION",
            "AUTHORIZE",
        )

        assert ctx.engine.vm.run_validator() is False
        print("A20_CAPTURED_VALIDATOR_PRESERVED=PASS")
        print("A20_DENY_LEADER_AUTHORIZE_VALIDATOR_DISAGREEMENT=PASS")
    finally:
        base.close_context(ctx)


def test_a21_forbidden_bypass_surface_is_absent():
    auth_source = base.AUTHORIZATION.read_text(encoding="utf-8").lower()
    mandates_source = base.MANDATES.read_text(encoding="utf-8").lower()
    forbidden = (
        "force_authorize",
        "admin_approve",
        "set_verdict",
        "skip_consensus",
        "owner_finalize",
    )
    for token in forbidden:
        assert token not in auth_source
        assert token not in mandates_source

    ctx = base.new_context()
    try:
        auth_cls = ctx.engine._classes[ctx.authorization_address.lower()]
        mandates_cls = ctx.engine._classes[ctx.mandates_address.lower()]
        for token in forbidden:
            assert not hasattr(auth_cls, token)
            assert not hasattr(mandates_cls, token)
    finally:
        base.close_context(ctx)


def test_a22_request_lifetime_over_mandate_max_rejects_before_nonce():
    ctx = base.new_context()
    try:
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=122,
                expires_at=NOW + 3601,
            )
        assert not nonce_used(ctx, 122)
    finally:
        base.close_context(ctx)


def test_a23_evidence_count_over_mandate_max_rejects_before_nonce():
    ctx = base.new_context()
    try:
        evidence, _ = base.make_evidence(ctx)
        too_many = [
            evidence[index % len(evidence)]
            for index in range(9)
        ]
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=123,
                evidence=too_many,
            )
        assert not nonce_used(ctx, 123)
    finally:
        base.close_context(ctx)


def test_a24_request_expiry_equality_rejects_before_nonce():
    ctx = base.new_context()
    try:
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=124,
                expires_at=NOW,
            )
        assert not nonce_used(ctx, 124)
    finally:
        base.close_context(ctx)


def test_a25_empty_action_type_rejects_before_nonce():
    ctx = base.new_context()
    try:
        with pytest.raises(Exception):
            create_request_custom(
                ctx,
                nonce=125,
                action_type="",
            )
        assert not nonce_used(ctx, 125)
    finally:
        base.close_context(ctx)
