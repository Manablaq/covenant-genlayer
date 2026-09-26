import hashlib
import importlib.metadata as metadata
import os
import re
import sys
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(os.environ.get("COVENANT_REPO", Path(__file__).resolve().parents[1])).resolve()
MANDATES = REPO / "contracts" / "covenant_mandates.py"
AUTHORIZATION = REPO / "contracts" / "covenant_authorization.py"

EXPECTED_MANDATES_SHA = "c921da40757968260e7acb0555db93d2ba4c3ca9ce81760ca51f6087d494333f"
EXPECTED_AUTH_SHA = "09e5f5493f02d94fad1601128330a4a1572a87a833f6278f5133c2d81ee5faf2"
SDK = "v0.2.16"
EXPECTED_SDK_FRAGMENT = "/extracted/v0.2.16/py-lib-genlayer-std/11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v/genlayer/"

EXPECTED_GENLAYER_TEST_VERSION = "0.29.2"
EXPECTED_SDK_LOADER_SHA = "cc2de8fe9396e07c8edb4733c73c5fb0f5ab83b5e18dfd91c9263728b285d21e"
EXPECTED_DIRECT_LOADER_SHA = "4e3582b5bfc34650de1786b02c5ea40ffecdf6da33930d0e15baad2406766ab9"
EXPECTED_GLSIM_ENGINE_SHA = "b6c3fb9f77e43e72d4d6b2142c53972c7f1fd4d68da80d391c933dbec5b6c54e"

# Installed genlayer-test 0.29.2 chooses the newest cached GenVM whenever
# setup_sdk_paths(..., version=None) is used. SimEngine.deploy() reaches that
# exact path. Apply a process-local test shim mapping only None -> v0.2.16.
# The installed package itself is never modified.
assert metadata.version("genlayer-test") == EXPECTED_GENLAYER_TEST_VERSION
assert "genlayer" not in sys.modules
assert not any("gltest-direct" in p for p in sys.path)

from gltest.direct import sdk_loader
from gltest.direct import loader as direct_loader
from glsim import engine as glsim_engine

assert "genlayer" not in sys.modules

def _file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

assert _file_sha(sdk_loader.__file__) == EXPECTED_SDK_LOADER_SHA
assert _file_sha(direct_loader.__file__) == EXPECTED_DIRECT_LOADER_SHA
assert _file_sha(glsim_engine.__file__) == EXPECTED_GLSIM_ENGINE_SHA

_ORIGINAL_SETUP_SDK_PATHS = sdk_loader.setup_sdk_paths
_PIN_SHIM_EVENTS = []

def _pinned_setup_sdk_paths(contract_path=None, version=None):
    effective_version = SDK if version is None else version
    if effective_version != SDK:
        raise RuntimeError(
            f"Covenant Gate D refuses GenVM version {effective_version!r}; expected {SDK!r}"
        )

    result = _ORIGINAL_SETUP_SDK_PATHS(contract_path, effective_version)
    _PIN_SHIM_EVENTS.append(
        (
            str(contract_path) if contract_path is not None else None,
            version,
            effective_version,
            tuple(str(p) for p in result),
        )
    )
    print(
        "GLSIM_PIN_SHIM_SETUP"
        + "|REQUESTED_VERSION=" + repr(version)
        + "|EFFECTIVE_VERSION=" + repr(effective_version)
        + "|CONTRACT=" + repr(str(contract_path) if contract_path is not None else None)
    )
    return result

sdk_loader.setup_sdk_paths = _pinned_setup_sdk_paths

# Direct Mode's generic public-method proxy calldata roundtrip decodes nested
# dataclasses to ordinary dicts. Real GenLayer supports dataclasses as public
# method parameters, so this test-local adapter restores only the exact
# EvidenceInput shape after the generic roundtrip. It does not alter Covenant
# or the installed genlayer-test package.
_ORIGINAL_CALLDATA_ROUNDTRIP_ARGS = direct_loader._calldata_roundtrip_args
_ACTIVE_EVIDENCE_INPUT = None
_ACTIVE_EVIDENCE_FIELDS = None
_TYPED_ADAPTER_REHYDRATION_COUNT = 0

