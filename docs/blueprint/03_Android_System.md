# 03 — Android System Specification (overlay, services, permissions, compatibility)

Visual: **VB-07** floating overlay architecture. Builds on the repo's `CharacterOverlayService`, `MainActivity`, and manifest. API-behaviour statements marked **(verify)** must be re-checked against the current Android docs for the target SDK during Spike S1/S2; they are written from platform knowledge, not from device testing in this blueprint.

## 1. Services and their foreground types (D05)

| Service | FGS type | Starts when | Stops when | Notification |
|---|---|---|---|---|
| `OverlayService` | `specialUse` (subtype "User-visible floating character companion", already in the repo manifest) | user enables VALIS from visible UI / quick tile / notification action | user stops VALIS | persistent, low importance: *Summon · Mute mic · Stop* |
| `VoiceService` | `microphone` | user arms listening **from a visible UI moment** (activity, tile, notification action) | user disarms, or screen-off policy | shares the persistent notification (one channel, two roles) |
| `CaptureService` | `mediaProjection` | only after the system consent dialog result, per session | session expires (idle 10 min default) or user stops | separate notification: "VALIS can see your screen — Stop" |

`PresenceCoordinator` (singleton, process-scoped) owns the state of all three and exposes a single `PresenceState` flow to UI and character. The services contain no business logic beyond lifecycle and OS integration.

Manifest additions over the current scaffold: `FOREGROUND_SERVICE_MICROPHONE`, `FOREGROUND_SERVICE_MEDIA_PROJECTION`, `VIBRATE`, `<queries>` for launcher intents (package visibility, API 30+), `android:foregroundServiceType` per service, a Quick Settings `TileService`, `BIND_NOTIFICATION_LISTENER_SERVICE` (optional, user-enabled), `PACKAGE_USAGE_STATS` (special access; optional). Avoid `QUERY_ALL_PACKAGES` (Play-restricted).

## 2. Overlay architecture

**Window:** one `TYPE_APPLICATION_OVERLAY` window (API 26+), `PixelFormat.TRANSLUCENT`, flags `FLAG_NOT_FOCUSABLE | FLAG_NOT_TOUCH_MODAL | FLAG_LAYOUT_NO_LIMITS | FLAG_HARDWARE_ACCELERATED`, gravity `TOP|START` with absolute `x,y` (the repo uses `TOP|END`; switch to `START` for simpler maths). The window is a **tight box around the character** (rest bounds + 12% headroom reserve above, 6% margins), default 200 × 270 dp × scale preset. Content = Filament surface (doc 02) + a thin `View` layer for the chips below.

