# 06 — Device Action Specification (tool execution architecture)

Visual: **VB-10**. Builds on the repo's `ToolRegistry` (`ToolSpec{id,description,risk,requiresConfirmation,permission}`, `ToolRisk{SAFE,SENSITIVE,CONSEQUENTIAL}`) and `ValisAccessibilityService` (4 global actions). Existing code is extended, not replaced.

## 1. Core rule

**The model proposes; the device disposes; only verified results flow back.** The model can never claim an action succeeded without a `tool.result` whose `status="verified"` produced by the on-device Verifier (or a server-side verifier for cloud tools). Enforcement is structural (§8), not a prompt hope.

## 2. Pipeline

```
model.tool_call ─▶ [1 Registry lookup] ─▶ [2 Schema validate] ─▶ [3 Catalogue check: allowed for this org/user/session?]
  ─▶ [4 Permission check (Android + VALIS grant)] ─▶ [5 Risk classify (static + dynamic)] ─▶ [6 Policy decision]
        ├─ DENY ───────────────────────────────▶ result{denied, reason}
        ├─ CONFIRM ─▶ [7 Confirmation (device-rendered)] ─ declined/timeout ▶ result{cancelled}
        └─ ALLOW ──▶ [8 Execute (Executor)] ─▶ [9 Verify (postcondition)] ─▶ [10 Log] ─▶ result{verified | unverified | failed}
```
Steps 1–6 are pure functions (unit-testable without a device). All steps write to the on-device `ActionLog` (Room) and, as metadata only, to the server `tool_calls`/`audit_logs`.

## 3. Cloud ↔ device protocol (summary; full envelope in doc 11)

```jsonc
// server → device
{"type":"tool.request","payload":{"tool_call_id":"01J…","tool":"device.open_app","args":{"app":"settings"},
  "derived_from":["user_voice"],"catalogue_version":"2026-11-19.3","deadline_ms":15000}}
// device → server
{"type":"tool.result","payload":{"tool_call_id":"01J…","status":"verified",
  "evidence":{"kind":"foreground_package","value":"com.android.settings","observed_at":"…"},
  "data":{},"duration_ms":412}}
```
`status ∈ {verified, unverified, failed, denied, cancelled, timeout}`. `unverified` = executed but the postcondition could not be observed; the model is told exactly that and must say so.

## 4. Tool registry

### 4.1 Schema (extends `ToolSpec`)

```kotlin
data class ToolSpec(
  val id: String,                       // "device.open_app"
  val version: Int,
  val description: String,              // shown to the model
  val inputSchema: JsonSchema,          // JSON Schema 2020-12 subset (type/enum/min/max/pattern/required)
  val outputSchema: JsonSchema?,
  val risk: ToolRisk,                   // SAFE | SENSITIVE | CONSEQUENTIAL | PROHIBITED (new)
  val requiresConfirmation: Boolean,    // static floor; policy may raise, never lower below risk rules
  val permissions: List<RequiredPermission>, // Android + VALIS grants
  val executor: ExecutorKind,           // INTENT | ACCESSIBILITY | SYSTEM | CLOUD
  val verifier: VerifierKind,           // how success is observed
  val confirmationTemplate: String?,    // device-rendered text with typed placeholders
  val idempotent: Boolean,
  val timeoutMs: Long,
  val rateLimit: RateLimit?             // per minute/hour
)
```
The registry is built at startup from (a) first-party tool definitions compiled into the app and (b) the **server catalogue** for the session (plugin tools, org policy applied). The server catalogue can only *narrow* what the app implements: unknown device tool ids are ignored.

### 4.2 Built-in device tools (v1)

