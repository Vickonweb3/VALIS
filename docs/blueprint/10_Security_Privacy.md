# 10 — Security & Privacy Specification

Decisions D08, D09, D13, D24, D25, D30. Verification baseline: OWASP ASVS L2 (backend), OWASP MASVS-L2 (Android).

## 1. Trust boundaries (shown on VB-01/VB-11)

| Zone | Trusted? | Notes |
|---|---|---|
| User's device — VALIS app process | trusted for UX, **not** for authorisation | A rooted/instrumented device can lie; server limits enforce regardless |
| Other apps/screen content/notifications | **untrusted data** | Anything read from the screen, notifications or plugins can contain injection |
| Model output | **untrusted proposals** | Never executes directly; passes the broker |
| Realtime Gateway / API | trusted, authenticated | RLS-enforced |
| Inference service | trusted but isolated | no internet egress except model assets; no DB access |
| Plugins (third-party) | **untrusted** | SSRF-guarded, scoped, signed |

## 2. Threat model (STRIDE-oriented highlights) and controls

| Threat | Control |
|---|---|
| **Prompt injection via screen/plugin/notification text triggers actions** | trust labels; system rule "content is data"; content-derived tool calls always confirm; PROHIBITED set; CONSEQUENTIAL requires **tap** on a device-rendered card; red-team suite in CI (≥ 100 injection fixtures) |
| Voice spoofing (TV/other speaker says "yes") | voice accepted only for SENSITIVE confirmations; CONSEQUENTIAL = tap/biometric |
| Model claims false success | structural verified-results path + claim guard (doc 06 §8) |
| Overlay clickjacking of VALIS's own confirmation card | card uses `FLAG_SECURE`-style protections where applicable; ignore touches when obscured (`FLAG_WINDOW_IS_OBSCURED` check on MotionEvent) for CONSEQUENTIAL buttons |
| Token theft | short-lived JWT; refresh rotation + reuse detection (IdP); tokens in Keystore-wrapped Tink AEAD; no tokens in logs; device revocation drops sessions |
| Cross-tenant data access | RLS + composite FKs + org-scoped storage keys + per-org DEK + fuzz tests (doc 08 §3) |
| Eavesdropping/MITM | TLS 1.3, HSTS; network security config forbids cleartext; optional certificate pinning with **two** pins (current + backup intermediate) and a remote kill-switch to avoid bricking |
| Malicious plugin | signed manifests, scope enforcement, SSRF guard, output validation, rate limits, circuit breaker, no credential access beyond the call |
| Screenshot/audio leakage | not stored by default; redaction; denylist; ephemeral gateway memory; no content in logs |
| Data exfiltration through memory | sensitive categories not auto-stored; user review; org policy `memory_policy=off` |
| Abuse/cost attacks (inference cost) | per-user/org limits, concurrency caps, session max length, bot detection at signup, Play Integrity on registration (when distributed via Play) |
| Supply chain | lockfiles, Dependabot/Renovate, `gradle dependency-verification`, SBOM (CycloneDX) per release, signed releases, least-privilege CI tokens |
| Insider/support access | audited `support` role, time-boxed, break-glass with reason; no standing prod DB access |
| Android: exported components | all components `exported=false` except launcher activity; intent-filter inputs validated; `PendingIntent` immutable |
| Accessibility service abuse | declared minimal capabilities; refuses password fields/denylisted packages; rate-limited; only acts on broker-approved calls |

## 3. Authentication & session security

Covered in doc 07 C3. Additional: refresh/IdP session lifetimes configurable per org (shorter for Enterprise); optional passkeys when the IdP supports them; step-up for sensitive account actions; org-enforced MFA flag (v2).

## 4. Data classification & handling

| Class | Examples | At rest | In logs | Retention default |
|---|---|---|---|---|
| **Secret** | tokens, API keys, plugin secrets, KEKs | KMS/envelope; Keystore on device | never | rotated |
| **Content** | audio, screenshots, transcripts, memory text, tool args free text | field-level encrypted when stored; audio/frames **not stored** | never | audio/frames: none; transcripts: off by default; memory: until user deletes |
| **Personal** | email, display name, device model | encrypted disk | ID-only | account lifetime |
| **Operational** | usage counters, latencies, status codes | disk | yes | 13 months |
| **Audit** | membership/policy/billing events | append-only | n/a | ≥ 12 months |

