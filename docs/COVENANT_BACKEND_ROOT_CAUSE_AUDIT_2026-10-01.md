# Covenant backend root-cause audit — 2026-10-01

## Executive result

The repository had two independent blockers conflated in its release logic:

1. It invented a strict-unanimity blocker. GenLayer protocol acceptance is
   majority-based, and a finalized `FINISHED_WITH_RETURN` transaction is not
   made unsuccessful merely by a timeout, a deterministic-violation vote, or
   non-uniform validator result hashes. Those observations remain evidence.
2. The R3 unsigned candidate became stale because the sender's nonce advanced
   from `1516` to `1517` before R4 authorization. R4 correctly stopped before
   signing. The sender is operationally shared; regenerating the old candidate
   would repeat the race.

The current source itself was not changed and does not require redeployment.
The current Authorization source differs from the predecessor only by four
static typing annotations/casts; the semantic contract behavior is unchanged.
Current-source Gate I behavioral proof is still incomplete, and Bradbury
effective-origin provenance remains a real platform blocker under the frozen
evidence policy. Therefore `BACKEND_COMPLETE = NO`.

## Required findings

- `ROOT_CAUSE_NONCE_RACE`: R3 froze an unsigned candidate at EVM nonce `1516`;
  R4's fresh read found `latest=pending=1517` and stopped before signing. The
  sender is evidently used by other activity outside the frozen Covenant
  workflow. The stale fingerprint
  `f24a8482e8d608592e3e7268bfeb3288b18ab08161b6381a1308cbaa98fcbdba` is
  retired and must never be reused.
- `ROOT_CAUSE_FALSE_UNANIMITY_GATE = YES`: the manifest, verifier, and
  behavioral evidence previously treated `strict_unanimity` and
  `DETERMINISTIC_VIOLATION == 0` as release blockers. That is not in
  `BACKEND_RELEASE_GATES.md` and conflicts with the official majority/finality
  model. The fix removes only that blocker; raw votes, result hashes, and
  dissent remain in the evidence records.
- `EFFECTIVE_ORIGIN_GATE = PLATFORM_BLOCKER`: the requirement is explicit in
  the frozen evidence policy/threat model, so it is not merely a new
  self-imposed check. Exact immutable URL, authority, freshness, action,
  publisher, and body digest bindings still provide substitution protection,
  but they do not establish what URL a redirect-following transport actually
  fetched. The available Bradbury behavior does not expose enforceable
  effective URL/history through the supported response API.
- `CONTRACT_SOURCE_DEFECT = NO`: the pinned/local runtime and GLSim evidence
  support `response.status` and `response.headers` for the deployed source.
  Public examples use `status_code`, but that naming difference does not prove
  a defect in the pinned/deployed API. No contract source mutation was made.
- `CONTRACT_REDEPLOY_REQUIRED = NO`: the source hash remains
  `582463cffbe3e0fd55d3154f905a6b5b1cdb1ae3e2c087c08cedfad2d80d405e`, and
  its deployed address remains
  `0x1e55a34a91b227a1fdc27bd7ce675a7f01dc30a2` with source parity.

## Protocol and release-policy correction

The corrected acceptance rule is:

```text
protocol success = consensus_result=AGREE
                   AND status=FINALIZED
                   AND execution_result=FINISHED_WITH_RETURN
```

The `AGREE` result is reached by committee majority under the documented
Equivalence Principle; unanimity is not required. A Covenant semantic result
such as `AUTHORIZED`, `DENIED`, or `EXPIRED` is recorded separately. Validator
dissent and `DETERMINISTIC_VIOLATION` evidence are preserved, and tribunal
handling is recorded as separate judicial/economic handling that does not
automatically rewrite the transaction outcome.

This correction does not mark release complete. Existing behavioral receipts
are bound to predecessor Authorization source `306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c`
at `0x8c1c7169756287a30bceeb28caee4991b5566076`; they cannot prove current
source Gate I behavior.

## Runtime/API audit

Evidence checked:

- pinned `py-genlayer` Depends artifact and local `glsim==0.29.2` / pinned
  `genlayer-test==0.29.2` environment;
- local GLSim response mocks and `glsim/live_io.py`;
- pinned GenVM v0.2.16 provenance recorded in `runtime/README.md`, including
  source commit `387e1a66e920cb2dfadcdce40ab2d28da02efd1e` and the tracked
  no-redirect patch;
- `docs/CURRENT_SOURCE_REDIRECT_PROBE_2026-09-27.json`;
- Authorization GLSim tests.

Answers:

A. `response.status` is correct for the pinned/deployed runtime path and local
GLSim mocks. The public Web Access page's `response.status_code` is a separate
documented surface spelling; it is not evidence that the deployed source must
be edited.

B. `response.headers` is exposed by the local GLSim full response and by the
pinned runtime adapter. The tests and persisted local probe exercise the
headers mapping and observe `Location`.

C. The local GLSim live HTTP handler and the unpatched pinned `reqwest` client
follow redirects before the contract sees the response. The tracked v0.2.16
patch changes this behavior only in the patched local runtime; its probe sees
`status=302` and `Location` without fetching the final resource. The current
Bradbury provenance record reports redirect following and no effective URL or
history field.

D. No supported documented/current API in the checked artifacts, GLSim types,
linter stubs, or official Web Access examples exposes effective URL or redirect
history. An Intelligent Contract cannot enforce effective-origin/history on
Bradbury with the currently evidenced API. The `Location` rejection remains
valid when a redirect response is observable, but is not effective-origin proof
when redirects are followed.

