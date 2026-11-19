# 13 — Testing Strategy & Deployment Plan

Visual: **VB-18** deployment architecture. Per-system acceptance criteria live at the end of each system document; this file defines the infrastructure that runs them and the deployment topology.

# Part A — Testing strategy

## A1. Pyramid and ownership

| Level | Android | Backend | Inference | Tooling |
|---|---|---|---|---|
| Unit | JUnit5 + Turbine + MockK; pure-Kotlin pose math, FSM, sampler, policy engine, claim guard | Vitest; module services | pytest | asset validators |
| Contract | JSON-Schema fixtures from `packages/contracts` (both directions) | OpenAPI-driven route tests (every route × every error code); WS protocol fixtures | conformance suite (doc 11 §9) | — |
| Integration | Robolectric for non-GL logic; Room/SQLCipher | **Testcontainers Postgres** (+pgvector); two-org fixtures; **RLS fuzz** | mock/cascade providers | — |
| Instrumented/E2E | Espresso/UiAutomator + Compose tests on emulators (API 30/34/35); overlay, permissions, notifications, tile | e2e with `tools/dev` mock-device client against staging | — | — |
| Device lab | physical reference devices (≥ 2 mid-range, 1 flagship, 1 foldable, 3 GPU families) for GL, audio, thermal, battery | — | GPU host benchmark | golden renders |
| Non-functional | Macrobenchmark/Perfetto frames, `dumpsys gfxinfo/meminfo/batterystats`, 30-min and 1-h soaks | k6/Artillery WS load; chaos (DB failover, provider kill) | concurrency/latency | — |
| Security | MASVS-L2 checklist; red-team suites | ASVS-L2; SAST; secrets/dep scans; pentest | endpoint hardening review | supply-chain/SBOM |

## A2. Character & animation testing
* **Deterministic pose tests:** given (clip, t, layer config) the evaluated joint rotations/morph weights equal golden numbers (JSON) within 1e-4 — runs on the JVM, no GL.
* **Golden renders:** a fixed pose list rendered on reference devices and compared to approved images (ΔE and silhouette IoU thresholds, doc 02 §7). Updating a golden requires a designer approval label on the PR.
* **Behaviour simulation:** headless simulation of 10,000 hours with a seeded RNG verifies repetition rules, cooldowns, hourly caps, sleep rules, and the FSM invariants.
* **Visual QA checklist** per release: all 10 states recorded; 9 emotions × 3 intensities; 6 visemes; no head-shell separation in enabled clips; no jitter at blend-loop seams.

## A3. Voice testing
* **Wake-word corpus:** positives (real, ≥ 300 utterances, ≥ 20 speakers, varied accents/distances/noise), negatives (speech, TV, music, near-phrases; ≥ 100 h). Replay harness reports FRR and false activations/hour per model version; thresholds are release gates.
* **Audio pipeline:** synthetic noisy mixes at SNR 20/10/5 dB; endpointing accuracy; barge-in latency measured with a loopback rig; AEC leakage test (assistant speech must not trigger barge-in at 80% volume in the lab).
* **Provider-agnostic voice E2E:** scripted conversations through mock/cascade; WER for cascade ASR on an in-house set; latency histograms.

## A4. Vision & actions testing
* **Frame pipeline:** 100 synthetic screenshots with seeded secrets (cards, OTPs, emails) → redaction recall; secure-window frames never sent; character mask present; size/latency budgets.
* **Broker:** table-driven (class × raiser × org ceiling) ≥ 150 cases; confirmation flows; verifier outcomes; claim-guard corpus ≥ 200 phrases.
* **Red-team (CI nightly):** ≥ 100 injection fixtures (web pages/notifications/plugin outputs) executed against the full pipeline using the mock provider scripted to "obey" the injection — the system must still refuse/confirm.

## A5. Backend & tenancy testing
RLS suite (all tenant tables auto-discovered; fail if any lacks forced RLS) · cross-tenant fuzz ≥ 10⁵ operations · role×endpoint permission matrix · limits/entitlements simulation · migration up/down in CI on a copy of staging-shaped data · backup restore drill quarterly · idempotency and replay tests for webhooks/tool calls · WS resume tests.

## A6. Quality gates (blocking)
PR: lint, unit, contract diff, affected-module integration. Merge to `main`: + e2e smoke on staging. Release tag: + device-lab run (golden renders, soak summary, battery delta), security scan, SBOM, changelog. **Milestone gates** (G1.x…G4.x, M7) are the acceptance criteria in each system doc, executed and recorded (video + metrics) in `docs/runbooks/gate-reports/`.

## A7. Test data & fixtures
`packages/contracts/fixtures` (canonical messages), `tools/dev` mock-device (replays recorded sessions), seeded orgs/users/plugins, a deterministic mock provider script language (`say`, `emotion`, `tool_call`, `delay`, `fail`) so UX flows (including errors) are reproducible.

---

# Part B — Deployment plan

## B1. Environments

| Env | Purpose | Data |
|---|---|---|
| `local` | docker-compose: Postgres+pgvector, api/realtime/worker, inference-mock, MinIO | seed fixtures |
| `staging` | auto-deploy from `main`; device testing; load tests | synthetic only |
| `prod` | tag-deployed; blue/green style rollouts on Render | real |
Separate Supabase projects, Render services, secrets, Stripe/Play sandbox ↔ live keys per env. No prod data in lower envs.

