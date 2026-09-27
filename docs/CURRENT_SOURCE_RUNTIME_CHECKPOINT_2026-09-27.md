# Current-source supported-runtime checkpoint — 2026-09-27

This checkpoint records the exact current-source backend state through the
Phase 6D-R1 fresh unsigned approval preparation. It does **not** claim backend
completion, transaction authorization, Bradbury deployment, or production
release.

## Frozen source identity

- Source commit: `78280f3e82e056424342b3233f420332d6e2a71f`
- Authorization SHA-256: `24ad76f931ccef6dca2ca6fbe94971b3eb22d7a98facb5c3de9c4491d6e507ed`
- Mandates SHA-256: `aa38488fb44815a248ffbf5fa9938449a66954bfa94717686bc7b7cf4fdee4b2`
- Chain ID: `61999`
- Validators: `5`
- Mandates: `0xdFEce9C4ae3124B8de273B75227F6DC1DE30297C`
- Authorization: `0xEBb2863137Dff7e96886090D303373E8Ec9CF5B8`

The contract bytes are unchanged by this checkpoint commit.

## Completed current-source runtime work

### Phase 6A — Mandates deployment

- Result: `FINALIZED / MAJORITY_AGREE`
- Transaction: `0x4f8814f7f84db106f47a947ddefcb902f2f782dc1c703e4a370c72aea1e6922b`
- Source parity: `PASS`
- Submission count: `1`

### Phase 6B — Authorization deployment

- Result: `FINALIZED / MAJORITY_AGREE`
- Transaction: `0x32687d2ff5b61f1ab8a4bfcb59ba9d3685c1e6e806ce737425d78276b1fdb2bb`
- Authorization source parity: `PASS`
- Authorization -> Mandates binding: `PASS`
- Submission count: `1`

### Phase 6C initial create_mandate attempt

- Result: `FINALIZED / NO_MAJORITY`
- Transaction: `0xba95cfa6b46895e7b0533b3230ae40233a0580b4b2f4f70402a798e1bd3d9c63`
- Submission count: `1`
- No automatic resubmission occurred.
- This terminal unsuccessful attempt is retained as evidence and is not counted
  as successful mandate creation.

### Phase 6C-R2 — successful mandate creation

- Result: `FINALIZED / MAJORITY_AGREE`
- Transaction: `0xd2a0e3cf3461c96af3cbbdb06f14eb971fddcbb58d4f845824eefca58008b727`
- Mandate ID: `0xcc8506d1809fc4664c5f9287816f8c51198c250fe995cc505c340d4b12de8ab7`
- Version: `1`
- Mandate state parity: `PASS`
- Submission count: `1`
- Authorized unsigned fingerprint: `d5333afb1cb1cc86d2e20a08ef76d4bce0cb0bdb2fd8f6eca62ad2a5002ef033`
- No additional chain write occurred after the authorized transaction.

## Phase 6D — approval create_request STOP

The frozen approval request candidate had unsigned fingerprint:

`440bb1c43323dc138fe1bac7458d99165affa63f4ce4f68a6572f2d7d100b620`

Pre-sign revalidation passed repository/source/runtime/nonce/database/calldata and
mandate-state checks, but freshness failed before signing:

- evidence observation age: `1352` seconds;
- mandate maximum observation age: `900` seconds;
- signer operation performed: `NO`;
- transaction submission performed: `NO`;
- submission count: `0`;
- chain write performed: `NO`;
- request created: `NO`.

The stopped fingerprint must not be reused.

## Phase 6D-R1 — fresh approval preparation

A new approval-path request was prepared **unsigned only** after refreshing only
the temporal evidence metadata while preserving the semantic vector and evidence
body bytes.

- Preparation time: `1790491733`
- EVM nonce: `39`
- Covenant request nonce: `1`
- Gas estimate: `500000`
- Freshness at preparation: `PASS`
- Method-call SHA-256: `eb6d2c9bb2fa597ca76215c41214b5acda805a7fc0e2dba224a00160e2f4ab50`
- Supported inner txData SHA-256: `ce72ed8b2ab1a2fa7fac63e0703fb35d0f68422ac782f978b56f94c8238b33cf`
- Outer calldata SHA-256: `6144eac3743d167dc9cfbc6daa6fef7e0e4e1a956ab891fdf18cee9556a47781`
- New unsigned fingerprint: `45b1b67bd5bf328119646411e4b55f4731997d6e92f08d9ddab5e811a36ae838`
- Old stopped fingerprint reused: `NO`
- Signing performed: `NO`
- Submission performed: `NO`
- Submission count: `0`
- Chain write performed: `NO`
- Sender latest/pending nonce remained `39/39`
- Covenant request nonce `1` remained unused
- Read-only DB rows for sender nonce >=39 remained `0`

The fresh fingerprint is **prepared, not authorized**. Signing/submission requires
separate exact transaction-level authorization.

## Evidence roots

Operator evidence is retained outside tracked source in the following frozen
roots:

- `covenant-phase6a-mandates-20260927-045218`
- `covenant-phase6b-authorization-20260927-052158`
- `covenant-phase6c-create-mandate-20260927-055329`
- `covenant-phase6c-r2-create-mandate-20260927-065642`
- `work/phase6d-approval-create-request-20260927-072012`
- `covenant-phase6d-r1-fresh-approval-prep-20260927-074028`

Evidence inventories were verified before this checkpoint was written. The
legacy Phase 6B launcher stderr is append-only, so its exact manifest-sized
frozen prefix is hash-bound and later diagnostics are outside the proof
boundary. The Phase 6D STOP has an empty manifest but a complete checksum
ledger, so every ledger-bound file plus the critical no-sign/no-submit
certificates is verified directly. Phase 6D-R1 accidentally self-listed its
manifest; the final manifest bytes are bound by `SHA256SUMS.txt`, while every
non-self artifact remains exact hash/size bound.

## Exact release boundary

Completed for the **current source**:

- deterministic/static gates;
- exact-source supported-local-runtime Mandates deployment;
- exact-source supported-local-runtime Authorization deployment;
- exact Authorization -> Mandates wiring;
- current mandate creation and stored-state parity;
- fresh unsigned approval-path `create_request` preparation at nonce `39`.

Still pending for the **current source**:

- exact authorization and successful submission/finality of the fresh approval-path `create_request`;
- approval `evaluate_request`;
- independent rejection path;
- repair/replacement live closure;
- timeout/recovery live closure without automatic resubmission;
- one-time receipt-consumption live closure;
- redirect/effective-origin provenance live closure;
- Bradbury/public deployment and verification;
- final reviewer evidence freeze.

Historical predecessor-source closure remains useful historical evidence only
and must not be substituted for these remaining current-source proofs.

Backend status: **UNRELEASED / NOT COMPLETE**.
