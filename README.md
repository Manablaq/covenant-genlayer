# Covenant

**Consensus-enforced authority for autonomous agents, built on GenLayer.**

> AI proposes. GenLayer verifies. Covenant authorizes the exact action.

Covenant is a GenLayer-native authorization protocol for autonomous agents. It determines whether an exact proposed action is permitted by an immutable mandate and evidence policy, then binds any successful authorization to the exact consequential action so it cannot be transferred, mutated, replayed, or consumed by the wrong executor.

## Backend-first rule

The frontend does not begin until the backend has passed all release gates:

1. Current GenLayer constraints researched and frozen.
2. Protocol, state machine, trust model and threat model frozen.
3. Contracts completely implemented.
4. GenVM lint, validation, typecheck and ABI/schema gates pass.
5. Deterministic and adversarial test suites pass.
6. Full-runtime consensus tests prove authorization and denial.
7. Exact reviewed artifacts deploy successfully.
8. Bradbury deployment completes.
9. Source/configuration parity and contract wiring are proven.
10. Live consensus, finality, recovery and receipt-consumption behavior are verified.
11. Backend release evidence is frozen.

Only then may a frontend directory be introduced.

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

## Current phase

**Phase 0 — GenLayer research and backend specification.**

No production contract is complete.
No Bradbury deployment has been attempted.