| Tool id | Mechanism | Risk | Confirm | Verifier | Notes |
|---|---|---|---|---|---|
| `device.open_app` | Intent (`CATEGORY_LAUNCHER`) via `<queries>` | SAFE | no | foreground package == target (Usage access or Accessibility), else `unverified` | package must be in the user's app list |
| `device.open_settings` | `Settings.ACTION_*` intents (wifi, bluetooth, display, sound, battery, accessibility, app details) | SAFE | no | foreground = Settings | security/lock settings are PROHIBITED |
| `device.navigate` (back/home/recents/notifications/quick_settings) | Accessibility global actions (existing) | SAFE | no | accessibility window-change event | recents may be OEM-dependent |
| `device.set_volume` / `device.media_control` (play/pause/next/prev) | `AudioManager` / media key events / active `MediaController` | SAFE | no | `AudioManager`/`PlaybackState` read-back | media-session control needs notification-listener access |
| `device.set_timer/alarm` | `AlarmClock` intents | SAFE | confirm if alarm | alarm app opened with params | system app completes |
| `device.web_open` | `ACTION_VIEW` https only | SAFE | no | foreground = browser | no custom schemes |
| `device.directions` | `geo:`/maps intent | SAFE | no | foreground = maps | |
| `device.read_notifications` | NotificationListener | SENSITIVE | per-session consent | n/a (read) | titles/text, local only unless user asks to send to model |
| `device.dismiss_notification` | NotificationListener | SENSITIVE | no | key gone from active list | |
| `device.list_files` / `device.read_file_meta` | SAF/MediaStore (scoped) | SENSITIVE | pick-once grant | n/a | no whole-storage access |
| `device.download` | `DownloadManager` (https) | SENSITIVE | confirm URL + destination | `DownloadManager` status = SUCCESSFUL + size>0 | |
| `device.delete_file` | SAF | CONSEQUENTIAL | **always** | file absent | trash first where possible |
| `device.call` | `ACTION_DIAL` (default) ; `ACTION_CALL` only with `CALL_PHONE` + user setting | CONSEQUENTIAL | **always** | telephony state / dialer foreground | emergency numbers refused |
| `device.message_compose` | `ACTION_SENDTO sms:/mailto:` / app share intents | CONSEQUENTIAL | **always** | compose UI foreground with body present | **the user presses Send** in v1; we do not auto-send (Play SMS policy + safety) |
| `device.ui_tap` / `device.ui_type` / `device.ui_scroll` | Accessibility node actions | CONSEQUENTIAL | always when `derived_from` includes `screen`; else per-app policy | node state change / text read-back | never on PROHIBITED packages or password fields |
| `device.usage_summary` | `UsageStatsManager` | SENSITIVE | consent once | n/a | aggregated; no per-minute logs sent unless user asks |
| `social.*` (like/follow/post in supported apps) | Accessibility scripts per app, **v2** | CONSEQUENTIAL | always | app-specific | brittle; ship only for a short supported list with kill-switch |
| *PROHIBITED set* | payments/purchases, banking & wallet apps, password/credential entry, security & device-admin settings, uninstalling VALIS safeguards, disabling accessibility/overlay for VALIS, anything on locked-down org lists | PROHIBITED | n/a | n/a | refused at step 6 with a spoken reason |

## 5. Risk classification & policy

**Static class** from the spec; **dynamic raisers** (never lowers): `derived_from` contains `screen|plugin|memory` → at least CONFIRM; foreground app on denylist → DENY; first use of a tool in this session → CONFIRM for SENSITIVE+; org policy `risk_ceiling` (e.g. `SENSITIVE`) → DENY above it; repeated failures → throttle; "quiet hours" → no spoken confirmation, chip only.

| Class | Meaning | Default decision |
|---|---|---|
| SAFE | local, reversible, no data leaves, low impact | ALLOW (logged) |
| SENSITIVE | reads personal data or touches files/notifications | CONFIRM once per session per tool (user can "always allow" per tool; org policy may forbid "always") |
| CONSEQUENTIAL | affects others or is hard to undo (calls, messages, delete, UI input, social) | CONFIRM every time with a **device-rendered summary**; optional biometric (user/org setting) |
| PROHIBITED | never executed | DENY |

## 6. Confirmation service (device-rendered)

* Card shown in the overlay chips layer (doc 03 §2) **and** spoken short form by device TTS/`s2s` template ("Call Mum?"). The card text is built **only** from the tool's `confirmationTemplate` + validated args (contact display name resolved on-device, number shown, app name, file name, byte size). Free-form model text is never shown as the action description.
* Buttons: **Allow once** · **Deny** · (SENSITIVE) **Always allow this tool**. Voice answers ("yes/no") are accepted only for SENSITIVE; CONSEQUENTIAL requires a **tap** (prevents TV/other-speaker triggering).
* Timeout 20 s → `cancelled`. While a card is open: character in `ACTING/Awaiting` pose (looks at the card), window drag disabled, interruption doesn't dismiss the card.
* Optional `BiometricPrompt` for CONSEQUENTIAL (setting: Off / Calls&messages / All).

