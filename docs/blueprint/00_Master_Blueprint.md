# VALIS — Master Product Blueprint

**Revision:** R1 · **Date:** 2026-11-19 · **Status:** Implementation-ready plan (nothing in this package claims implemented code)
**Scope:** Current repo state → platform fully built, integrated, tested and waiting for the trained model.
**Out of scope:** Model training and the final model hookup (Milestone M8, separate).

---

## 0. What was inspected (facts, not assumptions)

| Input | What it actually contains |
|---|---|
| Repo `Vickonweb3/VALIS` (`main`, 11 commits) | Android scaffold only: `app/` module (Kotlin 2.0.21, AGP 8.7.3, compileSdk/targetSdk 35, minSdk 26, applicationId `ai.valis.companion`), a developer-shell `MainActivity`, a **placeholder** `CharacterOverlayService` (a purple "V" circle + drag, no renderer), contracts: `CharacterRenderer`, `CharacterStateMachine` (8 states), `ModelProvider`, `ToolRegistry` (3 risk levels), `VoiceController` (system SpeechRecognizer + TextToSpeech), `WakeWordEngine` (interface only), `ValisAccessibilityService` (4 global actions), `ScreenCaptureConsentActivity`, `LocalMemoryStore` (one DataStore string), Filament 1.56.0 declared. `.gitattributes` enables Git LFS for `.glb`. Docs: `ARCHITECTURE.md`, `INTEGRATION_CHECKLIST.md`, `VALIS_MODEL_PROFILE.md`. **No GLB, no Gradle wrapper, no backend, no tests, no CI.** |
| `VALIS_rigged.glb` (37.2 MiB) | glTF 2.0. 29 nodes, **27 skin joints**, 2 meshes, 2 materials, **48 animation clips @ 30 fps**, 26 face morph targets on `VALIS_body`, 6 viseme morph targets on `VALIS_mouth`. |
| `Blue_Futuristic_Mascot-…glb` (26.5 MiB) | The un-rigged source mesh (1 mesh, no skin, no animations). Kept as the archival source only. |
| `MiniCPM-o 4.5` (web-verified 2026-11) | Released Feb 2026 by OpenBMB; ~9B params (SigLip2 + Whisper-medium + CosyVoice2 + Qwen3-8B); streaming/full-duplex speech + vision; instruct and thinking modes; 40,960-token context; model card states Apache-2.0; GPTQ W4A16 and GGUF builds exist. **Not found documented:** a native tool-calling format. We therefore treat tool calling as *unverified* (see doc 11). Licence must be re-read from the exact weights used at integration time. |

### 0.1 Findings that change the plan (read these first)

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F1 | **The character is blue, near-black and white — not purple.** | Rendered from the real asset: cobalt ≈ `#1B55FF`, face ink ≈ `#0E0E19`, ear/shell pearl ≈ `#E3E4F1`; chest "V" emblem. | The asset is the source of truth (your rule). The UI palette is derived from the asset. The repo's purple placeholder (`#6A4DFF`) is retired. |
| F2 | **The GLB is ~10× too heavy for a phone overlay.** | `VALIS_body`: **286,174 vertices / 500,000 triangles**; 4096² albedo PNG (9.7 MiB) + 2048² normal (2.3 MiB); 37 MiB file. | A derived `VALIS_runtime.glb` is mandatory (doc 02 §3). The source GLB is never modified. This is Risk R1. |
| F3 | **26 morph targets sit on a 286k-vertex mesh.** Dense morph data ≈ 286k × 26 × 12 B ≈ **89 MB** before normals. | Accessor inspection. | Face must be split into its own primitive (≈10–14k verts) so morph cost is bounded (≈ <8 MB). |
| F4 | **Every one of the 48 clips keys all 29 nodes and the morph weights.** | All clips: 32 channels over `translation/rotation/scale/weights`. | Clips are full-body takes, not additive layers. Layering needs build-time *masks* and a custom runtime blender (doc 04). Filament's stock animator plays one clip at a time and cannot layer. |
| F5 | **All clips bake in leg sway, ear/tail float, blinks and eye-look weights.** | Legs (`upperLeg/lowerLeg/foot`) are "active" (>3°) in nearly every clip; `eyeBlink_*` peaks ≈1.0 in nearly every clip. | Without masking you get double blinks and dangling legs fighting each other. Weight channels are grouped (BLINK / GAZE / BROW / MOUTH / VISEME) and masked per layer. |
| F6 | **Only 14 of 48 clips loop cleanly** (end pose within 5° / 1 cm of start): `wave_left/right, yawn, peek, sit_swing_legs`, and all nine `expression_*`. `idle` (8 s) misses its loop point by ≈19°. | Per-clip loop-error analysis (`appendix/clip_inventory.csv`). | The runtime uses blend-looping (overlap crossfade) for non-seamless loops; the behaviour engine treats the rest as one-shots. |
| F7 | **Root/hips translation reaches 0.20 units (jump) on a ~1.0-unit-tall character; scale tracks deviate up to 0.13 (squash).** Non-root bone translation is 0. | Same analysis. | Root motion is applied inside the overlay viewport (20% headroom required), never to the window. Squash scale is retained; sub-0.02 scale noise is stripped at bake. |
| F8 | **The expression clips are face poses.** `expression_*` (3 s, loop-safe) drive brows, squint/wide, mouthSmile/Frown/Pucker and some visemes. `talk` drives all six visemes and `mouthWide/Pucker`. | Morph activity table. | Expressions are *sampled as face poses* (one time slice), not played as animations. Speech uses a real-time viseme driver, not the baked `talk` loop. |
| F9 | **Head shell visibly separates in `droop`, `bow` and `expression_shy`** (helmet lifts away from the face). | Rendered frames. | Asset QA item for the 3D TD (T-ASSET-04). Until fixed, those clips are low-priority in behaviour weights. |
| F10 | The mouth is a separate collapsed mesh (a single point at rest) opened only by viseme morphs; the resting smile is texture-baked. | Mesh bounds + render. | Speech needs the mouth mesh visible and driven. Rest face needs no morphs. |

