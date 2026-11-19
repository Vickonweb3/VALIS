# 12 — Repository Structure & Development Roadmap

Visual: **VB-17** roadmap. Decisions D20, D21, D26, D29.

# Part A — Repository

## A1. Migration policy ("do not discard working code")

The existing scaffold is kept. One dedicated commit does `git mv` only (history preserved), no code edits:

| From | To |
|---|---|
| `app/` | `apps/android/app/` |
| `build.gradle.kts`, `settings.gradle.kts`, `gradle.properties` | `apps/android/` |
| `docs/ARCHITECTURE.md`, `INTEGRATION_CHECKLIST.md`, `VALIS_MODEL_PROFILE.md` | stay in `docs/` (ARCHITECTURE.md gets a header pointing to the blueprint; MODEL_PROFILE.md gets the two confirmations: clips are full-rig; viseme/face morphs exist) |
| `app/src/main/assets/valis/README.md` | moves with `app/` |
Reason: a root-level Android project cannot coexist cleanly with Node workspaces, Python services and shared contracts. After the move, the existing contracts (`CharacterRenderer`, `ToolRegistry`, `ModelProvider`, `WakeWordEngine`, …) are **evolved in place**, not rewritten.

## A2. Final structure

```
VALIS/
├─ apps/
│  ├─ android/                      Gradle root (settings.gradle.kts, libs.versions.toml, gradlew)
│  │  ├─ app/                       shell: Application, Hilt graph, manifest, navigation host   (existing :app)
│  │  ├─ core/                      created when first needed (M1+), each a Gradle module:
│  │  │  ├─ character/              render/ (Filament), anim/ (PoseRuntime, clip data), behaviour/, state/
│  │  │  ├─ overlay/                OverlayService, window mgmt, anchors, chips, touch
│  │  │  ├─ voice/                  audio engine, wake word, VAD, turn manager, playback, viseme tap
│  │  │  ├─ vision/                 CaptureService, policy, redaction, frame pipeline
│  │  │  ├─ actions/                ToolBroker, registry, policy, confirmations, executors, verifiers, ActionLog
│  │  │  ├─ model/                  SessionClient (WSS), ModelGateway, protocol DTOs (generated)
│  │  │  ├─ data/                   Room+SQLCipher, DataStore, SecureStore, AuthClient, MemoryCache
│  │  │  ├─ design/                 tokens, theme, components (Compose)
│  │  │  └─ common/                 result types, logging, clock, dispatchers
│  │  ├─ feature/companion/         Compose screens (M6)
│  │  ├─ benchmark/                 Macrobenchmark + baseline profiles
│  │  └─ lab/                       developer-only "Character Lab" (debug variant)
│  └─ admin/                        Next.js admin console (M5)
├─ services/
│  ├─ api/                          TypeScript modular monolith (roles: api | realtime | worker)
│  │  ├─ src/modules/{identity,tenancy,memory,sessions,orchestrator,tools,plugins,files,billing,usage,audit,notifications,admin}/
│  │  ├─ src/platform/              config, db, otel, errors, crypto, rate-limit
│  │  ├─ migrations/                SQL-first (forward + down)
│  │  ├─ prompts/                   versioned policy/persona/org blocks
│  │  └─ test/                      unit, integration (Testcontainers), rls-fuzz, contract, load
│  └─ inference/                    Python: providers/{mock,cascade,minicpm_o}, server, conformance/
├─ packages/
│  └─ contracts/                    openapi.yaml · realtime/*.schema.json · tool & plugin-manifest schemas · generated/{ts,kotlin} · fixtures/
├─ tools/
│  ├─ asset-pipeline/               build_runtime_glb, bake_clips, golden_render, validate_rig (Node/TS + Blender scripts)
│  ├─ wakeword/                     data synthesis, training, evaluation harness, model export
│  └─ dev/                          mock-device client, session replayer, fixtures loader
├─ assets-src/                      (Git LFS) VALIS_rigged.glb (frozen source), Blue_Futuristic_Mascot.glb (archive), reference renders
├─ design/                          tokens.json, blueprint sheets, mockups, app screens (the visual package)
├─ docs/                            blueprint/ (00–14), ADRs/, runbooks/, appendix/ (clip_inventory.csv, …) + the 3 existing docs
├─ infra/                           render.yaml, Dockerfiles, env templates, runbooks, (terraform/ later)
├─ .github/                         workflows/, CODEOWNERS, PULL_REQUEST_TEMPLATE.md, dependabot.yml
└─ README.md · CONTRIBUTING.md · SECURITY.md · LICENSE (decide)
```