def _rehydrate_evidence_input(value):
    global _TYPED_ADAPTER_REHYDRATION_COUNT

    cls = _ACTIVE_EVIDENCE_INPUT
    fields = _ACTIVE_EVIDENCE_FIELDS

    if isinstance(value, list):
        return [_rehydrate_evidence_input(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_rehydrate_evidence_input(item) for item in value)

    if (
        cls is not None
        and fields is not None
        and isinstance(value, dict)
        and frozenset(value.keys()) == fields
    ):
        _TYPED_ADAPTER_REHYDRATION_COUNT += 1
        return cls(**value)

    return value

def _typed_calldata_roundtrip_args(args, kwargs):
    decoded_args, decoded_kwargs = _ORIGINAL_CALLDATA_ROUNDTRIP_ARGS(args, kwargs)
    return (
        tuple(_rehydrate_evidence_input(value) for value in decoded_args),
        {
            key: _rehydrate_evidence_input(value)
            for key, value in decoded_kwargs.items()
        },
    )

direct_loader._calldata_roundtrip_args = _typed_calldata_roundtrip_args

print("GLSIM_TYPED_CALLDATA_ADAPTER=ENABLED")
print("GLSIM_TYPED_CALLDATA_ADAPTER_SCOPE=EXACT_EVIDENCEINPUT_FIELD_SHAPE")
print("GLSIM_TYPED_CALLDATA_NEGATIVE_CONTROL_PREFLIGHT_R1=PASS")
print("GLSIM_PREDEPLOY_GENLAYER_IMPORTED=NO")
print("GLSIM_PREDEPLOY_SDK_PATH_INJECTED=NO")
print("GLSIM_TEST_LOCAL_SETUP_SDK_PIN_SHIM=ENABLED")
print("GLSIM_INSTALLED_PACKAGE_MODIFIED=NO")
print("GLSIM_LOCAL_SDK_LOADER_SHA256=" + EXPECTED_SDK_LOADER_SHA)
print("GLSIM_LOCAL_DIRECT_LOADER_SHA256=" + EXPECTED_DIRECT_LOADER_SHA)
print("GLSIM_LOCAL_ENGINE_SHA256=" + EXPECTED_GLSIM_ENGINE_SHA)

# strict_mocks emits RuntimeWarning for any registered mock that is never hit.
# Convert those warnings to failures so the mocks are evidence, not decoration.
warnings.filterwarnings("error", category=RuntimeWarning)

NOW = 1893456000  # 2030-01-01T00:00:00Z
NOW_ISO = "2030-01-01T00:00:00Z"
TARGET = b"contract://merchant/42"
RECIPIENT = bytes.fromhex("66" * 20)
PAYLOAD = b'{"invoice":"INV-2030-0001"}'

STATE_PENDING = 1
STATE_REPAIR_REQUIRED = 2
STATE_AUTHORIZED = 3
STATE_DENIED = 4
STATE_EXPIRED = 5
STATE_CONSUMED = 6

REPAIR_NONE = 0
REPAIR_SOURCE_UNAVAILABLE = 1
REPAIR_SOURCE_MALFORMED = 3
REPAIR_EVIDENCE_INTEGRITY_MISMATCH = 4
REPAIR_EVIDENCE_STALE = 5
REPAIR_EVIDENCE_AUTHORITY_INVALID = 6
REPAIR_EVIDENCE_REFERENCE_INVALID = 7
REPAIR_CORROBORATION_MISSING = 8
REPAIR_HUMAN_APPROVAL_MISSING = 9


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_authorization_source = AUTHORIZATION.read_text(encoding="utf-8")
assert "def _registry(" not in _authorization_source
assert _authorization_source.count("    def _require_registry_binding(self) -> None:\n") == 1
assert "registry = CovenantMandatesIface(self.mandates_address)" in _authorization_source
print("GLSIM_PRODUCTION_R2_REGISTRY_HELPER_SHAPE=PASS")


def new_context(*, human_mode=0):
    assert sha(MANDATES) == EXPECTED_MANDATES_SHA
    assert sha(AUTHORIZATION) == EXPECTED_AUTH_SHA
    assert os.environ.get("GENVM_VERSION") == SDK
    assert metadata.version("genlayer-test") == EXPECTED_GENLAYER_TEST_VERSION
    assert sdk_loader.setup_sdk_paths is _pinned_setup_sdk_paths
    assert "genlayer" not in sys.modules
    assert not any("/v0.6.0-rc5/" in p for p in sys.path)

    print("GLSIM_NEW_CONTEXT_BEGIN")

    from glsim.engine import SimEngine
    from glsim.state import StateStore

    print("GLSIM_ENGINE_IMPORT=PASS")
    assert "genlayer" not in sys.modules

    state = StateStore(chain_id=4221, seed=f"covenant-tests-{human_mode}")
    engine = SimEngine(state)
    engine.vm._datetime = NOW_ISO
    engine.vm.strict_mocks = True
    engine.vm.check_pickling = True
    engine.activate()

    print("GLSIM_ENGINE_ACTIVATE=PASS")

    mandates_address, _ = engine.deploy(str(MANDATES))
    print("GLSIM_MANDATES_DEPLOY=PASS")

    import genlayer as active_genlayer
    active_sdk_file = str(Path(active_genlayer.__file__).resolve())
    print("GLSIM_CONTEXT_ACTIVE_GENLAYER_SDK_FILE=" + active_sdk_file)
    assert EXPECTED_SDK_FRAGMENT in active_sdk_file

    from genlayer import u256
    from genlayer.py.types import Address

    issuer = Address(bytes.fromhex("22" * 20))
    agent = Address(bytes.fromhex("44" * 20))
    consumer = Address(bytes.fromhex("55" * 20))
    human = Address(bytes.fromhex("77" * 20))
    zero = Address(bytes(20))

    authority_ids = [
        hashlib.sha256(b"covenant-authority-a").digest(),
        hashlib.sha256(b"covenant-authority-b").digest(),
        hashlib.sha256(b"covenant-authority-c").digest(),
    ]
    publishers = ["Authority A", "Authority B", "Authority C"]
    prefixes = [
        "https://a.example/evidence/",
        "https://b.example/evidence/",
        "https://c.example/evidence/",
    ]

    create_args = [
        u256(9),
        u256(1_000_000),
        u256(3600),
        u256(600),
        [hashlib.sha256(b"PAYMENT").digest()],
        [hashlib.sha256(TARGET).digest()],
        [hashlib.sha256(RECIPIENT).digest()],
        "AUTHORIZE only when verified evidence proves the exact payment is permitted.",
        u256(1),
        u256(2),
        u256(3600),
        u256(900),
        u256(1800),
        u256(8),
        [u256(1), u256(2), u256(2)],
        authority_ids,
        publishers,
        prefixes,
        u256(human_mode),
        human if human_mode == 1 else zero,
        u256(2),
    ]
    mandate_id = engine.call_method(
        mandates_address,
        "create_mandate",
        args=create_args,
        sender=issuer.as_hex,
    )
    commitment = engine.call_method(
        mandates_address,
        "get_mandate_commitment",
        args=[mandate_id, u256(1)],
    )

    mandates_obj = Address(bytes.fromhex(mandates_address[2:]))
    authorization_address, _ = engine.deploy(
        str(AUTHORIZATION),
        args=[mandates_obj],
    )
    print("GLSIM_AUTHORIZATION_DEPLOY=PASS")

    import genlayer as post_authorization_genlayer
    post_auth_sdk_file = str(Path(post_authorization_genlayer.__file__).resolve())
    print("GLSIM_POST_AUTHORIZATION_ACTIVE_GENLAYER_SDK_FILE=" + post_auth_sdk_file)
    assert EXPECTED_SDK_FRAGMENT in post_auth_sdk_file
    assert not any("/v0.6.0-rc5/" in p for p in sys.path)
    assert _PIN_SHIM_EVENTS
    assert _PIN_SHIM_EVENTS[-1][2] == SDK

    auth_cls = engine._classes[authorization_address.lower()]
    auth_module = sys.modules[auth_cls.__module__]
    EvidenceInput = auth_module.EvidenceInput

    global _ACTIVE_EVIDENCE_INPUT, _ACTIVE_EVIDENCE_FIELDS
    _ACTIVE_EVIDENCE_INPUT = EvidenceInput
    _ACTIVE_EVIDENCE_FIELDS = frozenset(EvidenceInput.__dataclass_fields__.keys())

    expected_fields = frozenset(
        {
            "authority_id",
            "role",
            "publisher_name",
            "record_id",
            "immutable_reference",
            "version",
            "content_digest",
            "published_at",
            "observed_at",
            "expires_at",
        }
    )
    assert _ACTIVE_EVIDENCE_FIELDS == expected_fields
    print("GLSIM_TYPED_CALLDATA_ACTIVE_EVIDENCEINPUT=BOUND")

    return SimpleNamespace(
        engine=engine,
        state=state,
        Address=Address,
        u256=u256,
        issuer=issuer,
        agent=agent,
        consumer=consumer,
        human=human,
        authority_ids=authority_ids,
        publishers=publishers,
        prefixes=prefixes,
        mandate_id=mandate_id,
        mandate_version=u256(1),
        mandate_commitment=commitment,
        mandates_address=mandates_address,
        authorization_address=authorization_address,
        EvidenceInput=EvidenceInput,
        auth_module=auth_module,
    )


def close_context(ctx):
    global _ACTIVE_EVIDENCE_INPUT, _ACTIVE_EVIDENCE_FIELDS

    ctx.engine.vm.clear_mocks()
    ctx.engine.deactivate()

    _ACTIVE_EVIDENCE_INPUT = None
    _ACTIVE_EVIDENCE_FIELDS = None

    assert sdk_loader.setup_sdk_paths is _pinned_setup_sdk_paths
    assert direct_loader._calldata_roundtrip_args is _typed_calldata_roundtrip_args
    assert "genlayer" not in sys.modules
    assert not any("/v0.6.0-rc5/" in p for p in sys.path)
    assert not any(".cache/gltest-direct/extracted/" in p for p in sys.path)


def make_evidence(ctx, *, missing_c=False, authority_bad=False, reference_bad=False, stale=False, a_body=None):
    bodies = {
        "a": b"primary evidence confirms exact permitted payment",
        "b": b"independent corroboration B confirms exact permitted payment",
        "c": b"independent corroboration C confirms exact permitted payment",
    }
    if a_body is not None:
        bodies["a"] = a_body

    published = NOW - 100
    observed = NOW - 10
    expires = NOW + 1800
    if stale:
        published = NOW - 4000

    a_id = bytes.fromhex("ff" * 32) if authority_bad else ctx.authority_ids[0]
    a_ref = "https://evil.example/evidence/a-1" if reference_bad else ctx.prefixes[0] + "a-1"

    values = [
        ctx.EvidenceInput(
            authority_id=a_id,
            role=ctx.u256(1),
            publisher_name=ctx.publishers[0],
            record_id="A-1",
            immutable_reference=a_ref,
            version="v1",
            content_digest=hashlib.sha256(bodies["a"]).digest(),
            published_at=ctx.u256(published),
            observed_at=ctx.u256(observed),
            expires_at=ctx.u256(expires),
        ),
        ctx.EvidenceInput(
            authority_id=ctx.authority_ids[1],
            role=ctx.u256(2),
            publisher_name=ctx.publishers[1],
            record_id="B-1",
            immutable_reference=ctx.prefixes[1] + "b-1",
            version="v1",
            content_digest=hashlib.sha256(bodies["b"]).digest(),
            published_at=ctx.u256(published),
            observed_at=ctx.u256(observed),
            expires_at=ctx.u256(expires),
        ),
    ]
    if not missing_c:
        values.append(
            ctx.EvidenceInput(
                authority_id=ctx.authority_ids[2],
                role=ctx.u256(2),
                publisher_name=ctx.publishers[2],
                record_id="C-1",
                immutable_reference=ctx.prefixes[2] + "c-1",
                version="v1",
                content_digest=hashlib.sha256(bodies["c"]).digest(),
                published_at=ctx.u256(published),
                observed_at=ctx.u256(observed),
                expires_at=ctx.u256(expires),
            )
        )
    return values, bodies


def create_request(ctx, *, nonce, evidence=None, value=250000, expires_at=NOW + 1800, target=TARGET):
    if evidence is None:
        evidence, _ = make_evidence(ctx)
    return ctx.engine.call_method(
        ctx.authorization_address,
        "create_request",
        args=[
            ctx.agent,
            ctx.mandate_id,
            ctx.mandate_version,
            ctx.mandate_commitment,
            "PAYMENT",
            target,
            RECIPIENT,
            ctx.u256(value),
            PAYLOAD,
            ctx.consumer,
            ctx.u256(nonce),
            ctx.u256(expires_at),
            evidence,
        ],
        sender=ctx.agent.as_hex,
    )


def set_mocks(
    ctx,
    evidence,
    bodies,
    *,
    llm="AUTHORIZE",
    statuses=None,
    body_overrides=None,
    web_limit=None,
):
    ctx.engine.vm.clear_mocks()
    ctx.engine.vm.clear_validators()
    statuses = statuses or {}
    body_overrides = body_overrides or {}

    selected = evidence if web_limit is None else evidence[:web_limit]
    for index, item in enumerate(selected):
        body_key = ("a", "b", "c")[index]
        ctx.engine.vm.mock_web(
            re.escape(item.immutable_reference),
            {
                "status": statuses.get(index, 200),
                "body": body_overrides.get(index, bodies[body_key]),
                "method": "GET",
            },
        )

    if llm is not None:
        ctx.engine.vm.mock_llm(r"COVENANT V1 AUTHORIZATION DECISION", llm)


def state_of(ctx, request_id):
    return int(ctx.engine.call_method(ctx.authorization_address, "get_request_state", args=[request_id]))


def repair_of(ctx, request_id):
    return int(ctx.engine.call_method(ctx.authorization_address, "get_request_repair_reason", args=[request_id]))


def set_time(ctx, iso_value):
    ctx.engine.vm._datetime = iso_value
    ctx.auth_module.gl.message_raw["datetime"] = iso_value


def test_g01_public_binding_and_pending_creation():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx)
        before_rehydration_count = _TYPED_ADAPTER_REHYDRATION_COUNT
        request_id = create_request(ctx, nonce=1, evidence=evidence)
        assert _TYPED_ADAPTER_REHYDRATION_COUNT >= before_rehydration_count + len(evidence)
        print("GLSIM_TYPED_CALLDATA_REHYDRATION_EXERCISED=PASS")
        assert state_of(ctx, request_id) == STATE_PENDING
        assert ctx.engine.call_method(ctx.authorization_address, "request_exists", args=[request_id])
        assert ctx.engine.call_method(
            ctx.authorization_address,
            "is_nonce_used",
            args=[ctx.agent, ctx.u256(1)],
        )
        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_nonce_request_id",
            args=[ctx.agent, ctx.u256(1)],
        ) == request_id
    finally:
        close_context(ctx)


