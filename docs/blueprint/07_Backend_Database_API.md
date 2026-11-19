# 07 — Backend Architecture, Database Specification, API Documentation

Visuals: **VB-11** backend infrastructure, **VB-12** database ERD, **VB-18** deployment. Decisions D10–D14, D17, D26.

# Part A — Backend architecture

## A1. Shape: one modular monolith, three process roles, one inference service

```
                 Android ─┐                 Admin Console ─┐
                          ▼ HTTPS/WSS                       ▼ HTTPS
                  ┌──────────────── Edge (Render LB / Cloudflare) ────────────────┐
                  │  TLS 1.3 · WAF/rate limit · WebSocket upgrade                 │
                  └───────┬───────────────────────────────────────┬───────────────┘
              role=api    ▼                          role=realtime▼
      ┌──────────────────────────────┐     ┌────────────────────────────────────┐
      │ REST /v1 (Fastify)           │     │ WSS /v1/realtime  (Gateway)        │
      │ identity · tenancy · memory  │     │ session · turn · media relay       │
      │ plugins · files · billing    │     │ orchestrator · tool broker (cloud) │
      │ usage · audit · admin        │     └──────────────┬─────────────────────┘
      └────────────┬─────────────────┘                    │ internal WSS/HTTP (signed)
                   │            role=worker               ▼
                   │   pg-boss: embeddings · summarise  ┌──────────────────────────┐
                   │   retention · billing sync · email │ Inference service (GPU)  │
                   ▼                                    │ providers: mock·cascade· │
        PostgreSQL 16 (+pgvector, RLS)                  │ minicpm-o (M8)           │
        Object storage (S3 API)                         └──────────────────────────┘
```
The three roles are the **same image** started with `ROLE=api|realtime|worker` (shared code, separate scaling). There are no other services at launch; module boundaries are enforced by lint rules (a module may import only another module's `index.ts` public API).

## A2. Module boundaries (service boundaries inside the monolith)

| Module | Owns | Public API (in-process) | Talks to |
|---|---|---|---|
| `identity` | JWT verification (JWKS), device registration, refresh binding, `users`, `devices` | `authenticate(req)`, `registerDevice()` | IdP (Supabase Auth) |
| `tenancy` | `organizations`, `memberships`, `invitations`, `org_settings`, RBAC | `requirePermission(ctx, perm)`, `withOrgContext(orgId, fn)` | all modules |
| `memory` | `memory_items`, `memory_events`, embeddings, retrieval, proposal policy | `query()`, `propose()`, `export()`, `erase()` | worker (embed), inference (embed provider) |
| `sessions` | `conversations`, `turns`, resume tokens | `openTurn()`, `closeTurn()` | orchestrator |
| `orchestrator` | prompt/context assembly, catalogue assembly, provider calls, claim guard | `runTurn()` | memory, tools, inference, usage |
| `tools` | tool catalogue, device-tool relay, cloud tool broker, `tool_calls` | `catalogueFor(ctx)`, `invoke()` | plugins, gateway |
| `plugins` | registry, versions, installs, credentials, invocation signing | `register()`, `install()`, `invokeHttp()` | tools |
| `files` | pre-signed uploads, `files` metadata, scanning, TTL | `presignUpload()` | object store |
| `billing` | plans, subscriptions, entitlements, Stripe/Play webhooks | `entitlementsFor(org)`, `BillingPort` | usage |
| `usage` | `usage_events`, rollups, limit enforcement | `record()`, `checkLimit()` | billing |
| `audit` | `audit_logs` (append-only) | `log()` | all |
| `notifications` | in-app + push (FCM) + email | `send()` | worker |
| `admin` | admin-only aggregate endpoints | — | all (read) |

## A3. Request lifecycle (REST)

1. Edge: TLS, WAF rules, IP rate limit.
2. `onRequest`: generate `request_id` (UUIDv7), start OTel span.
3. `authenticate`: verify JWT (aud/iss/exp; JWKS cached 10 min), load `user`, resolve `device_id` if present.
4. `resolveOrg`: `X-Org-Id` header (or default personal org) → verify membership (cached 30 s) → `ctx{user, org, role, permissions, plan}`.
5. `validate`: TypeBox schema for params/query/body; reject unknown fields.
6. `authorize`: `requirePermission(ctx, 'memory.read')`.
7. `withOrgContext`: open transaction, `SELECT set_config('app.org_id', …, true), set_config('app.user_id', …, true)`; **all queries run under RLS**.
8. Handler → module service.
9. `usage.record`/`audit.log` as applicable (inside the same transaction for mutations).
10. Serialise, `ETag` where useful, problem+json on error, span end, access log (no bodies).

## A4. Realtime lifecycle (WSS)

`GET /v1/realtime` with `Authorization` (JWT) and `X-Org-Id`; `session.start{client, capabilities, locale, active_org, resume_token?}` → entitlement + limit check → provider chosen from `model_endpoints` by plan/org policy → `session.ready{session_id, provider, capabilities, limits, tool_catalogue_version}`. Heartbeat 15 s; idle timeout 60 s outside a turn; max session 30 min (renewable). Full protocol in doc 11 §4.

## A5. Memory service (user-controlled)

**Layers:** working (context window, per turn) · episodic (conversation summaries, `memory_items.kind='episode'`) · semantic facts (`kind='fact'`, `'preference'`, `'person'`, `'task'`).
**Write path:** the model emits `memory.propose{kind, text, sensitivity, source_turn}` (a tool call). Policy (`org_settings.memory_policy` ∧ user setting): `auto` (store directly, non-sensitive kinds only), `ask` (default — status `pending`, character asks "Remember that?"), `off`. Sensitive categories (health, financial, government IDs, immigration, minors, credentials) are never auto-stored and can be blocked org-wide.
**Read path:** hybrid retrieval — pgvector HNSW cosine (top 20) ∪ Postgres FTS (top 20) → rerank by recency × confidence × scope → top *k*≈6, token-budgeted, injected as `source=memory, trust=user-owned` context.
**Controls:** list/edit/delete/pin, "forget everything", export JSON, erase on account deletion (hard delete + embeddings, tombstone in `audit_logs` without content). **Local-only mode:** items stay in SQLCipher on the device with FTS5 retrieval; the device injects the top-k into the request; the server persists nothing.
**Embeddings:** `EmbeddingProvider` interface (dimension configurable; default 1024) run on the inference host or a managed API; `memory_items.embedding_model` is stored so a re-embed job can migrate.

## A6. Orchestrator responsibilities

Assemble `InferenceRequest` (doc 11): system policy block (non-negotiable rules, trust-label legend), persona block (VALIS voice), org policy block, memory snippets, recent turns (token budget), tool catalogue (filtered: org policy ∩ user grants ∩ risk ceiling ∩ device capabilities), inputs. Stream provider events to the device; intercept `tool.call`; run the claim guard; record usage; trigger memory proposals; summarise the conversation asynchronously (worker) when it exceeds N turns.

## A7. Observability & operations

OTel traces across `api → realtime → inference`; metrics (RED per endpoint, turn latency segments, tokens, GPU queue depth, WS connections); structured logs (pino) with `request_id, org_id, user_id, device_id` only; Sentry for errors; SLO dashboards (availability, turn p95, tool verified-rate, claim-guard rate); audit log is separate from ops logs and append-only (revoked `UPDATE/DELETE`).

## A8. Error handling

All REST errors: RFC 9457 `application/problem+json`:
```json
{"type":"https://api.valis.ai/problems/limit-reached","title":"Usage limit reached","status":429,
 "code":"USAGE_LIMIT_REACHED","detail":"Monthly voice minutes exhausted for this workspace.","request_id":"01J…","retry_after":3600}
```
Stable `code` vocabulary: `AUTH_REQUIRED, AUTH_INVALID, FORBIDDEN, ORG_REQUIRED, NOT_MEMBER, VALIDATION_FAILED, NOT_FOUND, CONFLICT, IDEMPOTENCY_REPLAY, RATE_LIMITED, USAGE_LIMIT_REACHED, ENTITLEMENT_REQUIRED, PLUGIN_ERROR, PROVIDER_UNAVAILABLE, PROVIDER_TIMEOUT, POLICY_BLOCKED, PAYLOAD_TOO_LARGE, INTERNAL`. Retries: clients retry idempotent calls (GET, Idempotency-Key POSTs) on 429/503 with backoff; providers failing → orchestrator tries fallback provider per `model_endpoints.priority` before erroring.

---

# Part B — Database specification (PostgreSQL 16)

Conventions: `id uuid` (UUIDv7, app-generated), `created_at/updated_at timestamptz`, soft delete only where stated, **`org_id uuid not null` on every tenant-scoped table**, composite FKs `(org_id, x_id)` to prevent cross-tenant references, extensions `pgcrypto`, `vector`, `pg_trgm`.

## B1. Core DDL (excerpt; migrations are SQL-first in `services/api/migrations`)

```sql
-- Identity
create table users (
  id uuid primary key, idp_subject text not null unique, email citext unique,
  display_name text, locale text default 'en', created_at timestamptz not null default now(),
  deleted_at timestamptz
);
create table devices (
  id uuid primary key, user_id uuid not null references users(id) on delete cascade,
  platform text not null check (platform in ('android')), model text, os_api int,
  app_version text, push_token text, key_thumbprint text,         -- device keystore key (optional binding)
  attestation_level text, last_seen_at timestamptz, revoked_at timestamptz,
  created_at timestamptz not null default now()
);

-- Tenancy (D14: everything is a workspace)
create table organizations (
  id uuid primary key, kind text not null check (kind in ('personal','company')),
  name text not null, slug citext unique, owner_user_id uuid not null references users(id),
  plan_id text not null default 'free', status text not null default 'active',
  created_at timestamptz not null default now()
);
create table memberships (
  org_id uuid not null references organizations(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  role text not null check (role in ('owner','admin','billing_admin','member','guest')),
  status text not null default 'active', joined_at timestamptz not null default now(),
  primary key (org_id, user_id)
);
create table invitations (
  id uuid primary key, org_id uuid not null references organizations(id) on delete cascade,
  email citext not null, role text not null, token_hash bytea not null, invited_by uuid not null references users(id),
  expires_at timestamptz not null, accepted_at timestamptz, created_at timestamptz not null default now(),
  unique (org_id, email)
);
create table org_settings (
  org_id uuid primary key references organizations(id) on delete cascade,
  risk_ceiling text not null default 'CONSEQUENTIAL' check (risk_ceiling in ('SAFE','SENSITIVE','CONSEQUENTIAL')),
  vision_policy text not null default 'user_choice' check (vision_policy in ('off','allowlist','user_choice')),
  vision_allowlist text[] not null default '{}', memory_policy text not null default 'ask' check (memory_policy in ('off','ask','auto')),
  history_policy text not null default 'user_choice', retention_days int not null default 30,
  allow_always_allow boolean not null default true, plugin_policy jsonb not null default '{"mode":"allowlist"}',
  data_region text not null default 'default', updated_at timestamptz not null default now()
);

-- Conversations (metadata by default; content only if history is enabled)
create table conversations (
  id uuid primary key, org_id uuid not null references organizations(id) on delete cascade,
  user_id uuid not null references users(id), device_id uuid references devices(id),
  started_at timestamptz not null default now(), ended_at timestamptz,
  provider text, model_id text, provider_version text, summary text, history_enabled boolean not null default false
);
create table turns (
  id uuid primary key, org_id uuid not null, conversation_id uuid not null references conversations(id) on delete cascade,
  seq int not null, started_at timestamptz not null, ended_at timestamptz,
  input_kinds text[] not null, latency_first_audio_ms int, latency_first_token_ms int,
  tokens_in int, tokens_out int, status text not null, claim_guard_triggered boolean not null default false,
  content_enc bytea,                   -- null unless history_enabled; envelope-encrypted
  unique (conversation_id, seq)
);

-- Memory
create table memory_items (
  id uuid primary key, org_id uuid not null references organizations(id) on delete cascade,
  user_id uuid references users(id), scope text not null check (scope in ('user','org')),
  kind text not null check (kind in ('fact','preference','person','task','episode')),
  text_enc bytea not null, text_tsv tsvector, embedding vector(1024), embedding_model text,
  sensitivity text not null default 'normal' check (sensitivity in ('normal','sensitive')),
  status text not null check (status in ('pending','active','rejected','deleted')),
  confidence real not null default 0.7, pinned boolean not null default false,
  source_turn_id uuid, expires_at timestamptz, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index memory_embedding_hnsw on memory_items using hnsw (embedding vector_cosine_ops) where status='active';
create index memory_tsv on memory_items using gin (text_tsv);
create table memory_events (id uuid primary key, org_id uuid not null, memory_id uuid not null, actor text not null, event text not null, at timestamptz not null default now());

-- Tools, plugins
create table plugins (id text primary key, publisher text not null, display_name text not null, kind text not null check (kind in ('builtin','http')), status text not null default 'active');
create table plugin_versions (
  plugin_id text not null references plugins(id), version text not null, manifest jsonb not null, manifest_sig bytea,
  min_platform text, deprecated_at timestamptz, created_at timestamptz not null default now(), primary key (plugin_id, version)
);
create table org_plugin_installs (
  org_id uuid not null references organizations(id) on delete cascade, plugin_id text not null, version text not null,
  config jsonb not null default '{}', secret_ref text, enabled boolean not null default true, scopes_granted text[] not null default '{}',
  installed_by uuid not null references users(id), installed_at timestamptz not null default now(), primary key (org_id, plugin_id),
  foreign key (plugin_id, version) references plugin_versions(plugin_id, version)
);
create table plugin_credentials (
  id uuid primary key, org_id uuid not null, user_id uuid not null, plugin_id text not null,
  token_enc bytea not null, refresh_enc bytea, scopes text[] not null, expires_at timestamptz, created_at timestamptz not null default now(),
  unique (org_id, user_id, plugin_id)
);
create table tool_calls (
  id uuid primary key, org_id uuid not null, conversation_id uuid, turn_id uuid, device_id uuid,
  tool text not null, risk text not null, decision text not null, confirmed_by text, status text not null,
  evidence_kind text, derived_from text[] not null default '{}', args_hash bytea, duration_ms int, at timestamptz not null default now()
);

-- Usage, billing
create table plans (id text primary key, name text not null, kind text not null check (kind in ('personal','team','enterprise')), limits jsonb not null, features jsonb not null);
create table subscriptions (
  id uuid primary key, org_id uuid not null references organizations(id), plan_id text not null references plans(id),
  provider text not null check (provider in ('stripe','play','manual')), provider_ref text, status text not null,
  seats int, current_period_start timestamptz, current_period_end timestamptz, cancel_at timestamptz
);
create table entitlements (org_id uuid not null references organizations(id), feature text not null, value jsonb not null, source text not null, expires_at timestamptz, primary key (org_id, feature));
create table usage_events (
  id uuid primary key, org_id uuid not null, user_id uuid, device_id uuid, at timestamptz not null default now(),
  meter text not null check (meter in ('voice_seconds','vision_frames','tokens_in','tokens_out','tool_calls','storage_bytes','embedding_tokens')),
  quantity bigint not null, ref_turn_id uuid, provider text, model_id text
) partition by range (at);
create table usage_rollups (org_id uuid not null, day date not null, meter text not null, quantity bigint not null, primary key (org_id, day, meter));
create table usage_limits (org_id uuid not null, meter text not null, period text not null check (period in ('day','month')), hard_limit bigint, soft_limit bigint, primary key (org_id, meter, period));

-- Files, notifications, audit, models, consent
create table files (id uuid primary key, org_id uuid not null, user_id uuid, bucket_key text not null, mime text, bytes bigint, sha256 bytea, purpose text not null, expires_at timestamptz, created_at timestamptz not null default now());
create table notifications (id uuid primary key, org_id uuid not null, user_id uuid not null, kind text not null, payload jsonb not null, read_at timestamptz, created_at timestamptz not null default now());
create table audit_logs (
  id bigint generated always as identity primary key, org_id uuid not null, actor_user_id uuid, actor_kind text not null,
  action text not null, target_kind text, target_id text, meta jsonb not null default '{}', ip inet, at timestamptz not null default now()
);  -- append-only: REVOKE UPDATE, DELETE
create table model_endpoints (
  id uuid primary key, provider text not null, model_id text not null, provider_version text, url text not null,
  capabilities jsonb not null, config jsonb not null, priority int not null default 100, enabled boolean not null default true,
  plan_ids text[] not null default '{}', created_at timestamptz not null default now()
);
create table consent_records (id uuid primary key, org_id uuid not null, user_id uuid not null, kind text not null, version text not null, granted boolean not null, at timestamptz not null default now());
create table api_keys (id uuid primary key, org_id uuid not null, name text not null, prefix text not null, hash bytea not null, scopes text[] not null, last_used_at timestamptz, revoked_at timestamptz);
```

## B2. Row-level security (the isolation backbone)

```sql
alter table memory_items enable row level security; alter table memory_items force row level security;
create policy tenant_isolation on memory_items
  using (org_id = nullif(current_setting('app.org_id', true), '')::uuid)
  with check (org_id = nullif(current_setting('app.org_id', true), '')::uuid);
-- user-scope rows additionally require the owner
create policy user_scope on memory_items as restrictive
  using (scope = 'org' or user_id = nullif(current_setting('app.user_id', true), '')::uuid);
```
Applied to **every** tenant-scoped table via a migration helper; CI test enumerates all tables with an `org_id` column and fails if RLS is not enabled+forced. The application connects as a non-superuser role without `BYPASSRLS`; migrations run as a separate owner role. Cross-tenant jobs (rollups, retention) use a dedicated `worker` role with explicit `SECURITY DEFINER` functions that iterate orgs and set context per org.

## B3. Indexing, partitioning, retention

`usage_events` partitioned monthly (drop/archive after rollup + 13 months). `audit_logs` partitioned monthly, retained ≥ 12 months (org-configurable up to 7 years on Enterprise). `turns.content_enc` null by default; retention job purges per `org_settings.retention_days`. Hot indexes: `(org_id, user_id, created_at desc)` on conversations/memory; `(org_id, at)` on usage/audit/tool_calls; FKs indexed.

## B4. Encryption

Postgres disk encryption (provider) + **field-level envelope encryption** for `text_enc`, `content_enc`, `token_enc`, `refresh_enc` (AES-256-GCM; DEK per org wrapped by a KMS KEK; key id stored alongside; rotation job). Enterprise tier: customer-specific KEK. Embeddings are derived data and are deleted with their source rows.

---

# Part C — API documentation (`/v1`, OpenAPI 3.1 is the source of truth in `packages/contracts/openapi.yaml`)

Common: `Authorization: Bearer <jwt>`; `X-Org-Id` (defaults to the user's personal org); `Idempotency-Key` on POST/PATCH that create or charge; cursor pagination `?limit=&cursor=`; JSON; `request_id` echoed in `X-Request-Id`.

## C1. Endpoint catalogue

| Module | Method & path | Purpose | Permission |
|---|---|---|---|
| **Auth/identity** | `POST /v1/devices` | register device (+ optional keystore thumbprint, attestation token) | auth |
| | `GET /v1/me` | profile, memberships, default org, entitlements | auth |
| | `PATCH /v1/me` | update display name, locale | auth |
| | `GET /v1/devices` · `DELETE /v1/devices/{id}` | list / revoke | auth |
| | `POST /v1/me/export` · `DELETE /v1/me` | data export job / account deletion job | auth (step-up) |
| **Orgs** | `POST /v1/orgs` | create company workspace | auth |
| | `GET /v1/orgs/{id}` · `PATCH` | read / update | `org.read` / `org.manage` |
| | `GET /v1/orgs/{id}/members` · `PATCH /{userId}` · `DELETE /{userId}` | members & roles | `member.read` / `member.manage` |
| | `POST /v1/orgs/{id}/invitations` · `GET` · `DELETE /{invId}` · `POST /v1/invitations/accept` | invites | `member.invite` |
| | `GET/PATCH /v1/orgs/{id}/settings` | policies (risk ceiling, vision, memory, retention, plugins) | `org.policy` |
| | `GET /v1/orgs/{id}/usage` · `GET .../audit` | usage & audit | `usage.read` / `audit.read` |
| **Memory** | `GET /v1/memory?kind=&status=&q=&scope=` | list/search | `memory.read` |
| | `POST /v1/memory` | create (user-authored) | `memory.write` |
| | `PATCH /v1/memory/{id}` · `DELETE /v1/memory/{id}` | edit / delete | `memory.write` |
| | `POST /v1/memory/{id}/approve` · `.../reject` | resolve pending proposals | `memory.write` |
| | `POST /v1/memory/query` | retrieval (debug/Admin; the orchestrator uses it in-process) | `memory.read` |
| | `POST /v1/memory/export` · `DELETE /v1/memory` | export / forget all | `memory.write` |
| **Conversations** | `GET /v1/conversations` · `GET /{id}` · `DELETE /{id}` | history (only if enabled) | `history.read` |
| **Realtime** | `GET /v1/realtime` (WebSocket) | sessions/turns (doc 11 §4) | auth + entitlement |
| | `POST /v1/vision/frames` | pre-signed upload for oversize frames | auth |
| **Tools & plugins** | `GET /v1/tools/catalogue?device=` | effective catalogue for this user/org/device | auth |
| | `GET /v1/plugins` · `GET /v1/plugins/{id}` | marketplace/registry | auth |
| | `POST /v1/orgs/{id}/plugins` | install (scopes consent) | `plugin.install` |
| | `PATCH/DELETE /v1/orgs/{id}/plugins/{pluginId}` | configure / uninstall | `plugin.manage` |
| | `GET /v1/plugins/{id}/oauth/start` · `GET /v1/plugins/oauth/callback` | per-user plugin auth | auth |
| | `POST /v1/admin/plugins` · `POST /v1/admin/plugins/{id}/versions` | publish (platform admins) | platform |
| **Activity** | `GET /v1/activity?kind=tool|session` | tool-call/session history (metadata) | `activity.read` |
| **Billing** | `GET /v1/billing/plans` · `GET /v1/orgs/{id}/subscription` | plans / current | `billing.read` |
| | `POST /v1/orgs/{id}/billing/checkout` · `POST .../portal` | Stripe checkout / portal | `billing.manage` |
| | `POST /v1/billing/play/verify` | Play Billing receipt verify | auth |
| | `POST /v1/webhooks/stripe` · `POST /v1/webhooks/play-rtdn` | provider webhooks (signature-verified) | public + signature |
| **Files** | `POST /v1/files` (presign) · `GET /v1/files/{id}` · `DELETE` | uploads (e.g. saved frames) | `file.write` |
| **Notifications** | `GET /v1/notifications` · `POST /v1/notifications/{id}/read` | in-app inbox | auth |
| **Admin/platform** | `GET /v1/admin/models` · `POST` · `PATCH` | model endpoint registry & rollout | platform |
| | `GET /v1/health` · `GET /v1/ready` · `GET /v1/version` | probes | public |

## C2. Representative contracts

```jsonc
// POST /v1/memory
{ "kind":"preference","text":"Prefers short answers","scope":"user","sensitivity":"normal" }
// 201
{ "id":"01J…","status":"active","kind":"preference","text":"Prefers short answers","created_at":"…" }

// GET /v1/tools/catalogue?device=android
{ "catalogue_version":"2026-11-19.3","tools":[
  {"id":"device.open_app","version":1,"description":"…","input_schema":{…},"risk":"SAFE","requires_confirmation":false},
  {"id":"acme.crm.find_contact","version":3,"description":"…","input_schema":{…},"risk":"SENSITIVE","requires_confirmation":true,"plugin":"acme.crm@1.4.0"}]}

// PATCH /v1/orgs/{id}/settings
{ "risk_ceiling":"SENSITIVE","vision_policy":"allowlist","vision_allowlist":["com.acme.crm"],"memory_policy":"ask","retention_days":14 }
```

## C3. Authentication flow

1. App → IdP (Supabase Auth): email OTP / Google → access JWT (15 min) + refresh token (rotating, reuse-detected by the IdP).
2. App → `POST /v1/devices` (JWT) → `device_id`; optional Android Keystore ES256 key thumbprint stored; Play Integrity token (when distributed via Play) checked and stored as `attestation_level`.
3. Every API call and the WS handshake carry the JWT; the gateway re-validates on `session.start` and every 10 min (`session.refresh_auth` message).
4. Step-up (account deletion, export, billing changes, adding "always allow" for CONSEQUENTIAL): biometric/OTP re-auth within 5 min.
5. Revocation: device revoke → gateway drops live sessions for that `device_id`; org removal → membership cache invalidated (≤ 30 s) and WS sessions for that org closed.

## C4. Rate limits (initial)

Per user: 120 req/min REST, 6 concurrent WS sessions; per org: plan-based; per IP: 600 req/min; webhooks exempt but signature-verified. `429` with `Retry-After`.

## C5. Testing & acceptance (backend)

* Contract tests generated from OpenAPI (every route, every error code); Testcontainers Postgres for integration; **RLS suite**: for every tenant table, user A in org X cannot select/insert/update/delete rows of org Y — including via joins, views, and `SECURITY DEFINER` functions; fuzz with random org/user pairs.
* Load: 200 concurrent WS sessions with the mock provider, p95 session start ≤ 600 ms, no memory growth over 1 h.
* Security: ASVS L2 checklist (doc 10); dependency scanning; secrets scanning.
* **Acceptance:** all endpoints implemented per OpenAPI; RLS suite green; migrations reversible in staging; backup restore drill passed; 0 P1 findings in pre-launch pentest.
