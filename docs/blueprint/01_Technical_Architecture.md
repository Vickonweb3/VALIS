# 01 — Technical Architecture Specification

Defers to decisions D01–D30 in `00_Master_Blueprint.md`. Visual: **VB-01** (master), **VB-11** (backend), **VB-18** (deployment).

## 1. System decomposition

Three deployables plus tooling, one monorepo (doc 12):

| Deployable | Tech | Responsibility |
|---|---|---|
| **VALIS Android** (`apps/android`) | Kotlin, Filament, Compose | Character, overlay, voice I/O, vision capture, device actions, local memory cache, companion UI |
| **VALIS Cloud** (`services/api`) | TypeScript/Fastify, Postgres | Identity mapping, tenancy, memory, sessions/realtime gateway, tool broker (cloud side), plugins, usage, billing, audit, admin API |
| **VALIS Inference** (`services/inference`) | Python | `InferenceProvider` implementations: `mock`, `cascade`, later `minicpm-o`. Never reachable from the internet; only from the gateway |
| **Admin Console** (`apps/admin`) | Next.js | Org administration (members, policies, plugins, usage, audit) |
| **Tooling** (`tools/`) | Node/Python | Asset pipeline (runtime GLB, clip bake), wake-word training, contract codegen |

## 2. On-device component model

```
presentation   CompanionUI (Compose)            OverlayHost (Window + SurfaceView)
                     │                                   │
presence       PresenceCoordinator ── owns lifecycle of ─┤
                     │      OverlayService · VoiceService · CaptureService
character      CharacterRuntime
                 ├─ Renderer (Filament)        ├─ PoseRuntime (layers, masks, blend)
                 ├─ BehaviourEngine (utility)  └─ CharacterStateMachine
intelligence   SessionClient (WSS) ── ModelGateway (client of the Realtime Gateway)
                 ├─ AudioPipeline (capture → AEC/NS → VAD → Opus)   └─ PlaybackPipeline (jitter buffer → AudioTrack → viseme tap)
                 └─ VisionPipeline (capture → redact → mask → encode)
control        ToolBroker ── Registry · PolicyEngine · ConfirmationService · Executors · Verifier · ActionLog
data           MemoryCache (Room+SQLCipher) · Settings (DataStore) · SecureStore (Keystore/Tink) · AuthClient
```

Rules: (1) UI never calls executors; it talks to `PresenceCoordinator`/`ToolBroker`. (2) `CharacterRuntime` has **no** dependency on network, voice, or tools; it consumes a small event stream (`CharacterEvent`). (3) Everything crosses module boundaries as immutable data classes defined in `packages/contracts` where it also crosses the network.

### 2.1 `CharacterEvent` (the only way the world reaches the character)

`Summoned`, `Dismissed`, `UserTouched(zone)`, `ListeningStarted/Stopped`, `UserSpeechLevel(rms)`, `Thinking(started)`, `SpeechStarted(visemeSource)`, `SpeechLevel(rms)`, `SpeechEnded`, `Interrupted(by)`, `ActionStarted(kind)`, `ActionFinished(status)`, `EmotionHint(label,intensity)`, `GestureHint(name)`, `Error(kind)`, `Environment(kind)` (charging, low-battery, rotation, quiet-hours), `SleepRequested`, `WakeRequested`.

## 3. Inter-system communication (summary matrix)

| From → To | Channel | Contract |
|---|---|---|
| WakeWord → PresenceCoordinator | in-process callback | `WakeDetected(confidence, ts)` |
| Presence → Character | `CharacterEvent` flow | §2.1 |
| Audio/Vision/Text → Cloud | WSS `/v1/realtime` (+ HTTPS upload for large frames) | doc 11 §4 |
| Cloud → ToolBroker (device) | WSS `tool.request` | doc 06 §3 |
| ToolBroker → Executors | Kotlin interface `ToolExecutor` | doc 06 §4 |
| Gateway → Orchestrator | in-process | `Turn` |
| Orchestrator → Inference | internal WSS/HTTP (mTLS or signed JWT) | `InferenceRequest/Event` (doc 11) |
| Orchestrator → Memory | in-process module API | `MemoryQuery`, `MemoryProposal` |
| Orchestrator → Plugins | HTTPS `POST /invoke` (signed) | doc 09 |
| API → Postgres | pooled TLS, RLS session vars | doc 07 |
| Companion UI → API | HTTPS REST `/v1/*` | OpenAPI |

## 4. End-to-end reference flow: "Yo, VALIS. Look at this post. What do you think?"