def test_g02_wrong_agent_caller_rejects():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx)
        other = ctx.Address(bytes.fromhex("88" * 20))
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "create_request",
                args=[
                    ctx.agent, ctx.mandate_id, ctx.mandate_version, ctx.mandate_commitment,
                    "PAYMENT", TARGET, RECIPIENT, ctx.u256(1), PAYLOAD, ctx.consumer,
                    ctx.u256(2), ctx.u256(NOW + 1800), evidence,
                ],
                sender=other.as_hex,
            )
    finally:
        close_context(ctx)


def test_g03_nonce_replay_rejects_permanently():
    ctx = new_context()
    try:
        request_id = create_request(ctx, nonce=3)
        assert state_of(ctx, request_id) == STATE_PENDING
        with pytest.raises(Exception):
            create_request(ctx, nonce=3, expires_at=NOW + 1700)
    finally:
        close_context(ctx)


def test_g04_deterministic_policy_violation_is_denied_at_creation():
    ctx = new_context()
    try:
        request_id = create_request(ctx, nonce=4, value=1_000_001)
        assert state_of(ctx, request_id) == STATE_DENIED
        assert repair_of(ctx, request_id) == REPAIR_NONE
    finally:
        close_context(ctx)


def test_g05_missing_corroboration_enters_bounded_repair():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx, missing_c=True)
        request_id = create_request(ctx, nonce=5, evidence=evidence)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_CORROBORATION_MISSING
        deadline = int(ctx.engine.call_method(ctx.authorization_address, "get_request_repair_deadline", args=[request_id]))
        assert deadline == NOW + 600
    finally:
        close_context(ctx)


