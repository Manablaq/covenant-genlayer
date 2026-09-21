# Covenant Canonicalization — v1

Status: Gate B freeze.

This document defines the exact byte commitments that bind a Covenant authorization to one consequential action.

These rules are protocol rules, not UI conventions.

Changing any rule in this document creates a new protocol version and invalidates verification evidence derived from the old rule.

## Hash primitive

Covenant v1 uses SHA-256.

Notation:

- `H(x) = SHA256(x)`;
- every digest is exactly 32 bytes;
- concatenation is written `||`;
- structural commitments concatenate fields in the exact order documented here.

The pinned GenVM `v0.2.16` artifact was verified to contain SHA-256 support and the pinned contract toolchain successfully validated a disposable contract using `hashlib.sha256(...).digest()`.

Full-runtime execution proof remains a later Gate F/G requirement.

## Primitive encodings

### Domain labels

For an ASCII domain label `L`:

`DOMAIN(L) = H(ASCII(L))`

Every domain tag is exactly 32 bytes.

### Unsigned integers

Every consequential `u256` value is encoded as exactly 32 unsigned big-endian bytes.

No variable-width integer representation is permitted inside a Covenant commitment.

### Addresses

An address that appears structurally in a commitment is encoded as the exact raw 20 bytes exposed by `Address.as_bytes`.

No hexadecimal string representation, checksum capitalization or textual prefix participates in structural address encoding.

### Text

Text commitments use:

`TEXT(value) = H(value.encode("utf-8"))`

Covenant v1 performs no Unicode normalization, whitespace trimming, case folding or locale transformation.

The exact UTF-8 bytes are consequential.

Protocol-controlled enum-like strings SHOULD therefore use fixed ASCII spellings.

### Arbitrary byte payloads

Binary or otherwise dynamic byte values use:

`BLOB(value) = H(exact_bytes)`

Dynamic-length material is reduced to a fixed 32-byte digest before structural concatenation.

This prevents delimiter and variable-length ambiguity.

## Frozen v1 domain tags

The exact ASCII labels and resulting SHA-256 domain tags are:

- `COVENANT/V1/MANDATE_ID` = `6f1c37d3b61bb57668ffe1eda40172d9abb44ef206057761ef9848a0058cd25c`;
- `COVENANT/V1/MANDATE` = `cf58baa874cb6940bdcf4a855ccf07c4b746f77b3df6fd913fb0f932a852e2c4`;
- `COVENANT/V1/ACTION_SUBJECT` = `4690d38d423417d1669a2d29fbc2234508e5a64f3fdeb91090c09a5242dc5126`;
- `COVENANT/V1/EVIDENCE_RECORD` = `cac63b3e2880c12b78d35841ce5be0b3a9956a6909ddfc32c040fe22da90914c`;
- `COVENANT/V1/EVIDENCE_SET` = `c2511857c12b26d5f9fed63a32b03e35f4af272ef3ca3ff326c69dafcd76523e`;
- `COVENANT/V1/ACTION_INTENT` = `c1de800cbac3af21eab66209b04331fe45dc07db9a5c72cfc312ddfbdf58af1f`;
- `COVENANT/V1/REQUEST_ID` = `24d6d54181b72607af6b9f665355952e27d933d1bacc4f8663f0dee3061d2ab1`;
- `COVENANT/V1/RECEIPT_ID` = `25bcf73e68ed57d377b99b64a7c706570c9ccc364ec8b4076559b374f12311a5`;
- `COVENANT/V1/NONCE_KEY` = `c65377be12c6d8434cd46664e9f3a96c320adac5700b56f982b4ef18d45805b3`.

Domain labels are immutable for Covenant v1.

## Mandate ID

A mandate ID is created independently of a mandate version.

The preimage is:

```text
DOMAIN("COVENANT/V1/MANDATE_ID")
|| U256(chain_id)
|| ADDRESS(covenant_mandates_contract)
|| ADDRESS(issuer)
|| U256(issuer_nonce)
```