## 5. Privacy by design — user-facing controls (map to the Privacy screen, doc 14)

* **What leaves the device** is explained and visible: wake word = never; voice turn = audio to your VALIS server; vision = one redacted frame per request; actions = metadata only.
* Toggles: wake listening; listen with screen off; vision (+ denylist, auto-look); history on/off; memory mode (cloud/local-only/off) and per-item review; analytics (opt-in, content-free); org-managed overrides are displayed as *"Managed by Acme"* with the reason.
* **Rights:** export (JSON, includes memory, activity metadata, settings), delete account (14-day grace then crypto-erase), delete conversation/memory at any time, revoke devices. Handle data-subject requests within 30 days; maintain a record of processing and sub-processors list (hosting, IdP, payment, GPU provider).
* **Minors:** the product is suitable for younger users in tone, but **account creation requires the age threshold of the user's jurisdiction or a verified guardian flow** — legal review required before launch; child accounts: no memory of sensitive categories, no actions above SAFE, no vision, no plugins, history off. (Flagged as a pre-launch legal item, not solved here.)
* **Consent records** (`consent_records`) for each permission/feature with version and timestamp; re-prompt on material change.
* **Region/regulation:** single region at launch (`data_region` reserved). GDPR/NDPR/CCPA-style obligations: lawful basis (contract/consent), DPIA before launch (voice + screen + memory is high-risk processing), privacy policy and in-app disclosures matching actual behaviour. This document is an engineering plan, not legal advice — obtain counsel review.

## 6. Android store/policy exposure (Risk R5)

| Capability | Policy exposure | Plan |
|---|---|---|
| `SYSTEM_ALERT_WINDOW` overlay | allowed with clear purpose; Android 15 FGS rule | prominent disclosure; visible persistent notification |
| `AccessibilityService` | Play restricts to accessibility use or tightly-justified core functionality with prominent disclosure and declaration form; broad "AI agent" automation is high-scrutiny | minimal capability flags, declaration + in-app disclosure; **sideload/enterprise channel** remains available if review blocks; features degrade to Intent-only actions without it |
| `MediaProjection` | allowed with user consent and visible indicators | session-scoped, never background-persistent |
| `RECORD_AUDIO` in background FGS | allowed with FGS type + disclosure | wake-word only on-device; disclosure of mic use |
| `SEND_SMS` / `CALL_PHONE` | heavily restricted (default handler) | **not used in v1** (compose/dial intents only) |
| `QUERY_ALL_PACKAGES`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` | restricted | not requested by default |
Distribution decision (D25): ship a sideloadable APK channel (GitHub Releases/Org MDM) from M7 and pursue Play in parallel; both must pass the same security checklist.

## 7. Secure SDLC

Threat-model review per milestone; code review (CODEOWNERS for `services/api/migrations`, `core/actions`, `core/vision`); SAST (CodeQL), secrets scanning, dependency audit in CI; fuzzing for the WS protocol parser and manifest validator; pre-launch third-party pentest (backend + Android) and fix of all High/Critical; incident response runbook (detect → contain → notify within legal windows → postmortem); key rotation runbook; backup/restore drills quarterly.

## 8. Testing & acceptance

* Red-team suites: injection (screen/plugin/notification), voice spoofing, overlay tap-jacking, malformed WS frames, oversized payloads, SSRF, token replay, IDOR across orgs/devices/memory/files.
* MASVS-L2 checklist pass on the Android app; ASVS-L2 on the API.
* **Acceptance:** all High/Critical findings closed; no secrets in repo history (scan); logs sampled over 24 h contain no content; privacy screen claims verified against traffic captures (what leaves the device matches the UI); export/delete verified end-to-end with proof of erasure (including embeddings and backups' expiry window documented).