---

## 1. Product vision (locked)

VALIS is a **living, character-first AI companion**. The character is the interface and physical presence of the intelligence. It floats over supported Android apps, appears on **"Yo, VALIS."**, moves and emotes autonomously, listens and speaks, understands *permitted* screen content, performs *authorised* phone actions, and remembers only what the user lets it remember. The companion app UI is a control centre, built last.

Design direction: premium, modern, minimal, distinctive, friendly-but-intelligent, all ages; solid colours, deliberate hierarchy; no generic AI-dashboard look, no gradients/neon/glassmorphism.

### 1.1 Non-negotiable principles

1. **Character first.** Every system ends in something the character visibly does.
2. **Model proposes, device disposes.** The model never touches the device. Every action passes schema validation → permission → risk policy → (confirmation) → execution → **verification**. The model only ever sees *verified* results.
3. **Vision ≠ control.** Seeing the screen never implies permission to act on it.
4. **Wake word ≠ main model.** A tiny separate on-device detector runs continuously; the multimodal model runs only after a wake/turn.
5. **User-owned memory.** Inspectable, editable, deletable, exportable. Local-only mode exists.
6. **Tenant isolation is foundational.** Every row carries `org_id`; Postgres RLS enforces it.
7. **Honest about Android.** No overlay over secure/system surfaces; background mic is restricted (doc 03 §9).
8. **Model-agnostic platform.** One provider interface; a mock provider ships so everything is testable before the real model exists.

---

## 2. Decision register (single source of truth — all documents defer to this)

