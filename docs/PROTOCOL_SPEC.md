# Covenant Protocol Specification — v1 Gate B Freeze

## Question Covenant answers

> May this exact autonomous agent perform this exact consequential action under this exact immutable mandate, using this exact evidence?

A semantic “yes” is not enough.

The authorization must be bound to the exact consequence.

## Mandate

A mandate is versioned.

A request binds:

- mandate ID
- version
- mandate commitment

A later mandate version cannot retroactively alter an existing request.

A mandate defines:

- issuer
- active state
- deterministic constraints
- semantic criteria
- evidence authorities
- freshness rules
- corroboration rules
- risk tier
- optional human co-authorization requirements

## Action Intent

The Action Intent is Covenant's canonical consequential commitment.

Required fields are:

- agent
- mandate ID
- mandate version
- mandate commitment
- action type
- target
- recipient
- value
- payload hash
- evidence-set commitment
- authorized consumer
- nonce
- chain/domain
- issued-at boundary
- expiry

The canonical serialization and domain-separation algorithm is frozen in `CANONICALIZATION.md`.

The stable Request ID is derived from the immutable Action Subject.

Permitted evidence repair may change the Evidence Set and final Action Intent without changing the Request ID.

Any Authorization Receipt binds the stable Request ID plus the exact final Action Intent that was actually authorized.

## Evidence

Evidence must be authority-bound.

A record must carry enough identity to establish:

- approved publisher/authority;
- stable record ID;
- immutable or versioned reference where applicable;
- digest;
- publication time;
- observation time;
- expiry/freshness;
- evidence role.

A random page containing the expected statement is not trusted evidence.

## Request states

Covenant v1 freezes exactly six persistent request states:

- `PENDING`
- `REPAIR_REQUIRED`
- `AUTHORIZED`
- `DENIED`
- `EXPIRED`
- `CONSUMED`

`DENIED`, `EXPIRED` and `CONSUMED` are terminal.

`PENDING`, `REPAIR_REQUIRED` and `AUTHORIZED` are nonterminal and each has a deterministic expiry or recovery path.

Repairable source, evidence, corroboration or human-approval conditions use `REPAIR_REQUIRED` with a fixed non-extending deadline.

Infrastructure or source failure must never silently become policy denial.

Mandate supersession is not a request state. A later mandate version may affect eligibility for new requests but cannot retroactively rewrite or cancel an existing frozen request.

GenLayer network lifecycle states such as `Accepted`, `Undetermined` and `Finalized` are not Covenant request states.

## Receipt

An Authorization Receipt exists only after the request reaches `AUTHORIZED` and binds the stable Request ID plus one exact final Action Intent.

`AUTHORIZED` is Covenant application state, not GenLayer transaction finality.

Irreversible consumers must separately wait for the authorization-creating transaction to reach the required network finality.

It must not be usable for:

- another action;
- another amount;
- another recipient;
- another target;
- another payload;
- another agent;
- another mandate;
- another evidence set;
- another chain;
- another consumer;
- another nonce.

Consumption is one-time.

## Deterministic rules

Deterministic contract logic handles facts such as:

- mandate/version equality;
- eligibility for new requests and immutable historical mandate-version binding;
- nonce use;
- expiry;
- consumer equality;
- exact hashes;
- value ceilings;
- replay state;
- receipt consumption state.

## Semantic rules

GenLayer consensus handles questions that actually require interpretation, such as:

- whether a deliverable satisfies a specification;
- whether evidence proves a natural-language requirement;
- whether an action serves the purpose allowed by a mandate.

We do not use LLM consensus for arithmetic/equality checks deterministic code can prove.

## No admin bypass

Forbidden surfaces include:

- `force_authorize`
- `admin_approve`
- `set_verdict`
- `skip_consensus`
- `owner_finalize`

Administrators may create future mandate versions.

They cannot mutate frozen requests or manufacture authorization receipts.
