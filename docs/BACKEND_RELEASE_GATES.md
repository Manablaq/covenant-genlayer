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

## Immutable backend-verification action record

This release-gates record is the authoritative evidence record for the exact
backend verification action below. It proves the action fields themselves; it
does not claim that production release has already been certified.

- `action_type`: `backend_release_verification`
- `target`: `docs/BACKEND_RELEASE_GATES.md`
- `recipient`: empty bytes
- `value`: `0`
- `payload`: `verify`

The requested action is to verify this backend release-gates record against the
immutable mandate and evidence policy. The target, empty recipient, zero value,
and `verify` payload above are the exact action subject that the authorization
request binds and the evidence substantively proves.

## Fresh Bradbury backend-verification evidence publication — 2026-10-01

This section is a fresh immutable evidence record for the exact backend
verification action defined above. It does **not** claim Gate I, Gate J, or
production release completion.

Current reviewed repository parent:

- `01fc00fc17e64b0e5a6675816666051b92669bb4`

Current Bradbury graph:

- Mandates: `0xd4C0945533C959b094967781815e31ecd0C345F7`
- Authorization: `0x1e55a34a91b227a1fdc27bd7ce675a7f01dc30a2`
- Mandate ID: `0x02efac38045c666e86c806678f31ca80413f21936b415a3f788f0081bacb0e3c`
- Mandate version: `3`
- Mandate commitment: `0x1f16e8de8f41827bdfd93145f4cb10a48f61f52ec39aa233a147bcf08b414b2e`

Observed Bradbury domains are recorded without conflation:

- EVM/transport `eth_chainId`: `4221`
- finalized GenVM execution `gl.message.chain_id`: `1`

`docs/CURRENT_SOURCE_BRADBURY_DOMAIN_PROVENANCE_2026-10-01.json` reproduces the
already-finalized mandate ID and version-3 commitment from execution-domain `1`
and proves the same preimages do not match when `4221` is substituted. This is
an observation of current Bradbury behavior, not a claim that the public
documentation defines the two values as separate namespaces.

The exact action evidenced by this immutable release-gates record remains:

- `action_type`: `backend_release_verification`
- `target`: `docs/BACKEND_RELEASE_GATES.md`
- `recipient`: empty bytes
- `value`: `0`
- `payload`: `verify`

The evidence substantively verifies that this is the requested backend
verification action. Current typed-deployment behavioral recertification,
strict-consensus closure, Bradbury redirect/effective-origin provenance, and
Gate J remain release gates and are not claimed complete by this publication.