Then:

`mandate_id = H(preimage)`

The reference-vector preimage is exactly 136 bytes.

The reference mandate ID is:

`6a4e11b9ce55c52e8869fef1114de33c243c47e08f763a4684cc55b43b1b1960`

The issuer nonce namespace prevents two mandate IDs from collapsing merely because their later policy content happens to match.

## Immutable mandate-version commitment

Each mandate version has an immutable content commitment.

The preimage field order is:

```text
DOMAIN("COVENANT/V1/MANDATE")
|| U256(chain_id)
|| ADDRESS(covenant_mandates_contract)
|| mandate_id[32]
|| U256(mandate_version)
|| ADDRESS(issuer)
|| deterministic_policy_hash[32]
|| semantic_criteria_hash[32]
|| evidence_policy_hash[32]
|| U256(risk_tier)
|| human_policy_hash[32]
```

Policy hashes are exact 32-byte commitments to the frozen canonical policy representation chosen for the corresponding policy field.

The policy representation itself must be deterministic and must be covered by implementation tests before Gate B closes.

The reference-vector preimage is exactly 328 bytes.

The reference mandate commitment is:

`8965e6b0715fab9718f4538f753c97f9b0a268fa395a07e4b755afa473db68af`

### Operational eligibility is separate

Whether a mandate version is currently eligible for new requests is operational registry state.

That eligibility flag is deliberately not part of the immutable mandate-content commitment.

Changing eligibility may prevent new requests from using the version, but it may not rewrite the committed historical policy or the mandate commitment already frozen into an existing request.

## Action Subject commitment

The Action Subject is the complete consequential action binding before evidence-set commitment is added.

Its fixed field order is:

```text
DOMAIN("COVENANT/V1/ACTION_SUBJECT")
|| U256(chain_id)
|| ADDRESS(covenant_authorization_contract)
|| ADDRESS(agent)
|| mandate_id[32]
|| U256(mandate_version)
|| mandate_commitment[32]
|| action_type_hash[32]
|| target_commitment[32]
|| recipient_commitment[32]
|| U256(value)
|| payload_hash[32]
|| ADDRESS(authorized_consumer)
|| U256(nonce)
|| U256(issued_at)
|| U256(expires_at)
```

Then:

`action_subject = H(preimage)`

### Dynamic Action Subject fields

For v1:

- `action_type_hash = TEXT(exact_action_type)`;
- `target_commitment = BLOB(exact_target_bytes)`;
- `recipient_commitment = BLOB(exact_recipient_bytes)`;
- `payload_hash = BLOB(exact_payload_bytes)`.

The target and recipient are commitments rather than structural addresses because Covenant must support action domains whose target or recipient representation is not necessarily a GenLayer address.

For an address recipient, the exact recipient bytes are its normalized raw 20-byte address representation before `BLOB(...)`.

The Action Subject reference preimage is exactly 476 bytes.

The reference Action Subject commitment is:

`87bc99583c6504b9943d3aaa63ff1f315ab3bbbc71fe7b2b2ada68db7194ff61`

## Action Subject invariants

Changing any consequential field changes the Action Subject commitment.

This includes at minimum:

- chain;
- authorization-contract address;
- agent;
- mandate ID;
- mandate version;
- mandate commitment;
- action type;
- target;
- recipient;
- value;
- payload;
- authorized consumer;
- nonce;
- issued-at;
- expiry.

No semantic validator decision may authorize a mutated Action Subject by tolerance or approximate matching.

## Evidence Record commitment

Every evidence record is bound to the exact Action Subject before it can participate in an evidence set.

The fixed preimage order is:

```text
DOMAIN("COVENANT/V1/EVIDENCE_RECORD")
|| action_subject[32]
|| authority_id[32]
|| role_hash[32]
|| record_id_hash[32]
|| immutable_reference_hash[32]
|| version_hash[32]
|| content_digest[32]
|| U256(published_at)
|| U256(observed_at)
|| U256(expires_at)
```

Where:

- `authority_id` is the exact 32-byte authority identity commitment required by the mandate evidence policy;
- `role_hash = TEXT(exact_role)`;
- `record_id_hash = TEXT(exact_record_id)`;
- `immutable_reference_hash = TEXT(exact_immutable_or_versioned_reference)`;
- `version_hash = TEXT(exact_evidence_version)`;
- `content_digest` is the exact 32-byte digest bound by the evidence policy.

The Evidence Record preimage is exactly 352 bytes.

An Evidence Record commitment is:

`evidence_record = H(preimage)`

Evidence from the same source cannot be transplanted to another Action Subject without changing its Evidence Record commitment.

## Evidence content-digest processing

Covenant v1 freezes the exact byte input used by the `content_digest` field.

Evidence retrieval uses the exact committed `immutable_reference` as the request URL inside GenLayer nondeterministic execution. The v1 transport operation is HTTP GET through `gl.nondet.web.request(immutable_reference, method="GET")`.

A retrieval is body-eligible only when the request completes and `200 <= response.status < 300`.

For a body-eligible response:

`exact_response_body_bytes = response.body`

and:

`content_digest = SHA256(exact_response_body_bytes)`

`exact_response_body_bytes` means the exact byte sequence exposed by GenVM Web Access as `response.body`. Covenant performs no application-level transformation before hashing.

Before computing `content_digest`, Covenant v1 does not decode the body as text, render the page, parse or reserialize JSON, normalize Unicode, normalize line endings, trim whitespace, case-fold text, rewrite HTML, perform LLM extraction, or substitute another URL.

`gl.nondet.web.render(...)` output is not a valid v1 `content_digest` input.

A completed non-2xx response cannot authorize and is classified as `SOURCE_UNAVAILABLE`. A transport timeout is `SOURCE_TIMEOUT`. Another retrieval failure that produces no body-eligible response is `SOURCE_UNAVAILABLE`.

For a body-eligible response, SHA-256 mismatch against the committed Evidence Record `content_digest` is `EVIDENCE_INTEGRITY_MISMATCH`.

Only after exact digest equality may Covenant decode evidence for semantic interpretation. V1 semantic evidence text uses strict UTF-8 decoding of the already digest-verified body. UTF-8 decoding failure is `SOURCE_MALFORMED`.

Digest equality does not establish publisher authority by itself and does not override the approved-authority, approved-source-prefix, immutable-reference, redirect, freshness, role, or corroboration rules.


## Evidence Set commitment

An evidence set is canonicalized from Evidence Record commitments, not from submission order.

Rules:

1. every record commitment must be exactly 32 bytes;
2. sort all record commitments by ascending raw 32-byte value;
3. reject duplicate commitments;
4. include the exact record count;
5. concatenate only after sorting and duplicate rejection.

The preimage is:

```text
DOMAIN("COVENANT/V1/EVIDENCE_SET")
|| action_subject[32]
|| U256(record_count)
|| record_commitment_0[32]
|| record_commitment_1[32]
|| ...
```

Then:

`evidence_set_commitment = H(preimage)`

The same unique record set therefore produces the same commitment regardless of caller-provided ordering.

Duplicate evidence records are invalid rather than silently deduplicated.

## Final Action Intent commitment

The complete Action Intent binds the Action Subject to the canonical evidence set:

```text
DOMAIN("COVENANT/V1/ACTION_INTENT")
|| action_subject[32]
|| evidence_set_commitment[32]
```

Then:

`action_intent = H(preimage)`

The Action Intent is the final exact authorization commitment.

No authorized consequence may substitute a different Action Subject or Evidence Set while retaining the same authorization.

## Request ID

