# Covenant Request State Machine — v1

Status: Gate B freeze.

This document defines Covenant application state.

It does not duplicate GenLayer transaction lifecycle state.

## Lifecycle separation

GenLayer transaction statuses such as `Pending`, `Accepted`, `Undetermined`, `LeaderTimeout`, `ValidatorsTimeout` and `Finalized` belong to the network transaction lifecycle.

Covenant request states belong to protocol application storage.

The two must never be conflated.

In particular:

- Covenant has no application state named `FINALIZED`;
- Covenant has no application state named `UNDETERMINED`;
- an `Accepted` GenLayer transaction is still provisional;
- a GenLayer `Undetermined` result does not fabricate a Covenant request-state transition;
- transaction consensus status and GenVM execution success are verified separately.

If validator consensus is not reached, no newly proposed Covenant application mutation is assumed to have occurred.

## Frozen request states

Covenant v1 uses exactly six persistent request states:

1. `PENDING`
2. `REPAIR_REQUIRED`
3. `AUTHORIZED`
4. `DENIED`
5. `EXPIRED`
6. `CONSUMED`

No other persistent request-state enum may be added without a protocol-version change.

## PENDING

`PENDING` means:

- the Request ID exists;
- its Action Subject is frozen;
- its nonce is reserved/used;
- a current Evidence Set and Action Intent are stored;
- structural request validation passed;
- the request has not reached a terminal application outcome;
- semantic evaluation may proceed.

`PENDING` is not an authorization.

## REPAIR_REQUIRED

`REPAIR_REQUIRED` is a bounded nonterminal state.

It means Covenant has preserved the request because a correctable evidence, source, corroboration or human-approval condition prevents authorization or denial from being decided safely.

The state stores at minimum:

- a frozen Request ID;
- the same frozen Action Subject;
- current Evidence Set commitment;
- current Action Intent;
- evidence revision;
- exact repair reason;
- fixed repair deadline.

Entering `REPAIR_REQUIRED` never authorizes the action.

Repair never changes the Request ID or Action Subject.

## AUTHORIZED

`AUTHORIZED` means Covenant semantic and deterministic policy checks produced an authorization result and a receipt ID is bound to the exact final Action Intent.

`AUTHORIZED` is an application state, not proof that the transaction creating that state has reached GenLayer `Finalized`.

Irreversible consumers must separately respect GenLayer finality.

An authorized receipt remains usable only until the Action Subject expiry and only by its exact authorized consumer.

## DENIED

`DENIED` is terminal.

It means the request received a genuine policy-denial outcome rather than merely experiencing repairable infrastructure or evidence failure.

No receipt exists for a denied request.

No repair transition is allowed from `DENIED`.

## EXPIRED

`EXPIRED` is terminal.

It means a request or receipt crossed a frozen time boundary without reaching the required next transition.

No authorization receipt may be newly created or consumed after expiry.

Expiry is not semantic policy denial.

## CONSUMED

`CONSUMED` is terminal.

It means the exact authorized consumer successfully consumed the exact receipt once.

A consumed receipt can never become unconsumed.

## Terminal states

The terminal application states are:

- `DENIED`;
- `EXPIRED`;
- `CONSUMED`.

No method may transition out of a terminal application state.

## Nonterminal states

The nonterminal states are:

- `PENDING`;
- `REPAIR_REQUIRED`;
- `AUTHORIZED`.

Every nonterminal state has a deterministic expiry or recovery path.

## Request creation identity rule

The `agent` field is an explicit GenLayer address.

For Covenant v1 request creation:

`gl.message.sender_address` must equal the frozen `agent` address.

`gl.message.origin_address` is not substituted for the immediate caller in this authorization check.

This means relayed request creation is not part of Covenant v1.

A later protocol version may introduce explicit delegation, but v1 does not infer delegation.

## Mandate issuance identity rule

For mandate-version issuance, the immediate sender must equal the mandate issuer or the exact issuance authority explicitly frozen by the registry rules.

