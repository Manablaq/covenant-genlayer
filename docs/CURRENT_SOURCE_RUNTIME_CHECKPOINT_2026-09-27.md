# Historical pre-compact source supported-runtime checkpoint — 2026-09-27

This checkpoint records only the pre-compact source deployment and
supported-local runtime closure. It is retained for audit history and is
superseded for current-source claims by
`docs/CURRENT_SOURCE_BRADBURY_LIVE_PROOF_2026-09-29.json`. Nothing below may be
used as current Bradbury source-parity evidence or as final release
certification.

## Frozen source and deployments

- Source commit: `40417500c938ae59de4fded587e3bfefd562e07c`
- Authorization SHA-256: `24ad76f931ccef6dca2ca6fbe94971b3eb22d7a98facb5c3de9c4491d6e507ed`
- Mandates SHA-256: `76b86c2aa6e181593f9d18e5506c60c2499e123278bde41876245bc87a173244`
- Chain ID: `61999`; validators: `5`
- Mandates: `0x4817FA4E770B1bE4633BD938991bcdB97EAA8E19`
- Authorization: `0xCe751D8399639157268a55F12e6f2aB081d49c72`
- Mandates deployment: `0x093cb27ac4de83a210249b68076e3f262ef6874130d1778161e623b09492811f`
- Authorization deployment: `0xfa3a4bfc19056a3776490fcc0943ce58054a31dfd1aa426cb80c993a9ccbee66`
- Mandate creation: `0xf27766dc65cb24ddcaf7c83e043e0e830a5b954959f27ff15026e0837db595fc`
- Mandate ID: `0x1615e279a430992697a633ad6e63af597be430c52f079d70eb2a641887db4a2c`
- Mandate commitment: `0x603ea67502d1b4d563cc7a2200d0e71c0a7a457ac169d0d0c9fdad1f784c0d72`

All successful writes below reached `FINALIZED / MAJORITY_AGREE` with five
committed and revealed validator votes. Each write was prepared from a
persisted unsigned transaction, bound to an exact fingerprint, signed once,
submitted once, and recovered by transaction ID.

## Historical pre-compact live closure

### Approval

- Create request: `0x7ca94d4d04ab94d3860f5b62a6c6c2473da4b728e483f9e41487378d7098b6ee`
- Request ID: `0x594f617cb3aca07f932b4ccbec34ac99b8d38f3404cd1b12072c921a58b3dec2`
- Evaluation: `0x08c6660afe722216fd0672449b604f1bcfa139990b3b42daed85c73fe8565247`
- Result: terminal `AUTHORIZED`; receipt binding and source parity passed.

### Independent rejection

- Create request: `0x96a781b4c7722c4931f72976afc50626f344d3887809b544421af0462754b2df`
- Request ID: `0x24bdd5c1342e415d65309af4de376e48c352664543afbb2190927bf2e1fdb7d9`
- Evaluation: `0xb6634e9542f5d982696ada388dceb135e89a2c47a8044ef41c745b480e299f99`
- Result: terminal `DENIED`; no receipt; source parity passed.

### Repair and replacement

- Create request: `0xe8aa4b57e0bc9a7321d85119732f87bd461475d3e88198d306daf52913622616`
- Request ID: `0xbbca9874d6b7101ef51bf5367081b806bd01b16c0bdd97e6343581e7bf98728f`
- Valid replacement: `0x54bbcbf3c5c141697b75f2683897f06122e71854f6272b971de3c71252777873`
- Repaired evaluation: `0x4cdd2f35e951ca055b236548f06efe4faf0097c5db04d3f7b3bd9217ada04eec`
- Result: terminal `AUTHORIZED`; evidence revision advanced to `2`; request identity remained fixed.
- An invalid replacement was separately finalized as `REPAIR_REQUIRED`, proving invalid evidence cannot advance the request.

### Timeout and recovery

- Fresh timeout-case create: `0xda4481914f2df2c986374d6452446b37dc411b90e81e2d0fd7866ec4b9333d8d`
- Request ID: `0xb0659624dec1feaf4cc5770a22d420a80d08a7f9b049aa2fcf50e684229d4dd7`
- Evaluation after the fixed expiry: `0x84c2afae5cfe928c2e55b40cfafb7ed5b23ed8c0fa07be0225d2d76b3e29348e`
- Result: terminal `EXPIRED`; no receipt, no replacement, and no automatic resend.

### Receipt consumption, replay, and wrong consumer

- Request ID: `0xbbca9874d6b7101ef51bf5367081b806bd01b16c0bdd97e6343581e7bf98728f`
- Receipt ID: `0x985975c8f7b78d9a8f08a9550b118c3f97b534ec9cf8e3a8290e4cceb4a6afaa`
- Authorized consumption: `0x9d62334de4af6adf408f3e9a30a524279f413b7b1e1ebd1dc3ce1a08a136b74c`
- Exact replay rejection: `0xb7b62b795779a480c9c3acc1b78d1ce877b5708dba209939126299d1f04065b6`
- Wrong-consumer rejection: `0x1aa0bb79318752c2ff749431ab7e2dbf981f647725b759df98774b5a0b425c90`
- Result: terminal `CONSUMED`; `receipt_consumed=true`; both negative paths finalized authorization errors and left state unchanged.

### Redirect/effective-origin provenance

The active local GenVM manager was rerun against a deterministic 302 fixture.
The runtime returned:

`status=302;location=b'/final'`

It exposed the redirect response and `Location` header without fetching `/final`.
That makes the no-redirect boundary enforceable: body bytes from a redirected
origin cannot silently inherit approved-host provenance. The tracked summary is
`docs/CURRENT_SOURCE_REDIRECT_PROBE_2026-09-27.json`.

## Release boundary

This historical local closure is not the current Bradbury release boundary.
The current-source Bradbury boundary is recorded in the new machine-readable
proof artifact; the repository remains `UNRELEASED` because the remaining
external gates are not complete:

- Bradbury runtime provenance and redirect compatibility;
- Gate J reviewer evidence freeze and final certification.

The Mandates source was estimated read-only at `16,516,613` gas against the
observed `16,777,216` deployment ceiling, then deployed once and finalized.
Bradbury returned contract code with the exact current-source hash. The
current Authorization source was separately measured at `31,890,852` gas and
was rejected before acceptance as `gas limit too high`; its nonce was not
consumed. A reviewed Authorization size/gas redesign is therefore required
before its Bradbury deployment.

The machine-readable Bradbury deployment evidence is
`docs/CURRENT_SOURCE_BRADBURY_MANDATES_DEPLOYMENT_2026-09-27.json`; the
current-source live proof is
`docs/CURRENT_SOURCE_BRADBURY_LIVE_PROOF_2026-09-29.json`. Release status is
recorded in `deployments/release-manifest.json`.
