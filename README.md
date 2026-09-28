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

**UNRELEASED CURRENT CANDIDATE — the Mandates source has been redesigned to fit
Bradbury’s observed gas ceiling without removing protocol features and is now
deployed/finalized there with exact source parity. The authorized compact
Authorization attempt fit the observed gas ceiling but failed during GenVM
parsing because its required dependency-header blank line had been removed.
That format defect is fixed in source hash
`306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c1`; the
corrected deployment is accepted with successful GenVM execution but awaits
separate finalization. Current-source parity, Gate I live verification, and
final release certification remain pending.**

The candidate retains mandate-bound evidence-body limits, bounded user-controlled
inputs, one-time verified mandate-policy loading, all public Mandates methods,
validation branches, commitment preimages, storage values, and state transitions.
The compact diagnostic-code redesign and the corrected local candidate pass
Direct, GLSim, adversarial, runtime-calldata, reference-vector, and Gate D
coverage. The supported-local live deployment evidence in the checkpoint is
explicitly pre-compact evidence and is not current-candidate source parity.

The first current-source approval `create_request` candidate did **not** reach
the chain: mandatory pre-sign freshness revalidation found evidence observation
age `1352` seconds against the mandate maximum of `900`, so the runner stopped
before signing with submission count `0`. That fingerprint is not reusable.

Approval, rejection, repair/replacement, timeout, receipt consumption,
replay, wrong-consumer, and redirect provenance are recorded only for the
pre-compact supported-local deployment in
`docs/CURRENT_SOURCE_RUNTIME_CHECKPOINT_2026-09-27.md`.

`docs/GATE_F_LIVE_CLOSURE_2026-09-27.md` remains historical predecessor-source
evidence and is not used to establish the current-source claims.

`deployments/release-manifest.json` records the current supported-local
source-parity checkpoint, finalized Bradbury Mandates deployment, rejected
Authorization deployment attempt, and historical predecessor proof. The
backend and nested `production_deployment.status` remain `UNRELEASED` until
the remaining Bradbury/public gates are closed.

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