No transaction origin shortcut grants issuance authority.

## Receipt-consumer identity rule

Manual receipt consumption requires:

`gl.message.sender_address == authorized_consumer`

The transaction origin is not used as a substitute.

## Request creation sequence

A request-creation write follows this deterministic ordering:

1. authenticate the immediate caller as the agent;
2. load the exact mandate ID/version;
3. require the mandate version to be eligible for new requests;
4. verify the supplied/frozen mandate commitment;
5. derive deterministic transaction `issued_at` from GenVM transaction time;
6. validate the requested expiry under the mandate lifetime rules;
7. derive the Action Subject;
8. derive the stable Request ID from the Action Subject;
9. derive the nonce namespace key;
10. require the nonce key to be unused;
11. structurally validate the evidence submission;
12. derive the current Evidence Set and Action Intent;
13. reserve the nonce permanently for that Request ID;
14. persist the request in exactly one initial application state.

`issued_at` is contract-derived transaction time. It is not trusted caller input.

## Invalid creation versus persisted outcome

Covenant distinguishes malformed creation from a valid request that receives a negative outcome.

Conditions that prevent a request identity from being safely created cause the transaction to fail without creating request state.

Examples include:

- wrong agent caller;
- nonexistent mandate version;
- mandate version not eligible for new requests;
- mandate commitment mismatch;
- already-used nonce;
- invalid expiry encoding;
- malformed consequential field width.

Once a structurally valid request identity is created, negative protocol outcomes are persisted rather than disguised as missing state.

## Initial state selection

After structural creation succeeds:

- deterministic mandate violation may persist `DENIED` with a deterministic-policy reason;
- repairable evidence/policy incompleteness persists `REPAIR_REQUIRED`;
- otherwise the request enters `PENDING`.

Request creation itself does not semantically authorize an action.

## Evidence revision

Every request stores an `evidence_revision`.

Initial evidence uses revision `0`.

Every accepted evidence replacement increments the revision exactly once.

A source retry that changes no evidence does not increment the revision.

Evidence revision is protocol metadata and does not replace cryptographic commitment comparison.

## Repair deadline

On the first transition of a request into `REPAIR_REQUIRED`, Covenant sets:

```text
repair_deadline = min(
    request_expires_at,
    transition_time + mandate_repair_window
)
```

`transition_time` is deterministic GenVM transaction time.

Once set, the repair deadline is never extended for that request.

Re-entering `REPAIR_REQUIRED` preserves the original repair deadline.

A repair is timely only while:

```text
now < repair_deadline
and
now < request_expires_at
```

Equality with either deadline is expired, not timely.

This prevents repeated repairs or retries from extending the request indefinitely.

## Request expiry

The Action Subject `expires_at` is the ultimate request and receipt expiry.

Covenant v1 does not create a separate later receipt-expiry timestamp.

No transition may authorize or consume a request when:

`now >= request_expires_at`

Expiry may be materialized by a permissionless deterministic expiry write.

Passage of time does not require Covenant to invent an automatic background transaction.

## Mandate supersession

Mandate supersession or deactivation affects future request creation only.

An already-created request continues under the exact immutable mandate version and commitment frozen at creation until the request reaches a terminal state or expires.

A mandate issuer cannot retroactively cancel, rewrite or deny an existing request merely by publishing a later mandate version.

This rule prevents future-facing administrative authority from becoming an authorization bypass or retroactive veto.

## Permissionless progress

Semantic evaluation and deterministic expiry may be triggered by any caller unless a later implementation constraint requires a narrower caller for a documented security reason.

The caller who pays to advance evaluation receives no authorization right merely by advancing it.

Evidence replacement is not permissionless; it follows the repair authority rule frozen in the evidence-policy section.

## Semantic evaluation

Semantic interpretation occurs only inside GenLayer nondeterministic execution.

The accepted structured result is consumed by deterministic code after consensus.

The semantic result may direct exactly one of these application outcomes:

- `AUTHORIZED`;
- `DENIED`;
- `REPAIR_REQUIRED`.