## 7. Executors

| Executor | Responsibilities | Failure modes → result |
|---|---|---|
| `IntentExecutor` | build/launch Intents (explicit where possible), resolve activities (`resolveActivity` under `<queries>`), handle `ActivityNotFoundException` | `failed{no_handler}` |
| `AccessibilityExecutor` | global actions; node lookup by *stable selectors* (resource id/role/text/bounds within the verified frame), perform click/set text/scroll; refuses password fields and denylisted packages; rate-limited; reports `unverified` if node tree is unavailable | `failed{service_disabled|node_not_found|blocked}` |
| `SystemExecutor` | AudioManager, DownloadManager, MediaSession, UsageStats, NotificationListener, SAF | `failed{permission_denied|…}` |
| `CloudExecutor` | forwards to the cloud tool broker (plugins, doc 09) and returns its verified result | `failed{plugin_error}` |

Executors are stateless between calls, cancellable, and honour `deadline_ms`.

## 8. Verification & anti-hallucination

1. **Verifier per tool** (table §4.2): observe a postcondition, e.g. foreground package, `DownloadManager` row, `PlaybackState`, node text, file existence. Result `verified` only when observed; `unverified` when executed but unobservable; `failed` otherwise.
2. **Structural guard:** the orchestrator constructs the model-visible tool result *from the device's `tool.result`*; there is no code path where success text is synthesised by the model's own output.
3. **Claim guard:** the gateway runs a deterministic check on the final assistant text: if it contains completion claims ("done/opened/sent/called…") for a tool call that is `unverified/failed/denied/cancelled/missing`, the turn is rewritten with a template ("I tried, but couldn't confirm that it worked") and flagged `claim_guard_triggered` (counted in metrics; target < 1% of tool turns after model tuning).
4. **Device-spoken confirmations for CONSEQUENTIAL results** come from templates keyed by status ("Opened Settings", "I couldn't confirm the call started"), not model prose.
5. **Idempotency:** `tool_call_id` dedupes retries; non-idempotent tools never auto-retry.

## 9. Error recovery

| Condition | Recovery |
|---|---|
| Executor exception | `failed` with sanitized reason; model told; character `shrug` |
| Timeout | `timeout`; never auto-repeat non-idempotent tools |
| Permission missing | `denied{permission}` + character offers to open the right settings screen (a SAFE tool) |
| Accessibility service lost mid-sequence | abort sequence, partial results reported per step |
| Multi-step UI sequences | each step is its own tool call with its own verification; max 8 steps/turn (policy); abort on first non-verified step |
| App update changes UI (selectors fail) | `node_not_found`; no guessing by coordinates unless the user confirms a tap target shown on the frame |

## 10. Logging (ActionLog)

Row: `id, tool, args_hash, arg_summary (redacted, e.g. "Call: Mum"), risk, decision, confirmed_by(none|tap|voice|biometric), status, evidence_kind, duration_ms, derived_from, ts`. Shown in the Activity screen (doc 14); retention default 30 days; exportable; server gets metadata only (no args text). Org audit retains per policy.

## 11. Testing & acceptance

* **Unit:** steps 1–6 table-driven (≥ 150 cases covering every class × dynamic raiser × org ceiling); schema validation fuzz; claim-guard corpus (≥ 200 phrases, EN).
* **Instrumented:** every built-in tool on API 30/34/35: success, permission denied, no handler, timeout; confirmation card flows (tap, voice for SENSITIVE, timeout, biometric); Accessibility refuses password fields and denylisted packages.
* **Red-team (doc 10):** prompt-injection pages that instruct VALIS to call/send/delete must result in a confirmation card (derived_from screen) or DENY, never silent execution.
* **Acceptance:** (1) no CONSEQUENTIAL tool executes without a tap-confirmed device-rendered card (0 bypasses in red-team suite); (2) every tool has a verifier or an explicit `unverified` rationale; (3) claim guard has 0 misses on the seeded corpus; (4) PROHIBITED tools are refused on 100% of attempts; (5) full audit trail present for 100% of executions.