def test_g06_invalid_authority_enters_repair():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx, authority_bad=True)
        request_id = create_request(ctx, nonce=6, evidence=evidence)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_EVIDENCE_AUTHORITY_INVALID
    finally:
        close_context(ctx)


def test_g07_invalid_reference_enters_repair():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx, reference_bad=True)
        request_id = create_request(ctx, nonce=7, evidence=evidence)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_EVIDENCE_REFERENCE_INVALID
    finally:
        close_context(ctx)


def test_g08_stale_evidence_enters_repair():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx, stale=True)
        request_id = create_request(ctx, nonce=8, evidence=evidence)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_EVIDENCE_STALE
    finally:
        close_context(ctx)


def test_g09_human_approval_is_exact_and_returns_pending():
    ctx = new_context(human_mode=1)
    try:
        request_id = create_request(ctx, nonce=9)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_HUMAN_APPROVAL_MISSING
        subject = ctx.engine.call_method(ctx.authorization_address, "get_request_action_subject", args=[request_id])
        wrong = ctx.Address(bytes.fromhex("88" * 20))
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "submit_human_approval",
                args=[request_id, subject],
                sender=wrong.as_hex,
            )
        ctx.engine.call_method(
            ctx.authorization_address,
            "submit_human_approval",
            args=[request_id, subject],
            sender=ctx.human.as_hex,
        )
        assert state_of(ctx, request_id) == STATE_PENDING
        assert ctx.engine.call_method(ctx.authorization_address, "is_request_human_approved", args=[request_id])
        assert int(ctx.engine.call_method(
            ctx.authorization_address, "get_request_evidence_revision", args=[request_id]
        )) == 0
    finally:
        close_context(ctx)


