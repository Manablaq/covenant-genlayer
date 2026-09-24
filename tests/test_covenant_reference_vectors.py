import hashlib


def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def u256(value: int) -> bytes:
    return value.to_bytes(32, "big", signed=False)


def text(value: str) -> bytes:
    return h(value.encode("utf-8"))


def blob(value: bytes) -> bytes:
    return h(value)


DOMAINS = {
    "MANDATE_ID": h(b"COVENANT/V1/MANDATE_ID"),
    "MANDATE": h(b"COVENANT/V1/MANDATE"),
    "ACTION_SUBJECT": h(b"COVENANT/V1/ACTION_SUBJECT"),
    "EVIDENCE_RECORD": h(b"COVENANT/V1/EVIDENCE_RECORD"),
    "EVIDENCE_SET": h(b"COVENANT/V1/EVIDENCE_SET"),
    "ACTION_INTENT": h(b"COVENANT/V1/ACTION_INTENT"),
    "REQUEST_ID": h(b"COVENANT/V1/REQUEST_ID"),
    "RECEIPT_ID": h(b"COVENANT/V1/RECEIPT_ID"),
    "NONCE_KEY": h(b"COVENANT/V1/NONCE_KEY"),
}


def evidence_set(action_subject: bytes, records: list[bytes]) -> bytes:
    ordered = sorted(records)
    if len(ordered) != len(set(ordered)):
        raise ValueError("duplicate evidence commitment")
    return h(DOMAINS["EVIDENCE_SET"] + action_subject + u256(len(ordered)) + b"".join(ordered))


def fixture():
    chain_id = 4221
    authorization = bytes.fromhex("33" * 20)
    agent = bytes.fromhex("44" * 20)
    consumer = bytes.fromhex("55" * 20)
    recipient = bytes.fromhex("66" * 20)
    mandate_id = bytes.fromhex("6a4e11b9ce55c52e8869fef1114de33c243c47e08f763a4684cc55b43b1b1960")
    mandate_version = 7
    mandate_commitment = bytes.fromhex("8965e6b0715fab9718f4538f753c97f9b0a268fa395a07e4b755afa473db68af")
    action_subject = h(
        DOMAINS["ACTION_SUBJECT"]
        + u256(chain_id)
        + authorization
        + agent
        + mandate_id
        + u256(mandate_version)
        + mandate_commitment
        + text("PAYMENT")
        + blob(b"contract://merchant/42")
        + blob(recipient)
        + u256(250000)
        + blob(b'{"invoice":"INV-2026-0042"}')
        + consumer
        + u256(123456789)
        + u256(1790000000)
        + u256(1790003600)
    )
    return {
        "chain_id": chain_id,
        "authorization": authorization,
        "agent": agent,
        "consumer": consumer,
        "action_subject": action_subject,
    }


def test_v01_domain_vectors():
    expected = {
        "MANDATE_ID": "6f1c37d3b61bb57668ffe1eda40172d9abb44ef206057761ef9848a0058cd25c",
        "MANDATE": "cf58baa874cb6940bdcf4a855ccf07c4b746f77b3df6fd913fb0f932a852e2c4",
        "ACTION_SUBJECT": "4690d38d423417d1669a2d29fbc2234508e5a64f3fdeb91090c09a5242dc5126",
        "EVIDENCE_RECORD": "cac63b3e2880c12b78d35841ce5be0b3a9956a6909ddfc32c040fe22da90914c",
        "EVIDENCE_SET": "c2511857c12b26d5f9fed63a32b03e35f4af272ef3ca3ff326c69dafcd76523e",
        "ACTION_INTENT": "c1de800cbac3af21eab66209b04331fe45dc07db9a5c72cfc312ddfbdf58af1f",
        "REQUEST_ID": "24d6d54181b72607af6b9f665355952e27d933d1bacc4f8663f0dee3061d2ab1",
        "RECEIPT_ID": "25bcf73e68ed57d377b99b64a7c706570c9ccc364ec8b4076559b374f12311a5",
        "NONCE_KEY": "c65377be12c6d8434cd46664e9f3a96c320adac5700b56f982b4ef18d45805b3",
    }
    assert {k: v.hex() for k, v in DOMAINS.items()} == expected


