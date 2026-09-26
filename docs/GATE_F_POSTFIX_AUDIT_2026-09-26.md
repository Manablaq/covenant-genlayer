# Gate F Post-Fix Audit — 2026-09-26

Status: **Progress 3 remains open. This is not a backend-complete certificate.**

## Source and deterministic proof

- Baseline repository commit bound by R52: `82a1bd3c660afe0898b42e7088cc2ab817993c3d`.
- Authorization source after the policy-loading refactor: `89b5311d0bb6adb6dac0868f8c90355fc5082b00f444d91baacb07439d58e19b`.
- Mandates source: `c921da40757968260e7acb0555db93d2ba4c3ca9ce81760ca51f6087d494333f`.
- GLSim base test: `d45b82f3923b8fd30d03b1070251310d887d5a658fb6829ff5c7314bd700d61e`.
- R52 was completed read-only before the source refactor and classified the prior failure as a GenVM-internal VM error, not host/container OOM. No R47–R51 rerun was performed.
- The refactor materializes immutable mandate policy once per execution path and passes it through deterministic, authority, freshness, evidence-policy, and repair helpers. Authority/freshness helpers contain no registry view calls.
- Deterministic tests passed in isolated processes: 47 GLSim/adversarial/closure tests, 5 Direct mandate tests, and 13 runtime-calldata/reference tests; 65 total.
- Lint and Python syntax compilation passed. The pinned linter's later validate/typecheck rerun was unable to reload its missing cached SDK tarball; earlier validate and strict typecheck results for these exact source hashes passed.

## Deployment and exactly-once G11 attempt

The schema-validated runtime deployment finalized with majority agreement:

The deployed runtime candidate was `78e3cf5362759787cf144e4031e5d24629bd836949e7dd2ca1d19d4d1c6172bc`, a separately persisted compatibility envelope derived from the reviewed source. It is **not** identical to the repository source hash above, so this deployment is retained as diagnostic evidence and is not a release deployment binding.

- Authorization: `0x4d8Cd6Caa7D7681AeF2E3B6e21FFB3238eCb4814`
- Deployment transaction: `0x79995bc51bed6a8e7930412e7b018141d70a751a3618127d28839d0f154950dc`
- Mandates: `0x5346943019730Ff7C193D75e6067e1d317a09777`
- Chain ID: `61999`
- Validator count read before construction: `5`

The supported-runtime G11 `create_request` transaction was constructed offline, with raw calldata and unsigned fingerprint persisted before signing, and submitted exactly once:

- Raw calldata SHA-256: `44e30fa4e9e2dec2c6f07b1671141d106fd4cae5cd58d38015a32801c5e2854d`
- Unsigned fingerprint: `5a985d282e68a70ffe0a13a86d8212663b700a02b297837b0fa7dad2d6a54556`
- Signed transaction hash: `0x0db5b76afd554ea2da8f39cdbaf32f9443b10f1a4bf32dfe98ed291167e1a6e5`
- GenLayer transaction ID: `0x9ca7d333bd99f0c024858be1cba8da6d6b57e70a226220625403e4b315b64496`
- Submission count: `1`
- Final result: `FINALIZED / NO_MAJORITY`
- Execution hash: empty

This is a terminal unsuccessful result. It is not approval, rejection, or successful request creation. The transaction status also reports `type=0`, empty `tx_data`, no round validators, and zero votes; this is consistent with the envelope not entering the GenLayer consensus path. This is an observed runtime transport failure, not evidence that Covenant validation should be weakened.

## Post-transaction state audit

Using the exact request vector and request ID `0x791f48f6dbcdb7256864ae0f85aafa23aa6bf7790d16b3152cd0d4d693ea15cd`, read-only verification found:

- `request_exists`: `false`
- `is_nonce_used(agent, 11)`: `false`
- `get_nonce_request_id(agent, 11)`: empty bytes
- Contract address binding: unchanged
- Mandates address binding: unchanged
- Chain ID: `61999`

The unsuccessful G11 therefore did not commit a request, nonce reservation, evidence records, or request commitments. No second G11 call is permitted under the release instructions.

## Release decision

Approval, independent rejection, real repair/replacement, timeout, redirect/effective-URL provenance, post-finality receipt, Progress 4 recovery, and Progress 5 release-freeze checks were not run because the required successful finalized G11 request was not established. The repository must not be labeled **BACKEND COMPLETE**, committed as a release checkpoint, or pushed as complete until a future authorized run fixes the transaction-envelope path and repeats the required single-write protocol from a new checkpoint.