def test_g10_authorize_validator_agrees_and_receipt_consumes_once():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=10, evidence=evidence)
        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_AUTHORIZED
        assert ctx.engine.vm.run_validator() is True

        receipt = ctx.engine.call_method(ctx.authorization_address, "get_request_receipt_id", args=[request_id])
        intent = ctx.engine.call_method(ctx.authorization_address, "get_request_action_intent", args=[request_id])
        assert len(receipt) == 32

        wrong = ctx.Address(bytes.fromhex("88" * 20))
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "consume_receipt",
                args=[request_id, receipt, intent],
                sender=wrong.as_hex,
            )

        ctx.engine.call_method(
            ctx.authorization_address,
            "consume_receipt",
            args=[request_id, receipt, intent],
            sender=ctx.consumer.as_hex,
        )
        assert state_of(ctx, request_id) == STATE_CONSUMED
        assert ctx.engine.call_method(ctx.authorization_address, "is_receipt_consumed", args=[request_id])
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "consume_receipt",
                args=[request_id, receipt, intent],
                sender=ctx.consumer.as_hex,
            )
    finally:
        close_context(ctx)


def test_g11_semantic_deny_is_terminal_and_validator_agrees():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=11, evidence=evidence)
        set_mocks(ctx, evidence, bodies, llm="DENY")
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_DENIED
        assert ctx.engine.vm.run_validator() is True
        assert ctx.engine.call_method(ctx.authorization_address, "get_request_receipt_id", args=[request_id]) == b""
    finally:
        close_context(ctx)


