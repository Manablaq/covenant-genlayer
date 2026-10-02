# Current-source local Gate F evidence — 2026-10-02

The current source completed the behavioral Gate F matrix on the supported local full runtime (chain `61999`, five validators, GenVM `v0.2.16`). The tracked machine-readable record is [CURRENT_SOURCE_LOCAL_GATE_F_2026-10-02.json](CURRENT_SOURCE_LOCAL_GATE_F_2026-10-02.json).

The run finalized current-source mandate creation, approval, independent denial, repair/replacement, source-failure repair, expiry, receipt consumption, wrong-consumer and mutated-intent rejection, replay rejection, and restart recovery. Every write was submitted once; the recovery evaluation resumed the original transaction after the worker restart, with no resend or replacement.

The run proves local current-source behavior only. It does not prove that Bradbury runs the patched GenVM, exposes an enforceable effective origin, or preserves redirect provenance. The local raw request/response, unsigned transaction, signed transaction, and finality records remain under the ignored evidence directory `work/current-source-gate-f-20261002/` and are not treated as target-network evidence.

Accordingly, Gate F is closed for the supported local current-source runtime, while Bradbury Gate I, target-network runtime provenance/effective-origin proof, and Gate J remain open. The release manifest remains `UNRELEASED`.
