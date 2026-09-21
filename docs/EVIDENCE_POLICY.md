# Covenant Evidence and Mandate Policy — v1

Status: Gate B freeze.

This document defines Covenant policy semantics for deterministic limits, evidence authority, provenance, freshness, corroboration, human co-authorization and repair.

GenLayer supplies nondeterministic execution and validator consensus. GenLayer does not decide which publisher Covenant trusts or which evidence is fresh enough. Those are explicit Covenant mandate rules.

## Policy families

Covenant v1 freezes three mandate policy families:

- policy type `1`: deterministic policy;
- policy type `2`: evidence policy;
- policy type `3`: human co-authorization policy.

The exact canonical byte representations are frozen in `CANONICALIZATION.md`.

## Deterministic policy

The deterministic policy contains:

- maximum authorized value;
- maximum request lifetime in seconds;
- repair window in seconds;
- allowed action-type commitments;
- optional allowed target commitments;
- optional allowed recipient commitments.

### Maximum value

`max_value` is an exact inclusive ceiling.

There is no magic zero value meaning unlimited.

If a mandate intends effectively unrestricted `u256` value, it must encode the corresponding explicit maximum rather than rely on a sentinel.

### Request lifetime

`max_request_lifetime_seconds` must be positive.

For request creation:

```text
expires_at > issued_at
and
expires_at - issued_at <= max_request_lifetime_seconds
```

`issued_at` is contract-derived deterministic GenVM transaction time.

### Repair window

`repair_window_seconds` must be positive and must not exceed the maximum request lifetime.

Once a request first enters `REPAIR_REQUIRED`, the State Machine computes the fixed repair deadline and never extends it.

### Allowed action types

The allowed-action list contains unique 32-byte `TEXT(action_type)` commitments sorted by ascending raw bytes for policy canonicalization.

At least one action type is required.

An Action Subject action type must match an allowed commitment exactly.

### Optional target allowlist

A zero-length target list means the mandate does not impose an additional deterministic target allowlist.

A non-empty target list means the Action Subject target commitment must exactly equal one listed commitment.

### Optional recipient allowlist

A zero-length recipient list means the mandate does not impose an additional deterministic recipient allowlist.

A non-empty recipient list means the Action Subject recipient commitment must exactly equal one listed commitment.

No approximate target, recipient or value comparison is permitted.

## Semantic criteria

The mandate semantic criteria are committed separately by `semantic_criteria_hash`.

For Covenant v1:

`semantic_criteria_hash = TEXT(exact_semantic_criteria)`

The criteria text uses exact UTF-8 with no trimming, case folding or Unicode normalization.

The criteria must describe only questions that genuinely require semantic interpretation.

Deterministic arithmetic, equality, caller, expiry, nonce and commitment checks remain deterministic contract logic.

## Evidence authority model

An Evidence Record is not trusted merely because its URL or digest looks valid.

The governing mandate freezes approved publisher authorities.

Each authority rule contains:

- allowed evidence role mask;
- 32-byte authority identity commitment;
- exact publisher name;
- exact approved HTTPS source prefix.

The authority identity and source rule are policy inputs, not values chosen by the semantic leader.

## Authority identity

`authority_id` is an exact 32-byte identity commitment selected by the mandate issuer.

The corresponding Evidence Record must carry the same authority identity.

A record from an authority not present in the frozen mandate policy is not authorized evidence.

## Publisher name

Publisher name is committed as exact UTF-8 text.

It is descriptive identity material and does not replace the authority ID or approved source rule.

## Approved source prefix

Every v1 source prefix:

- must begin with exact lowercase `https://`;
- must end with `/`;
- must contain no whitespace;
- is compared as exact UTF-8 text;
- is immutable within a published mandate version.

An Evidence Record immutable reference must begin with an approved source prefix belonging to the same authority and permitted role.

String-prefix matching is only one part of provenance. The authority ID, record ID, version, content digest, timing and corroboration rules must also pass.

## Redirect boundary

Covenant v1 does not assume that content reached through an HTTP redirect inherits the authority of the original approved reference.

The current reviewed Web Access documentation does not establish a redirect/final-URL verification primitive that Covenant can safely assume.

Therefore runtime implementation and tests must prove the transport behavior before redirected evidence can be accepted.

Until such proof exists, an implementation must not deliberately treat a transition to an unapproved publisher origin as authoritative evidence.

Bradbury is not used to discover this behavior by trial and error.

## Immutable or versioned reference

Every Evidence Record requires a non-empty immutable or explicitly versioned reference.

The reference itself is committed into the Evidence Record.

A mutable landing page without a stable record/version identity is insufficient for consequential authorization.

## Stable record ID

Every Evidence Record requires a non-empty stable `record_id`.

The record ID identifies the real-world or publisher-level evidence record independently of the URL text.

A repair may replace an invalid evidence record only through the State Machine repair path.

## Evidence version

Every Evidence Record requires a non-empty version string.

The version may be a source version, immutable revision, commit identifier, publication edition or equivalent publisher-defined immutable/versioned identifier.

The semantic validator may not silently substitute another version.

## Content digest

Every Evidence Record requires an exact 32-byte content digest.

