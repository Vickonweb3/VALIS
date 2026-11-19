# 14 — Final UI/UX Design Package (companion app)

Visual: **VB-16** navigation & screens, full-fidelity screens in `app.html`, in-use overlay states in `experience.html`. The companion app is a **control centre**, not a chat dashboard: the character is the interface; this app configures, explains and audits it. Built last (M6). Palette is derived from the real asset (F1).

## 1. Design language — "VALIS Console"

**Principles:** character-first (the character appears on Home, Welcome, Character and Voice screens, rendered from the real asset); calm and legible; explain every permission in plain words; show truth (real states, real data flows); solid colours only; generous whitespace; **no overlap, ever** (every element has its own row/cell; layouts verified at 360–412 dp widths and 200% font scale).

**Tokens** (`design/tokens.json`, mirrored in `core/design`):

| Token | Value | Use |
|---|---|---|
| `cobalt` | `#1B55FF` | primary actions, presence dot, active tab, links |
| `cobalt-700` / `cobalt-100` | `#123BB8` / `#E3EAFF` | pressed / tinted fills |
| `ink` | `#0E0E19` | primary text, dark surfaces (hero cards, overlay chips) |
| `ink-700` / `ink-500` / `ink-400` | `#2B2D45` / `#5A5D7A` / `#8A8DA6` | secondary text, icons, hints |
| `pearl-50` | `#F6F6FB` | app background |
| `pearl-100` / `pearl-200` | `#ECEDF6` / `#E3E4F1` | cards on pearl-50 / dividers & fills |
| `white` | `#FFFFFF` | elevated cards |
| `signal-amber` | `#C77700` on `#FFF1D6` | needs attention / permission / unverified |
| `signal-red` | `#C62F2F` on `#FFE3E3` | error / prohibited / destructive |
| `signal-green` | `#12805C` on `#DDF5EA` | verified / healthy |
Contrast: text on pearl/white ≥ 7:1 (ink), secondary ≥ 4.5:1; amber/red/green label colours are the *dark* variants above.
**Type:** DM Sans (UI), tabular numerals for metrics. Scale 12 / 14 / 16 / 20 / 28 / 40; weights 400/500/700; line-height 1.35–1.5.
**Shape & space:** 4-pt grid; screen padding 20; card radius 20; control radius 14; pills 999; min touch 48 dp.
**Signature elements:** the **presence dot** (cobalt; pulses only when VALIS is actively listening/speaking, otherwise static) used consistently for live state; **pebble icons** (circular tinted containers) for rows; a **hero disc** (solid ink circle) that the character sits in on Welcome/Home/Voice.
**Motion:** 150–250 ms ease-out; no parallax; reduced-motion respected (static presence dot).
**Not used:** gradients, glows/neon, glassmorphism, stock Material elevations, generic purple "AI" styling.

## 2. Navigation structure

```
Onboarding (first run only): Welcome → Overlay access → Microphone → Meet VALIS (test summon) → Done
Main (bottom bar, 4 tabs; workspace chip + avatar in every top bar)
├─ Home            presence preview · quick toggles · today · recent activity
├─ Memory          mode · pending approvals · items · forget
├─ Activity        timeline of conversations & actions (verified/unverified/failed/declined) → detail sheet
└─ Control         hub list
    ├─ Permissions Center
    ├─ Character        (size · autonomy · sleep · quiet hours · position)
    ├─ Voice            (wake phrase · sensitivity · voice · interruption)
    ├─ Services & plugins
    ├─ Privacy          (what leaves your phone · vision · history · blocked apps · data rights)
    ├─ Security         (devices · confirmations · always-allow · sign-in)
    ├─ Plan & billing
    └─ Workspace        (switcher · members · roles · managed policies)  — admin tools open the web Admin Console
Overlay-native surfaces (not in the app): confirmation card, caption bubble, mini-menu, health-check chip
```
Deep links: `valis://permissions`, `valis://memory/pending`, `valis://activity/{id}`, `valis://workspace/{id}`. Back-stack: tabs keep state; Control sub-pages are a stack.

## 3. Screen specifications (each has its own composition — see `app.html`)