1. `VoiceService` mic ring buffer → wake model + VAD gate (on-device only). Score ≥ threshold → `WakeDetected`.
2. `PresenceCoordinator`: ensure overlay (D05), emit `Summoned` → character plays summon (doc 04 §7), picks a corner (doc 03 §5), opens a *turn*.
3. Session established (or reused): `session.start` → `session.ready{capabilities, limits}`.
4. User speech streams as Opus frames; client VAD marks `speech_start/end`; character in **LISTENING** (head tilt, gaze to user).
5. The utterance + "this post" triggers the model to request vision: `vision.request` (or the client attaches a frame if the session policy is `auto-attach-on-deictic`; default is **ask first** → character says/shows "Look at your screen?" chip). Consent state is checked: MediaProjection session granted? foreground app on denylist?
6. `CaptureService` grabs one frame → redaction → character-mask → resize/encode → `vision.frame` (≤ policy bytes).
7. Orchestrator builds `InferenceRequest` (history, memory snippets, trust-labelled frame, tool catalogue filtered by org policy + user grants) → provider.
8. Provider streams `text.delta`, `audio.chunk`, `emotion`, optional `tool.call`. Gateway forwards to device. Character: **THINKING** until first audio, then **SPEAKING** with live visemes.
9. If a tool call arrives, `ToolBroker` runs the pipeline (doc 06) → `tool.result{verified}` back; orchestrator feeds the verified result to the model; only then may the response claim completion.
10. Turn ends; usage events recorded; memory proposals evaluated (doc 07 §5); character returns to IDLE.

## 5. Non-functional requirements (targets; measured at gates)

| Area | Target | Measured how |
|---|---|---|
| Wake → character visible | ≤ 400 ms p50, ≤ 700 ms p95 | instrumented trace |
| End of user speech → first audio (cloud, omni) | ≤ 1.2 s p50, ≤ 2.0 s p90 *(to be validated with the real model; mock provider validates plumbing only)* | gateway trace |
| Barge-in: user speech → local audio stopped | ≤ 150 ms | on-device trace |
| Render | 30 fps while active; ≤ 15 fps idle; 0 fps when fully static & tucked | Perfetto/`gfxinfo` |
| Frame budget (mid-range reference device) | CPU ≤ 8% average idle; GPU memory ≤ 80 MB; RSS for character ≤ 150 MB | Macrobenchmark + `dumpsys` |
| Wake-word | FRR ≤ 10%, ≤ 1 false activation per 10 h in quiet-home corpus | replay harness (doc 13) |
| Battery (wake-word armed, screen on, idle character) | measured in 1 h soak; target ≤ 4%/h on the mid-range reference device *(initial target; revise after M2 measurement)* | `batterystats` |
| API availability | 99.5% monthly at launch (single region) | uptime SLO |
| Realtime session start | ≤ 600 ms p95 (warm) | gateway metrics |
| Data durability | PITR ≥ 7 days; RPO ≤ 5 min; RTO ≤ 2 h | restore drill |
| Security | ASVS L2 (doc 10); zero cross-tenant reads in RLS fuzz | CI + pre-launch pentest |

## 6. Technology stack (final)

| Layer | Choice | Why |
|---|---|---|
| Android language/build | Kotlin 2.0.21, AGP 8.7.3 (repo) → bump with D29, Gradle KTS, version catalog | Already in repo |
| Render | Filament 1.56.0 + gltfio (repo) | D01 |
| Async | Kotlin coroutines + Flow | Event-driven pipelines |
| DI | Hilt (KSP) | Standard; test seams |
| Local data | Room + SQLCipher; DataStore (Proto) for settings; Keystore-wrapped Tink AEAD for tokens | D19 |
| ML on device | ONNX Runtime Mobile (wake word, VAD), ML Kit on-device text recognition (redaction) | One runtime for audio models |
| Network | OkHttp (HTTP + WebSocket), Retrofit + kotlinx.serialization | Repo already has OkHttp |
| Audio codec | libopus (NDK) | Low-bitrate speech |
| Backend | Node 22 LTS, TypeScript, Fastify, TypeBox/Zod, Kysely, pg-boss, pino, OpenTelemetry | D10–D12 |
| DB | PostgreSQL 16 (+pgvector, pgcrypto), RLS | D11 |
| Inference | Python 3.11, FastAPI/uvicorn, vLLM or transformers (decided at M8 after benchmarks) | D16 |
| Admin | Next.js (App Router), Tailwind | D28 |
| CI/CD | GitHub Actions; Render deploy hooks; Vercel for admin | D21 |
| Errors/metrics | Sentry; OTLP → Grafana Cloud (free tier acceptable at launch) | D22 |

## 7. Cross-cutting conventions

* **IDs:** UUIDv7 everywhere (time-ordered). **Time:** UTC ISO-8601 on the wire. **Money:** integer minor units + ISO currency.
* **Errors:** RFC 9457 `application/problem+json` with stable `code` (doc 07 §8). On-device, a sealed `ValisError` hierarchy mapped 1:1 to `CharacterEvent.Error(kind)`.
* **Idempotency:** `Idempotency-Key` on mutating POSTs; `tool_call_id` is the idempotency key for tool execution.
* **Versioning:** REST `/v1`; realtime protocol `v` field; plugin manifest semver; model `provider_version` + `model_id` recorded on every turn.
* **Feature flags:** server-driven `capabilities` and `limits` in `session.ready`; client flags via signed config; every flag has an owner and expiry.
* **Logging policy:** never log audio, frames, transcripts, memory text or tool arguments' free text; log IDs, sizes, durations, status codes.
