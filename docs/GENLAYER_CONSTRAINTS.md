# Covenant — GenLayer Constraints

Status: research baseline.

This file records implementation-sensitive GenLayer facts that must be verified against current official documentation before Covenant contracts are frozen.

## Verified current constraints

### GenVM version pinning

Every Intelligent Contract must begin with the GenVM dependency/version comment.

Covenant pins the following reviewed runner identity:

`py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`

The matching SDK/artifact environment is explicitly pinned to GenVM `v0.2.16`.

SDK-dependent linter operations must run with `GENVM_VERSION=v0.2.16` so unrelated newer cached artifacts cannot silently change validation behavior.

Production Covenant contracts must therefore begin with the exact runner dependency declaration. Under the pinned SDK/toolchain, the second line carries the narrow Pyright compatibility directive `# pyright: reportUnknownMemberType=false` because the SDK's public decorator typing is incomplete under strict Pyright.

No broader strict-typecheck suppression is permitted.

Any runner, GenVM release or compatibility-rule change requires the affected static, deterministic, full-runtime and deployment-parity gates to be rerun.

### Persistent storage

Persisted collections must use supported GenLayer storage types.

Examples:

- `DynArray[T]` instead of persisted `list[T]`
- `TreeMap[K, V]` instead of persisted `dict[K, V]`
- fixed-size integer types such as `u256`, `i32`, etc. instead of an ordinary persisted Python `int` unless `bigint` is intentionally required

Only fully instantiated generic storage types are allowed.

### Nondeterministic execution

Web/LLM work belongs inside GenLayer nondeterministic execution.

Storage mutation, cross-contract consequences and message emission must remain outside the nondeterministic block and consume only the accepted result.

### Leader output is untrusted

A validator must independently verify decision substance.

The following are insufficient by themselves:

- valid JSON;
- an allowed enum;
- non-empty reasoning;
- confidence within a numeric range.

Authorization-driving fields must be independently derived or independently checked against authoritative evidence and explicit criteria.

### Structured consequential consensus

Covenant will compare exact decision-bearing fields whenever exact values determine a consequence.

Open-ended reasoning may vary. Consequential fields may not.

### Finality

`Accepted` is provisional.

A successful appeal may change the eventual outcome.

Irreversible consequences must wait for `Finalized`.

External EVM messages are finalized-only.

### Execution result

Consensus status and execution success are separate facts.

A transaction being Accepted or Finalized does not by itself prove successful GenVM execution.

Backend verification must record both lifecycle/status and execution result.

### Testing layers

Direct Mode is used for:

- storage logic;
- state-machine logic;
- deterministic invariants;
- mocked nondeterministic behavior;
- fast validator-unit checks.

It is not sufficient by itself for backend release.

Full GenVM/multi-validator runtime testing is required for consensus-sensitive release paths before Bradbury.

### Static tooling

Every contract must pass, as supported by the pinned toolchain:

- `genvm-lint check`
- `genvm-lint validate`
- `genvm-lint typecheck --strict`
- `genvm-lint schema`

Any toolchain limitation must be documented rather than silently ignored.

## Contract sizing policy

Previous projects encountered deployment-size pressure.

The current official documentation reviewed for this baseline does not establish a universal Bradbury source-byte limit that we can safely treat as a fixed architectural constant.

Therefore Covenant will not invent a numeric limit.

Instead:

1. architecture starts modular;
2. every contract has a single explicit responsibility;
3. exact UTF-8 source size is measured continuously;
4. ABI/schema artifact size is recorded;
5. growth is gated in CI;
6. the complete graph is tested in the full runtime before Bradbury;
7. any actual runtime/CLI size boundary encountered is recorded with exact tool/version evidence;
8. Bradbury is not used as a trial-and-error compiler/deployment debugger.

## Official references

- https://docs.genlayer.com/developers/intelligent-contracts/first-contract
- https://docs.genlayer.com/developers/intelligent-contracts/storage
- https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle
- https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism
- https://docs.genlayer.com/developers/intelligent-contracts/features/messages
- https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/finality
- https://docs.genlayer.com/developers/intelligent-contracts/testing
- https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup
- https://docs.genlayer.com/api-references/genlayer-linter
- https://docs.genlayer.com/developers/intelligent-contracts/deploying