The request identifier is derived from the frozen Action Subject, not from the repairable evidence-bearing Action Intent:

```text
request_id = H(
    DOMAIN("COVENANT/V1/REQUEST_ID")
    || action_subject[32]
)
```

The Request ID is therefore stable across every permitted evidence repair because repair may not mutate the Action Subject.

Evidence repair may change the Evidence Set commitment and final Action Intent without changing request identity.

For v1, identical Action Subjects intentionally derive the same Request ID.

The nonce inside the Action Subject participates in request uniqueness.

A used nonce must prevent recreation of the same request namespace entry.

## Receipt ID

An authorization receipt ID is derived only after a request has reached the authorization-granted state.

The identifier is:

```text
receipt_id = H(
    DOMAIN("COVENANT/V1/RECEIPT_ID")
    || request_id[32]
    || action_intent[32]
)
```

The receipt therefore cannot be detached from either its stable Request ID or its exact final Action Intent.

If permitted evidence repair changes the Evidence Set, the Request ID remains stable while the Action Intent changes. A receipt created after that repair therefore binds the repaired final Action Intent.

Receipt existence does not override GenLayer lifecycle finality requirements.

## Nonce namespace

Nonce replay protection is scoped to:

```text
DOMAIN("COVENANT/V1/NONCE_KEY")
|| U256(chain_id)
|| ADDRESS(covenant_authorization_contract)
|| ADDRESS(agent)
|| U256(nonce)
```

Then:

`nonce_key = H(preimage)`

The namespace deliberately includes:

- chain;
- CovenantAuthorization deployment address;
- agent;
- nonce.

The same numeric nonce may therefore exist for another agent or another CovenantAuthorization deployment without collision.

For one agent on one CovenantAuthorization deployment and chain, nonce reuse is rejected.

A nonce used by an existing request is never reset by an administrator.

## Reference vectors

The following vectors are mandatory Covenant v1 fixtures.

### Structured policy inputs for this fixture

The authorization reference fixture uses the frozen structured policy encodings defined later in this document.

Its exact policy commitments are:

- deterministic policy: `d38e38d6e9fec4476f52d92a20b2bed139b46c6d431c41416d085bb6392bc57f`;
- semantic criteria: `a9aef1d6bea6c93475eaa8d3d5c8695ff83317e41902ccc229afb1dc630ebbdc`;
- evidence policy: `85d37b6ed0b45a20bed81f90aea4b13cd7d9ab4709ef7ca47ba064055bae512d`;
- human policy: `0f8507fca3fa51f0b6826f09b7ba23db7e099c6ae016559257b9d3af4cb3aa45`;
- risk tier: `2`.

The evidence-policy fixture requires exactly one primary authority and at least two distinct corroborating authorities.

The authorization fixture therefore contains exactly three Evidence Records:

- Evidence A: primary authority;
- Evidence B: first corroborating authority;
- Evidence C: second corroborating authority.

The primary authority is not counted toward the corroboration minimum.

All three reference records satisfy the frozen reference freshness windows at the fixture evaluation time.



### Mandate

- mandate ID: `6a4e11b9ce55c52e8869fef1114de33c243c47e08f763a4684cc55b43b1b1960`
- mandate commitment: `8965e6b0715fab9718f4538f753c97f9b0a268fa395a07e4b755afa473db68af`

### Action Subject

- Action Subject: `87bc99583c6504b9943d3aaa63ff1f315ab3bbbc71fe7b2b2ada68db7194ff61`

### Evidence records

- Evidence A: `e2101af44756583b31045385118f1c0be1f2b13ab9dd86b3ca0e064c05c12892`
- Evidence B: `00d95e4f1fcbee1001a7d0c8aee386d8c90a17f3df6e77348df2428d3c280373`
- Evidence C: `c2f59fc84f6b5400a561ec64741b97094323fae2bf1e3a79a52c302dc7fcd6e1`

### Evidence set