| ID | Decision | Alternatives considered (why not) |
|---|---|---|
| D01 | **Renderer: Filament (gltfio)** in a small `SurfaceView` inside the overlay window; `TextureView` fallback if the Spike S1 alpha/z-order test fails. | SceneView (wrapper, little gain here); Unity-as-library (≈25+ MB, heavy); raw GLES (re-implements skinning/morphs/PBR); Godot embed (immature on overlays). Filament is already in the repo. |
| D02 | **Derived runtime asset** `VALIS_runtime.glb`: ≤45k tris, face split into its own primitive, normals baked from the hi-poly, textures ≤2048² KTX2/ETC2; source GLB frozen in Git LFS. | Shipping the 37 MiB asset (rejected: GPU/RAM/APK size). |
| D03 | **Custom pose runtime** over build-time-baked clip data (`valis_anim.v1`); Filament's `Animator` is *not* used for playback — only `TransformManager`, `setMorphWeights`, `updateBoneMatrices` (verified in Spike S1). | Filament Animator + `applyCrossFade` (no layering/masks). |
| D04 | **Behaviour: layered utility selector + 10-state FSM** (dormant, summoned, idle, listening, thinking, speaking, acting, interrupted, sleeping, error). | Pure behaviour tree (poor for spontaneity/cooldown scoring); ML-driven (unpredictable). |
| D05 | **Overlay: one small `TYPE_APPLICATION_OVERLAY` window**, repositioned by `updateViewLayout`. Three separate foreground services: `OverlayService` (specialUse), `VoiceService` (microphone), `CaptureService` (mediaProjection, only during consent). | One full-screen transparent window (fill-rate cost, touch-blocking). |
| D06 | **Wake word:** custom "Yo VALIS" model (openWakeWord-style, Apache-2.0 tooling) + Silero-VAD gate on **ONNX Runtime Mobile**. Fallback: Picovoice Porcupine (paid) only if M2 gate targets fail. | Porcupine first (per-device licensing cost); Vosk grammar KWS (heavier); always-on cloud (privacy/battery: rejected). |
| D07 | **Voice transport:** WSS to the Realtime Gateway; control = JSON, media = binary frames (Opus 16 kHz up, PCM16/Opus 24 kHz down). Barge-in is decided on-device. | WebRTC (best jitter/AEC but TURN + complexity; Phase-2 option); gRPC (poor Android/Cloudflare fit). |
| D08 | **Vision:** MediaProjection, session-scoped consent, on-demand frame grab, on-device redaction, self-mask of the character. | Accessibility `takeScreenshot` (kept as a documented alternative; Play-policy exposure). |
| D09 | **Actions:** `IntentExecutor`, `AccessibilityExecutor`, `SystemExecutor` behind one `ToolBroker`; risk classes `SAFE / SENSITIVE / CONSEQUENTIAL / PROHIBITED`; **device-rendered** confirmations; mandatory verification. | Model-written confirmation text (spoofable). |
| D10 | **Backend: TypeScript modular monolith (Fastify)**, one image, three process roles: `api`, `realtime`, `worker`. Inference is a separate Python service. | Microservices (premature); NestJS (more ceremony than value); Python-everywhere (weaker fit for your Node/Render workflow). |
| D11 | **PostgreSQL 16 + pgvector + RLS**, SQL-first migrations, Kysely typed queries. | ORM-owned schema (RLS and vector indexes need raw SQL anyway). |
| D12 | **Jobs on Postgres (pg-boss); no Redis at launch.** Add Valkey/Redis only when >1 realtime instance (pub/sub, shared rate limits). | Redis from day 1 (extra moving part). |
| D13 | **Identity: Supabase Auth** (OIDC JWT, email OTP, Google, TOTP; passkeys when available) behind an `IdentityPort`; authorisation (orgs/roles) is ours. | Clerk (fast, per-MAU cost, lock-in); Auth0/WorkOS (enterprise SSO later); self-built (security risk). |
| D14 | **Everything is a workspace.** Every user gets a personal workspace; companies are additional workspaces. All data is keyed by `org_id`. | Separate user vs. org data models (two code paths, leak risk). |
| D15 | **Plugins are HTTPS-hosted tool providers** with signed manifests + first-party built-ins (`device`, `memory`). No third-party code runs in our infra in v1. | In-process/WASM plugins (v2 option). |
| D16 | **`InferenceProvider` with capability negotiation**; providers: `mock`, `cascade` (ASR→LLM→TTS), `minicpm-o` (M8). | Hard-coding one model API. |
| D17 | **Realtime protocol v1** (doc 11 §4): versioned envelope, sequence numbers, explicit `interrupt`. | Ad-hoc messages. |
| D18 | **Billing: `BillingPort`**; Stripe for orgs/web, Google Play Billing for consumer Android if listed on Play. Confirm Stripe supports your legal entity's country; else Paystack / Paddle / Lemon Squeezy behind the same port. | Single provider hard-wired. |
| D19 | **Android UI: Jetpack Compose + custom design system (no stock Material look), Hilt, Room + SQLCipher, DataStore.** | XML views (slower to build the custom look). |
| D20 | **Monorepo via one `git mv` commit:** `app/` → `apps/android/app/` (history preserved). | Leave `app/` at root (collides with Node workspaces and root Gradle). |
| D21 | **CI: GitHub Actions**, path-filtered; produces debug APK artifacts (matches a Termux → GitHub → APK workflow). | Local-only builds (Gradle/AGP is impractical in Termux). |
| D22 | **Observability:** OpenTelemetry, Sentry (client+server), structured JSON logs, defined SLOs. | Vendor-specific agents. |
| D23 | **Memory:** cloud-synced (pgvector) *or* local-only (SQLCipher + FTS5); every item carries source, sensitivity, status. | Opaque model-side memory. |
| D24 | **Prompt-injection posture:** screen text and plugin output are *untrusted*; trust labels travel with context; content-derived tool calls always confirm. | Trusting model judgement alone. |
| D25 | **Distribution is dual-path (sideload APK / Google Play).** Play policy exposure on Accessibility, overlay and MediaProjection is a tracked risk (R5). | Assuming Play approval. |
| D26 | **Contracts first:** OpenAPI 3.1 + JSON Schema in `packages/contracts`, codegen to TS/Kotlin, contract tests both sides. | Hand-synced DTOs. |
| D27 | **Emotion/gesture hints are closed enums** (doc 04 §6) mapped to real clips; the model never names bones or clips. | Free-text animation commands. |
| D28 | **Admin console: Next.js on Vercel** (`apps/admin`), minimal in M5. | Building admin in the Android app. |
| D29 | **Android API levels:** minSdk 26 (repo). compileSdk/targetSdk: raise to the Play-required level (36 per the 2026 policy cycle — verify in M0). | Staying on 35. |
| D30 | **Analytics opt-in, content-free.** | Default-on telemetry. |

