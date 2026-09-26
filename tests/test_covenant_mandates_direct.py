import hashlib
import os
from pathlib import Path

import pytest

pytest_plugins = ("gltest.direct.pytest_plugin",)

REPO = Path(os.environ.get("COVENANT_REPO", Path(__file__).resolve().parents[1])).resolve()
MANDATES = REPO / "contracts" / "covenant_mandates.py"
SDK = "v0.2.16"
EXPECTED_SHA = "9c715d57731a031d2c217b3845ba74f08bf3fd7e3dcaa1bb44ffd6e2dc9896d6"
EXPECTED_SDK_FRAGMENT = "/extracted/v0.2.16/py-lib-genlayer-std/11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v/genlayer/"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy_args(
    Address,
    u256,
    *,
    nonce=9,
    max_value=1_000_000,
    semantic_criteria=None,
    max_evidence_body_bytes=8_192,
    publisher_name=None,
    source_prefix=None,
):
    zero = Address(bytes(20))
    target = b"contract://merchant/42"
    recipient = bytes.fromhex("66" * 20)
    authority_ids = [
        hashlib.sha256(b"covenant-authority-a").digest(),
        hashlib.sha256(b"covenant-authority-b").digest(),
        hashlib.sha256(b"covenant-authority-c").digest(),
    ]
    semantic_criteria = semantic_criteria or (
        "AUTHORIZE only when verified evidence proves the exact payment is permitted."
    )
    publisher_name = publisher_name or "Authority A"
    source_prefix = source_prefix or "https://a.example/evidence/"
    return [
        u256(nonce),
        u256(max_value),
        u256(3600),
        u256(600),
        [hashlib.sha256(b"PAYMENT").digest()],
        [hashlib.sha256(target).digest()],
        [hashlib.sha256(recipient).digest()],
        semantic_criteria,
        u256(1),
        u256(2),
        u256(3600),
        u256(900),
        u256(1800),
        u256(8),
        u256(max_evidence_body_bytes),
        [u256(1), u256(2), u256(2)],
        authority_ids,
        [publisher_name, "Authority B", "Authority C"],
        [
            source_prefix,
            "https://b.example/evidence/",
            "https://c.example/evidence/",
        ],
        u256(0),
        zero,
        u256(2),
    ]


def deployed(direct_vm, direct_deploy):
    assert sha(MANDATES) == EXPECTED_SHA
    direct_vm._chain_id = 4221
    direct_vm.strict_mocks = True
    direct_vm.check_pickling = True
    contract = direct_deploy(str(MANDATES), sdk_version=SDK)

    import genlayer
    from genlayer import u256
    from genlayer.py.types import Address

    sdk_file = str(Path(genlayer.__file__).resolve())
    print("MANDATES_DIRECT_ACTIVE_GENLAYER_SDK_FILE=" + sdk_file)
    assert EXPECTED_SDK_FRAGMENT in sdk_file
    return contract, Address, u256


def test_m01_deploy_identity_and_chain(direct_vm, direct_deploy):
    contract, Address, _ = deployed(direct_vm, direct_deploy)
    expected_address = Address(direct_vm._contract_address)
    assert contract.get_contract_address() == str(expected_address)
    assert int(contract.get_chain_id()) == 4221


def test_m02_create_and_read_mandate(direct_vm, direct_deploy):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    mandate_id = contract.create_mandate(*policy_args(Address, u256))
    assert len(mandate_id) == 32
    assert contract.mandate_exists(mandate_id)
    assert int(contract.get_latest_version(mandate_id)) == 1
    assert contract.version_exists(mandate_id, u256(1))
    assert contract.is_version_eligible(mandate_id, u256(1))
    commitment = contract.get_mandate_commitment(mandate_id, u256(1))
    assert len(commitment) == 32


def test_m03_issuer_nonce_is_single_use(direct_vm, direct_deploy):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    contract.create_mandate(*policy_args(Address, u256, nonce=77))
    with pytest.raises(Exception):
        contract.create_mandate(*policy_args(Address, u256, nonce=77))


def test_m04_only_issuer_controls_eligibility(direct_vm, direct_deploy):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    mandate_id = contract.create_mandate(*policy_args(Address, u256, nonce=78))
    contract.set_version_eligible(mandate_id, u256(1), False)
    assert not contract.is_version_eligible(mandate_id, u256(1))
    other = Address(bytes.fromhex("99" * 20))
    direct_vm.sender = other
    with pytest.raises(Exception):
        contract.set_version_eligible(mandate_id, u256(1), True)


def test_m05_publish_is_append_only(direct_vm, direct_deploy):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    mandate_id = contract.create_mandate(*policy_args(Address, u256, nonce=79))
    old_commitment = contract.get_mandate_commitment(mandate_id, u256(1))
    next_args = policy_args(Address, u256, nonce=999, max_value=2_000_000)[1:]
    version = contract.publish_next_version(mandate_id, *next_args)
    assert int(version) == 2
    assert contract.version_exists(mandate_id, u256(1))
    assert contract.version_exists(mandate_id, u256(2))
    assert contract.get_mandate_commitment(mandate_id, u256(1)) == old_commitment
    assert contract.get_mandate_commitment(mandate_id, u256(2)) != old_commitment


@pytest.mark.parametrize(
    ("field", "value", "should_pass"),
    [
        ("max_evidence_body_bytes", 8_191, True),
        ("max_evidence_body_bytes", 8_192, True),
        ("max_evidence_body_bytes", 8_193, False),
        ("semantic_criteria", "x" * 4_095, True),
        ("semantic_criteria", "x" * 4_096, True),
        ("semantic_criteria", "x" * 4_097, False),
        ("publisher_name", "x" * 255, True),
        ("publisher_name", "x" * 256, True),
        ("publisher_name", "x" * 257, False),
        (
            "source_prefix",
            "https://" + "x" * (2_047 - len("https://") - 1) + "/",
            True,
        ),
        (
            "source_prefix",
            "https://" + "x" * (2_048 - len("https://") - 1) + "/",
            True,
        ),
        (
            "source_prefix",
            "https://" + "x" * (2_049 - len("https://") - 1) + "/",
            False,
        ),
    ],
)
def test_m06_protocol_size_boundaries(
    direct_vm,
    direct_deploy,
    field,
    value,
    should_pass,
):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    kwargs = {field: value}
    if should_pass:
        contract.create_mandate(*policy_args(Address, u256, **kwargs))
    else:
        with pytest.raises(Exception):
            contract.create_mandate(*policy_args(Address, u256, **kwargs))


def test_m07_body_limit_is_stored_and_commitment_bound(direct_vm, direct_deploy):
    contract, Address, u256 = deployed(direct_vm, direct_deploy)
    first = contract.create_mandate(
        *policy_args(
            Address,
            u256,
            nonce=880,
            max_evidence_body_bytes=8_191,
        )
    )
    second = contract.create_mandate(
        *policy_args(
            Address,
            u256,
            nonce=881,
            max_evidence_body_bytes=8_192,
        )
    )
    assert int(contract.get_max_evidence_body_bytes(first, u256(1))) == 8_191
    assert int(contract.get_max_evidence_body_bytes(second, u256(1))) == 8_192
    assert contract.get_mandate_commitment(first, u256(1)) != contract.get_mandate_commitment(
        second,
        u256(1),
    )