The implementation must verify that fetched/decoded evidence corresponds to the digest under the frozen evidence-processing rule before relying on its meaning.

A digest establishes content identity; it does not by itself establish publisher authority.

## Frozen evidence-body processing rule

Covenant v1 verifies Evidence Record `content_digest` against the exact byte sequence exposed by GenVM Web Access as `response.body` for the exact committed immutable/versioned evidence reference.

The retrieval operation is HTTP GET through `gl.nondet.web.request(reference, method="GET")`.

Only a completed response satisfying `200 <= response.status_code < 300` is body-eligible.

For a body-eligible response:

`content_digest = SHA256(exact response.body bytes)`

The digest is computed before UTF-8 decoding, JSON parsing, HTML interpretation, rendering, normalization, trimming, LLM extraction, or any other application-level content transformation. `gl.nondet.web.render(...)` output is not a valid v1 digest input.

A completed non-2xx HTTP response is `SOURCE_UNAVAILABLE`. A transport timeout is `SOURCE_TIMEOUT`. Another retrieval failure that produces no body-eligible response is `SOURCE_UNAVAILABLE`.

A body-eligible response whose SHA-256 digest differs from the committed Evidence Record `content_digest` is `EVIDENCE_INTEGRITY_MISMATCH`.

Only after exact digest verification may v1 decode the body for semantic interpretation. Semantic evidence text uses strict UTF-8. UTF-8 decoding failure is `SOURCE_MALFORMED`.

The raw-body digest rule does not weaken provenance. The same record must still satisfy its frozen authority identity, publisher/source rule, immutable or versioned reference, stable record ID, version, timing, role, and corroboration requirements.

Redirect authority remains governed by the separate redirect boundary; matching body bytes never grant authority to an otherwise unapproved origin.


## Evidence roles

V1 uses two evidence roles:

- role `1`: `PRIMARY`;
- role `2`: `CORROBORATION`.

The frozen authority-rule role mask determines which role or roles an authority may satisfy.

Unknown evidence roles are invalid.

## Primary evidence

Covenant v1 requires exactly one distinct primary authority for an evidence policy that uses the standard evidence model.

The reference policy fixture uses exactly one primary record.

Multiple records from the same primary authority do not create multiple independent primary authorities.

## Corroboration

`required_corroboration_count` is the minimum number of distinct corroborating authorities.

Corroboration independence is measured by authority identity, not by number of URLs or records.

The primary authority may not also count toward the corroboration minimum.

Two records from the same corroborating authority count as one authority for the minimum.

Every counted corroborating authority must be permitted for the corroboration role by the frozen mandate policy.

## Evidence count bound

`max_evidence_records` is a deterministic upper bound on records supplied to one request revision.

It must be at least:

`required_primary_count + required_corroboration_count`

The cap prevents unbounded evidence growth and does not weaken the distinct-authority requirement.

## Freshness policy

The evidence policy freezes:

- `max_publication_age_seconds`;
- `max_observation_age_seconds`;
- `max_publish_observe_gap_seconds`.

All three windows must be positive.

Freshness is re-evaluated against deterministic transaction time when Covenant evaluates the evidence.

For evaluation time `now`, an Evidence Record is fresh only if all of the following hold:

```text
published_at <= observed_at
observed_at <= now
now < expires_at
now - published_at <= max_publication_age_seconds
now - observed_at <= max_observation_age_seconds
observed_at - published_at <= max_publish_observe_gap_seconds
```

The configured age limits are inclusive.

Evidence expiry is exclusive: `now == expires_at` is expired.

Future observation time is invalid.

Publication after observation is invalid.

## Evidence evaluation time

Freshness is evaluated using the transaction time of the evaluation attempt.

It is not frozen forever at request creation.

An Evidence Record that was fresh earlier may correctly become stale before authorization.

## Leader and validator evidence rule

The leader proposes a structured evidence/decision result.

Validators must independently verify decision-bearing substance from the same frozen mandate policy and authoritative evidence.

They may independently fetch sources, independently extract the relevant facts and compare exact consequential decision fields.

Leader-only schema validation is insufficient.

Exact consequence-bearing values use exact comparison.

## Source-failure separation

Source and infrastructure failure are not semantic denial.

Covenant distinguishes repairable evidence/source conditions from genuine policy violation.

The repair-reason enum is:

- `0 NONE`;
- `1 SOURCE_UNAVAILABLE`;
- `2 SOURCE_TIMEOUT`;
- `3 SOURCE_MALFORMED`;
- `4 EVIDENCE_INTEGRITY_MISMATCH`;
- `5 EVIDENCE_STALE`;
- `6 EVIDENCE_AUTHORITY_INVALID`;
- `7 EVIDENCE_REFERENCE_INVALID`;
- `8 CORROBORATION_MISSING`;
- `9 HUMAN_APPROVAL_MISSING`.

No other v1 repair-reason code is valid.

`NONE` is the zero/default value and is not a reason for entering `REPAIR_REQUIRED`.

## Repair remediation matrix

### SOURCE_UNAVAILABLE

Permissionless source retry is allowed before the fixed deadline.

