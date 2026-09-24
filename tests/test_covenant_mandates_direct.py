import hashlib
import os
from pathlib import Path

import pytest

pytest_plugins = ("gltest.direct.pytest_plugin",)

REPO = Path(os.environ.get("COVENANT_REPO", Path(__file__).resolve().parents[1])).resolve()
MANDATES = REPO / "contracts" / "covenant_mandates.py"
SDK = "v0.2.16"
EXPECTED_SHA = "a561a7a76a612cae8cae044452619e966f549baede471a59f6e08033e9d05cd4"
EXPECTED_SDK_FRAGMENT = "/extracted/v0.2.16/py-lib-genlayer-std/11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v/genlayer/"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy_args(Address, u256, *, nonce=9, max_value=1_000_000):
    zero = Address(bytes(20))
    target = b"contract://merchant/42"
    recipient = bytes.fromhex("66" * 20)
    authority_ids = [
        hashlib.sha256(b"covenant-authority-a").digest(),
        hashlib.sha256(b"covenant-authority-b").digest(),
        hashlib.sha256(b"covenant-authority-c").digest(),
    ]
    return [
        u256(nonce),
        u256(max_value),
        u256(3600),
        u256(600),
        [hashlib.sha256(b"PAYMENT").digest()],
        [hashlib.sha256(target).digest()],
        [hashlib.sha256(recipient).digest()],
        "AUTHORIZE only when verified evidence proves the exact payment is permitted.",
        u256(1),
        u256(2),
        u256(3600),
        u256(900),
        u256(1800),
        u256(8),
        [u256(1), u256(2), u256(2)],
        authority_ids,
        ["Authority A", "Authority B", "Authority C"],
        [
            "https://a.example/evidence/",
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