| # | Screen | Job | Key content & behaviour |
|---|---|---|---|
| 1 | **Welcome** | Introduce VALIS; start setup | Hero disc with the real character; one sentence promise; primary "Set up VALIS"; secondary "How VALIS handles your data" |
| 2 | **Home** | Presence at a glance | Hero card: live character render + state line ("Listening for “Yo, VALIS”"); three quick controls (Summon / Sleep / Mic); *Today* tiles (conversations, verified actions, voice minutes); 3 latest activity rows; health banner if something is broken (service killed, permission lost) |
| 3 | **Permissions Center** | Truthful state of every access | Summary "5 of 6 ready"; rows: Overlay, Microphone, Notifications, Screen sight (per-session), Accessibility, Notification access, Usage access — each: state pill, one-line why, what it unlocks, deep link; Accessibility has an expandable disclosure (what it can/can't do); revoked permissions flagged amber |
| 4 | **Character** | Tune presence | Live preview with state chips (Idle · Listening · Thinking · Speaking); Size S/M/L; Autonomy slider (Calm ↔ Balanced ↔ Playful); Sleep after (1 / 3 / 10 min / Never); Quiet hours; Handedness; "Remember my position per app" |
| 5 | **Voice** | Wake phrase & speech | Wake-phrase card ("Yo, VALIS") with sensitivity slider + **Test** (live level meter + detected/not); Listen with screen off (warning); Voice picker with preview; Interrupt me to speak (barge-in) on/off; follow-up window; privacy line "Nothing leaves your phone before the wake phrase" |
| 6 | **Memory** | User-owned memory | Mode segmented (Cloud / This phone only / Off); *Waiting for you* card (approve/reject proposals); search; grouped items (Preferences, People, Facts) each with source & date; swipe/delete; Export; "Forget everything" (destructive, step-up) |
| 7 | **Services & plugins** | Connected abilities | Installed list (first-party: Device actions, Memory, Time; plus org/3rd-party) with scope chips and toggles; Available list with Install → scope consent sheet; "Managed by Acme" lock for org-controlled items; per-user connect (OAuth) state |
| 8 | **Activity** | Audit what VALIS did | Day-grouped timeline; filter chips (All · Actions · Conversations · Declined); each action: tool name, summary (e.g., "Opened Settings"), status badge, confirmation method; tap → detail sheet with evidence ("foreground = Settings at 14:02:11") and "Why was this allowed?" |
| 9 | **Privacy** | Control data flow | "What leaves your phone" three rows (Wake word: never · Voice: to your VALIS server only after wake · Screen: one redacted picture only when allowed); toggles: Screen sight, Conversation history, Analytics; Blocked apps editor; Export my data; Delete my data; org-managed banner when applicable |
| 10 | **Security** | Safety rails | This device + other devices (revoke); "Confirm with fingerprint" setting (Off / Calls & messages / All); "Always allowed" tools list (revoke); sign-in methods; **"VALIS never does…"** list (payments, passwords, security settings) |
| 11 | **Plan & billing** | Subscription & usage | Current plan card; usage meters (voice minutes, vision looks, actions) with soft/hard limit markers; plan comparison; next invoice; Manage (Stripe portal / Play) |
| 12 | **Workspace** | Switch & govern | Workspace list (Personal, companies) with active marker; members avatars + roles; managed policies summary (risk ceiling, vision policy, retention); Invite; admin tools → web console |
| 13 | **Confirmation card** (overlay) | Safe consent | Device-rendered, dark card: action + resolved details (contact name & number), character looking at it; **Deny** / **Allow once**; no "always allow" for consequential actions; auto-timeout 20 s |

## 4. Component inventory (`core/design`)
`PresenceDot`, `HeroDisc`, `CharacterPreview` (Filament view reused from `core/character`), `StatusPill`, `PebbleIcon`, `SettingRow` (toggle/nav/value), `SegmentedControl`, `SteppedSlider`, `MeterBar`, `Chip` (filter/choice), `ConfirmCard`, `Banner` (info/amber/red), `Sheet`, `EmptyState` (with character pose), `Skeleton`. Every component ships with previews in light only (dark theme is **overlay-only** in v1), TalkBack labels, and 200%-font-scale snapshot tests.

## 5. User journeys

| Journey | Steps (screens) |
|---|---|
| **J1 First run → first summon** | Welcome → Overlay access (system settings round-trip) → Microphone → "Say 'Yo, VALIS'" test (Voice test card) → character appears over the home screen → Done → Home |
| **J2 "Look at this post. What do you think?"** | wake → character appears → user asks → "Look at your screen?" chip → system capture consent → one redacted frame → answer spoken; Activity logs the look (no image) |
| **J3 Risky action** | "Call Mum" → device-rendered confirmation card → tap **Allow once** (optional fingerprint) → dialer opens → Activity shows *Verified* with evidence; if declined, shows *Declined* |
| **J4 Memory review & forget** | VALIS asks "Remember that you prefer short answers?" (voice/chip) → Memory › Waiting for you → Approve → later Delete one item / Forget everything (step-up auth) |
| **J5 Join a company workspace** | Invite link → sign in → Workspace tab shows "Acme Studio" → policies appear as *Managed* (vision allowlist, risk ceiling) → switch workspace → memory and plugins differ |

## 6. Accessibility, localisation, content
TalkBack order and roles for every screen; 200% font scale without clipping/overlap; 7:1 primary text contrast; no colour-only status (pill text + icon); reduced motion; captions option for speech (also useful in noisy places); RTL-ready layouts; string tables with ICU plurals; copy tone — plain, warm, never cute about permissions or data. Character expressions in empty/error states reuse real poses (`shrug`, `expression_sleepy`, `expression_happy`).

## 7. Testing & acceptance
Compose previews + screenshot tests per screen/state (loading, empty, error, managed-by-org, permission-lost); layout tests at 360/392/412 dp and 200% font (no overlap/clipping assertions); TalkBack walkthrough per journey; usability test of J1–J5 with ≥ 5 people. **Acceptance:** all screens implemented to `app.html`; J1 completed unaided by ≥ 4/5 testers in < 3 min; every permission/data statement in the UI matches actual behaviour verified against traffic captures (doc 10 §8); zero overlap/clipping defects in the layout test matrix.