**LFS:** `.gitattributes` already tracks `.glb`; extend to `*.ktx2`, `*.onnx` (wake/VAD models), `*.bin` under `assets/`. The runtime assets live in `apps/android/app/src/main/assets/valis/` (LFS). **Never commit secrets**; `.env.example` only.

## A3. CI/CD (GitHub Actions, path-filtered)

| Workflow | Trigger paths | Jobs |
|---|---|---|
| `android.yml` | `apps/android/**`, `packages/contracts/**` | lint (ktlint/detekt), unit tests, `assembleDebug` → **APK artifact**, optional emulator tests (API 30/34) nightly |
| `api.yml` | `services/api/**`, `packages/contracts/**` | typecheck, lint, unit, Testcontainers integration, RLS fuzz, contract tests, build image |
| `inference.yml` | `services/inference/**` | ruff, pytest, conformance (mock/cascade) |
| `contracts.yml` | `packages/contracts/**` | validate OpenAPI/JSON Schemas, regenerate TS/Kotlin, fail on diff |
| `assets.yml` | `tools/asset-pipeline/**`, `assets-src/**` | validate rig names/counts, rebuild runtime GLB (when Blender available) or validate checked-in artefact hash |
| `security.yml` | all, weekly | CodeQL, dependency audit, secrets scan, SBOM |
| `release.yml` | tags | signed APK (secrets in Actions), changelog, deploy hooks |
Branching: trunk-based with short-lived feature branches and PRs; `main` always green; staging deploys from `main`, production from tags.

## A4. Technology summary (full table in doc 01 §6)
Kotlin/Compose/Filament/Hilt/Room+SQLCipher/OkHttp/ONNX Runtime Mobile · TypeScript/Fastify/Kysely/pg-boss/PostgreSQL+pgvector · Python/FastAPI (inference) · Next.js (admin) · GitHub Actions · Render + Supabase (Auth/Postgres/Storage) + GPU host (Modal/RunPod-class, chosen at M3) + Vercel (admin) · OpenTelemetry + Sentry.

---

# Part B — Execution roadmap (dependency-aware)

Effort is in **engineer-weeks (1 experienced full-time engineer)** and is an *estimate for planning*, not a commitment; the asset TD work is separate. Calendar time depends on team size; streams marked ∥ can run in parallel.

```
M0 Foundations ──▶ M1 Character in overlay ──▶ M2 Voice loop ──────────────┐
      │                                    ∥                                 ├─▶ M4 Vision & Actions ─▶ M6 Companion UI ─▶ M7 Hardening ─▶ [M8 model]
      └────────▶ M3 Cloud core ─────────────┘──▶ M5 Plugins·Orgs·Billing ───┘
```

| Milestone | Est. | Depends on | Parallel with |
|---|---|---|---|
| M0 Foundations & asset pipeline | 2 | — | — |
| **M1 Character in the Android overlay** | 4–5 | M0 | M3 |
| M2 Voice loop on device | 4 | M1 (reactions), M0 contracts | M3 |
| M3 Cloud platform core | 6 | M0 contracts | M1, M2 |
| M4 Vision & device actions | 5 | M2, M3 | M5 |
| M5 Plugins, organisations, billing | 5 | M3 | M4 |
| M6 Companion app UI | 5 | M3–M5 APIs; M1–M2 for live preview | — |
| M7 Hardening & model-readiness | 4 | all | — |
| **Total** | **≈ 35–36 eng-weeks** | critical path M0→M1→M2→M4→M6→M7 ≈ 24 wks | with 3 engineers ≈ 16–20 calendar weeks |

