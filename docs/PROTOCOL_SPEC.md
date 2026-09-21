# Covenant Protocol Specification — Draft 0

## Question Covenant answers

> May this exact autonomous agent perform this exact consequential action under this exact immutable mandate, using this exact evidence?

A semantic “yes” is not enough.

The authorization must be bound to the exact consequence.

## Mandate

A mandate is versioned.

A request binds:

- mandate ID
- version
- mandate hash

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

Required fields will include:

- agent
- mandate ID
- mandate version
- mandate hash
- action type
- target
- recipient
- value
- payload hash
- evidence-set hash
- consumer
- nonce
- chain/domain
- issued-at boundary
- expiry

The canonical serialization and domain-separation algorithm must be frozen before implementation.

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

## Decision family

Initial draft:

- `AUTHORIZED`
- `DENIED_POLICY_VIOLATION`
- `EVIDENCE_REPAIR_REQUIRED`
- `EVIDENCE_EXPIRED`
- `CORROBORATION_REQUIRED`
- `HUMAN_APPROVAL_REQUIRED`
- `SOURCE_RETRY_REQUIRED`
- `MANDATE_SUPERSEDED`
- `REQUEST_EXPIRED`

The final state enum may be reduced after size/state-machine review.

Infrastructure failure must never silently become policy denial.

## Receipt

A finalized Authorization Receipt binds one exact Action Intent.

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
- active/superseded state;
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
