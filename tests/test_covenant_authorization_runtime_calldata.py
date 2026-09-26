import importlib.util
import os
import pathlib
import re
import sys

import pytest


TEST_MODULE = (
    pathlib.Path(os.environ["COVENANT_REPO"]).resolve()
    / "tests"
    / "test_covenant_authorization_glsim.py"
)

spec = importlib.util.spec_from_file_location(
    "covenant_runtime_faithful_authorization_tests",
    TEST_MODULE,
)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


REQUIRED_KEYS = {
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


def open_runtime_context():
    # The canonical historical harness must be intact before context creation.
    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._typed_calldata_roundtrip_args
    )

    before = (
        module._TYPED_ADAPTER_REHYDRATION_COUNT
    )

    ctx = module.new_context()

    # new_context itself must not need EvidenceInput rehydration.
    assert (
        module._TYPED_ADAPTER_REHYDRATION_COUNT
        == before
    )

    # For this isolated probe only, restore the installed original public-call
    # calldata path. This is the runtime-faithful boundary under test.
    module.direct_loader._calldata_roundtrip_args = (
        module._ORIGINAL_CALLDATA_ROUNDTRIP_ARGS
    )

    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._ORIGINAL_CALLDATA_ROUNDTRIP_ARGS
    )

    return ctx, before


def close_runtime_context(ctx, before):
    # No exact-shape EvidenceInput rehydration may have occurred while the
    # runtime-faithful path was active.
    assert (
        module._TYPED_ADAPTER_REHYDRATION_COUNT
        == before
    )

    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._ORIGINAL_CALLDATA_ROUNDTRIP_ARGS
    )

    # Restore the historical test harness BEFORE invoking its own cleanup,
    # because close_context explicitly certifies that invariant.
    module.direct_loader._calldata_roundtrip_args = (
        module._typed_calldata_roundtrip_args
    )

    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._typed_calldata_roundtrip_args
    )

    module.close_context(ctx)

    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._typed_calldata_roundtrip_args
    )


def assert_runtime_roundtrip_shape(evidence):
    args, kwargs = (
        module._ORIGINAL_CALLDATA_ROUNDTRIP_ARGS(
            (evidence,),
            {},
        )
    )

    assert kwargs == {}
    assert len(args) == 1

    decoded = args[0]

    assert isinstance(decoded, list)
    assert len(decoded) == len(evidence)

    for item in decoded:
        assert isinstance(item, dict)
        assert set(item) == REQUIRED_KEYS

        assert isinstance(
            item["authority_id"],
            bytes,
        )

        assert isinstance(
            item["content_digest"],
            bytes,
        )

        assert len(
            item["authority_id"]
        ) == 32

        assert len(
            item["content_digest"]
        ) == 32

        assert isinstance(
            item["role"],
            int,
        )

        assert not isinstance(
            item["role"],
            bool,
        )

        for key in (
            "publisher_name",
            "record_id",
            "immutable_reference",
            "version",
        ):
            assert isinstance(
                item[key],
                str,
            )

        for key in (
            "published_at",
            "observed_at",
            "expires_at",
        ):
            assert isinstance(
                item[key],
                int,
            )

            assert not isinstance(
                item[key],
                bool,
            )

    return decoded


def assert_runtime_adapter_state(before):
    assert (
        module.direct_loader._calldata_roundtrip_args
        is module._ORIGINAL_CALLDATA_ROUNDTRIP_ARGS
    )

    assert (
        module._TYPED_ADAPTER_REHYDRATION_COUNT
        == before
    )


def install_single_tampered_primary_mock(
    ctx,
    evidence,
):
    # Integrity mismatch is expected on the FIRST record. Register only the
    # one HTTP response that the contract is expected to consume. This keeps
    # strict_mocks meaningful instead of registering deliberately-unused
    # corroboration and LLM mocks.
    ctx.engine.vm.clear_mocks()
    ctx.engine.vm.clear_validators()

    ctx.engine.vm.mock_web(
        re.escape(
            evidence[0].immutable_reference
        ),
        {
            "status":200,
            "body":b"tampered",
            "method":"GET",
        },
    )