## Effective-origin threat-model decision

This is `PLATFORM_BLOCKER`, not `SELF_IMPOSED`. `docs/EVIDENCE_POLICY.md`
explicitly freezes the redirect boundary and says runtime behavior must prove
the transport before redirected evidence is accepted. The exact body digest,
immutable reference, approved source prefix, authority, publisher, timestamps,
and independent validator re-fetch protect against content substitution but
cannot prove the origin actually observed by a redirect-following runtime.
The release blocker must remain until Bradbury provides a supported no-redirect
boundary or effective URL/history, or the frozen requirement is formally
reviewed and changed.

## Predecessor/current source diff

The predecessor hash is
`306e0ab52bb3c4697bbf4e3c42b62b6eda3a878acee9eecd07ce5a0054ca01c1`; it is
the file at predecessor commit
`3243a739395d4d457a736ac6099dcb7fb79fcac4`. The current hash is
`582463cffbe3e0fd55d3154f905a6b5b1cdb1ae3e2c087c08cedfad2d80d405e` at the
typed deployment commit `6da89ec6e75cd9e8f1aee2be93a539020129c7f2`.

The semantic diff is four typing-only changes:

- `_require_registry_binding`: cast the registry returned by
  `gl.get_contract_at` to `Y`;
- `_lm`: annotate the mandate loaded from `bg.view()` as `Y`;
- `_rf`: cast the registry returned by `gl.get_contract_at` to `Y`;
- `create_request`: cast the registry returned by `gl.get_contract_at` to `Y`.

There are no changed validation branches, storage values, commitments, state
transitions, web access calls, or release semantics.

## Exact remaining work

### Current-source Gate F/G/H/I

Already evidenced and reusable for the current deployment: current Mandates and
Authorization addresses, exact source parity, deployment finality, source
hashes, configured Mandates binding, and typed deployment submission history.
Predecessor behavioral receipts are not reused as current-source proof. The
persisted full-runtime local checkpoint has predecessor Authorization source,
so it does not close Gate G for the current graph.

The minimum remaining live operations are:

1. Against current Authorization `0x1e55a34a91b227a1fdc27bd7ce675a7f01dc30a2`
   and current Mandates `0xd4C0945533C959b094967781815e31ecd0C345F7`, create a
   current-source mandate/request and obtain a finalized successful
   authorization result.
2. Obtain a current-source denial result and preserve validator-independent
   decision-substance evidence.
3. Exercise malformed/failing evidence and the designed repair/retry path on
   current source, including finality and recovery/expiry behavior.
4. Prove exact current-source receipt generation and post-finality consumption.
5. Prove current-source mutation rejection, replay rejection, and wrong-consumer
   rejection with finalized receipts.
6. Preserve raw validator/transaction evidence and bind every result to the
   current source hash/address. No automatic resend, replacement, or rebuild is
   allowed after an authorized candidate becomes stale.

No additional live operation is required solely to obtain unanimous hashes or
zero deterministic-violation votes. Gate G still needs one exact current-source
graph deployment proof in the pinned full runtime, with source/schema hashes,
ordering, wiring, and resulting identities recorded before treating that gate
as closed. Gate H's current typed deployment has a frozen one-plan submission
history and needs no new write in this pass. The remaining behavioral work is
Gate F/I proof, not a redeployment of the already-parity-matched Bradbury
contracts.

### Exact Gate J remaining

After the current-source Gate F/I evidence and the platform provenance boundary
are resolved, freeze the reviewed git commit/tree, current source and
ABI/schema hashes, deployment and transaction identities, toolchain/runtime
versions, machine-readable evidence, and reviewer handoff. Gate J is not
complete now.

## Nonce-race prevention

`scripts/covenant_write_guard.py` is intentionally read-only. Immediately before
any separately authorized signing workflow it checks latest and pending nonce,
requires equality with the frozen candidate nonce, requires the explicitly
authorized fingerprint, rejects the retired R3 fingerprint, and rejects any
candidate that records signing or submission. It never rebuilds after
authorization. It explicitly warns that it is not a cross-process lock; the
sender must be treated as shared, and a dedicated Covenant signer is recommended
for future mandates/releases.

## Safety and handoff

- `signing_performed = NO` for this pass.
- `submission_performed = NO` for this pass.
- `blockchain_writes = 0` for this pass.
- `git_push = NO`.
- No private-key or secret contents are present in the repository changes or
  audit artifacts.
- Production remains `UNRELEASED`; this audit does not fabricate Gate I or Gate
  J proof.

`NEXT_ACTION`: do not regenerate or sign the stale R3 candidate. Close the
exact current-source Gate G full-runtime proof, resolve the Bradbury runtime
provenance blocker with the runtime owner, then schedule one fresh current-source
Gate F/I evidence run using a dedicated Covenant signer and the read-only
pre-sign guard, followed by the Gate J evidence freeze.

## Official documentation checked

- [Transaction statuses](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/transactions/transaction-statuses)
- [Finality](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/finality)
- [Transaction execution](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/transactions/transaction-execution)
- [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [Deterministic violations and tribunals](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/deterministic-violations-and-tribunals)
- [Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access)
- [Querying a transaction](https://docs.genlayer.com/developers/decentralized-applications/querying-a-transaction)
