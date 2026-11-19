# 08 — Multi-Company (Multi-Tenant) Architecture

Visual: **VB-13**. Decisions D13, D14, D18, D28. Schema in doc 07 Part B.

## 1. Model: everything is a workspace

Every user has a **personal workspace** (`organizations.kind='personal'`, created at signup). Companies are additional workspaces (`kind='company'`). *All* product data (memory, conversations, tool calls, usage, plugin installs, settings) is keyed by `org_id`. A person using VALIS for themselves and for two employers is one `users` row with three memberships and **three isolated data sets**. One code path serves individuals and companies; there is no "user data vs org data" fork to leak across.

**Active workspace:** a device session runs in exactly one active workspace at a time (switcher in the app and via voice "switch to Acme"). The orchestrator, memory, catalogue, risk ceiling, vision and retention policy all come from the active org. Switching closes the current realtime session and clears the on-device context cache for the previous org.

## 2. Roles and permissions

| Role | Intent |
|---|---|
| `owner` | Full control incl. deletion, billing, ownership transfer (≥ 1 per org) |
| `admin` | Members, policies, plugins, integrations, audit (no ownership transfer/deletion) |
| `billing_admin` | Subscription, invoices, usage; no access to content/policies |
| `member` | Uses VALIS in this workspace; manages own memory/devices |
| `guest` | Limited use (e.g. contractors): no org memory write, no plugin credentials, risk ceiling capped to SAFE/SENSITIVE |

Permission strings (stable): `org.read, org.manage, org.policy, org.delete, member.read, member.invite, member.manage, billing.read, billing.manage, plugin.install, plugin.manage, plugin.use, memory.read, memory.write, memory.org.write, history.read, activity.read, audit.read, usage.read, file.write`. A static role→permission map ships in code (`tenancy/roles.ts`) and is tested; custom roles are a v2 feature (table reserved: `roles`, `role_permissions`).

## 3. Isolation (foundational, layered)

1. **Application layer:** every handler runs inside `withOrgContext(orgId)`; there is no query helper that works without it.
2. **Database layer:** RLS on every tenant table, `FORCE`d, app role without `BYPASSRLS` (doc 07 §B2). Composite FKs `(org_id, …)` prevent cross-org references.
3. **Storage layer:** object keys prefixed `org/{org_id}/…`; pre-signed URLs are minted per object, short-lived (≤ 5 min), org-bound.
4. **Encryption layer:** DEK per org (KMS-wrapped); Enterprise may bring/rotate its own KEK; crypto-erase on org deletion.
5. **Realtime layer:** sessions carry `org_id`; the tool catalogue, plugin credentials, and memory queries are all derived from it; cache keys include `org_id`.
6. **Observability layer:** metrics/logs are labelled `org_id` but never contain content; Admin console queries go through the same RLS (platform operators use a separate audited `support` role with time-boxed, logged access).
7. **Testing layer:** RLS fuzz in CI; "two-org" fixtures in every integration test.

*Dedicated tier (later):* database-per-tenant or dedicated cluster for customers who require it; the code already isolates by `org_id`, so this is a deployment/config change.

## 4. Organisation lifecycle & member management

* **Create:** `POST /v1/orgs` → org + owner membership + default `org_settings` + free-plan subscription row.
* **Invite:** email invite with single-use token (hashed at rest, 7-day expiry); accept requires login; domain-restricted invites optional (`allowed_domains`).
* **Join/Leave/Remove:** removal revokes memberships, closes live sessions, **retains the member's personal workspace** and removes their access to org memory; org-scope memory authored by them stays with the org (policy-controlled).
* **Offboarding:** admin "remove & erase member's org-scoped personal items" optional.
* **Transfer/Delete:** ownership transfer requires step-up; org deletion = 14-day soft delete → crypto-erase + purge job + audit tombstone.
* **SSO (v2, Enterprise):** SAML/OIDC via the IdP (Supabase SSO or WorkOS); SCIM provisioning later. Not required for M5.

## 5. Organisation settings (policy as data)

