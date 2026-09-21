# Covenant Backend Release Gates

The frontend is blocked until Gate J.

## Gate A — Research freeze

- Current official GenLayer docs reviewed.
- Exact runner/tool versions recorded.
- Storage restrictions verified.
- Nondeterminism/equivalence rules verified.
- Finality/message rules verified.
- Current deployment workflow verified.
- No undocumented size number treated as fact.

## Gate B — Architecture freeze

- Contract graph documented.
- Responsibility of every contract documented.
- State machine frozen.
- Trust boundaries documented.
- Action canonicalization/domain separation frozen.
- Evidence authority/freshness/corroboration rules frozen.
- Every non-terminal state has recovery or expiry.
- Admin powers and prohibited bypasses documented.

## Gate C — Static verification

Every contract passes:

- GenVM lint
- SDK validation
- strict typecheck
- ABI/schema extraction
- source-size measurement

## Gate D — Deterministic tests

Complete coverage of storage, state transitions, authorization binding, replay protection, expiry/recovery and access control.

## Gate E — Adversarial tests

Every applicable threat-model attack has a reproducible test.

## Gate F — Full-runtime consensus tests

Must prove at minimum:

- authorization reaches a consequential result;
- denial reaches a consequential result;
- validator independently verifies decision substance;
- malformed/failing evidence follows the designed repair/retry behavior;
- irreversible consequence does not execute before finality.

Raw validator/transaction evidence is preserved before decoding or summarization.

## Gate G — Pre-Bradbury deployment proof

The exact reviewed graph must deploy in the full runtime before Bradbury.

Record:

- exact source sizes;
- source hashes;
- ABI/schema hashes;
- deployment ordering;
- constructor arguments;
- cross-contract wiring;
- resulting runtime identities.

## Gate H — Bradbury deployment

Use one frozen reviewed deployment plan.

After a transaction is submitted, track it.

Do not blindly retry, rebroadcast or replace it because a client lost state.

## Gate I — Live verification

Prove:

- deployment addresses;
- source parity;
- configuration parity;
- binding/wiring parity;
- consensus status;
- execution result;
- appeal/finality behavior;
- exact receipt generation;
- exact receipt consumption;
- mutation rejection;
- replay rejection;
- wrong-consumer rejection;
- recovery/expiry behavior.

## Gate J — Backend freeze

Freeze:

- git commit/tree;
- source hashes;
- ABI/schema hashes;
- addresses;
- transaction hashes;
- toolchain versions;
- machine-readable verification artifacts;
- reviewer handoff.

Only after Gate J may frontend development begin.
