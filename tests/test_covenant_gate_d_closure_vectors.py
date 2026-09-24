import hashlib
import os
from pathlib import Path

REPO = Path(os.environ["COVENANT_REPO"]).resolve()

EXPECTED_REFERENCE_TEST_SHA = "7fa6d6714971b9d3c82fb7ef73110157a7c85492e9251c25247b3f3c7bd8586a"
REFERENCE_TEST = REPO / "tests" / "test_covenant_reference_vectors.py"

DOMAIN_ACTION_SUBJECT = bytes.fromhex(
    "4690d38d423417d1669a2d29fbc2234508e5a64f3fdeb91090c09a5242dc5126"
)
DOMAIN_REQUEST_ID = bytes.fromhex(
    "24d6d54181b72607af6b9f665355952e27d933d1bacc4f8663f0dee3061d2ab1"
)

EXPECTED_BASE_ACTION_SUBJECT = (
    "87bc99583c6504b9943d3aaa63ff1f315ab3bbbc71fe7b2b2ada68db7194ff61"
)
EXPECTED_BASE_REQUEST_ID = (
    "cc552250beccee9cde45d7d1e3dfe16b9e305d4653aa5267a24ce472b9f71c0b"
)

EXPECTED_MUTATIONS = {
    "chain_id": (
        "6eb6994b2475b4be3e00bb5d1d990d2d5138119ec6719fd392bfa364b313d8fa",
        "dda11511e552441721847055fd657b45ef9286f5048762519da17c54f1df3bf2",
    ),
    "authorization": (
        "9a6ddaae31c0d0b7af599bdaafad0fe9be6fd5099eeff6dea283aeac57f6bd4c",
        "055ea8bf312f0c600b4e70834d74e4933e8ed5673b16b53d77a51082ee2050a3",
    ),
    "agent": (
        "a417bee6f08cf6cf74bea923ae300052438f5783c4a93c774ac01c3e867f1585",
        "fc27305b0564614a8f58a81f9cc08543d96b7f170a62b05fe8e28fac29affa5d",
    ),
    "mandate_id": (
        "e32a145b1c01c73f56be861f30cd22df8eef3939fb950634d0d63eb0e6ee04df",
        "9da7bc01e07da25bcf87e3213a316f0bc5536aa97ca0a4ef9ae697ed67ed56ff",
    ),
    "mandate_version": (
        "22937a5e6402c388d457df5501887e0f1cdbc842dd2513e180d1dd11541a8fd1",
        "53fc7628d32adb332cdee36b282d84a7b65856ce6a55c6ca756e9128772c0c75",
    ),
    "mandate_commitment": (
        "0edce7a4191de6f6709d29de05681a60086104f0761b271e518f9f8c80240e53",
        "f5cba0c3e1070aac57bb5f7c2305e469e2c968d5cee137c483450d059abe19d8",
    ),
    "action_type": (
        "1e6bfc9f865b8f25c900bc75cf0a2c38163c176209fdb4ec60a3e343da890e0c",
        "9456f0ed9f9049690ec3b18b51e71966d96bd0d3351df6fb4374aa2b7f455746",
    ),
    "target": (
        "1f56cdfd3fe47d8ede1b56d2bf6589cc369203797880da99c7a05602904d9d1c",
        "e90ddbf67e1774044d0856728e1ac6f775507333d02f55297c0aa74b82832c28",
    ),
    "recipient": (
        "d7d1f2124bb474b0d91c8f245beff213a6a872d0b940efc50b3d22c58102afdb",
        "ad1a70e5e7f45a3e501e8158dcb724c6a63fec039047387cced1dc50e32df659",
    ),
    "value": (
        "2ac7e29e9d2e044b9165e10045b9cadb7506f4c29695dfa470bd1af7998f8077",
        "9937fcadcb349c48cb5d0c6538219e57b28e7a8c060fad3515041875d8338f0a",
    ),
    "payload": (
        "745bb169997e5f546ec81355786e2818d31a7873636e3e3a5d6a7c41e5685fb7",
        "f74d69b25e1ad6c7a67e439eb956d6428b970684b77ba94105e5c333ae9999cc",
    ),
    "consumer": (
        "f528883ff86a1f937e5b340679722717d175ab59e154b60e7f6a98976963133a",
        "1a37b5624193acec2d9b2e6be2b420dafd25cfa5df4736f4e2a44658de07deb7",
    ),
    "nonce": (
        "66ea22c9895a58fa91866ca0d4541d5738762f17ac9c0c3a17ede88e930d603c",
        "f06990b4c8ec3878d535827c47e8a8181ba985511d12a64deeb6edc100cb0d1f",
    ),
    "issued_at": (
        "775be88cec1bfea7596137091b40100645a68ccd26363eeca7c78448c6802a9f",
        "9966dcd68deae0bf901336c370f8df93e9c2b275aecc29de5ca9098b9d06a172",
    ),
    "expires_at": (
        "e7499413eb4c48446c8ff9ca0bc4bc78ea2be11f700b5fffb0801e5a01f1e286",
        "ec911cda1bed51c805c5dd71e27eb1a490c4844588e299e73fe228bad5a4967d",
    ),
}


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _u256(value: int) -> bytes:
    return value.to_bytes(32, "big", signed=False)