Validators must independently verify the decision-bearing substance under the same frozen mandate and evidence criteria.

Validator checks that inspect only leader JSON shape, allowed enums or confidence ranges are insufficient.

## Consensus failure is not an application state

If the network does not accept a semantic evaluation transaction, Covenant does not synthesize `DENIED`, `REPAIR_REQUIRED` or any other request outcome merely from that consensus failure.

An `Undetermined`, timeout, rejected execution or other network-level unsuccessful attempt is tracked as transaction evidence while the last successfully materialized Covenant application state remains authoritative.

This distinction is mandatory for reviewer evidence and retry logic.

## Legal transition table

The only legal v1 application transitions are:

```text
ABSENT -> PENDING
ABSENT -> REPAIR_REQUIRED
ABSENT -> DENIED

PENDING -> AUTHORIZED
PENDING -> DENIED
PENDING -> REPAIR_REQUIRED
PENDING -> EXPIRED

REPAIR_REQUIRED -> PENDING
REPAIR_REQUIRED -> AUTHORIZED
REPAIR_REQUIRED -> DENIED
REPAIR_REQUIRED -> REPAIR_REQUIRED
REPAIR_REQUIRED -> EXPIRED

AUTHORIZED -> CONSUMED
AUTHORIZED -> EXPIRED
```

No other transition is legal.

## Meaning of REPAIR_REQUIRED -> REPAIR_REQUIRED

This self-transition is permitted only when:

- the request is still before its already-fixed repair deadline;
- a permitted retry or repaired evidence attempt is evaluated;
- the accepted result still identifies a repairable condition;
- the original repair deadline is preserved;
- the Action Subject and Request ID remain unchanged.

It must never refresh or extend liveness.

## Evidence replacement transition

A successful evidence repair follows:

```text
REPAIR_REQUIRED
    -> validate repair authority and deadline
    -> validate allowed evidence-only mutation
    -> increment evidence_revision
    -> replace current Evidence Set commitment
    -> replace current Action Intent
    -> preserve Action Subject
    -> preserve Request ID
    -> PENDING
```

The receipt ID does not exist before authorization.

## Source retry transition

If the repair reason is specifically source retry and no evidence bytes change, evaluation may retry from `REPAIR_REQUIRED` without incrementing evidence revision.

A source retry never extends the existing repair deadline.

The accepted retry outcome may move directly to `AUTHORIZED`, `DENIED`, remain `REPAIR_REQUIRED`, or reach `EXPIRED` if the deadline has passed.

## Authorization transition

`PENDING -> AUTHORIZED` or permitted source-retry `REPAIR_REQUIRED -> AUTHORIZED` requires:

- request not expired;
- repair deadline satisfied when applicable;
- exact Action Subject unchanged;
- current evidence policy satisfied;
- current Action Intent recomputed and matched exactly;
- semantic consensus result authorizes the exact current Action Intent;
- deterministic constraints rechecked before storage mutation;
- receipt ID derived from stable Request ID plus exact final Action Intent.

After authorization, evidence repair is closed.

## Denial transition

`DENIED` may result from deterministic mandate violation or an accepted semantic policy-denial result.

Infrastructure failure, source timeout, missing repairable corroboration or other correctable evidence problems must not be silently mapped to `DENIED`.

## Consumption transition

`AUTHORIZED -> CONSUMED` requires all of the following deterministic checks:

- caller equals authorized consumer;
- request state is exactly `AUTHORIZED`;
- receipt exists;
- receipt ID matches stored receipt;
- supplied Action Intent matches the exact authorized final Action Intent;
- current time is strictly before request expiry;
- receipt has not already been consumed.

Successful consumption permanently closes the receipt.

## Finality precondition for irreversible consumption consequences

The Covenant state machine cannot substitute for GenLayer transaction finality.

A consumer integration must not treat an authorization as irreversible until the transaction that created the authorization is `Finalized`.

