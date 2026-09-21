# Covenant Architecture — v1 Gate B Freeze

Status: Gate B freeze.

No production Intelligent Contract implementation begins until every Gate B item is frozen.

## Protocol question

Covenant answers:

> May this exact autonomous agent perform this exact consequential action under this exact immutable mandate version using this exact evidence?

A semantic yes is insufficient. Authorization must be bound to the exact consequence.

## v1 contract graph

Covenant v1 owns exactly two production Intelligent Contracts:

1. `CovenantMandates`
2. `CovenantAuthorization`

Downstream executors and consumer contracts are integration boundaries. They are not additional Covenant-owned state contracts.

```text
mandate issuer
      |
      v
CovenantMandates
  immutable/versioned mandate records
      |
      | synchronous exact-version view
      v
CovenantAuthorization
  request -> evidence -> decision -> receipt -> consumption
      |
      | authorized-consumer boundary
      v
external consumer / executor
```

## CovenantMandates responsibility

`CovenantMandates` is the append-only registry of mandate versions.

A published mandate version is immutable.

Creating version N+1 never rewrites version N.

It owns:

- mandate identity and version;
- issuer identity;
- eligibility for new requests;
- deterministic policy constraints;
- semantic criteria;
- evidence-authority rules;
- freshness rules;
- corroboration rules;
- risk tier;
- optional human co-authorization policy;
- the frozen mandate commitment once canonicalization is finalized.

Issuer powers are future-facing only. An issuer cannot rewrite a historical version, set an authorization verdict, manufacture a receipt, consume a receipt, or bypass validator consensus.

## CovenantAuthorization responsibility

`CovenantAuthorization` owns the complete lifecycle after request creation.

It owns:

- frozen Action Intent fields;
- exact mandate ID, version and commitment binding;
- evidence-set binding;
- evidence validation and repair state;
- semantic decision state;
- bounded deadlines and expiry;
- authorization receipt state;
- authorized consumer binding;
- nonce and replay state;
- one-time receipt consumption.

Keeping decision, receipt and consumption state together avoids an unnecessary asynchronous Covenant-to-Covenant write boundary.

Only `CovenantAuthorization` may create a Covenant authorization receipt.

Only `CovenantAuthorization` records whether that receipt has been consumed.

## Deployment relationship

`CovenantMandates` is deployed first.

`CovenantAuthorization` is then deployed with the frozen `CovenantMandates` address.

That registry binding is not replaceable after deployment in v1.

Both production contracts are frozen/non-upgradable by default.

## Trust boundaries

Covenant treats the following as distinct trust boundaries:

- mandate issuer;
- autonomous agent;
- transaction submitter;
- immediate caller;
- evidence publisher;
- evidence transport or web source;
- GenLayer leader;
- validating committee;
- authorized receipt consumer;
- downstream executor;
- RPC, browser and frontend state.

No boundary inherits authority merely because another boundary supplied matching data.

In particular, matching text on an arbitrary web page is not authority, a leader proposal is not a verdict, a browser cache is not canonical state, and transaction submission is not final authorization.

## Caller and origin boundary

GenVM exposes the immediate caller as `gl.message.sender_address` and the original transaction submitter as `gl.message.origin_address`.

Covenant treats those identities as semantically different.

Access-control rules must explicitly choose the correct identity for the rule being enforced.

No authorization rule may silently substitute origin for sender or sender for origin.

Agent identity is an explicit Action Intent field. It is not inferred merely from whichever caller field is convenient.

The exact request-creation caller rule is frozen with the Action Intent and state machine before implementation.

## Chain and execution-domain boundary

`gl.message.chain_id` supplies the current chain identity.

The Action Intent binds a chain/domain value so an authorization created for one execution domain cannot be reused in another.

The final canonical domain-separation bytes are frozen separately before production code.

## Time boundary

Covenant expiry and repair arithmetic uses deterministic GenVM transaction time.

It does not use validator host wall-clock time.

It does not depend on a block number because ordinary GenVM transaction context does not expose block height.

Every non-terminal application state must either have an explicit deadline or an explicitly defined deterministic next transition.

## Finality boundary

GenLayer `Accepted` is provisional.

An accepted transaction may still be appealed and later recomputed.

`Accepted` therefore does not mean that an authorization may already drive an irreversible external consequence.

Consensus status and successful GenVM execution are separate facts and both must be verified.

Covenant contract code must not claim to introspect the future finality of the transaction currently executing.

Lifecycle finality is established by GenLayer transaction status and lifecycle processing.

Applications that act on Covenant state must use finalized state for irreversible behavior.

## Internal message finality rule

Internal Intelligent Contract writes are asynchronous child transactions.

An internal message is not a synchronous atomic continuation of the parent transaction.

For any irreversible Covenant-triggered internal consequence, v1 uses `emit(..., on="finalized")`.

V1 does not use `on="accepted"` for irreversible authorization consequences.

The child transaction enters consensus independently and its own execution result must still be checked.

## External message finality rule

External GenVM-to-EVM messages are finalized-only in GenLayer.

Covenant does not design around an acceptance-stage external EVM effect.

External execution success remains a separate fact from Covenant authorization.

## Receipt finality rule

An authorization receipt may exist in provisional contract execution state before the transaction that created it has finalized.

That provisional observation is not permission for irreversible action.

A consumer or integration must not treat receipt creation as durable until the creating transaction is Finalized.