## M0 — Foundations & asset pipeline
* **Tasks:** (1) monorepo `git mv` commit + `gradle wrapper` + version catalog + bump SDK (D29) + CI workflows + CODEOWNERS · (2) `packages/contracts` skeleton: OpenAPI stub, realtime envelope + message schemas, tool/plugin manifest schemas, TS/Kotlin codegen · (3) **Asset pipeline:** T-ASSET-01..03 (decimate+bake, face split, KTX2/ETC2), T-BAKE (clip bake + `clip_overrides.json`), `validate_rig`, golden renders; T-ASSET-04 shell-separation fix requested from the TD · (4) **Spike S1** on one device with a crudely decimated asset: Filament in an overlay window — alpha, z-order, `SurfaceView` vs `TextureView`, `TransformManager` joint writes + `updateBoneMatrices`, morph weights, gltfio morph limits.
* **Deliverables:** green CI + APK artifact; `VALIS_runtime.glb`; `valis_anim.v1.*`; golden renders; S1 report (go/no-go for D01/D03).
* **Files/modules:** `tools/asset-pipeline/**`, `packages/contracts/**`, `.github/workflows/**`, `assets-src/**` (LFS).
* **Decisions:** D01/D02/D03 confirmed or amended by S1; D29 target SDK confirmed.
* **Visuals required:** none new (VB-01…18 exist); asset reference sheet.
* **Testing:** asset validators; bake unit tests; contracts diff gate.
* **Definition of done:** CI green; runtime asset within budget and TD-approved; S1 written up.
* **GitHub:** migration commit (alone), CI, contracts, pipeline, LFS assets — separate PRs.

## M1 — Character in the Android overlay (first major milestone)
Internal gates: **G1.1** rest-pose render in overlay (transparent, 30 fps) · **G1.2** `PoseRuntime`: clips, masks, blend-loops, expressions, visemes (driven from Lab) · **G1.3** `BehaviourEngine` + 10-state FSM + `CharacterEvent` API · **G1.4** overlay behaviours (anchors, drag, snap, tuck, chips) + perf/thermal/battery pass.
* **Tasks:** `core/character` (render, anim, behaviour, state) · `core/overlay` (window, anchors, touch, chips, notification, tile) · `apps/android/lab` Character Lab (trigger any state/emotion/viseme/gesture; FPS/GPU HUD; event fuzz) · replace the placeholder `CharacterOverlayService` UI (keep service skeleton) · unit + golden + instrumented tests.
* **Deliverables:** the real VALIS floating over other apps, autonomous, emoting, draggable; video of all 10 states; perf report.
* **Dependencies:** M0 artefacts.
* **Decisions:** blend-loop durations, procedural limits, anchor weights tuned visually (doc 02/03/04 defaults).
* **Visuals required:** VB-02…07 + `experience.html` (done); Character Lab UI is functional, not designed.
* **Testing:** doc 02 §7, doc 04 §10, doc 03 §14 (character/overlay subset).
* **DoD:** doc 02 §8 + doc 04 §10 + doc 03 §14 criteria 1–4 met on the reference devices; 30-min soak; 100 attach cycles clean.
* **GitHub:** one PR per gate; asset binaries via LFS.

## M2 — Voice loop on device
Gates: **G2.1** FGS/mic lifecycle on API 34/35 incl. re-arm (R3) · **G2.2** wake-word targets or Porcupine decision (R4) · **G2.3** barge-in ≤ 150 ms · **G2.4** battery measurement.
* **Tasks:** audio engine (capture, AEC/NS, ring buffer), Silero VAD, wake model training + evaluation (`tools/wakeword`), `WakeWordEngine` implementation, `VoiceService`, turn manager, Opus, `SessionClient` against a **local fake gateway** (in `tools/dev`) until M3 lands, playback + jitter + viseme tap, barge-in, local fallback (existing `VoiceController` as mode `local`), privacy controls, notification/tile actions.
* **Deliverables:** "Yo, VALIS" summons the character and holds a (mock) conversation with speech animation and interruption.
* **Dependencies:** M1; M0 contracts. **Testing/DoD:** doc 05 §A11.
* **GitHub:** `tools/wakeword`, `core/voice`, model assets (LFS).

