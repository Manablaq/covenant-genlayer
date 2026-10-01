#!/usr/bin/env python3
"""Read-only last-moment guard for an authorized Covenant write.

This module deliberately stops before signing. It validates an already frozen
unsigned candidate against a fresh latest/pending nonce read and an explicitly
authorized fingerprint. It never rebuilds a candidate after authorization and
it is not a cross-process lock.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RETIRED_FINGERPRINTS = frozenset(
    {
        "f24a8482e8d608592e3e7268bfeb3288b18ab08161b6381a1308cbaa98fcbdba",
    }
)


class GuardError(ValueError):
    """The unsigned candidate is unsafe to authorize."""


def normalize_fingerprint(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise GuardError(f"{label} must be a 64-character SHA-256 hex digest")
    normalized = value.lower()
    if any(character not in "0123456789abcdef" for character in normalized):
        raise GuardError(f"{label} must be a 64-character SHA-256 hex digest")
    return normalized


def validate_candidate(
    candidate: dict[str, Any],
    *,
    latest_nonce: int,
    pending_nonce: int,
    authorized_fingerprint: str,
) -> dict[str, Any]:
    """Validate public unsigned metadata without signing or submitting it."""

    if latest_nonce != pending_nonce:
        raise GuardError(
            "latest and pending nonce differ; abort and prepare a new candidate "
            "only before a new authorization"
        )
    candidate_nonce = candidate.get("nonce")
    if not isinstance(candidate_nonce, int) or isinstance(candidate_nonce, bool):
        raise GuardError("candidate nonce must be an integer")
    if candidate_nonce != pending_nonce:
        raise GuardError("candidate nonce does not match the fresh pending nonce")

    candidate_fingerprint = normalize_fingerprint(
        candidate.get("fingerprint_sha256"), "candidate fingerprint_sha256"
    )
    authorized = normalize_fingerprint(
        authorized_fingerprint, "authorized fingerprint"
    )
    if candidate_fingerprint in RETIRED_FINGERPRINTS:
        raise GuardError("candidate fingerprint is retired and must never be reused")
    if authorized in RETIRED_FINGERPRINTS:
        raise GuardError("authorized fingerprint is retired and must never be reused")
    if candidate_fingerprint != authorized:
        raise GuardError("candidate fingerprint does not match the authorized fingerprint")

    for field in ("signing_performed", "submission_attempted", "submission_performed"):
        if candidate.get(field):
            raise GuardError(f"candidate records {field}; refusing reuse")

    return {
        "status": "READ_ONLY_PRE_SIGN_GUARD_PASS",
        "candidate_nonce": candidate_nonce,
        "latest_nonce": latest_nonce,
        "pending_nonce": pending_nonce,
        "fingerprint_sha256": candidate_fingerprint,
        "pre_sign_recheck": True,
        "signing_performed": False,
        "submission_attempted": False,
        "submission_performed": False,
        "auto_rebuild_after_authorization": False,
        "cross_process_lock": False,
        "operator_warning": (
            "This read-only check is not a cross-process lock. Sign immediately "
            "in the same controlled workflow and abort if the signer observes "
            "any nonce or fingerprint change."
        ),
        "recommended_sender_policy": (
            "Use a dedicated Covenant signer account; the observed sender is shared "
            "with other activity and cannot provide nonce isolation."
        ),
    }


def rpc_nonce(rpc: str, sender: str, tag: str) -> int:
    request_body = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [sender, tag],
            "id": 1 if tag == "latest" else 2,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    try:
        response = urllib.request.urlopen(
            urllib.request.Request(
                rpc,
                data=request_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=30,
        )
        decoded = json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise GuardError(f"read-only nonce RPC failed for {tag}: {type(exc).__name__}") from exc
    if not isinstance(decoded, dict):
        raise GuardError(f"read-only nonce RPC returned a non-object for {tag}")
    if decoded.get("error") is not None:
        raise GuardError(f"read-only nonce RPC returned an error for {tag}")
    result = decoded.get("result")
    if not isinstance(result, str):
        raise GuardError(f"read-only nonce RPC returned an invalid result for {tag}")
    try:
        return int(result, 16)
    except ValueError as exc:
        raise GuardError(f"read-only nonce RPC returned a non-hex result for {tag}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--sender", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--authorized-fingerprint", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            raise GuardError("candidate JSON must be an object")
        latest_nonce = rpc_nonce(args.rpc, args.sender, "latest")
        pending_nonce = rpc_nonce(args.rpc, args.sender, "pending")
        summary = validate_candidate(
            candidate,
            latest_nonce=latest_nonce,
            pending_nonce=pending_nonce,
            authorized_fingerprint=args.authorized_fingerprint,
        )
    except (OSError, json.JSONDecodeError, GuardError) as exc:
        raise SystemExit(f"Covenant write guard refused: {exc}") from exc

    encoded = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        if args.output.exists():
            raise SystemExit(f"refusing to overwrite existing output: {args.output}")
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