- Evidence Set: `0110de666ffca86d92adaebcb56b547037d4b2dedc4bf4b6cc7b4ce9985920a2`

### Final identifiers

- Action Intent before repair: `a5fa809a1218db9ed9f40fa5ad98498d8487faf053fa831883d3e0e7792b78bd`
- Request ID: `cc552250beccee9cde45d7d1e3dfe16b9e305d4653aa5267a24ce472b9f71c0b`
- Receipt ID before repair: `ac2d028281605965f6227e8d0f5196410039bf56d1af397ceefad54ca3644f2c`
- Nonce Key: `eac139f13810a72dedab9efc71e6bd3b3af3571b6bb0795938a2fe3942613cfc`

### Evidence-repair invariance vector

Replacing Evidence B while preserving Evidence A and Evidence C with the permitted repaired Evidence B reference vector produces:

- repaired Evidence B: `acd4ea3c5fa79ff923ecde592f43c72ef12e1230ddc4cdf78fd31c8b9933444d`;
- Evidence Set after repair: `1b3d2cc4189fdcc908c23dd34e5ff627a222e7d103eddd7c836d1ae362e50f93`;
- Action Intent after repair: `88d33d7ea468c53212b0fec60fa94c89a801f81d7aa2c8c441353b674dcde48a`;
- Request ID after repair: `cc552250beccee9cde45d7d1e3dfe16b9e305d4653aa5267a24ce472b9f71c0b`;
- Receipt ID after repair: `a21d33e08e6cd6afacb97bf0f73f55b8e313f095144129712be48f418cb58e4c`.

The before-repair and after-repair Request IDs are identical.

The before-repair and after-repair Action Intents are different.

The before-repair and after-repair Receipt IDs are different because each receipt binds the exact final Action Intent that was actually authorized.

These values must be reproduced exactly by deterministic tests.

## Evidence-set invariants

The following are hard v1 rules:

- evidence ordering does not change the Evidence Set commitment;
- duplicate Evidence Record commitments are rejected;
- every Evidence Record is bound to one Action Subject;
- evidence from another Action Subject cannot be substituted;
- record count participates in the Evidence Set commitment;
- no record may be omitted while preserving the same Evidence Set commitment.

## Mutation invariants

Every consequential mutation must change the corresponding commitment or fail deterministic validation.

Tests must cover at minimum mutation of:

- agent;
- mandate ID;
- mandate version;
- mandate commitment;
- action type;
- target;
- recipient;
- value;
- payload;
- evidence set;
- authorized consumer;
- nonce;
- chain;
- authorization-contract address;
- issued-at;
- expiry.

The reference-vector probe already proves that recipient mutation changes the Action Subject and nonce mutation changes the nonce namespace key.

The deterministic test suite must extend this to every consequential field.

## No tolerance rule

No approximate comparison or numeric tolerance may preserve authorization after a consequential field changes.

An amount, recipient, target, consumer, nonce, mandate identity, evidence commitment or other consequence-bearing field must match exactly.

## Commitment graph

Covenant v1 has the following acyclic commitment graph:

```text
Mandate ID
    |
    v
Mandate Version Commitment
    |
    v
Action Subject
    |
    +---------------------------> Request ID
    |
    +----------------------+
    |                      |
    v                      v
Evidence Record A      Evidence Record B ...
    \                      /
     \                    /
      v                  v
       Evidence Set Commitment
                |
                v
          Action Intent
                |
                +----------------------+
                                       |
Request ID ----------------------------+
                                       |
                                       v
                                   Receipt ID
```

The Evidence Record binds to the Action Subject rather than the final Action Intent so the evidence-set commitment can be incorporated without a circular hash dependency.

The Request ID also binds directly to the Action Subject so permitted evidence repair cannot change request identity.

The Receipt ID combines the stable Request ID with the exact final Action Intent, so receipt identity changes when repaired evidence changes the authorized final intent.