## M3 — Cloud platform core (∥)
* **Tasks:** `services/api` scaffold (Fastify, config, pino, OTel, error model) · migrations (doc 07 core DDL) + RLS helper + **RLS fuzz harness first** · identity (JWKS verify, device registration) · tenancy (orgs, memberships, roles) · realtime gateway (protocol v1) · orchestrator + `InferenceProvider` + Python **`mock`** and **`cascade`** providers (cascade ASR/LLM/TTS components chosen by a latency/cost bench; licences verified) · memory service (pgvector + FTS + proposals) · sessions/turns · usage events + limits · audit · notifications (minimal) · deploy staging+prod on Render, Supabase project, secrets, backups/PITR · conformance suite v1 · Android `AuthClient`, real `SessionClient`, `MemoryCache`.
* **Deliverables:** deployed API + realtime + worker; device ↔ cloud ↔ mock/cascade turn works end-to-end; contract tests and RLS fuzz green.
* **Testing/DoD:** doc 07 C5; a recorded session replays from fixtures.
* **GitHub:** `services/api`, `services/inference`, `infra/render.yaml`, migrations (CODEOWNERS-protected).

## M4 — Vision & device actions
Gates: **G4.1** vision session lifecycle on API 34/35 · **G4.2** broker unit+instrumented · **G4.3** red-team v1 (zero unconfirmed consequential calls).
* **Tasks:** `core/vision` (CaptureService, VisionPolicy, frame pipeline, ML Kit redaction, denylist, self-mask, secure-frame detection) · `core/actions` (registry extension, schema validation, policy engine, confirmation service + overlay card, executors, verifiers, ActionLog) · v1 device tools (doc 06 §4.2) · cloud tool relay + catalogue endpoint + claim guard · injection fixtures v1.
* **Deliverables:** "Look at this post. What do you think?" works with the mock/cascade provider using a real screen frame; verified and failed actions both demonstrated end-to-end.
* **DoD:** doc 05 §B9 and doc 06 §11.

## M5 — Plugins, organisations, billing (∥ with M4)
* **Tasks:** plugin registry/install/auth/invoke + manifest tooling + mock CRM fixture · org invites/roles/settings/audit · `apps/admin` (Vercel) · billing (`BillingPort`, plans/entitlements/usage rollups, Stripe sandbox + webhooks, Play verification stub if listing on Play) · FCM + email notifications · limit enforcement UX in-character.
* **DoD:** doc 08 §10 + doc 09 §9; billing sandbox end-to-end (subscribe → entitlement → limit → downgrade).

## M6 — Companion application UI
* **Tasks:** `core/design` (tokens, components) · navigation · all screens in doc 14 (Welcome/onboarding, Home, Permissions Center, Character, Voice, Memory, Services & plugins, Activity, Privacy, Security, Plan & billing, Organisation & workspace switcher) · in-app disclosures · accessibility (TalkBack, 200% font scale, contrast) · localisation scaffold · live character preview on Home.
* **DoD:** every screen implemented against `app.html` designs; the five user journeys (doc 14 §5) walked by ≥ 5 testers; a11y checks pass.

## M7 — Hardening & model-integration readiness
* **Tasks:** third-party pentest + fixes · perf/battery/thermal matrix · load test (200 WS sessions) · DR/restore drill · RLS fuzz at 10⁵ ops · store/compliance packaging (Data safety, accessibility declaration, privacy policy, DPIA) · sideload release channel · closed beta · conformance suite final · model readiness checklist (doc 11 §10) · cost model validation.
* **DoD:** doc 00 §5 satisfied; no open High/Critical findings; readiness checklist signed.

## M8 (separate milestone — not part of this plan)
Model fine-tuning (tool format, honesty behaviours, persona, voice), serving stack selection (vLLM/transformers/llama.cpp) with GPU benchmarks, adapter `providers/minicpm_o`, conformance run, canary rollout.

## First 10 working days (concrete start)
Day 1–2: migration commit, wrapper, CI, SDK bump. Day 2–4: contracts skeleton + codegen. Day 3–8: asset pipeline with the TD (decimation/bake/face split are the long pole; start immediately). Day 6–10: Spike S1 on a physical device. Parallel from day 5: M3 scaffold (API, DB, RLS fuzz) if a second engineer exists.

## Risks to the schedule
R1 asset budget (TD time) · R3/R4 mic + wake-word gates · Play policy (R5, affects distribution, not engineering) · GPU access/cost (M8) · scope creep in plugin ecosystem (hold to the three first-party plugins until M7 is done).
