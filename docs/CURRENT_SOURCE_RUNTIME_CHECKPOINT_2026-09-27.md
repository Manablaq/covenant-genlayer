# Current-source supported-runtime checkpoint — 2026-09-27

This checkpoint records the exact current-source backend through complete
supported-local-runtime behavioral closure. It does not claim a public or
Bradbury deployment, production release, or Gate J freeze.

## Frozen source identity

- Source commit: `3601eb4c1715afe9a607a4685ec290338913bf7c`
- Source tree: `9436b3a12861c63c30105cd2b1f485b6c5780aa0`
- Authorization SHA-256: `24ad76f931ccef6dca2ca6fbe94971b3eb22d7a98facb5c3de9c4491d6e507ed`
- Mandates SHA-256: `aa38488fb44815a248ffbf5fa9938449a66954bfa94717686bc7b7cf4fdee4b2`
- Chain ID: `61999`
- Validators: `5`
- Mandates: `0xdFEce9C4ae3124B8de273B75227F6DC1DE30297C`
- Authorization: `0xEBb2863137Dff7e96886090D303373E8Ec9CF5B8`

The live contract source hashes match the frozen repository source hashes.

## Deployment and mandate setup

- Mandates deployment: `0x4f8814f7f84db106f47a947ddefcb902f2f782dc1c703e4a370c72aea1e6922b`
- Authorization deployment: `0x32687d2ff5b61f1ab8a4bfcb59ba9d3685c1e6e806ce737425d78276b1fdb2bb`
- Mandate creation: `0xd2a0e3cf3461c96af3cbbdb06f14eb971fddcbb58d4f845824eefca58008b727`
- Mandate ID: `0xcc8506d1809fc4664c5f9287816f8c51198c250fe995cc505c340d4b12de8ab7`
- Mandate version: `1`
- Mandate state parity: `PASS`
- Authorization → Mandates binding: `PASS`

All successful writes below reached `FINALIZED / MAJORITY_AGREE`. Each was
prepared from a persisted unsigned transaction, bound to an exact fingerprint,
signed once, submitted once, and recovered by transaction ID. Failed or
expired attempts were not blindly retried.

## Current-source live closure

### Approval

- Create request: `0x819e5ecbe813fd570145d6e8b6b29d89816ac43c0993c28704ac271a042c760a`
- Request ID: `0x8bfd66e1166ebd047919d45e3c13a6a27d075dff219093e6635e7a7f598e59e8`
- Evaluation: `0x3cef554f5954d63f94c8756de86c87c33eb2087de2950f22cca6ff76b2b09761`
- Result: `AUTHORIZED`; request/evidence/action/receipt parity passed.

### Independent rejection

- Create request: `0xce41bada44665e5176df386a26ea5f07488ea0087323aae5a36c6ae6e68edef1`
- Request ID: `0xa93a5026d5a339d9a9729da90d6b2965fd4b54c05c43748aff25781dc62418e0`
- Evaluation: `0xaab35ae6b5b2f9453305bcf2278874c6372240b417ea1d29322100ca628a568e`
- Result: terminal `DENIED`; action identity and evidence parity passed; no receipt.

### Repair and replacement

- Create request: `0xa3d9c20e1480042a1e295f0414d4fbd138326138769d897ab0e356ff4aaf130e`
- Request ID: `0x691309a9fc6a3f8f69dde6be838649c926167200f3ec0f37a74988bc25e8872f`
- Evaluation to `REPAIR_REQUIRED`: `0x1552e4249614a54b324bcb0cdb807baf9e3cac891fed1679241cbae172bd2253`
- Evidence replacement: `0xda06c3d9dceebe07c0a25871ae03153623a24b8bf97bb6117465e9b27cde9178`
- Re-evaluation: `0x930dfa24b47fb729b2e9350e9a95e2ee0c56a0fd062ae3d4b797dcddb7a17e1f`
- Result: `AUTHORIZED`; revision advanced to `1`, request ID/action subject stayed fixed,
  action intent matched the replacement, and the repair deadline stayed fixed.

### Timeout and recovery

- Request ID: `0x8722ea20195a5b559c6f826d1eba5631ac4c091dc8755d0cf655ff97ef51e921`
- A replacement submitted after its fixed repair deadline was finalized as an
  execution error: `0x2d65db44997c64e937572780ca22350437b75406fffe186371ca7210e58260db`.
- No resend or replacement was performed after that error.
- After the persisted deadline and request expiry passed, explicit expiry finalized:
  `0x38c7939fa7c4c9ddfd59fb98d344eb81fbd92ec409370352e1a848b7ab5ba6f7`.
- Result: terminal `EXPIRED`; repair reason cleared; no receipt.

### Receipt consumption and replay protection

- Request ID: `0x73552aa5e65d451bac6a2e9ca162ec410891c8ecc650f671189b5c4abf896df1`
- Create request: `0xbe531abe20fd25a7b2d8e5e773cc9843085953e963c6a7b0acb0f28424bf93ae`
- Evaluation: `0x0185a4230dd8a3e7ed203078edd376c39814eedcdfdb57a08a17310b02d596c6`
- Authorized consumption: `0x8a0a175b5dab5bfd150945ca8d9159b96d3ad1abdf11e1f01528d31e9b328bc2`
- Result: terminal `CONSUMED`; `receipt_consumed=true`.
- Fresh replay attempt: `0x07ad4b8ae6d4a6cdfb3d878f0da79e9a8d2eca22ddc774ed5561f3866388afd7`.
- Replay result: finalized terminal-state rejection; request remained `CONSUMED`.

### Redirect/effective-origin provenance

The active local JSON-RPC GenVM manager was probed against the deterministic
302 fixture using the mounted current runtime. The result was:

`status=302;location=b'/final'`

This proves the active runtime exposed the redirect response and `Location`
header instead of following `/final`. Runtime source, patch, binary,
configuration, and mounted-component hashes remain recorded in
`deployments/release-manifest.json`. The machine-readable probe summary is
under `work/phase6d-current-redirect-probe-20260927-current/`.

## Release boundary

The backend contract implementation and all supported-local-runtime behavioral
gates are complete for this source candidate. The repository remains
`UNRELEASED` because the following are external release gates, not bypassed:

- Bradbury runtime provenance and redirect compatibility;
- Bradbury deployment and Gate I live verification;
- Gate J reviewer evidence freeze and final certification.

The exact release state is machine-readable in
`deployments/release-manifest.json`. Historical predecessor-source evidence is
not used as current-source proof. Two current-source Bradbury deployment paths
were rejected before acceptance because the network reported `gas limit too
high`; the returned identities were not visible through
`eth_getTransactionByHash`, the sender nonce remained unchanged, and no
Bradbury transaction or deployment address is recorded as successful.

The exact current-source signed transaction used gas limit `17,060,259` and
was bound to fingerprint
`1e2ae661318e46a762b204f05a94260a1f2d3198dc2846582bdfa1115319d399`. A
read-only probe returned `execution reverted` for gas caps through
`16,777,216`, so lowering the gas limit would be an unsafe out-of-gas guess,
not a valid deployment recovery. Bradbury deployment and Gate I therefore
remain externally blocked pending a supported network deployment envelope or a
separately reviewed source-size/gas reduction.