A consumer integration must likewise not treat manual consumption as irreversible until the consumption transaction reaches the required finality for that consequence.

Where Covenant itself dispatches an irreversible internal message, v1 uses finalized message timing.

## Terminal-state immutability

For `DENIED`, `EXPIRED` and `CONSUMED`:

- evidence replacement is forbidden;
- semantic reevaluation is forbidden;
- nonce reset is forbidden;
- Action Subject mutation is forbidden;
- Request ID mutation is forbidden;
- receipt fabrication or replacement is forbidden.

## State-machine invariants

The following are hard Covenant v1 invariants:

1. one Request ID maps to one immutable Action Subject;
2. one used nonce key cannot create another request;
3. evidence repair can change Evidence Set and Action Intent but not Request ID;
4. repair deadlines never extend;
5. mandate supersession never rewrites an existing request;
6. authorization receipt creation requires an authorization outcome;
7. a receipt binds the exact final Action Intent;
8. one receipt can be consumed at most once;
9. wrong-consumer consumption fails;
10. expired requests cannot authorize or consume;
11. semantic consensus failure does not fabricate application state;
12. terminal application states have no outgoing transitions;
13. admin or issuer authority cannot directly create `AUTHORIZED` or `CONSUMED`;
14. accepted-but-not-final network state is never treated as irreversible finality.

## Consequential semantic-result schema

The nondeterministic semantic path returns a small structured result whose consequential fields are checked exactly.

V1 decision codes are:

- `1 AUTHORIZE`;
- `2 DENY`;
- `3 REPAIR`.

The consequential result contains at minimum:

- exact `request_id`;
- exact current `action_intent`;
- exact decision code;
- exact repair-reason code.

For `AUTHORIZE`, repair reason must be `NONE`.

For `DENY`, repair reason must be `NONE`.

For `REPAIR`, repair reason must be one of codes `1` through `9`.

Free-form analysis may exist for validator reasoning or test evidence, but it does not replace exact comparison of consequential result fields.

The contract derives the receipt deterministically. A leader never supplies an authoritative receipt ID.

## Validator obligation

The validator must independently verify the decision-bearing substance under the same:

- Request ID;
- Action Subject;
- current Action Intent;
- immutable mandate version;
- deterministic policy;
- semantic criteria;
- evidence policy;
- human co-authorization state.

A validator that checks only output shape, enum membership, reasoning presence or a confidence range is insufficient.

If the validator cannot independently justify the consequential result, it rejects the leader proposal.

If GenLayer cannot reach consensus, no new Covenant application transition is inferred.

## Repair-reason enum

The only persistent v1 repair-reason values are:

```text
0 NONE
1 SOURCE_UNAVAILABLE
2 SOURCE_TIMEOUT
3 SOURCE_MALFORMED
4 EVIDENCE_INTEGRITY_MISMATCH
5 EVIDENCE_STALE
6 EVIDENCE_AUTHORITY_INVALID
7 EVIDENCE_REFERENCE_INVALID
8 CORROBORATION_MISSING
9 HUMAN_APPROVAL_MISSING
```

`repair_reason` must be `NONE` whenever request state is not `REPAIR_REQUIRED`.

Entering `REPAIR_REQUIRED` requires a non-zero repair reason.

Leaving `REPAIR_REQUIRED` clears the active repair reason to `NONE`.

Transaction history and preserved test evidence remain available for audit; the active reason field does not need to remain non-zero after remediation.

## Repair classification rule

A repair reason describes why Covenant cannot safely decide or authorize yet.

It is not itself an authorization and is not semantic denial.

Correctable source/evidence/human-precondition conditions use `REPAIR_REQUIRED` while their fixed repair window remains open.

If the fixed repair deadline is reached, the request expires rather than being relabeled as policy denial.

## SOURCE_UNAVAILABLE

`SOURCE_UNAVAILABLE` means the required authoritative source could not be retrieved during an accepted evaluation attempt.

Permitted remediation before the fixed deadline:

- permissionless retry of unchanged evidence;
- request-agent replacement of evidence allowed by the frozen mandate.

