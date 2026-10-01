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
the consensus workers during the persisted redirect probe. The pinned source
commit, patch hash, built modules binary hash, active web configuration hash,
and mounted components are recorded in
`deployments/release-manifest.json`.

## API audit (2026-10-01)

The pinned/local runtime evidence answers the response questions as follows:

- `response.status` is correct for the deployed/pinned GenVM path and for the
  repository's GLSim mocks. The public Web Access examples use the separate
  `response.status_code` spelling, but that documentation naming does not
  prove that the deployed source should be changed.
- `response.headers` is exposed by the local GLSim full-response adapter and by
  the pinned runtime response adapter. The repository's tests exercise the
  nested `headers` mapping and the persisted probe observed `Location`.
- The local GLSim live HTTP handler and the unpatched pinned `reqwest` client
  follow redirects before the contract receives a response. The tracked
  `genvm-v0.2.16-no-redirect.patch` changes only that runtime behavior; its
  persisted probe observed `status=302` and `Location` without fetching the
  final resource. The available Bradbury provenance record reports the
  redirect-following behavior, so Bradbury cannot currently be treated as
  exposing the redirect boundary to the contract.
- No supported documented/current response field in the pinned artifact,
  GLSim types, linter stubs, or official Web Access examples exposes an
  effective URL or redirect history. An Intelligent Contract therefore cannot
  enforce effective-origin/history on Bradbury with the currently evidenced
  API. The existing `Location` rejection remains useful when a 3xx response is
  observable, but it is not effective-origin proof when redirects are followed.

This is a runtime/provenance finding, not a contract-source change. The
effective-origin requirement remains a real platform blocker for the frozen
release policy until Bradbury exposes a supported no-redirect boundary or
effective URL/history.

The persisted local-runtime checkpoint contains deployment and behavioral
probes, but its Authorization source is not the current Bradbury typed source
and therefore cannot close current-source Gate I. This is **local proof only**;
predecessor/local evidence is retained without being relabeled as current
Bradbury proof. Public/Bradbury behavioral recertification and final release
remain separately gated. See
`docs/CURRENT_SOURCE_RUNTIME_CHECKPOINT_2026-09-27.md` and
`deployments/release-manifest.json`.
