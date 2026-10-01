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

**UNRELEASED CURRENT CANDIDATE — the Mandates and corrected Authorization
sources are deployed/finalized on Bradbury with exact source parity. The
available approval, denial, repair/replacement, expiry recovery, receipt
consumption, and negative receipt paths are explicitly bound to the predecessor
Authorization deployment and are not current-source Gate I proof. Production
remains unreleased because current-source behavioral recertification is open,
Bradbury does not expose an enforceable effective URL/history for approved-host
provenance, and Gate J still requires the final evidence freeze.**

The candidate retains mandate-bound evidence-body limits, bounded user-controlled
inputs, one-time verified mandate-policy loading, all public Mandates methods,
validation branches, commitment preimages, storage values, and state transitions.
The compact diagnostic-code redesign and the corrected local candidate pass
Direct, GLSim, adversarial, runtime-calldata, reference-vector, and Gate D
coverage. The supported-local live deployment evidence in the checkpoint is
explicitly pre-compact evidence and is not current-candidate source parity.

The R3 unsigned `create_request` candidate was frozen at EVM nonce `1516`. R4
found latest/pending nonce `1517` and stopped before signing; the stale
fingerprint is retired and must not be reused. The sender is treated as shared
with other activity, so the read-only `scripts/covenant_write_guard.py` performs
a final latest/pending and fingerprint check but is not a cross-process lock.

The older supported-local live checkpoint is historical predecessor-source
evidence. It is not used for current-source parity or Bradbury claims.

`docs/GATE_F_LIVE_CLOSURE_2026-09-27.md` remains historical predecessor-source
evidence and is not used to establish the current-source claims.

`deployments/release-manifest.json` records the finalized current-source
Bradbury deployments and the remaining release boundaries. The backend and
nested `production_deployment.status` remain `UNRELEASED` until current-source
Gate F/G/I, effective-origin provenance, and Gate J are closed.

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

Before any separately authorized write workflow, run the read-only Covenant
guard against the already authorized unsigned candidate. It refuses nonce drift,
retired fingerprints, mismatched fingerprints, and any candidate that records
signing or submission; it never rebuilds a candidate after authorization.
