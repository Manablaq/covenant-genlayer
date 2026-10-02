# GenVM web redirect remediation

Date: 2026-10-02

## Outcome

A current GenVM patch is prepared and locally verified without removing a
Covenant feature. It adds an explicit runtime configuration boundary for web
redirects while preserving the existing behavior by default.

The patch is:

- upstream repository: `https://github.com/genlayerlabs/genvm-manager`
- upstream commit: `619dfad4bae51c191ef66c3e8cac6ed996961858`
- upstream tag: `v0.6.0-rc8`
- file: `runtime/patches/genvm-v0.6.0-rc8-configurable-web-redirects.patch`
- patch SHA-256: `c835f3beb94065fd0fa4a56040aa6882f455617a3218338b02c954eaa2241b68`

## Design invariants

1. `follow_redirects` belongs to the GenVM web-module configuration.
2. Its default is `true`, so existing deployments remain backward compatible.
3. Covenant validators must set it to `false`.
4. Both filtered web requests and allowlisted-host web requests use the
   configured value.
5. With `false`, reqwest uses `Policy::none()`, returning the original 3xx and
   `Location` header to the contract and never fetching the redirect target.
6. The operator-trusted signer uses a separate client with its prior behavior.
7. LLM/provider contexts continue through the original default constructor and
   retain their prior behavior.
8. Existing SSRF and HTTPS-to-HTTP downgrade protections remain active whenever
   redirect following is enabled.

## Verification performed

The patch was generated from a clean upstream base and checked against a
second clean checkout of the exact commit using `git apply --check`.

Formatting:

```text
cargo fmt --all -- --check
PASS
```

Targeted runtime tests used Rust `1.88-bookworm`, GenVM's documented
`vendored-lua` feature, executor submodule commit
`f7f95a31dddbef2aa9371e2228644f83dcce9fe3`, Lua 5.3.6 headers from the pinned
`lua-src` crate, and GenVM's pinned `lsqlite3` 0.9.6 source:

```text
cargo test --features vendored-lua --test request_localhost \
  test_unfiltered_client_ -- --nocapture

3 passed; 0 failed; 0 ignored; 3 filtered out
```

The passing cases prove:

- no-follow returns `302` plus the original `Location` and does not connect to
  the target;
- default behavior still follows the redirect to the final `200` response;
- the pre-existing allowlisted-host request behavior still works.

The two affected context consumers also compiled independently with one linker
job:

```text
cargo test --features vendored-lua --test providers --no-run -j 1
PASS

cargo test --features vendored-lua --test signing_server --no-run -j 1
PASS
```

An attempted all-test `--no-run` compile exceeded the local Docker memory limit
while several unrelated test binaries linked in parallel (`ld` was killed with
signal 9). It produced no Rust compile error. The affected binaries were then
compiled serially as recorded above; no full-suite pass is claimed here.

## Studio Next read-only preflight

The canonical endpoint `https://studio-dev.genlayer.com/api` was probed without
signing or submitting a transaction. It returned chain ID `0xf22d` (`61997`),
16 validators, and a live block number. The official `genlayer` CLI package
`0.40.0-rc.3` contains a first-class `studio-dev` profile with that endpoint
and chain ID. The installed stable CLI `0.39.2` does not contain that profile,
so it must not be used as if it were Studio Next tooling.

Exact preflight evidence is in
`docs/STUDIO_NEXT_READ_ONLY_PREFLIGHT_2026-10-02.json`.

## Remaining network boundary

Neither the source patch nor a successful Studio RPC preflight proves that
Studio Next or Bradbury validators run the patched runtime. Release requires:

1. an immutable GenLayer runtime build containing this patch or an equivalent
   upstream implementation;
2. validator configuration with `follow_redirects: false` on the target
   network;
3. a read-only contract probe showing the original 3xx and `Location` while a
   controlled target records no request;
4. identical results across the validator set; and
5. current-source Covenant behavioral recertification and the existing Gate J
   evidence freeze.

Until those external runtime facts are proven, the repository remains
`UNRELEASED`. That status is a deliberate evidence boundary, not an application
feature bypass.