def test_g12_validator_disagreement_is_detected_exactly():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=12, evidence=evidence)
        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_AUTHORIZED

        ctx.engine.vm.clear_mocks()
        for index, item in enumerate(evidence):
            key = ("a", "b", "c")[index]
            ctx.engine.vm.mock_web(
                re.escape(item.immutable_reference),
                {"status": 200, "body": bodies[key], "method": "GET"},
            )
        ctx.engine.vm.mock_llm(r"COVENANT V1 AUTHORIZATION DECISION", "DENY")
        assert ctx.engine.vm.run_validator() is False
    finally:
        close_context(ctx)


def test_g13_source_unavailable_retry_keeps_revision_and_deadline_fixed():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=13, evidence=evidence)
        set_mocks(ctx, evidence, bodies, statuses={0: 503}, llm=None, web_limit=1)
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_SOURCE_UNAVAILABLE
        rev_before = int(ctx.engine.call_method(ctx.authorization_address, "get_request_evidence_revision", args=[request_id]))
        deadline_before = int(ctx.engine.call_method(ctx.authorization_address, "get_request_repair_deadline", args=[request_id]))

        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(ctx.authorization_address, "retry_source", args=[request_id])
        assert state_of(ctx, request_id) == STATE_AUTHORIZED
        assert int(ctx.engine.call_method(ctx.authorization_address, "get_request_evidence_revision", args=[request_id])) == rev_before
        assert int(ctx.engine.call_method(ctx.authorization_address, "get_request_repair_deadline", args=[request_id])) == deadline_before
    finally:
        close_context(ctx)


