# 09 — Plugin Framework Specification

Visual: **VB-14**. Decision D15. Goal: add capabilities **without retraining the core model** — the model is trained once to use *a generic tool-calling protocol*; every plugin is data (a manifest with JSON-Schema tools) injected into the per-session catalogue.

## 1. Plugin kinds

| Kind | Where it runs | v1? |
|---|---|---|
| `builtin` | inside the platform (`memory`, `usage`, later `web_search`) | yes |
| `device` | the Android app's built-in tools (doc 06) — registered as the first-party `device` plugin so one catalogue pipeline covers everything | yes |
| `http` | a third-party/org-hosted HTTPS service implementing `/invoke` | yes |
| `wasm` / on-device scripts | sandboxed code | no (v2) |

## 2. Manifest (`plugin.json`, signed)

```jsonc
{
  "manifest_version": 1,
  "id": "acme.crm",                      // reverse-DNS, immutable
  "version": "1.4.0",                    // semver
  "publisher": { "name": "Acme", "verified": false },
  "display": { "name": "Acme CRM", "description": "Look up and update CRM contacts", "icon": "https://…" },
  "min_platform": "1.0",
  "hosting": { "type": "http", "base_url": "https://crm.acme.example/valis", "timeout_ms": 8000 },
  "auth": { "type": "oauth2",            // none | api_key | oauth2 | org_secret
            "authorize_url": "…", "token_url": "…", "scopes": ["contacts.read","contacts.write"] },
  "permissions": [                       // scopes VALIS enforces before calling
    { "scope": "contacts.read",  "label": "Read your CRM contacts", "level": "user" },
    { "scope": "contacts.write", "label": "Edit CRM contacts",       "level": "user" } ],
  "tools": [
    { "name": "find_contact", "description": "Find a contact by name or email.",
      "input_schema": { "type":"object","required":["query"],"properties":{"query":{"type":"string","maxLength":200}},"additionalProperties":false },
      "output_schema": { "type":"object","properties":{"contacts":{"type":"array","maxItems":10}} },
      "risk": "SENSITIVE", "required_scopes": ["contacts.read"], "idempotent": true,
      "confirmation_template": "Look up “{query}” in Acme CRM?", "timeout_ms": 5000 },
    { "name": "update_contact", "risk": "CONSEQUENTIAL", "required_scopes": ["contacts.write"],
      "idempotent": false, "confirmation_template": "Update {contact_name}: {change_summary}?", "…": "…" } ],
  "data_classification": "business-confidential",
  "webhooks": { "events_url": null },
  "signature": "ed25519:…"               // publisher key; platform verifies on registration
}
```
Tool ids exposed to the model: `acme.crm.find_contact` (namespace = plugin id). Descriptions are length-capped (≤ 600 chars) and **sanitised** (no instructions addressed to the model beyond describing the tool); the platform may wrap them with its own preamble.

## 3. Lifecycle

1. **Register** (platform admin or verified publisher via `POST /v1/admin/plugins/{id}/versions`): schema-validate manifest, verify signature, lint tool schemas (no `$ref` to remote, bounded sizes), static policy checks (risk labelled, confirmation template present for CONSEQUENTIAL), store in `plugin_versions`.
2. **Install** (`org.plugin.install`): admin picks version, reviews permissions, grants scopes → `org_plugin_installs`; org secrets stored encrypted (`secret_ref`).
3. **Authenticate:** per-user OAuth (`/v1/plugins/{id}/oauth/start`→callback) stored encrypted in `plugin_credentials`; `org_secret` plugins need no user step; `none` plugins skip.
4. **Expose:** `tools.catalogueFor(ctx)` merges `device` + `builtin` + installed enabled plugins, then **filters** by: org `plugin_policy`, granted scopes, user-level auth present, org `risk_ceiling`, role (guest limits), device capabilities, plugin health (circuit open → hidden). The result has a `catalogue_version` hash; the device and model both see only this.
5. **Execute:** orchestrator → `tools.invoke(tool_call)` (below).
6. **Update:** new version registered → orgs stay pinned until an admin updates (or enable auto-update for patch/minor); breaking schema changes require a major bump; old versions deprecated with a sunset date.
7. **Disable/Uninstall:** immediate removal from catalogues; credentials revoked/deleted; audit entry.

