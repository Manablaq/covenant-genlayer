#!/usr/bin/env python3
"""Read-only supported-runtime preflight with raw-response preservation.

This script intentionally has no signing, transaction submission, retry, or
contract-write path. It is the safe first step before a separately reviewed
deployment/G11 runner is authorized.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path


def rpc_call(rpc: str, output: Path, label: str, method: str, params: list[object], ident: int) -> object:
    body = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "id": ident},
        separators=(",", ":"),
    ).encode()
    (output / f"{label}.request.json").write_bytes(body)
    try:
        response = urllib.request.urlopen(
            urllib.request.Request(
                rpc,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=30,
        )
        raw = response.read()
        status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    (output / f"{label}.response.raw").write_bytes(raw)
    (output / f"{label}.http-status.txt").write_text(str(status) + "\n", encoding="utf-8")
    if status != 200:
        raise RuntimeError(f"{label}: HTTP {status}; raw_sha256={hashlib.sha256(raw).hexdigest()}")
    decoded = json.loads(raw)
    if decoded.get("error") is not None:
        raise RuntimeError(f"{label}: RPC error; raw_sha256={hashlib.sha256(raw).hexdigest()}")
    return decoded.get("result")


def number(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    raise TypeError(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", default="http://127.0.0.1:4000/api")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--mandates", required=True)
    parser.add_argument("--sender")
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {args.output}")
    args.output.mkdir(parents=True)

    chain_id = number(rpc_call(args.rpc, args.output, "chain-id", "eth_chainId", [], 8101))
    validator_count = number(
        rpc_call(args.rpc, args.output, "validator-count", "sim_countValidators", [], 8102)
    )
    mandates_code = rpc_call(
        args.rpc,
        args.output,
        "mandates-code",
        "gen_getContractCode",
        [args.mandates],
        8103,
    )
    authorization_code = rpc_call(
        args.rpc,
        args.output,
        "authorization-code",
        "gen_getContractCode",
        [args.authorization],
        8104,
    )
    sender_nonce_latest = None
    sender_nonce_pending = None
    if args.sender is not None:
        sender_nonce_latest = number(
            rpc_call(
                args.rpc,
                args.output,
                "sender-nonce-latest",
                "eth_getTransactionCount",
                [args.sender, "latest"],
                8105,
            )
        )
        sender_nonce_pending = number(
            rpc_call(
                args.rpc,
                args.output,
                "sender-nonce-pending",
                "eth_getTransactionCount",
                [args.sender, "pending"],
                8106,
            )
        )
    if not isinstance(mandates_code, str) or not mandates_code:
        raise SystemExit("mandates address has no deployed code")
    if not isinstance(authorization_code, str) or not authorization_code:
        raise SystemExit("authorization address has no deployed code")

    try:
        mandates_code_bytes = base64.b64decode(mandates_code, validate=True)
        authorization_code_bytes = base64.b64decode(authorization_code, validate=True)
    except Exception as exc:
        raise SystemExit(f"contract source is not valid base64: {exc}") from exc
    if not mandates_code_bytes:
        raise SystemExit("mandates address has empty deployed source")
    if not authorization_code_bytes:
        raise SystemExit("authorization address has empty deployed source")

    summary = {
        "status": "READ_ONLY_PREFLIGHT_PASS",
        "chain_id": chain_id,
        "validator_count": validator_count,
        "mandates": args.mandates,
        "authorization": args.authorization,
        "mandates_code_sha256": hashlib.sha256(mandates_code_bytes).hexdigest(),
        "authorization_code_sha256": hashlib.sha256(authorization_code_bytes).hexdigest(),
        "contract_code_encoding": "base64 UTF-8 GenLayer Python source via gen_getContractCode",
        "sender": args.sender,
        "sender_nonce_latest": sender_nonce_latest,
        "sender_nonce_pending": sender_nonce_pending,
        "writes_submitted": 0,
        "raw_responses_persisted_before_decode": True,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