def test_g14_integrity_mismatch_then_agent_replacement_increments_revision_once():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=14, evidence=evidence)
        set_mocks(ctx, evidence, bodies, body_overrides={0: b"tampered"}, llm=None, web_limit=1)
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_EVIDENCE_INTEGRITY_MISMATCH
        old_intent = ctx.engine.call_method(ctx.authorization_address, "get_request_action_intent", args=[request_id])

        replacement, _ = make_evidence(ctx, a_body=b"replacement primary evidence")
        ctx.engine.call_method(
            ctx.authorization_address,
            "replace_evidence",
            args=[request_id, replacement],
            sender=ctx.agent.as_hex,
        )
        assert state_of(ctx, request_id) == STATE_PENDING
        assert int(ctx.engine.call_method(
            ctx.authorization_address, "get_request_evidence_revision", args=[request_id]
        )) == 1
        new_intent = ctx.engine.call_method(ctx.authorization_address, "get_request_action_intent", args=[request_id])
        assert new_intent != old_intent
    finally:
        close_context(ctx)


def test_g15_strict_utf8_failure_is_repairable_malformed_source():
    ctx = new_context()
    try:
        bad_body = b"\xff\xfe\xfd"
        evidence, bodies = make_evidence(ctx, a_body=bad_body)
        request_id = create_request(ctx, nonce=15, evidence=evidence)
        set_mocks(ctx, evidence, bodies, llm=None, web_limit=1)
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        assert repair_of(ctx, request_id) == REPAIR_SOURCE_MALFORMED
    finally:
        close_context(ctx)


def test_g16_deactivation_blocks_new_requests_but_not_existing_request():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=16, evidence=evidence)
        ctx.engine.call_method(
            ctx.mandates_address,
            "set_version_eligible",
            args=[ctx.mandate_id, ctx.mandate_version, False],
            sender=ctx.issuer.as_hex,
        )
        with pytest.raises(Exception):
            create_request(ctx, nonce=17)

        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_AUTHORIZED
    finally:
        close_context(ctx)


def test_g17_repair_deadline_equality_materializes_expired():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx, missing_c=True)
        request_id = create_request(ctx, nonce=18, evidence=evidence, expires_at=NOW + 300)
        assert state_of(ctx, request_id) == STATE_REPAIR_REQUIRED
        deadline = int(ctx.engine.call_method(ctx.authorization_address, "get_request_repair_deadline", args=[request_id]))
        assert deadline == NOW + 300
        set_time(ctx, "2030-01-01T00:05:00Z")
        ctx.engine.call_method(ctx.authorization_address, "expire_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_EXPIRED
    finally:
        close_context(ctx)


def test_g18_authorized_receipt_cannot_be_consumed_at_expiry_equality():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=19, evidence=evidence, expires_at=NOW + 300)
        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE")
        ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_AUTHORIZED
        receipt = ctx.engine.call_method(ctx.authorization_address, "get_request_receipt_id", args=[request_id])
        intent = ctx.engine.call_method(ctx.authorization_address, "get_request_action_intent", args=[request_id])
        set_time(ctx, "2030-01-01T00:05:00Z")
        with pytest.raises(Exception):
            ctx.engine.call_method(
                ctx.authorization_address,
                "consume_receipt",
                args=[request_id, receipt, intent],
                sender=ctx.consumer.as_hex,
            )
        ctx.engine.call_method(ctx.authorization_address, "expire_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_EXPIRED
    finally:
        close_context(ctx)


def test_g19_duplicate_evidence_commitment_rejects_before_nonce_reservation():
    ctx = new_context()
    try:
        evidence, _ = make_evidence(ctx)
        duplicate = [evidence[0], evidence[0]]
        with pytest.raises(Exception):
            create_request(ctx, nonce=20, evidence=duplicate)
        assert not ctx.engine.call_method(
            ctx.authorization_address,
            "is_nonce_used",
            args=[ctx.agent, ctx.u256(20)],
        )
    finally:
        close_context(ctx)


def test_g20_malformed_semantic_output_does_not_authorize():
    ctx = new_context()
    try:
        evidence, bodies = make_evidence(ctx)
        request_id = create_request(ctx, nonce=21, evidence=evidence)
        set_mocks(ctx, evidence, bodies, llm="AUTHORIZE because it is fine")
        with pytest.raises(Exception):
            ctx.engine.call_method(ctx.authorization_address, "evaluate_request", args=[request_id])
        assert state_of(ctx, request_id) == STATE_PENDING
    finally:
        close_context(ctx)
