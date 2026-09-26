# Gate F live closure — 2026-09-27

This addendum supersedes the earlier Gate F blocker for the repaired source
candidate. It records local-runtime evidence only. The raw machine-readable
proof directories are retained in the operator's ignored local `work/`
directory; this document records their finalized results and identities.
The release manifest stays `UNRELEASED` until the production runtime binary
and deployment gates close.

## Frozen identity

- Live-proof source commit: `57dd722570d992cf9a754597ca50c2a95169e394`
- Chain ID: `61999`
- Validators: `5`
- Mandates: `0x3fA4E6e03Fbd434A577387924aF39efd3b4b50F2`
- Authorization: `0xf72aa51B6350C18966923073d3609e1356a3fbBA`
- Mandates source SHA-256: `9c715d57731a031d2c217b3845ba74f08bf3fd7e3dcaa1bb44ffd6e2dc9896d6`
- Authorization source SHA-256: `3a96887d4118c37602f379811e1486fe317a036d6b6f193a9f8a0fdca8f5d8b0`
- Runtime no-redirect patch SHA-256:
  `3cf216b1aa38daa6ff3024a0045b5a36c61e38abefa51274803ce6dfb8483d17`
- Active web-module configuration SHA-256:
  `b3499f5307c7eb1f181cc7944f8d9383ec9ad9dd3cad1aba1d94589ed263fa28`

## Finalized live proofs

All listed writes were prepared from persisted unsigned fingerprints, signed
once, submitted once, and recorded before response decoding.

| Proof | Transaction | Result |
| --- | --- | --- |
| Mandate create | `0x10e0181f9598f90909b57b556446480eab310999aad099192ad4e5fc2da2d89e` | `FINALIZED / MAJORITY_AGREE` |
| Fresh G11 request create | `0x59c0f1f033d6da8c932f28dee654b57935dc979921cb3fcd414eb1601dee3ad1` | `FINALIZED / MAJORITY_AGREE` |
| Approval evaluation | `0x0038c65c9ff1aa80e99fc1a9c3067af6b111c64a3b1e3bb1a725ac9ffd92184e` | `FINALIZED / MAJORITY_AGREE`, state `AUTHORIZED` |
| Rejection evaluation | `0xd72225eb58e255d3e8ffa6c5c22bda9a1105d58f4253f31558b5cf3b37a09551` | `FINALIZED / MAJORITY_AGREE`, state `DENIED` |
| Receipt consumption | `0x30ce3c18b42e57a4dfa6081c422ee6b338693696e06f8075fb1feaf62e3165ed` | `FINALIZED / MAJORITY_AGREE`, state `CONSUMED` |

Approval request ID:
`0xb005f1224fd89e1c49ccfce6b3d3d7fd11a85477085dc27cf8d9e9b93913c459`

Receipt ID:
`0x808f93bf25db64bccb749fb946104129584242bfec88f8d78166cb4d3fa31844`

The approval and rejection finality certificates both record five committed
and revealed votes, successful leader execution, source parity, three evidence
records, and one exact result among all agreeing validators. Receipt proof
records the exact action intent and `receipt_consumed=true`.

## Earlier required failure/recovery proofs

- Evidence integrity mismatch entered `REPAIR_REQUIRED` and the supported
  replacement advanced evidence revision before reevaluation.
- A real source-timeout path was materialized as the contract timeout/expiry
  behavior and left no receipt.
- An intentionally interrupted evaluation was recovered by the consensus worker
  and re-executed from the persisted transaction identity without resubmission.
- Redirect handling is enforced by the no-redirect runtime patch; the contract
  receives no unchecked effective URL provenance.

## Deterministic verification

The isolated suites passed: GLSim `49`, Direct Mandates `18`, adversarial `25`,
runtime-calldata `3`, Gate D GLSim `2`, closure vectors `1`, and reference
vectors `9` — `107` tests total. Repository verification reported `PASS`.

The final release is intentionally not labelled complete in Git metadata until
the clean-checkout CI and upstream synchronization gates are run against this
closure evidence.
