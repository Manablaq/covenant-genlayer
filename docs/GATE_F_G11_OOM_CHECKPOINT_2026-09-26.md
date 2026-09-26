# Gate F G11 OOM Checkpoint — 2026-09-26

This document records the Covenant Gate F runtime checkpoint reached on
2026-09-26.

It is a checkpoint/provenance record, not a claim that Gate F or Progress 3 is
complete. Runtime forensic runners and evidence directories remain outside the
Git repository and are not represented here as if their bytes were tracked by
Git.

## Repository baseline before this checkpoint commit

- Branch: `main`
- Parent HEAD: `f734accb957335b9a9055ac08a74bbfd5e723c05`
- Parent tree: `4941b7ecbd1d64f2bb87c9c7aa2c92eb083d1d2e`
- Authorization source SHA-256:
  `09e5f5493f02d94fad1601128330a4a1572a87a833f6278f5133c2d81ee5faf2`
- Mandates source SHA-256:
  `c921da40757968260e7acb0555db93d2ba4c3ca9ce81760ca51f6087d494333f`

The working checkpoint contains changes to the Authorization and Mandates
contracts plus their Direct/GLSim/adversarial/runtime-calldata verification
tests.

## Current Progress 3 runtime state

Progress 1 and Progress 2 are complete.

Progress 3 remains blocked on the G11 `create_request` supported-runtime
execution.

The consumed transaction is:

`0xf6eae12c7dff8e94b64ee33a696279edfed4d5239cdb78b57e042bc3fdf55cad`

The transaction finalized with:

- transaction status: `FINALIZED`
- execution result: `VM_ERROR`
- VM error payload: `OOM`
- outer EVM nonce consumed: `12`
- public post-write nonce: `13`
- Covenant request nonce: `11`
- request nonce used: `false`
- request-ID mapping: empty
- application state committed: `NO`
- application state rolled back: `YES`

The finalized failure therefore consumed the outer transaction nonce but did
not commit the Covenant request.

## R47/R49 OOM classification

The read-only forensic stages established that the failure is a GenVM-internal
OOM-class VM error, not a Docker/container OOM kill.

Observed properties include:

- all four runtime containers reported `OOM_KILLED=false`
- all failed leader/validator executions reported `ERROR`
- failed execution `gas_used` was `0`
- GenVM stdout/stderr were empty
- the exact internal OOM subtype remained unresolved from the persisted v0.65
  artifacts
- GenVM memlimiter detailed logging was disabled by the live configuration

R49 closed the post-forensics state check and confirmed request nonce `11`
remained safely unused.

R49 runner SHA-256:

`3fdbfa79ba5ed25fb818d020f74a66ae26a69f700224ba68bfd4e231b06b9a80`

R49 certificate SHA-256:

`aa10c1f7c8fa1d82621b31c8c1290a6624c50bda0fd2bef3be5e568e3595ad67`

## R50 partial read-only path reduction

R50 was a read-only continuation and must not be rerun.

Before stopping, Sections 0 through 4 passed.

Its existing-artifact/database analysis established:

- execution record count: `6`
- execution error count: `6`
- zero-gas execution count: `6`
- all six execution states had one identical SHA-256
- each execution state contained `53` entries
- decoded execution-state value bytes: `50712`
- no execution state exactly matched a snapshot subtree
- no execution state exactly matched a current-state subtree

The six persisted OOM executions had durations between `4557 ms` and
`5554 ms`, with a median of `5512 ms`.

Static `create_request` source analysis estimated:

- fixed registry view calls: `17`
- per-evidence registry view calls: `8`
- G11 evidence records: `3`
- evidence-dependent calls: `24`
- total estimated registry view calls: `41`

The 41-call result remains an investigation lead, not a proven OOM cause.

R50 runner SHA-256:

`55525b8cbcebbf02e0e760d5158d216d6e1d03a886e1253403b6fee042a292dc`

R50 stopped on its same-contract successful-read evidence assertion after the
preceding read-only gates had passed. No transaction, signing, runtime
mutation, database write, repository write, or blockchain write was performed
by R50.

## R51 consumed continuation

R51 must not be rerun.

Its runner hash was:

`03da3264642a28cc410ec676eee6e2af8e0b73521a976be65af51427749f86fb`

The runner integrity and Bash syntax gates passed, but R51 stopped immediately
in its R50-binding section with:

`STOP: R50 four-line detector source changed`

R51 therefore did not close the R50 analysis. It performed no transaction
submission, signing, GenVM path reproduction, runtime mutation, database
write, repository write, or blockchain write.

## Safety boundary

At this checkpoint:

- R41 rerun: **NO**
- R42 rerun: **NO**
- R43 rerun: **NO**
- R44 rerun: **NO**
- R45 rerun: **NO**
- R46 rerun: **NO**
- R47 rerun: **NO**
- R48 rerun: **NO**
- R49 rerun: **NO**
- R50 rerun: **NO**
- R51 rerun: **NO**
- automatic resubmission: **NO**
- blockchain write for OOM experimentation: **NO**
- runtime configuration mutation for diagnosis: **NO**
- fabricated runtime evidence: **NO**

## Next engineering boundary

Continue only with a new read-only stage that binds the exact consumed R50/R51
source and persisted artifacts before deciding on any implementation repair or
new supported-runtime write.

The OOM cause must not be declared solely from the 41-call static estimate.