def _text(value: str) -> bytes:
    return _sha(value.encode("utf-8"))


def _blob(value: bytes) -> bytes:
    return _sha(value)


def _baseline():
    return {
        "chain_id": 4221,
        "authorization": bytes.fromhex("33" * 20),
        "agent": bytes.fromhex("44" * 20),
        "mandate_id": bytes.fromhex(
            "6a4e11b9ce55c52e8869fef1114de33c243c47e08f763a4684cc55b43b1b1960"
        ),
        "mandate_version": 7,
        "mandate_commitment": bytes.fromhex(
            "8965e6b0715fab9718f4538f753c97f9b0a268fa395a07e4b755afa473db68af"
        ),
        "action_type": "PAYMENT",
        "target": b"contract://merchant/42",
        "recipient": bytes.fromhex("66" * 20),
        "value": 250000,
        "payload": b'{"invoice":"INV-2026-0042"}',
        "consumer": bytes.fromhex("55" * 20),
        "nonce": 123456789,
        "issued_at": 1790000000,
        "expires_at": 1790003600,
    }


def _action_subject(values) -> bytes:
    return _sha(
        DOMAIN_ACTION_SUBJECT
        + _u256(values["chain_id"])
        + values["authorization"]
        + values["agent"]
        + values["mandate_id"]
        + _u256(values["mandate_version"])
        + values["mandate_commitment"]
        + _text(values["action_type"])
        + _blob(values["target"])
        + _blob(values["recipient"])
        + _u256(values["value"])
        + _blob(values["payload"])
        + values["consumer"]
        + _u256(values["nonce"])
        + _u256(values["issued_at"])
        + _u256(values["expires_at"])
    )


def _request_id(action_subject: bytes) -> bytes:
    return _sha(DOMAIN_REQUEST_ID + action_subject)


def test_c01_exact_consequential_field_mutation_vectors():
    assert hashlib.sha256(REFERENCE_TEST.read_bytes()).hexdigest() == EXPECTED_REFERENCE_TEST_SHA

    baseline = _baseline()
    base_subject = _action_subject(baseline)
    base_request = _request_id(base_subject)

    assert base_subject.hex() == EXPECTED_BASE_ACTION_SUBJECT
    assert base_request.hex() == EXPECTED_BASE_REQUEST_ID

    mutations = {
        "chain_id": 4222,
        "authorization": bytes.fromhex("34" * 20),
        "agent": bytes.fromhex("45" * 20),
        "mandate_id": bytes.fromhex("77" * 32),
        "mandate_version": 8,
        "mandate_commitment": bytes.fromhex("88" * 32),
        "action_type": "TRANSFER",
        "target": b"contract://merchant/43",
        "recipient": bytes.fromhex("67" * 20),
        "value": 250001,
        "payload": b'{"invoice":"INV-2026-0043"}',
        "consumer": bytes.fromhex("56" * 20),
        "nonce": 123456790,
        "issued_at": 1790000001,
        "expires_at": 1790003601,
    }

    assert tuple(mutations) == tuple(EXPECTED_MUTATIONS)
    assert len(mutations) == 15

    observed_subjects = set()
    observed_requests = set()

    for field, replacement in mutations.items():
        values = dict(baseline)
        values[field] = replacement

        subject = _action_subject(values)
        request_id = _request_id(subject)
        expected_subject, expected_request = EXPECTED_MUTATIONS[field]

        assert subject.hex() == expected_subject
        assert request_id.hex() == expected_request
        assert subject != base_subject
        assert request_id != base_request

        observed_subjects.add(subject)
        observed_requests.add(request_id)

    assert len(observed_subjects) == 15
    assert len(observed_requests) == 15

    print("CONSEQUENTIAL_FIELD_MUTATION_COUNT=15")
    print("EACH_FIELD_CHANGES_ACTION_SUBJECT=PASS")
    print("EACH_FIELD_CHANGES_REQUEST_ID=PASS")
    print("ALL_MUTATED_ACTION_SUBJECTS_UNIQUE=PASS")
    print("ALL_MUTATED_REQUEST_IDS_UNIQUE=PASS")