## Implementation requirements

Production code must implement these commitment functions directly and deterministically.

The implementation must not rely on:

- Python object string representations;
- dictionary iteration order;
- JSON key order unless an independently frozen canonical JSON format is explicitly defined;
- locale-sensitive conversion;
- implicit integer width;
- textual address formatting;
- caller-provided evidence ordering;
- Unicode normalization not specified by this document.

Reference-vector tests must execute before any Bradbury deployment.

Full-runtime execution of the pinned hash/canonicalization implementation remains required by later release gates.

## Canonical mandate-policy encodings

The mandate policy hashes are structured binary commitments rather than informal text serialization.

Policy-family type codes act as fixed 32-byte `u256` family separators inside these inner policy commitments.

### Deterministic policy encoding

Policy type code: `1`.

Canonical preimage:

```text
U256(1)
|| U256(max_value)
|| U256(max_request_lifetime_seconds)
|| U256(repair_window_seconds)
|| U256(allowed_action_count)
|| sorted_allowed_action_hashes[32 each]
|| U256(allowed_target_count)
|| sorted_allowed_target_commitments[32 each]
|| U256(allowed_recipient_count)
|| sorted_allowed_recipient_commitments[32 each]
```

Every list is sorted by ascending raw 32-byte commitment and rejects duplicates.

An empty target or recipient list means no additional deterministic allowlist restriction for that field.

The reference deterministic-policy preimage is 256 bytes.

Reference deterministic-policy hash:

`d38e38d6e9fec4476f52d92a20b2bed139b46c6d431c41416d085bb6392bc57f`

### Authority-rule encoding

An authority rule is:

```text
H(
    U256(role_mask)
    || authority_id[32]
    || TEXT(publisher_name)
    || TEXT(approved_https_source_prefix)
)
```

The authority-rule preimage is exactly 128 bytes.

Authority rules are sorted by ascending 32-byte rule commitment before evidence-policy hashing and duplicate rules are rejected.

### Evidence policy encoding

Policy type code: `2`.

Canonical preimage:

```text
U256(2)
|| U256(required_primary_count)
|| U256(required_corroboration_count)
|| U256(max_publication_age_seconds)
|| U256(max_observation_age_seconds)
|| U256(max_publish_observe_gap_seconds)
|| U256(max_evidence_records)
|| U256(authority_rule_count)
|| sorted_authority_rule_hashes[32 each]
```

The reference evidence-policy preimage is 352 bytes.

Reference evidence-policy hash:

`85d37b6ed0b45a20bed81f90aea4b13cd7d9ab4709ef7ca47ba064055bae512d`

### Human co-authorization policy encoding

Policy type code: `3`.

Modes:

- `0 NONE`;
- `1 SINGLE_ADDRESS`.

Canonical preimage:

```text
U256(3)
|| U256(human_mode)
|| ADDRESS(approver_or_zero_address)
```

The human-policy preimage is exactly 84 bytes.

Mode `NONE` requires the exact zero address.

Mode `SINGLE_ADDRESS` requires a non-zero exact approver address.

Reference human NONE policy hash:

`0f8507fca3fa51f0b6826f09b7ba23db7e099c6ae016559257b9d3af4cb3aa45`

Reference human SINGLE_ADDRESS policy hash:

`d78747c780416c71fe56d8f00e030a008c374d6683a74573be5c2130f3e1635b`

### Semantic-criteria commitment

For v1:

`semantic_criteria_hash = TEXT(exact_semantic_criteria)`

No JSON serialization, whitespace normalization, case folding or Unicode normalization is applied implicitly.

### Policy implementation rule

Production mandate creation must compute these policy commitments on-chain from the exact structured policy fields accepted by the contract.

The caller must not be allowed to supply an arbitrary policy hash that is stored without recomputation.

The final mandate commitment uses those recomputed policy commitments exactly as defined earlier in this document.
