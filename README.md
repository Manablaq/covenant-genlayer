# Covenant

**Consensus-enforced authority for autonomous agents, built on GenLayer.**

> AI proposes. GenLayer verifies. Covenant authorizes the exact action.

Covenant is a GenLayer-native authorization protocol for autonomous agents. It determines whether an exact proposed action is permitted by an immutable mandate and evidence policy, then binds any successful authorization to the exact consequential action so it cannot be transferred, mutated, replayed, or consumed by the wrong executor.

## Backend-first rule

The frontend remains out of scope until the backend release gates are closed.
Deterministic tests and repository checks are automated in
`.github/workflows/backend.yml`. Live deployment is a separate, explicitly
authorized stage; an accepted transaction is not treated as finality.

## Core thesis

Covenant does not authorize vague intent such as “pay the contractor.”

It authorizes an exact action commitment bound to:

- agent identity;
- mandate ID/version/hash;
- action type;
- target;
- recipient;
- value;
- payload hash;
- evidence-set hash;
- authorized consumer;
- nonce;
- chain/domain;
- expiry.

Changing a consequential field invalidates the authorization.

## Current release status

**UNRELEASED CURRENT CANDIDATE — exact-source deployment parity is now proven
on the supported local runtime, and a current mandate has finalized with stored
state parity. Current-source request/evaluation behavioral closure and
Production/Bradbury deployment are still pending.**

The repaired candidate has mandate-bound evidence-body limits, bounded
user-controlled inputs, one-time verified mandate-policy loading, and complete
deterministic/adversarial/GLSim/runtime-calldata coverage. The exact current
Mandates and Authorization sources are deployed on the supported local runtime
and their wiring is proven. A current mandate also finalized successfully.

The first current-source approval `create_request` candidate did **not** reach
the chain: mandatory pre-sign freshness revalidation found evidence observation
age `1352` seconds against the mandate maximum of `900`, so the runner stopped
before signing with submission count `0`. That fingerprint is not reusable.

A new request has since been prepared **unsigned only** at EVM nonce `39` with
freshness `PASS` and fingerprint
`45b1b67bd5bf328119646411e4b55f4731997d6e92f08d9ddab5e811a36ae838`.
It has not been signed or submitted and requires separate exact transaction-level
authorization. See `docs/CURRENT_SOURCE_RUNTIME_CHECKPOINT_2026-09-27.md`.

`docs/GATE_F_LIVE_CLOSURE_2026-09-27.md` remains historical predecessor-source
evidence for the older full behavioral closure; those request/approval/rejection/
repair/timeout/recovery/receipt claims are not inherited by the current source.

`deployments/release-manifest.json` records both the current supported-local
source-parity checkpoint and the historical predecessor proof. The backend and
nested `production_deployment.status` remain `UNRELEASED` until the remaining
current-source behavioral gates and separately authorized Bradbury/public gates
are closed.

## Verification

Use Python 3.12 and install the exact pinned toolchain from
`requirements-lock.txt`.

```bash
python scripts/verify_backend.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 GENVM_VERSION=v0.2.16 pytest -q tests/test_covenant_mandates_direct.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 GENVM_VERSION=v0.2.16 pytest -q tests/test_covenant_authorization_glsim.py
```

The Direct and GLSim surfaces run in separate pytest processes because their
plugins cannot safely share one interpreter. The supported-runtime procedure
must preserve raw responses before decoding and must never resubmit a timed-out
write; its live evidence remains a release gate, not a mocked-test result.

The safe runtime starting point is read-only:

```bash
python scripts/live_preflight.py \
  --output /tmp/covenant-runtime-preflight \
  --mandates 0x... \
  --authorization 0x...
```

The preflight refuses to overwrite evidence and has no transaction-signing or
submission path.