def test_runtime_faithful_create_request_then_canonical_deny():
    ctx, before = open_runtime_context()

    try:
        evidence, bodies = module.make_evidence(
            ctx
        )

        decoded = assert_runtime_roundtrip_shape(
            evidence
        )

        assert all(
            isinstance(item, dict)
            for item in decoded
        )

        assert_runtime_adapter_state(before)

        request_id = module.create_request(
            ctx,
            nonce=31,
            evidence=evidence,
        )

        assert_runtime_adapter_state(before)

        assert module.state_of(
            ctx,
            request_id,
        ) == module.STATE_PENDING

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "request_exists",
            args=[request_id],
        )

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "is_nonce_used",
            args=[
                ctx.agent,
                ctx.u256(31),
            ],
        )

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_nonce_request_id",
            args=[
                ctx.agent,
                ctx.u256(31),
            ],
        ) == request_id

        module.set_mocks(
            ctx,
            evidence,
            bodies,
            llm="DENY",
        )

        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[request_id],
        )

        assert module.state_of(
            ctx,
            request_id,
        ) == module.STATE_DENIED

        assert (
            ctx.engine.vm.run_validator()
            is True
        )

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_receipt_id",
            args=[request_id],
        ) == b""

        assert_runtime_adapter_state(before)

    finally:
        close_runtime_context(
            ctx,
            before,
        )


def test_runtime_faithful_malformed_map_rejects_before_nonce_commit():
    ctx, before = open_runtime_context()

    try:
        evidence, _ = module.make_evidence(
            ctx
        )

        serialized = [
            dict(item)
            for item
            in assert_runtime_roundtrip_shape(
                evidence
            )
        ]

        assert_runtime_adapter_state(before)

        del serialized[0]["authority_id"]

        with pytest.raises(Exception):
            module.create_request(
                ctx,
                nonce=32,
                evidence=serialized,
            )

        assert not ctx.engine.call_method(
            ctx.authorization_address,
            "is_nonce_used",
            args=[
                ctx.agent,
                ctx.u256(32),
            ],
        )

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_nonce_request_id",
            args=[
                ctx.agent,
                ctx.u256(32),
            ],
        ) == b""

        assert_runtime_adapter_state(before)

    finally:
        close_runtime_context(
            ctx,
            before,
        )


def test_runtime_faithful_replace_evidence_then_deny():
    ctx, before = open_runtime_context()

    try:
        evidence, _ = module.make_evidence(
            ctx
        )

        assert_runtime_roundtrip_shape(
            evidence
        )

        assert_runtime_adapter_state(before)

        request_id = module.create_request(
            ctx,
            nonce=33,
            evidence=evidence,
        )

        assert_runtime_adapter_state(before)

        # This phase intentionally fails at evidence record zero. Do not
        # register mocks that are semantically unreachable after that failure.
        install_single_tampered_primary_mock(
            ctx,
            evidence,
        )

        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[request_id],
        )

        assert module.state_of(
            ctx,
            request_id,
        ) == module.STATE_REPAIR_REQUIRED

        assert module.repair_of(
            ctx,
            request_id,
        ) == module.REPAIR_EVIDENCE_INTEGRITY_MISMATCH

        replacement, replacement_bodies = (
            module.make_evidence(
                ctx,
                a_body=b"replacement primary evidence",
            )
        )

        assert_runtime_roundtrip_shape(
            replacement
        )

        ctx.engine.call_method(
            ctx.authorization_address,
            "replace_evidence",
            args=[
                request_id,
                replacement,
            ],
            sender=ctx.agent.as_hex,
        )

        assert_runtime_adapter_state(before)

        assert module.state_of(
            ctx,
            request_id,
        ) == module.STATE_PENDING

        assert int(
            ctx.engine.call_method(
                ctx.authorization_address,
                "get_request_evidence_revision",
                args=[request_id],
            )
        ) == 1

        # set_mocks first clears the single primary mock above. That mock must
        # have been consumed, so strict_mocks remains a real assertion.
        module.set_mocks(
            ctx,
            replacement,
            replacement_bodies,
            llm="DENY",
        )

        ctx.engine.call_method(
            ctx.authorization_address,
            "evaluate_request",
            args=[request_id],
        )

        assert module.state_of(
            ctx,
            request_id,
        ) == module.STATE_DENIED

        assert (
            ctx.engine.vm.run_validator()
            is True
        )

        assert ctx.engine.call_method(
            ctx.authorization_address,
            "get_request_receipt_id",
            args=[request_id],
        ) == b""

        assert_runtime_adapter_state(before)

    finally:
        close_runtime_context(
            ctx,
            before,
        )