The request agent may also replace permitted evidence material before the deadline.

### SOURCE_TIMEOUT

Permissionless source retry is allowed before the fixed deadline.

The request agent may also replace permitted evidence material before the deadline.

### SOURCE_MALFORMED

Permissionless retry of the same authoritative record is allowed before the fixed deadline.

The request agent may replace the malformed record through the evidence-repair path.

### EVIDENCE_INTEGRITY_MISMATCH

The mismatch is never silently accepted.

The request agent may submit corrected evidence material before the fixed deadline.

The replacement receives a new Evidence Record commitment and new Evidence Set/Action Intent as required.

### EVIDENCE_STALE

The stale record cannot authorize.

The request agent may replace it with fresh evidence allowed by the same frozen authority policy before the deadline.

### EVIDENCE_AUTHORITY_INVALID

The invalid authority cannot authorize.

The request agent may replace that evidence with evidence from a permitted authority before the deadline.

### EVIDENCE_REFERENCE_INVALID

The invalid reference cannot authorize.

The request agent may replace it with a valid immutable/versioned reference under the same frozen policy before the deadline.

### CORROBORATION_MISSING

The request agent may add or replace evidence so the distinct-authority corroboration requirement is met before the deadline.

### HUMAN_APPROVAL_MISSING

Evidence replacement does not satisfy this reason.

The exact frozen human approver must supply the required co-authorization before the repair deadline and request expiry.

## Evidence replacement authority

Only the exact request `agent` may replace evidence material for an existing request.

The immediate caller must equal the frozen agent.

Transaction origin is not substituted for the immediate caller.

Evidence replacement may never alter the Action Subject or Request ID.

## Permissionless source retry

Retrying the same evidence without changing committed evidence material is permissionless.

The caller gains no authorization authority by paying for a retry.

A retry that changes no evidence does not increment `evidence_revision`.

No retry extends the fixed repair deadline.

## Permissionless semantic evaluation

Any caller may trigger semantic evaluation of an eligible request.

The caller gains no right to influence the accepted result.

Authorization depends only on frozen request/policy state and validator consensus.

## Human co-authorization modes

Covenant v1 supports exactly:

- mode `0 NONE`;
- mode `1 SINGLE_ADDRESS`.

Unknown human-approval modes are invalid.

## Human mode NONE

Mode `NONE` uses the zero address in canonical policy encoding.

No human approval state is required.

## Human mode SINGLE_ADDRESS

Mode `SINGLE_ADDRESS` freezes one non-zero GenLayer address as the approver.

Human approval submission requires the immediate caller to equal that exact frozen address.

The approval is bound to the stable Request ID and immutable Action Subject.

The approver cannot alter the Evidence Set, Action Intent or Action Subject.

The approval must be submitted before both the fixed repair deadline and request expiry.

## Human approval state

A successful human approval records deterministic request metadata including:

- approved flag;
- exact frozen approver;
- deterministic approval transaction time.

Human approval does not increment `evidence_revision` because it does not replace evidence.

After valid approval, a request waiting only on human co-authorization may return to `PENDING` for evaluation.

The existence of an eventual authorization receipt proves that every required deterministic prerequisite, including human approval, was satisfied when the request was authorized.

## Human approver powers

The approver may satisfy only the frozen co-authorization requirement.

The approver may not:

- change the Action Subject;
- change the mandate;
- replace evidence;
- set the semantic verdict;
- create a receipt directly;
- consume a receipt unless separately named as the authorized consumer;
- extend a deadline.

## Repair deadline rule

Every repair reason is bounded by the State Machine repair deadline.

No repair path extends that deadline.

Once the deadline is reached, repair and approval attempts are rejected and the request can be materialized as `EXPIRED`.

## Semantic denial

`DENIED` is reserved for an actual deterministic or accepted semantic policy violation.

A source fetch failure, timeout, malformed response, correctable integrity failure, stale replaceable evidence, invalid replaceable authority/reference, missing corroboration or missing human approval must not be silently mislabeled as semantic denial while the repair window remains open.

## Policy reference vectors

The reference policy-model probe freezes:

- deterministic policy hash: `d38e38d6e9fec4476f52d92a20b2bed139b46c6d431c41416d085bb6392bc57f`;
- evidence policy hash: `85d37b6ed0b45a20bed81f90aea4b13cd7d9ab4709ef7ca47ba064055bae512d`;
- human NONE policy hash: `0f8507fca3fa51f0b6826f09b7ba23db7e099c6ae016559257b9d3af4cb3aa45`;
- human SINGLE_ADDRESS policy hash: `d78747c780416c71fe56d8f00e030a008c374d6683a74573be5c2130f3e1635b`.

The authority-rule fixtures are:

- Authority A: `427588180976eba9da081c74cc2700129cd495cdd2c03e1da012629166bc4de1`;
- Authority B: `d3bb9b18590dee9a612d1ed2a2c38f4375ee411d95ba615c5e08839b876f5586`;
- Authority C: `0dd26b66e25ef94bb989b2f18f65ca3a72bf6a0a5a9bf9208838bf04402ee438`.

Deterministic tests must reproduce these values exactly.
