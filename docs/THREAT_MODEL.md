# Covenant Threat Model — Draft 0

Covenant treats agents, web content, evidence sources, leader output, browser state and transaction transport as potentially adversarial or unreliable.

## Required security properties

1. A leader cannot unilaterally choose an authorization result.
2. A valid authorization cannot be transformed into a different consequence.
3. A receipt cannot be replayed.
4. The wrong consumer cannot consume a receipt.
5. Unapproved evidence authorities cannot authorize actions.
6. Stale/expired evidence cannot authorize actions.
7. Later mandate edits cannot alter a frozen request.
8. Temporary source failure cannot masquerade as policy denial.
9. Every non-terminal application state has bounded recovery or expiry.
10. Irreversible consequence waits for finality.
11. UI/cache/RPC failure cannot fabricate canonical state.
12. Owner/admin capability cannot bypass consensus.

## Adversarial tests required before backend release

- valid authorization
- valid denial
- malicious leader proposes false authorization
- validator disagreement
- malformed leader output
- unauthorized evidence publisher
- stale evidence
- valid evidence reused for another request
- missing corroboration
- source temporarily unavailable
- source unavailable until expiry
- repair before deadline
- repair after deadline
- amount mutation
- recipient mutation
- target mutation
- payload mutation
- mandate-version mutation
- wrong consumer
- nonce replay
- receipt double consumption
- expired receipt
- mandate superseded while request active
- owner bypass attempt
- accepted-but-not-final consequence attempt
- successful finalized receipt consumption
- transaction submission succeeds but execution fails
- transaction hash recovered after client/UI interruption

A backend with only happy-path coverage is not complete.
