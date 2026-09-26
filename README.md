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

**RELEASED — backend source and the pinned local runtime candidate. Production
deployment remains UNRELEASED.**

The repaired candidate has mandate-bound evidence-body limits, bounded
user-controlled inputs, one-time verified mandate-policy loading, and complete
deterministic/adversarial/GLSim/runtime-calldata coverage. The supported local
runtime also now has source-parity deployments and persisted proofs for
successful request creation, approval finality, rejection finality, evidence
repair, timeout expiry, restart recovery, redirect refusal, and one-time
receipt consumption. See `docs/GATE_F_LIVE_CLOSURE_2026-09-27.md` and the
machine-readable evidence retained in the operator's ignored local `work/`
directory.

`deployments/release-manifest.json` now reports the backend release as
`RELEASED` and records the runtime source, patch, binary, configuration, and
mount identities. Its nested `production_deployment.status` remains
`UNRELEASED` until a public or Bradbury deployment is separately authorized
and verified.

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