def test_v02_action_subject_reference_vector():
    assert fixture()["action_subject"].hex() == "87bc99583c6504b9943d3aaa63ff1f315ab3bbbc71fe7b2b2ada68db7194ff61"


def test_v03_request_id_reference_vector():
    request_id = h(DOMAINS["REQUEST_ID"] + fixture()["action_subject"])
    assert request_id.hex() == "cc552250beccee9cde45d7d1e3dfe16b9e305d4653aa5267a24ce472b9f71c0b"


def test_v04_nonce_key_reference_vector():
    f = fixture()
    nonce_key = h(
        DOMAINS["NONCE_KEY"]
        + u256(f["chain_id"])
        + f["authorization"]
        + f["agent"]
        + u256(123456789)
    )
    assert nonce_key.hex() == "eac139f13810a72dedab9efc71e6bd3b3af3571b6bb0795938a2fe3942613cfc"


def test_v05_evidence_set_is_submission_order_independent():
    f = fixture()
    a = bytes.fromhex("e2101af44756583b31045385118f1c0be1f2b13ab9dd86b3ca0e064c05c12892")
    b = bytes.fromhex("00d95e4f1fcbee1001a7d0c8aee386d8c90a17f3df6e77348df2428d3c280373")
    c = bytes.fromhex("c2f59fc84f6b5400a561ec64741b97094323fae2bf1e3a79a52c302dc7fcd6e1")
    expected = "0110de666ffca86d92adaebcb56b547037d4b2dedc4bf4b6cc7b4ce9985920a2"
    assert evidence_set(f["action_subject"], [a, b, c]).hex() == expected
    assert evidence_set(f["action_subject"], [c, a, b]).hex() == expected


def test_v06_duplicate_evidence_commitment_rejects():
    f = fixture()
    a = bytes.fromhex("e2101af44756583b31045385118f1c0be1f2b13ab9dd86b3ca0e064c05c12892")
    try:
        evidence_set(f["action_subject"], [a, a])
    except ValueError:
        return
    raise AssertionError("duplicate evidence commitment did not reject")


def test_v07_action_intent_reference_vector():
    f = fixture()
    evidence = bytes.fromhex("0110de666ffca86d92adaebcb56b547037d4b2dedc4bf4b6cc7b4ce9985920a2")
    action_intent = h(DOMAINS["ACTION_INTENT"] + f["action_subject"] + evidence)
    assert action_intent.hex() == "a5fa809a1218db9ed9f40fa5ad98498d8487faf053fa831883d3e0e7792b78bd"


def test_v08_receipt_reference_vector():
    f = fixture()
    request_id = h(DOMAINS["REQUEST_ID"] + f["action_subject"])
    action_intent = bytes.fromhex("a5fa809a1218db9ed9f40fa5ad98498d8487faf053fa831883d3e0e7792b78bd")
    receipt = h(DOMAINS["RECEIPT_ID"] + request_id + action_intent)
    assert receipt.hex() == "ac2d028281605965f6227e8d0f5196410039bf56d1af397ceefad54ca3644f2c"


def test_v09_repair_preserves_request_and_changes_intent_and_receipt():
    f = fixture()
    request_id = h(DOMAINS["REQUEST_ID"] + f["action_subject"])
    repaired_set = bytes.fromhex("1b3d2cc4189fdcc908c23dd34e5ff627a222e7d103eddd7c836d1ae362e50f93")
    repaired_intent = h(DOMAINS["ACTION_INTENT"] + f["action_subject"] + repaired_set)
    repaired_receipt = h(DOMAINS["RECEIPT_ID"] + request_id + repaired_intent)
    assert request_id.hex() == "cc552250beccee9cde45d7d1e3dfe16b9e305d4653aa5267a24ce472b9f71c0b"
    assert repaired_intent.hex() == "88d33d7ea468c53212b0fec60fa94c89a801f81d7aa2c8c441353b674dcde48a"
    assert repaired_receipt.hex() == "a21d33e08e6cd6afacb97bf0f73f55b8e313f095144129712be48f418cb58e4c"