## 4. Execution protocol (`http` plugins)

```
POST {base_url}/invoke
Headers: Authorization: Bearer <platform-signed JWT: iss=valis, aud=plugin id, org, user, tool, scopes, exp ≤ 60 s, jti>
         X-Valis-Signature: HMAC-SHA256(body, per-install secret)    X-Request-Id, Idempotency-Key: <tool_call_id>
Body: { "tool":"find_contact","args":{…},"context":{"org_id":"…","user_id":"…","locale":"en","user_credentials":{"access_token":"…"}} }
→ 200 { "status":"ok","data":{…} }      // validated against output_schema
→ 4xx/5xx { "status":"error","code":"NOT_FOUND|RATE_LIMITED|UNAUTHORIZED|INVALID|UPSTREAM","message":"…","retryable":false }
```
Rules: HTTPS only, TLS verified, SSRF-guarded outbound (blocklist for private ranges, DNS pinning), response ≤ 256 KB, timeout per tool (≤ 15 s), **no redirects** to other hosts, retries only for `idempotent` tools (1 retry, jittered), circuit breaker (5 failures/30 s → open 60 s), per-org + per-plugin rate limits, concurrent invocation cap. The **user's** OAuth access token is passed only for the call and never logged.

## 5. Permission scopes & risk

Scopes are the plugin's declared permissions; VALIS enforces them **before** calling (tool requires scope S → user/org must have granted S). Each tool declares `risk`; the platform applies the same policy engine as device tools (doc 06 §5): CONSEQUENTIAL plugin tools need a **device-rendered confirmation** built from the manifest's `confirmation_template` + validated args (the plugin cannot supply free text for the card). Plugin results are **untrusted** (`source=plugin, trust=untrusted`) and cannot trigger tool calls on their own (D24); calls derived from them always confirm.

## 6. Errors, logging, versioning

* Errors from plugins are normalised to `PLUGIN_ERROR` with `{plugin_id, tool, code, retryable}` for the model and the user ("Acme CRM didn't respond"); raw upstream messages are logged (metadata) but not shown unvetted.
* `plugin_invocations` (an extension of `tool_calls`) record plugin_id, version, tool, status, duration, bytes in/out, org/user, `derived_from`; no args/results content in logs.
* Versions pinned per org; the model-visible tool id excludes the version, the catalogue binds it.

## 7. Organisation-level configuration

Per install: enabled flag, config JSON validated against the manifest's `config_schema`, allowed roles (e.g. only `admin`+`member`), tool allow/deny list (disable `update_contact` but keep `find_contact`), per-tool confirmation override (can only *raise* strictness), usage quotas. Changes are audited.

## 8. First-party plugins at launch

| Plugin | Tools |
|---|---|
| `device` (kind `device`) | the doc 06 tools |
| `memory` (builtin) | `memory.propose`, `memory.recall`, `memory.forget` (the model-side memory interface; policies in doc 07 §A5) |
| `valis.time` (builtin) | `now`, `timezone_convert` (trivial, proves the pipeline) |
Third-party examples are *fixtures* in the test suite (a mock CRM plugin) — no marketplace launch is assumed in v1.

## 9. Testing & acceptance

* Manifest schema + signature tests; catalogue filter matrix (policy × scopes × role × risk ceiling × circuit state); invocation tests against a mock plugin (success, 4xx, 5xx, timeout, oversize, schema-violating output, SSRF attempts); OAuth flow tests; version pin/upgrade tests; security tests: a plugin cannot read another org's credentials; plugin output containing "ignore previous instructions" is inert.
* **Acceptance:** a *new* mock plugin is installed and used end-to-end (catalogue → model tool call (mock provider) → confirmation → invoke → result) with **zero** changes to the app, orchestrator or model; uninstall removes it everywhere within one catalogue refresh; all failure modes produce user-readable outcomes.