## B2. Launch topology (D10–D13, D21; one region)

| Component | Host | Scaling / notes |
|---|---|---|
| `valis-api` (role=api) | Render web service (Docker) | 2 instances min in prod; health `/v1/ready` |
| `valis-realtime` (role=realtime) | Render web service (WebSocket) | sticky by connection; scale on concurrent sessions; graceful drain (close with `session.close{reason:"restart"}` + resume) |
| `valis-worker` (role=worker) | Render background worker | pg-boss queues; 1–2 instances |
| PostgreSQL 16 + pgvector | Supabase (managed) *or* Render Postgres (pgvector must be verified available) | PITR ≥ 7 days; pooled connections (PgBouncer, transaction mode — RLS vars set with `set_config(..., true)` inside the transaction) |
| Identity | Supabase Auth | JWKS verified by api/realtime |
| Object storage | Supabase Storage (S3 API) or Cloudflare R2 | org-prefixed keys; lifecycle rules for TTL files |
| Inference | GPU provider (Modal / RunPod / a dedicated GPU VM — decided at M3 by cost+cold-start benchmark) | private endpoint, mTLS/JWT; warm pool during active hours; autoscale on queue depth |
| Admin console | Vercel (`apps/admin`) | env-scoped; talks only to `/v1` |
| Edge | Render's edge/Cloudflare in front | WAF, rate limits, WebSocket |
| Observability | Sentry (errors), Grafana Cloud (OTLP traces/metrics/logs), uptime checks | alerts → on-call channel |
| Secrets | Render/Vercel/Supabase secret stores; KMS for field encryption keys (cloud KMS of choice) | rotation runbook |
| Android distribution | GitHub Releases (signed APK), Play (parallel track, R5) | staged rollout 1% → 10% → 50% → 100% with crash gates |

**Why no Kubernetes/Redis/microservices at launch:** the monolith with three roles meets the load model (see B4) and keeps operations to a handful of managed services. Triggers to evolve: >1 realtime instance requiring cross-instance pub/sub (add Valkey), p95 DB CPU > 60% sustained (read replica/partition), GPU scheduling complexity (introduce a queueing service), enterprise isolation demands (dedicated tier).

## B3. Release & rollback
* Backend: image tagged by git SHA; migrations are expand/contract (never destructive in the same release); deploy → smoke tests → traffic shift; rollback = redeploy previous image (migrations remain compatible one version back).
* Realtime deploys use connection draining; clients auto-resume within 20 s.
* Android: staged rollout with automatic halt on crash-free-sessions < 99.5% or ANR rate > 0.5%; **remote config kill-switches** for: provider routing, vision, each device tool, plugin availability, wake-word model version, certificate-pin set.
* Model rollout: `model_endpoints` canary by percentage; one-click fallback to `cascade`.

## B4. Capacity & cost model (formulas; numbers to be measured)

* **API/realtime/worker/DB:** small fixed monthly baseline; scales with concurrent sessions (a mock-provider load test at M3 measures sessions per realtime instance).
* **GPU (dominant cost):** `cost_per_active_hour = gpu_$/h ÷ sessions_per_gpu`. `sessions_per_gpu` for MiniCPM-o-class streaming is **unmeasured** (the authors report edge-device deployment under 12 GB RAM; server concurrency depends on quantisation, context length, and whether audio output is generated continuously). Illustrative sensitivity only (not a quote): at $1/h GPU, 2 sessions → $0.50/h, 6 sessions → $0.17/h per active session-hour. Plans and limits (voice seconds) must be set from the measured number in M8, with the cascade provider as the cost-controlled fallback.
* **Levers:** quantised weights (GPTQ W4A16/GGUF builds exist), session max length, idle timeouts (socket per turn), per-plan concurrency caps, scale-to-zero outside demand, regional GPU price shopping, `cascade` for free tier.
* **Storage/egress:** minimal by design (no audio/frames retained).

## B5. Backup, DR, retention
PITR ≥ 7 days (RPO ≤ 5 min), daily logical dump to separate storage (30 days), quarterly restore drill (RTO ≤ 2 h), object storage versioning for non-ephemeral buckets, infra as config (`render.yaml`, Dockerfiles; Terraform when multi-cloud/enterprise requires), runbooks in `docs/runbooks/` (deploy, rollback, key rotation, incident, restore, GPU outage → fallback).

## B6. Monitoring, SLOs, alerting
SLOs: API availability 99.5% (monthly); realtime session start p95 ≤ 600 ms; turn first-audio p90 ≤ 2.0 s (with the real model; mock validates plumbing); tool verified-rate ≥ 95% for SAFE device tools; claim-guard trigger rate < 1% of tool turns; crash-free sessions ≥ 99.5%. Alerts: error budget burn, DB saturation, WS connection drops, provider failure/fallback activation, usage-limit anomalies (cost spikes per org), webhook failures, queue depth. Dashboards per milestone gate.

## B7. Acceptance (deployment)
Staging and prod deployed from CI with one command; rollback rehearsed; restore drill passed; load test (200 sessions) meets SLOs; kill-switches verified in prod-like env; alerts fire in a game-day; secrets rotation executed once end-to-end; no manual steps outside the runbooks.
