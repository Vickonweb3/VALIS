-- 001_init: schema, forced row-level security on every tenant table.
-- NOT YET RUN against a live Postgres 16 (no database was available when written).
-- Run it on a scratch database and fix any errors before relying on it.
create extension if not exists pgcrypto;
create extension if not exists citext;
create extension if not exists vector;

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


-- Row-level security: every table that carries org_id is isolated by app.org_id.
do $$
declare t record;
begin
  for t in
    select c.table_name
    from information_schema.columns c
    join information_schema.tables tb on tb.table_schema = c.table_schema and tb.table_name = c.table_name
    where c.table_schema = 'public' and c.column_name = 'org_id' and tb.table_type = 'BASE TABLE'
  loop
    execute format('alter table %I enable row level security', t.table_name);
    execute format('alter table %I force row level security', t.table_name);
    execute format($p$create policy tenant_isolation on %I
      using (org_id = nullif(current_setting('app.org_id', true), '')::uuid)
      with check (org_id = nullif(current_setting('app.org_id', true), '')::uuid)$p$, t.table_name);
  end loop;
end $$;

alter table organizations enable row level security;
alter table organizations force row level security;
create policy tenant_isolation on organizations
  using (id = nullif(current_setting('app.org_id', true), '')::uuid);

-- user-scope memory rows additionally require the owner
create policy user_scope on memory_items as restrictive
  using (scope = 'org' or user_id = nullif(current_setting('app.user_id', true), '')::uuid);