The result may remain `REPAIR_REQUIRED`, return to `PENDING`, authorize, deny after a successful substantive evaluation, or expire according to the legal transition rules.

## SOURCE_TIMEOUT

`SOURCE_TIMEOUT` means retrieval did not complete in the evaluation attempt.

It is not policy denial.

Permitted remediation before the fixed deadline:

- permissionless unchanged-evidence retry;
- request-agent evidence replacement.

The original repair deadline is preserved.

## SOURCE_MALFORMED

`SOURCE_MALFORMED` means an authoritative response was retrieved but could not be safely interpreted under the required evidence-processing format.

Permitted remediation before the fixed deadline:

- permissionless retry of the same committed evidence;
- request-agent evidence replacement.

Malformed source material is never treated as proof of the semantic proposition.

## EVIDENCE_INTEGRITY_MISMATCH

`EVIDENCE_INTEGRITY_MISMATCH` means retrieved or supplied content does not satisfy its committed integrity binding.

The mismatching content cannot authorize.

Remediation requires request-agent evidence replacement before the fixed deadline.

The replacement produces a new Evidence Record commitment, Evidence Set commitment and Action Intent while preserving Action Subject and Request ID.

## EVIDENCE_STALE

`EVIDENCE_STALE` means the evidence fails the frozen freshness arithmetic at the current evaluation time.

Stale evidence cannot authorize.

Remediation requires request-agent replacement with evidence that satisfies the same frozen authority and freshness policy before the fixed deadline.

## EVIDENCE_AUTHORITY_INVALID

`EVIDENCE_AUTHORITY_INVALID` means the record does not satisfy the frozen authority identity/role rule.

The invalid authority cannot authorize.

Remediation requires request-agent replacement with evidence from a permitted authority.

Publishing more records from the same invalid authority does not satisfy the condition.

## EVIDENCE_REFERENCE_INVALID

`EVIDENCE_REFERENCE_INVALID` means the record fails the frozen immutable/versioned-reference or approved-source rule.

The invalid reference cannot authorize.

Remediation requires request-agent evidence replacement under the same mandate policy.

## CORROBORATION_MISSING

`CORROBORATION_MISSING` means the current Evidence Set does not satisfy the required number of distinct permitted corroborating authorities.

Remediation requires the request agent to add or replace evidence before the fixed deadline.

Multiple records from one corroborating authority do not satisfy multiple distinct-authority slots.

The primary authority cannot count toward the corroboration minimum.

## HUMAN_APPROVAL_MISSING

`HUMAN_APPROVAL_MISSING` means the frozen human policy requires co-authorization and the request has not yet recorded it.

Evidence replacement cannot satisfy this reason.

The exact frozen human approver must submit approval before both the fixed repair deadline and request expiry.

## Evidence-replacement method

Evidence replacement is allowed only from `REPAIR_REQUIRED` and only before the fixed repair deadline and request expiry.

The immediate caller must equal the frozen request agent.

The replacement method must:

1. load the existing request;
2. require state `REPAIR_REQUIRED`;
3. require an evidence-remediable active repair reason;
4. authenticate the immediate caller as the request agent;
5. require `now < repair_deadline`;
6. require `now < request_expires_at`;
7. preserve Action Subject exactly;
8. preserve Request ID exactly;
9. structurally validate replacement Evidence Records;
10. enforce evidence-record count bounds;
11. recompute Evidence Record commitments;
12. recompute Evidence Set commitment;
13. reject duplicate record commitments;
14. recompute Action Intent;
15. require the new Action Intent to differ when committed evidence actually changed;
16. increment `evidence_revision` exactly once;
17. clear active repair reason;
18. transition to `PENDING`.

Evidence replacement does not semantically authorize or deny the request.

Semantic evaluation happens in a separate legal transition.

## Evidence-remediable reasons

The request-agent replacement method is permitted for:

- `SOURCE_UNAVAILABLE`;
- `SOURCE_TIMEOUT`;
- `SOURCE_MALFORMED`;
- `EVIDENCE_INTEGRITY_MISMATCH`;
- `EVIDENCE_STALE`;
- `EVIDENCE_AUTHORITY_INVALID`;
- `EVIDENCE_REFERENCE_INVALID`;
- `CORROBORATION_MISSING`.

It is not a remediation for `HUMAN_APPROVAL_MISSING`.

## Permissionless unchanged-evidence retry

Permissionless unchanged-evidence retry is allowed only for:

- `SOURCE_UNAVAILABLE`;
- `SOURCE_TIMEOUT`;
- `SOURCE_MALFORMED`.

The retry must preserve:

- Action Subject;
- Request ID;
- Evidence Set commitment;
- Action Intent;
- evidence revision;
- repair deadline.

The accepted retry result may:

- move to `AUTHORIZED`;
- move to `DENIED` after genuine substantive evaluation;
- remain `REPAIR_REQUIRED` with the same or another valid repair reason;
- move to `EXPIRED` when the deterministic deadline condition is reached.

A permissionless caller gains no policy authority from triggering the retry.

## Human approval submission

Human approval is a deterministic request transition prerequisite, not an LLM verdict.

Approval submission is valid only when:

- request state is `REPAIR_REQUIRED`;
- active repair reason is `HUMAN_APPROVAL_MISSING`;
- mandate human mode is `SINGLE_ADDRESS`;
- immediate caller equals the exact frozen approver;
- approval has not already been recorded;
- `now < repair_deadline`;
- `now < request_expires_at`;
- Request ID matches stored Request ID;
- Action Subject matches stored Action Subject.

Successful approval:

- sets the approved flag;
- records the exact approver;
- records deterministic approval transaction time;
- does not alter evidence;
- does not increment evidence revision;
- does not alter Action Subject;
- does not alter Request ID;
- clears active repair reason;
- transitions `REPAIR_REQUIRED -> PENDING`.

Human approval never directly creates `AUTHORIZED`.

Semantic and deterministic authorization checks still execute afterward.

## Human mode NONE invariant

When human mode is `NONE`, no human-approval method can grant extra authority or change a request outcome.

Human approval state must not be required for evaluation under mode `NONE`.

## Evaluation preconditions

Before a semantic evaluation may produce `AUTHORIZED` or `DENIED`, deterministic code rechecks at minimum:

- request state is eligible for evaluation;
- request is not expired;
- fixed repair deadline is satisfied when applicable;
- stored Request ID matches the frozen Action Subject;
- mandate ID/version/commitment are unchanged;
- current Action Intent recomputes exactly;
- nonce association remains valid;
- deterministic policy constraints pass;
- evidence count bounds pass;
- authority and role rules pass;
- freshness arithmetic passes;
- distinct-authority corroboration passes;
- required human approval is present;
- authorized consumer remains unchanged.

Failure of a deterministic authorization prerequisite cannot be waived by an LLM or leader result.

## Semantic AUTHORIZE result

An accepted semantic `AUTHORIZE` result may transition to `AUTHORIZED` only if all deterministic preconditions still pass after nondeterministic consensus returns.

Deterministic code then:

- verifies exact returned Request ID;
- verifies exact returned Action Intent;
- requires repair reason `NONE`;
- recomputes the Receipt ID from stable Request ID and exact final Action Intent;
- stores the receipt;
- clears any active repair reason;
- enters `AUTHORIZED`.

The semantic leader cannot choose the stored Receipt ID.

## Semantic DENY result

An accepted semantic `DENY` result transitions to `DENIED` only when the request reached substantive policy evaluation rather than merely encountering a repairable source/evidence condition.

The returned Request ID and Action Intent must match exactly and repair reason must be `NONE`.

No authorization receipt is created.

## Semantic REPAIR result

An accepted semantic `REPAIR` result requires:

- exact Request ID;
- exact current Action Intent;
- decision code `REPAIR`;
- one non-zero valid repair-reason code.

