# Runtime provenance gate

Covenant's evidence policy rejects an exposed `Location` header, but that
contract check is only enforceable when the GenVM web transport does not follow
redirects before returning the response.

The pinned GenVM v0.2.16 source commit is
`387e1a66e920cb2dfadcdce40ab2d28da02efd1e`. Its default `reqwest::Client`
follows redirects and the response adapter exposes only status, headers, and
body. That unpatched runtime cannot pass the Covenant release gate.

`patches/genvm-v0.2.16-no-redirect.patch` is the minimal source change: it
configures the production GenVM HTTP client with
`reqwest::redirect::Policy::none()`. With that patch, a redirect is returned as
a 3xx response with its `Location` header, and Covenant repairs it as
`REPAIR_EVIDENCE_REFERENCE_INVALID`.

For this local candidate, the no-redirect behavior was active in JSON-RPC and
the consensus workers during the persisted redirect probe; the active web
configuration hash is recorded in
`docs/GATE_F_LIVE_CLOSURE_2026-09-27.md`. Before public release, the patched
GenVM modules binary must still be rebuilt from the pinned commit, mounted
into every runtime component, and its source commit, patch hash, binary hash,
and validator configuration must be recorded. A source patch file alone is
not a production deployment certificate, so the release manifest remains
`UNRELEASED`.