| Setting | Values | Effect |
|---|---|---|
| `risk_ceiling` | SAFE / SENSITIVE / CONSEQUENTIAL | Orchestrator removes tools above the ceiling; device broker enforces too |
| `vision_policy` | off / allowlist / user_choice (+ `vision_allowlist`) | Server tells the client at `session.ready`; client enforces; server rejects frames when `off` |
| `memory_policy` | off / ask / auto | Controls proposals and org-scope memory |
| `history_policy`, `retention_days` | per org | Content retention and purge cadence |
| `allow_always_allow` | bool | Whether users may create "always allow" tool grants |
| `plugin_policy` | allowlist / open / off | Which plugins members may use |
| `data_region` | default (more later) | Placement (single region at launch; field reserved) |
| `require_biometric_for` | none / consequential / all | Pushed to clients |
Settings changes are audited and take effect on the next session (and immediately for revocations).

## 6. Company integrations

Org-level plugin installs (`org_plugin_installs`) hold config and a `secret_ref` (KMS-encrypted secret blob) for org-wide credentials; per-user OAuth tokens live in `plugin_credentials`. Admins grant scopes at install; users consent individually for user-level scopes. Integration health (last success/error counts) is visible in the Admin console.

## 7. Billing, limits, usage

* **Plans:** `free`, `plus` (individual), `team` (per seat), `enterprise` (custom). Prices and exact limits are a business decision and live in the `plans` table (not hard-coded); the structure supports seat-based and usage-based components.
* **Meters:** `voice_seconds, vision_frames, tokens_in, tokens_out, tool_calls, storage_bytes, embedding_tokens`. Events are recorded per turn by the orchestrator; rollups hourly/daily by the worker.
* **Limits:** `usage_limits` per org/meter/period with `soft_limit` (warn user in-character and notify admins at 80%/100%) and `hard_limit` (reject new sessions with `USAGE_LIMIT_REACHED`; in-flight turn completes). Limits are enforced at `session.start` and every 60 s during a session.
* **Entitlements:** `entitlements(org_id, feature, value)` is the *only* thing the product code consults (e.g. `max_concurrent_sessions`, `vision`, `plugins`, `history`, `sso`). Billing events write entitlements; code never branches on plan names.
* **Providers (D18):** `BillingPort` with Stripe (organisations, web checkout, invoices, usage-based billing via meters) and Google Play Billing (consumer Android; server verification + RTDN). Confirm provider eligibility for your legal entity before M5; alternatives behind the same port: Paystack (card/bank in supported markets), Paddle or Lemon Squeezy (merchant-of-record, handles sales tax/VAT).
* **Dunning/grace:** failed payment → 7-day grace → downgrade entitlements (never delete data); admins notified.

## 8. Audit history

Append-only `audit_logs` (doc 07): who/what/when for membership changes, role changes, policy edits, plugin install/uninstall, billing changes, data export/erase, tool-call decisions with `risk>=SENSITIVE`, admin/support access. Searchable in the Admin console (filter by actor, action, date), exportable CSV/JSON, retention per plan (≥ 12 months). Content is never stored in audit meta — IDs, categories, counts only.

## 9. Admin console (`apps/admin`, M5)

Pages: Overview (usage, active members, health) · Members & roles · Invitations · Policies (§5) · Plugins & integrations · Usage & limits · Audit log · Billing (link to portal). Auth via the same IdP; every action goes through `/v1/orgs/{id}/…` endpoints with RBAC; no direct DB access from the front end.

## 10. Testing & acceptance

* RLS fuzz and two-org integration fixtures (doc 07 C5); role/permission matrix tests (every endpoint × every role = expected allow/deny); invitation/removal flows including live-session closure (≤ 30 s); limit enforcement (soft/hard) with simulated metering; policy propagation tests (change `risk_ceiling` → next catalogue excludes tools; vision `off` → frames rejected).
* **Acceptance:** zero cross-tenant reads/writes in CI fuzz (≥ 10⁵ randomised operations); member removal effective within 30 s; each org setting demonstrably changes behaviour in an end-to-end test using the mock provider; audit trail complete for all listed events.