---

## 3. Deliverable map (your 20 deliverables → files)

| # | Deliverable | Where |
|---|---|---|
| 1 | Master product blueprint | this file |
| 2 | Technical architecture specification | `01_Technical_Architecture.md` |
| 3 | Character system specification | `02_Character_System.md` |
| 4 | Android system specification | `03_Android_System.md` |
| 5 | Animation and autonomy specification | `04_Animation_Autonomy.md` |
| 6 | Voice and vision specification | `05_Voice_Vision.md` |
| 7 | Device action specification | `06_Device_Actions.md` |
| 8, 9, 10 | Backend architecture · Database spec · API documentation | `07_Backend_Database_API.md` |
| 11 | Multi-company architecture | `08_Multi_Company.md` |
| 12 | Plugin framework specification | `09_Plugin_Framework.md` |
| 13 | Security and privacy specification | `10_Security_Privacy.md` |
| 14 | Model integration contract | `11_Model_Integration_Contract.md` |
| 15, 16 | Repository structure · Development roadmap | `12_Repository_Roadmap.md` |
| 17, 18 | Testing strategy · Deployment plan | `13_Testing_Deployment.md` |
| 19 | Visual blueprint collection (18 sheets) | `blueprint.html` (sheets VB-01…VB-18) |
| 20 | Final UI/UX design package | `14_UI_UX_Package.md` + `app.html` |
| — | Character-in-use mockups (real asset) | `experience.html` |
| — | Clip inventory (all 48 clips, measured) | `appendix/clip_inventory.csv` |

## 4. Risk register (top items)

| ID | Risk | Likelihood / Impact | Mitigation | Gate |
|---|---|---|---|---|
| R1 | Runtime asset cannot reach budget while keeping morphs/identity | M / H | Hi→lo normal bake; face split; TD sign-off against golden renders | M0 |
| R2 | Overlay transparency/z-order with Filament `SurfaceView` misbehaves on some OEMs | M / H | Spike S1 matrix; `TextureView` fallback | M1 G1.1 |
| R3 | Background mic limits (Android 14/15 FGS-type start rules) break "always listening" | H / H | Start `VoiceService` from a visible UI moment; "tap to re-arm" notification after process death; never promise boot-time arming | M2 G2.1 |
| R4 | Wake-word accuracy/battery targets missed with open tooling | M / M | Dataset + threshold tuning; Porcupine fallback | M2 G2.2 |
| R5 | Play policy rejects Accessibility/overlay/MediaProjection use | M / H | Prominent disclosure, minimal scopes, sideload channel, org-managed distribution | M7 |
| R6 | Model lacks reliable tool calling | M / M | Constrained-JSON tool channel + verifier; fine-tune target defined in doc 11 | M8 |
| R7 | GPU cost per concurrent session too high | M / H | Quantised build, session caps, cascade fallback, per-plan limits | M3 + M8 |
| R8 | Prompt injection via screen/plugin content triggers actions | M / H | D24 controls; red-team suite | M4, M7 |
| R9 | Stripe cannot onboard the legal entity | L–M / M | `BillingPort` + alternatives | M5 |

## 5. Definition of "ready for the trained model"

All of: (a) M0–M7 gates passed; (b) the **Model Conformance Suite** (doc 11 §9) passes against the mock provider *and* the cascade provider; (c) the gateway, orchestrator, tool broker, memory and usage metering run end-to-end using only the `InferenceProvider` interface; (d) the readiness checklist (doc 11 §10) is signed off. Swapping `mock` → `minicpm-o` must be a configuration change plus an adapter, not a rebuild.
