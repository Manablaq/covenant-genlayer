# Gate F Recovery Checkpoint — 2026-09-25

This document records the exact Covenant backend recovery checkpoint reached on
2026-09-25.

It is a provenance/checkpoint record only. The recovered Gate F toolchain,
historical certificates, runtime evidence, and recovery backups remain outside
the Git repository and are not represented here as if their bytes were tracked
by Git.

## Repository checkpoint

- Branch: `main`
- Parent checkpoint commit: `0779b3192ee7fe3e999e181f592f7477d7fff8eb`
- Parent checkpoint tree: `789f625ec07b0fb0b2f1be980f441a1de498280b`
- Authorization contract SHA-256: `aa788a90711c6c2a67a810c86ee21f77d53caa019c2a1d7518712e8166175a03`
- Mandates contract SHA-256: `a561a7a76a612cae8cae044452619e966f549baede471a59f6e08033e9d05cd4`
- Project Pyright launcher SHA-256: `ac86a29c10854e7cbf4217e1ac7a6ed1e0d4c01368b479bd5b450538f6bf5a64`
- Repository worktree before this documentation commit: clean

The parent checkpoint was verified synchronized with `origin/main` before this
document was created.

## Restored Gate F toolchain surface

The external isolated Gate F RC toolchain is restored and certified with:

- GenLayer CLI: `0.40.0-rc2`
- genlayer-js: `2.0.0-rc.1`
- genlayer-py: `0.19.0rc2`
- genlayer-test: `0.30.0rc2`
- Historical Node dependency tree SHA-256:
  `9fa554016cfaf3fbc151ece6b7419ec284745f17703c6d803584d7ca65618bf7`
- Historical toolchain manifest SHA-256:
  `ffd0b9d33771897448d0172828e704a459cd5b0790ff06273377aed4097e52f6`
- Post-sync recovery manifest SHA-256:
  `624dc65d556d84e4716a45bee7884868450a3c0ebff1f06399890fda514ef1fb`

The historical Node tree was recovered byte-exactly. The original raw npm
debug-log bytes are no longer retained, and historical root
`package-lock.json` byte identity is not claimed.

## Restored historical Gate F certificates

The following historical certificate byte streams have been restored exactly:

- Step 2 RC surface certification:
  `25392cf22292ce82e135e566f945efcde1d9d30c97f7b9ba60fca20850fd2109`
- Step 3 matched-runtime certification:
  `dfecb7b406a12cf92f214d9e6643f27d5dc7c44fd7e4d104b68fc71a2d0125ad`
- Step 5 adapted-G10 handoff certificate:
  `2d365e713b739d699cd26e6f8f1a7abc6dfab6092b0a895220ae768dcf33012f`

Step 2 and Step 3 were not rerun. Historical Step 3 runtime evidence
directories were not fabricated.

The Step 5 adapted-G10 Direct/GLSim execution was not rerun during recovery.
Only its byte-exact historical handoff certificate has been restored so far.

## Current Step 5 recovery boundary

The next historical recovery action is:

`RESTORE_BYTE_EXACT_ADAPTED_G10_VECTOR_CONTEXT_DIFF_SUMMARY_WITHOUT_GLSIM_RERUN`

The handoff certificate binds the following still-to-be-restored adapted-G10
artifacts:

- `adapted-g10-vector.json`:
  `e7bea28a387a27fad05c056133a83498a9565a1cb1ecfaf08e37a0d5750891c0`
- `transaction-context-template.json`:
  `ce4f7245bcfacc75c00f4f275722296dd28a03bf75a34becfb124968e0d99421`
- `adaptation-diff.txt`:
  `ec80334e2a1ab0c3d59258acfd21bba29e44fbcb0343acbae8a9ef3f46f95a6c`
- `adapted-g10-summary.txt`:
  `b216dc5f711b8615bfeded6981334909cd0d5944fe4e1fa4d89fb7a1d1ea7f3b`

## Backend completion still outstanding

Gate F is not complete at this checkpoint.

After historical Step 5 recovery is finished, the remaining backend proof
requires supported-runtime execution demonstrating:

1. the real approval path,
2. exact consequential multi-validator agreement,
3. raw response persistence before decoding,
4. lifecycle/active-decision binding,
5. materialized terminal `Finalized` status,
6. post-finality authorized application state,
7. the independent rejection path with eventual `Finalized`,
8. proof that rejection does not produce authorization,
9. timeout/transport failure behavior and repairability, and
10. redirect/effective-URL provenance behavior.

A previous Step 5 empty-key runtime probe consumed exactly one read-only
`gen_call` and stopped on a non-200 HTTP result. Recovery must not silently
repeat that consumed probe.

## Recovery safety boundary

At this checkpoint:

- repository contract mutation during recovery: **NO**
- repository test mutation during recovery: **NO**
- Step 2 rerun: **NO**
- Step 3 matched-runtime rerun: **NO**
- adapted-G10 Direct/GLSim rerun during recovery: **NO**
- blockchain write during recovery: **NO**
- transaction signing during recovery: **NO**
- transaction submission during recovery: **NO**
- fabricated historical runtime evidence: **NO**

Step 5 handoff restoration record SHA-256:

`9b58fbc553b4fb0fab150b2df1dfa44cd370d60474c9c09a36ca48b7d7968ff8`