**Why small, not full-screen:** a full-screen translucent GL surface costs fill-rate every frame and blocks touches everywhere. Movement across the screen = repositioning this window (`updateViewLayout`, throttled to the display's vsync, interpolated by a spring on the main thread).

**Chips layer** (drawn *outside* the GL surface, native views, so text is crisp and accessible): caption bubble (what VALIS is saying, optional), confirmation card (doc 06 §6), listening indicator (level bars), small status icon (muted mic / vision active). Chips are *additional overlay windows* only when they would not fit inside the character window (confirmation card); otherwise they are children of the character window growing the box (see "Resizing" below). Confirmation cards are always **device-rendered** (never from model text).

**Resizing:** the window may grow (chips) or shrink (tucked/sleeping badge, ≈ 72 dp). Resizes are batched with the position update; surface resize debounced 80 ms. Growth direction is chosen away from the nearest screen edge.

**Known touch cost:** transparent corners of the window still swallow touches (Android routes by window bounds). The tight box keeps this small. A "click-through when idle" option would require `FLAG_NOT_TOUCHABLE` *and* window alpha ≤ the system's maximum obscuring opacity (default 0.8 on Android 12+, **verify**) so touches can reach the app below; we default it **off** because it dims the character.

## 3. Overlay lifecycle

```
NOT_ATTACHED ──enable──▶ ATTACHING ──surface+asset ready──▶ VISIBLE ◀─────────────┐
                                                           │  ▲                    │
                                            tuck/sleep ────▼  │ untuck/wake        │ unlock / secure-clear
                                                         TUCKED                    │
                                  keyguard / secure window / screen off ──▶ SUPPRESSED
                                  disable / revoke permission ──▶ DETACHED
```
* **Permission revoked** while attached → `WindowManager` throws on update; catch `BadTokenException/SecurityException`, detach, post a re-grant notification, state → DETACHED.
* **Configuration change** (rotation, fold, density, locale) → recompute safe area, re-anchor to the same *logical* corner, re-layout, keep animation running.
* **Process death** → `START_STICKY` re-creates `OverlayService` (overlay needs no special start privilege once permission is held *(verify Android 15 rule below)*); `VoiceService` is **not** auto-restarted into the mic from the background (see §9) — the notification offers *Re-arm*.

## 4. Summoning

Triggers: wake word (VoiceService) · tap on the persistent notification action · Quick Settings tile · launcher shortcut · optional hardware-button chord is **not** offered (not reliably available to third-party apps). Summon sequence: `Summoned` event → anchor selection (§5) → window attach at the chosen anchor with the character scaled 0.85→1.0 and fading in over 250 ms (the animation `dialogue.summon` plays inside) → open turn if triggered by voice. Dismiss: say "bye VALIS"/tap-hold menu/notification action → scale-out 250 ms → detach window → `DORMANT` (wake-word stays armed if enabled).

## 5. Dynamic positioning (not stuck in one corner)

Candidate anchors: four corners + two vertical-edge mid points; each inset by the **safe area** and a gesture margin.

**Safe area:** `WindowMetrics.windowInsets` types `systemBars | displayCutout | systemGestures` (API 30+; API 26–29 fallback: display metrics + resource-derived bar heights), IME inset when visible, and fold/hinge bounds via Jetpack WindowManager (`FoldingFeature`) on foldables. Keep ≥ 24 dp above the bottom gesture zone.

**Score** for anchor *a* (higher is better), initial weights:
`S(a) = 0.45·free(a) + 0.25·prefer(a) + 0.10·stability(a) − 0.10·travel(a) − 0.10·imeConflict(a)`

* `free(a)`: fraction of the candidate rect *not* covered by content. Source, best available: (1) **Accessibility node bounds** (if the service is enabled: text/clickable density in the rect), (2) **last captured frame** edge/text density (if a vision session is active), (3) otherwise 0.5 (unknown).
* `prefer(a)`: remembered corner for the foreground package (opt-in per-app memory), default bottom-right for right-handed layout, mirrored by a user "handedness" setting.
* `stability(a)`: hysteresis — bonus for the current anchor so VALIS does not hop on every screen change.
* `travel(a)`: normalised distance from the current position; `imeConflict`: 1 if bottom anchors and the keyboard is visible.
Re-evaluation: on summon, on foreground-package change (if observable), on IME show/hide, on rotation/fold, and never more than once per 8 s. If the user drags, their drop position becomes the preferred anchor for that app for 24 h.

## 6. Dragging, snapping, touch interaction

| Gesture | Behaviour |
|---|---|
| Touch down | `UserTouched(zone)` (head / body / ears) — character reacts (doc 04) |
| Drag (slop 8 dp) | window follows finger; character leans (L6); drag disabled while a confirmation card is open |
| Release | fling velocity → projected position (`pos + v·0.15 s`) → nearest anchor; spring snap (damping ≈ 0.8, ≈ 280 ms) |
| Drop within 24 dp of a side edge | **tuck**: 60% of the body slides off-screen (peeking); tap to untuck |
| Tap | toggle push-to-talk (fallback when wake word unavailable or off) |
| Double-tap | sleep ↔ wake |
| Long-press | radial mini-menu: Mute, Look at screen, Sleep, Dismiss (native chips, ≥ 48 dp targets) |
| Two-finger / pinch on character | not supported (conflicts with underlying app gestures) |

All touch handling happens on the main thread and posts `CharacterEvent`s; hit-testing uses the window bounds (no per-pixel alpha hit test is available).

## 7. Visibility rules and what overlays cannot do

Be explicit with users and in marketing:

* **Not shown over:** the lock screen, secure/`FLAG_SECURE` windows where the app opts to hide overlays, some system permission/consent dialogs, and some OEM system UI (the system hides overlays to prevent tap-jacking).
* **Notification shade and system dialogs** draw above overlays.
* **Android 12+ untrusted-touch rules** limit touches passing through overlays; our window is always touchable except in the optional click-through mode (§2).
* **Android 12+** apps can request that overlays be hidden (`setHideOverlayWindows` for apps holding that permission) — banking/password apps may do so; VALIS must tolerate being hidden without error.
* Screenshots by the user include the character; **MediaProjection captures include it too** → we mask it (doc 05 §8).
* Different behaviour per OEM (Samsung/Xiaomi/Oppo/Vivo/Huawei) around autostart, battery managers, and overlay permission UIs: the onboarding includes OEM-specific guidance links, and a *health check* screen detects the common failure (service killed) and explains the fix.

## 8. Permissions (progressive, just-in-time)

| Permission / access | Needed for | When asked | If denied |
|---|---|---|---|
| `SYSTEM_ALERT_WINDOW` (special; `ACTION_MANAGE_OVERLAY_PERMISSION`) | the character | first enable | app explains; no character |
| `POST_NOTIFICATIONS` (13+) | foreground notifications | with first enable | FGS still shows (system manages) but no actions; prompt again later |
| `RECORD_AUDIO` | wake word, voice | when the user turns on voice | character works via tap/text chips only |
| Screen capture (MediaProjection consent, per session) | vision | when VALIS first needs to look, or "Look at screen" | VALIS explains it can't see; keeps chatting |
| Accessibility service (special settings page) | context + UI actions | when the first action requiring it is requested | those actions unavailable; intents-only actions still work |
| Notification listener (special) | notification reactions/reading | when user enables "notification awareness" | feature off |
| Usage access (special) | foreground app / device-usage analysis | when user enables those features | feature off |
| Runtime: `CALL_PHONE`, `READ_CONTACTS`, `SEND_SMS`(avoid; see doc 06), storage/media (scoped) | specific tools | at first use of that tool | tool returns `permission_denied`, VALIS explains |
| Battery-optimisation exemption (`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`) | OEM-resilient background | never forced; offered in health check | rely on FGS |

Every request shows a VALIS-designed explainer first (purpose, what leaves the device, how to revoke), then the system dialog. The **Permissions Center** (doc 14) shows the true current state of each, with deep links to the right system settings page.

## 9. Background behaviour and the microphone (Risk R3)

* **Microphone from the background is restricted.** An FGS of type `microphone` generally cannot be *started* while the app is in the background; it must start from a visible/user-initiated moment (**verify** against the target API docs). Once running it continues in the background.
* **Boot:** do not plan to arm the mic at boot — Android 14/15 restrict starting several FGS types (including microphone) from `BOOT_COMPLETED` (**verify**). After reboot or process death, show a notification "VALIS is asleep — tap to wake" (tap = a user-initiated start).
* **Android 15 overlay rule:** apps holding `SYSTEM_ALERT_WINDOW` can no longer start an FGS from the background just by holding the permission; a *visible* overlay window is required (**verify**). Design consequence: keep the overlay (even tucked) attached while VALIS is "on"; use `DORMANT` = overlay detached *only* when the user dismisses VALIS.
* **Privacy indicators:** from Android 12 the system shows the mic indicator and a privacy toggle; the user can cut mic access system-wide. `AudioRecord` can also be silenced by the system if another app holds capture priority (calls). Detect "all-zero" audio for > 2 s → state `MIC_UNAVAILABLE`, show the muted-mic icon, do not retry-spam.
* **Screen off:** default **stop listening when the screen turns off** (battery + privacy); setting "Listen with screen off" is opt-in with an explicit warning.
* **Doze/App Standby:** foreground services are exempt from standard Doze restrictions while running; do not use alarms/WorkManager for anything that must happen in real time.

## 10. Battery optimisation

* Wake word: 16 kHz mono, 80 ms frames, INT8 models, ONNX Runtime with 1 thread pinned to little cores where the OS allows; VAD gate means the wake model runs only when speech-like energy is present.
* Render: adaptive fps (doc 02 §2.3), `PAUSED` when fully static and tucked/sleeping.
* Network: the realtime socket is opened **per turn/session**, not held open idle (idle keep-alive only during the 4 s follow-up window and active sessions).
* Spontaneous animations suppressed on battery saver (doc 04 §5.2).
* Measure: 1-hour soak for (a) wake word armed + idle character, (b) 10 conversations/hour, (c) vision session open. Targets in doc 01 §5; revise from M2 measurements.

## 11. Android version compatibility (minSdk 26 → current)

| API | Relevant behaviour | Handling |
|---|---|---|
| 26–28 | `TYPE_APPLICATION_OVERLAY`, notification channels; no `WindowMetrics`; no scoped storage | display-metrics safe-area fallback; legacy storage not used |
| 29 | background activity start limits; scoped storage | tools use SAF/MediaStore |
| 30 | `WindowMetrics`, package visibility, `takeScreenshot` for accessibility | `<queries>`; `WindowMetrics` path |
| 31–32 | background FGS start restrictions; untrusted touches; approximate-location etc.; mic/camera indicators | FGS start only from visible moments; touch rules |
| 33 | `POST_NOTIFICATIONS`; per-app language | request permission with first enable |
| 34 | mandatory FGS types + type permissions; MediaProjection per-session consent / single `VirtualDisplay` per projection; partial screen share | declare types; one projection token per capture session; handle app-window capture choice |
| 35 | FGS timeout for some types (not `specialUse`/`microphone` as of writing — **verify**); overlay+FGS-start rule; status-bar chip for projection | keep overlay visible; surface projection indicator in our UI |
| 36 | Play target requirement (2026 cycle); predictive back, adaptive layouts | bump `targetSdk` (D29) and run the compatibility test matrix |

Test matrix (minimum): API 26/28 (oldest supported), 30, 33, 34, 35, 36; one foldable; three GPU families; stock Android + at least two OEM skins.

## 12. Foreground notification & settings integration

Persistent notification: title "VALIS is on"; actions **Summon** / **Mute mic** / **Stop**; content text reflects state (listening armed, vision active, muted). Channels: `valis_presence` (low), `valis_capture` (low, vision), `valis_alerts` (default; permission-lost, re-arm). Quick Settings tile: toggle VALIS. App shortcuts: "Summon VALIS", "Look at screen".

## 13. Error handling

| Case | Behaviour |
|---|---|
| Overlay permission lost | detach, notify, `ERROR` reaction on next visible chance |
| `ForegroundServiceStartNotAllowedException` | do not retry loop; post "tap to start" notification |
| `SecurityException` on capture | end vision session, explain |
| Mic unavailable | muted-mic state + explain; offer tap-to-type chips |
| Service killed by OEM | health-check card + deep link; no silent failure |
| WindowManager `BadTokenException` | detach and re-attach once; otherwise DETACHED |

## 14. Testing & acceptance

* **Instrumented:** attach/detach × 100; drag/fling/snap/tuck; rotation/fold; permission revoke while attached; keyguard transitions; secure-window overlay behaviour; process kill → restore path; notification actions; tile.
* **Manual matrix** per §11; videos stored per release.
* **Acceptance:** (1) overlay appears within 400 ms of summon on the reference device; (2) 0 leaks/crashes over 100 attach cycles; (3) every restriction in §7/§9 is surfaced to the user in plain words, never as a silent failure; (4) anchor selection never places the character under the IME or in the gesture zone across the test apps; (5) permission revoke handled without crash on every API in the matrix.