Likewise, a receipt-consumption transaction is not an irreversible success merely because it is Accepted.

If a downstream consequence is dispatched by Covenant itself, the safe v1 path is finalized message emission.

If a downstream consequence is executed outside Covenant, that integration must independently wait for the relevant Covenant transaction finality before treating the authorization or consumption as irreversible.

## Consumer boundary

Every authorization receipt binds exactly one authorized consumer.

The consumer field is frozen with the Action Intent.

Receipt consumption must reject:

- a wrong consumer;
- a wrong action commitment;
- a missing receipt;
- a denied request;
- a repair or retry state;
- an expired receipt;
- an already consumed receipt.

Receipt consumption is a deterministic state transition.

One receipt can be consumed at most once.

Covenant does not claim arbitrary off-protocol external execution is atomically coupled to receipt consumption.

Atomicity beyond Covenant exists only when the specific integration architecture proves it.

## Evidence trust boundary

Evidence is untrusted until validated under the exact mandate version bound to the request.

An evidence record must bind enough information to verify, as applicable:

- approved publisher or authority identity;
- stable evidence record identity;
- immutable or explicitly versioned reference;
- content digest;
- publication time;
- observation time;
- freshness or expiry;
- evidence role;
- required corroboration relationship.

URL ownership or matching page text alone is not sufficient evidence authority.

A digest proves content identity only after the policy establishes why that content source is trusted.

Evidence requirements come from the frozen mandate version rather than from leader discretion.

## Leader and validator boundary

Leader output is untrusted proposed execution data.

A leader cannot authorize an action merely by returning valid JSON, an allowed enum, non-empty reasoning or a confidence value.

Validators must independently verify or independently derive the decision-bearing substance required by the frozen mandate and evidence policy.

Exact consequential fields use exact comparison after extraction.

No tolerance is permitted for mutation of recipient, target, value, consumer, nonce, mandate identity, action commitment, evidence-set commitment, chain/domain or another consequential binding.

Free-form explanatory reasoning may differ when it is not itself consequential.

## Nondeterminism boundary

Web access, LLM interpretation and other nondeterministic work occur only inside GenLayer nondeterministic execution.

Storage mutation and consequential message emission occur outside the nondeterministic block.

Deterministic execution consumes only the structured consensus result accepted under the configured equivalence principle.

Deterministic rules are not delegated to an LLM when contract code can prove them directly.

## Evidence failure classification

Covenant separates evidence or infrastructure failure from semantic policy denial.

Potentially correctable conditions include, where applicable:

- temporary source unavailability;
- fetch failure;
- transport failure;
- malformed retrieved representation;
- digest mismatch that can be corrected by an allowed replacement record;
- missing required corroboration that may still arrive before deadline.

Such conditions must not silently become policy denial.

The final state machine defines which conditions are repairable and which are terminal.

## Repair boundary

A repairable request persists an explicit repair or retry state plus a bounded deadline.

Repair may modify only evidence material explicitly permitted by the frozen state-machine transition.

Repair may never modify:

- agent identity;
- mandate ID;
- mandate version;
- mandate commitment;
- action type;
- target;
- recipient;
- value;
- payload commitment;
- authorized consumer;
- nonce;
- chain/domain;
- original request identity.

Repair before the deadline is processed under the same frozen action and mandate bindings.

Repair after the deadline is rejected.

No request may remain indefinitely repairable.

## Replay boundary

Covenant uses both nonce state and receipt-consumption state.

A request nonce cannot be silently reset for an existing request.

A valid authorization for one request cannot be replayed as a different request.

A consumed receipt cannot return to an unconsumed state.

The exact nonce namespace and receipt identifier derivation are frozen separately before implementation.

## Mandate supersession boundary

A later mandate version may stop an older version from accepting new requests according to the frozen mandate rules.

It cannot rewrite the mandate bytes already bound to an existing request.

The state machine will explicitly define whether an already-created request continues, expires, or terminates when its mandate is superseded.

That behavior will not be left to UI interpretation.

## Administrative boundary

Administrative or issuer authority is future-facing and narrowly scoped.

No administrative surface may manufacture consensus authorization for an existing request.

Forbidden powers include:

- `force_authorize`;
- `admin_approve`;
- `set_verdict`;
- `skip_consensus`;
- `owner_finalize`;
- historical mandate mutation;
- receipt fabrication;
- receipt-consumption override;
- nonce reset for an existing request;
- consumer replacement for a frozen request;
- unrestricted evidence replacement.

## Upgrade boundary

Covenant v1 production contracts are frozen by default.

No upgrader address is part of the intended v1 deployment plan.

A future protocol revision is deployed as new reviewed contracts rather than silently replacing the verified authorization logic behind existing addresses.

## Browser, RPC and client boundary

Browser state, RPC responses and local caches are observation layers, not canonical protocol state.

A client losing a transaction hash does not prove the transaction failed.

After transaction submission, recovery must search for and reconcile the original transaction before any retry or replacement decision.

No deployment or authorization transaction is blindly rebroadcast merely because a UI lost state.

## Architecture consequence

The trust model deliberately keeps the v1 owned graph small:

- immutable/versioned policy in `CovenantMandates`;
- request, decision, receipt and one-time consumption in `CovenantAuthorization`;
- external execution behind an explicit consumer boundary.

This minimizes asynchronous internal coordination while preserving exact authorization binding.
