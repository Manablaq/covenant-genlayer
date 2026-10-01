from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.covenant_write_guard import GuardError, validate_candidate


FINGERPRINT = "a" * 64
RETIRED = "f24a8482e8d608592e3e7268bfeb3288b18ab08161b6381a1308cbaa98fcbdba"


def candidate(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "nonce": 1517,
        "fingerprint_sha256": FINGERPRINT,
        "signing_performed": False,
        "submission_attempted": False,
        "submission_performed": False,
    }
    value.update(overrides)
    return value


def test_pass_requires_fresh_equal_nonces_and_authorized_fingerprint() -> None:
    summary = validate_candidate(
        candidate(),
        latest_nonce=1517,
        pending_nonce=1517,
        authorized_fingerprint=FINGERPRINT,
    )

    assert summary["status"] == "READ_ONLY_PRE_SIGN_GUARD_PASS"
    assert summary["pre_sign_recheck"] is True
    assert summary["signing_performed"] is False
    assert summary["submission_performed"] is False
    assert summary["auto_rebuild_after_authorization"] is False
    assert summary["cross_process_lock"] is False


@pytest.mark.parametrize(
    ("candidate_value", "latest", "pending", "authorized", "message"),
    [
        (candidate(fingerprint_sha256=RETIRED), 1517, 1517, RETIRED, "retired"),
        (candidate(), 1517, 1518, FINGERPRINT, "latest and pending"),
        (candidate(nonce=1516), 1517, 1517, FINGERPRINT, "pending nonce"),
        (candidate(), 1517, 1517, "b" * 64, "authorized fingerprint"),
        (candidate(signing_performed=True), 1517, 1517, FINGERPRINT, "signing_performed"),
        (candidate(submission_attempted=True), 1517, 1517, FINGERPRINT, "submission_attempted"),
    ],
)
def test_guard_refuses_stale_or_already_used_candidates(
    candidate_value: dict[str, object],
    latest: int,
    pending: int,
    authorized: str,
    message: str,
) -> None:
    with pytest.raises(GuardError, match=message):
        validate_candidate(
            candidate_value,
            latest_nonce=latest,
            pending_nonce=pending,
            authorized_fingerprint=authorized,
        )