The deterministic post-consensus path enters or remains in `REPAIR_REQUIRED` and preserves the original repair deadline if one already exists.

The leader cannot extend the deadline.

## Expiry materialization

Expiry is deterministic and permissionless.

For `PENDING` or `AUTHORIZED`, expiry is materializable when:

`now >= request_expires_at`

For `REPAIR_REQUIRED`, expiry is materializable when either:

```text
now >= repair_deadline
or
now >= request_expires_at
```

Expiry transitions the request to `EXPIRED`.

Expiry creates no receipt and grants no caller authority.

## Receipt lifecycle

A receipt exists only in `AUTHORIZED` or `CONSUMED`.

The receipt stores or permits deterministic recovery of:

- Receipt ID;
- Request ID;
- exact authorized final Action Intent;
- exact authorized consumer;
- consumed flag/state.

An expired authorization may retain historical receipt identity for audit, but the receipt is unusable after request expiry.

## Core v1 consumption model

Covenant v1 core uses explicit consumer-initiated receipt consumption.

It does not claim that an arbitrary downstream action is atomically executed by the CovenantAuthorization contract.

The authorized consumer calls the consumption method and must be the immediate caller.

The core protocol records one-time consumption.

Any external consequence beyond that boundary belongs to the reviewed consumer integration.

## Finality and consumption

The contract cannot treat its own currently executing transaction as proof of future GenLayer finality.

Therefore the core contract does not fabricate a `FINALIZED` request state.

The consumer integration must wait for the transaction that created `AUTHORIZED` to reach network finality before submitting an irreversible consequence that relies on that authorization.

Likewise, application code must distinguish consumption-transaction status from successful execution.

Gate F and Gate I must test accepted-but-not-final attempts explicitly.

## Supersession test semantics

Publishing or activating a newer mandate version while a request is active must not mutate that request.

The active request continues against its frozen mandate ID, version and commitment until terminal state or expiry.

The required adversarial supersession test therefore proves non-retroactivity rather than expecting a `MANDATE_SUPERSEDED` request state.

## Administrative impossibility rules

No issuer, owner or administrator may directly:

- transition `PENDING` to `AUTHORIZED`;
- transition `REPAIR_REQUIRED` to `AUTHORIZED` without the normal evaluation path;
- transition any state to `CONSUMED` without the authorized consumer path;
- replace the frozen agent;
- replace the authorized consumer;
- reset a used nonce;
- extend a repair deadline;
- extend request expiry;
- rewrite Action Subject;
- rewrite Request ID;
- fabricate or replace a receipt;
- convert an expired request back to a live state.

## Raw runtime evidence requirement

State-machine correctness in deterministic tests is necessary but insufficient for backend release.

Gate F full-runtime tests must preserve raw validator/transaction response evidence before decoding or summarizing it.

Those tests must show at minimum a real authorization path and a real denial path reaching consequential application results under validator consensus.

Repair/source-failure behavior must also be exercised at the full-runtime layer where applicable.

## State Machine Part 2 invariants

The following additional invariants are frozen:

1. repair reason `NONE` is never an active `REPAIR_REQUIRED` reason;
2. only codes `1..9` may explain `REPAIR_REQUIRED`;
3. unchanged-evidence permissionless retry is limited to source unavailable, timeout or malformed;
4. evidence replacement is agent-only;
5. evidence replacement never changes Request ID or Action Subject;
6. evidence replacement increments evidence revision exactly once;
7. human approval is approver-only and never increments evidence revision;
8. human approval returns the request to `PENDING`, never directly to `AUTHORIZED`;
9. semantic leader output never supplies authoritative Receipt ID;
10. deterministic authorization prerequisites are rechecked after consensus;
11. repair deadline cannot be extended by leader, validator, agent, approver or administrator;
12. repair deadline exhaustion produces expiry, not semantic denial;
13. mandate supersession is non-retroactive;
14. core receipt consumption is explicit and one-time;
15. network finality remains distinct from Covenant application state.
