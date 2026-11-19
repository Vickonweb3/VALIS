from bp import *

def vb13():
    s = Sheet('VB-13', 'Multi-Company Architecture', 'Everything is a workspace. A person is a user; a company is an organization; policy flows down, never up.', 'docs/08 · D14')
    s.zone(30, 92, 520, 790, 'Identity', 'plain')
    s.node('u', 50, 130, 220, 90, 'User', ['one IdP subject', 'many memberships'], 'ext')
    s.node('d', 290, 130, 240, 90, 'Devices', ['bound per user', 'revocable · attested'], 'dev')
    s.node('po', 50, 280, 220, 100, 'Personal org', ['kind=personal', 'created at signup'], 'cloud')
    s.node('co', 290, 280, 240, 100, 'Company org(s)', ['kind=company', 'invites · SSO later'], 'cloud')
    s.edge('u', 'po', 'owner', 'data', 'b.5', 't.5'); s.edge('u', 'co', 'member', 'data', 'b.8', 't.5', via=[(226, 250), (410, 250)])
    s.node('sw', 50, 440, 480, 100, 'Workspace switch', ['X-Org-Id header · JWT carries user only', 'server resolves membership → role per request'], 'perm')
    s.node('rl', 50, 580, 480, 150, 'Roles', ['owner · admin · billing_admin · member · guest', 'owner: all · admin: members/policy/plugins', 'billing_admin: plans/invoices only', 'guest: limited tools, no memory write'], 'dev')
    s.note(50, 760, 480, ['No cross-org reads, ever: RLS forced + composite FKs.', 'Personal memory never visible to company admins.'], 'Isolation rule')
    s.zone(580, 92, 1000, 790, 'Policy cascade (most restrictive wins)', 'dev')
    lv = [('Platform policy', 'PROHIBITED set · global kill switches', 'bad'), ('Plan entitlements', 'features + limits from subscription', 'ok'), ('Organization policy', 'risk ceiling · vision policy · memory policy · retention · plugin allowlist', 'perm'), ('Role grants', 'tool grants per role · lock-lists', 'perm'), ('User settings', 'autonomy · voice · per-app denylist · memory toggle', 'dev'), ('Per-call decision', 'broker: catalogue ∩ policy ∩ risk (VB-10)', 'ink')]
    y = 130
    for i, (t, d, k) in enumerate(lv):
        s.node('p%d' % i, 610, y, 940, 78, t, [d], k)
        if i: s.edge('p%d' % (i - 1), 'p%d' % i, None, 'ctrl', 'b.5', 't.5')
        y += 112
    s.node('aud', 610, 800, 940, 60, 'Audit: every policy change + admin action → audit_logs (append-only, no content)', [], 'store')
    return s

def vb14():
    s = Sheet('VB-14', 'Plugin Framework', 'Plugins are HTTPS tool providers with signed manifests. They never run in the app process.', 'docs/09 · D15')
    s.node('pub', 40, 130, 200, 90, 'Publisher', ['manifest + signature', 'tools · scopes · schema'], 'ext')
    s.node('rev', 290, 130, 220, 90, 'Review', ['automated checks', 'manual for public'], 'perm')
    s.node('reg', 560, 130, 220, 90, 'Registry', ['plugins · versions', 'min_platform'], 'store')
    s.node('ins', 830, 130, 220, 90, 'Org install', ['admin approves scopes', 'config + secret_ref'], 'perm')
    s.node('usr', 1100, 130, 220, 90, 'User connect', ['OAuth per user', 'tokens encrypted'], 'perm')
    s.node('cat', 1370, 130, 200, 90, 'Tool catalogue', ['merged per turn'], 'dev')
    for a, b in [('pub', 'rev'), ('rev', 'reg'), ('reg', 'ins'), ('ins', 'usr'), ('usr', 'cat')]:
        s.edge(a, b, None, 'ctrl')
    s.zone(30, 270, 1550, 300, 'Invocation path', 'cloud')
    s.node('m', 50, 320, 190, 100, 'Model tool_call', ['plugin.tool args'], 'model')
    s.node('b', 290, 320, 220, 100, 'Cloud tool broker', ['schema · policy · risk', 'confirm via device'], 'cloud')
    s.node('sg', 560, 320, 220, 100, 'Signed request', ['HMAC / JWT · org+user', 'no raw device data'], 'perm')
    s.node('ps', 830, 320, 220, 100, 'Plugin service', ['POST /invoke', '≤ 10 s · retries off'], 'ext')
    s.node('rs', 1100, 320, 220, 100, 'Result', ['validated vs schema', 'size cap · untrusted'], 'dev')
    s.node('or', 1370, 320, 200, 100, 'Orchestrator', ['derived_from=plugin'], 'cloud')
    for a, b in [('m', 'b'), ('b', 'sg'), ('sg', 'ps'), ('ps', 'rs'), ('rs', 'or')]:
        s.edge(a, b, None, 'data')
    s.note(50, 450, 1500, ['Plugin output is data, not instructions · results raise risk of follow-up calls to CONFIRM', 'Egress: allowlisted hosts only · per-plugin rate limits · circuit breaker after 5 failures/min'], 'Containment')
    s.zone(30, 600, 1550, 280, 'Manifest (plugin.json v1)', 'plain')
    s.note(50, 640, 740, ['id (reverse-DNS) · version · publisher', 'endpoint https://… · auth: oauth2|apikey|none', 'scopes[]: id, description, risk', 'tools[]: name, description, inputSchema, outputSchema,', '        risk, confirmationTemplate, timeoutMs', 'signature: ed25519 over canonical JSON'], 'Fields')
    s.note(830, 640, 740, ['Lifecycle: draft → review → published → deprecated → revoked', 'Revoke: catalogue drops tool in ≤ 60 s · tokens purged', 'Versioning: orgs pin a version; auto-update only for patch', 'Built-in tools are plugins of kind=builtin (device-executed)'], 'Lifecycle')
    return s

def vb15():
    s = Sheet('VB-15', 'Model Integration Architecture', 'MiniCPM-o 4.5 plugs in behind one interface. Everything above it is built and tested against a mock first.', 'docs/11 · D16 · capabilities unverified until M8')
    s.node('or', 40, 130, 240, 100, 'Orchestrator', ['InferenceRequest', 'messages · tools · media'], 'cloud')
    s.node('ip', 340, 130, 300, 100, 'InferenceProvider', ['stream(request) → events', 'capabilities() · health()'], 'ink', tag='contract')
    s.edge('or', 'ip', 'request ⇄ events', 'data', lw=100)
    s.zone(30, 280, 1550, 260, 'Providers (selected by model_endpoints + plan)', 'plain')
    s.node('mk', 50, 330, 340, 100, 'mock', ['scripted turns · fixtures', 'used by CI + app dev'], 'ok')
    s.node('cs', 430, 330, 340, 100, 'cascade', ['ASR → LLM → TTS', 'fallback + low-end path'], 'cloud')
    s.node('mc', 810, 330, 380, 100, 'minicpm-o (M8)', ['native audio in/out · vision · streaming', 'tool channel = json_schema by default'], 'model')
    s.node('fu', 1230, 330, 320, 100, 'future providers', ['same interface'], 'ext')
    for p in ['mk', 'cs', 'mc', 'fu']:
        s.edge('ip', p, None, 'data', 'b.5', 't.5') if p == 'mk' else None
    s.edge('ip', 'cs', None, 'data', 'b.5', 't.5'); s.edge('ip', 'mc', None, 'data', 'b.8', 't.5', via=[(600, 262), (1000, 262)])
    s.note(50, 450, 1500, ['Rule: no provider-specific code outside adapters. Capabilities are declared by the adapter, probed in the conformance suite, and negotiated to the client in session.ready.'], None)
    s.zone(30, 570, 760, 310, 'Conformance suite (must pass to enable a provider)', 'ok')
    s.note(50, 610, 720, ['text turn · streaming order · cancel ≤ 300 ms', 'tool call round-trip · malformed args recovery', 'audio in/out · barge-in · image input', 'emotion/gesture hints inside closed enums', 'latency budget · memory/VRAM footprint', 'injection corpus: screen text cannot trigger tools'], 'Tests')
    s.zone(820, 570, 760, 310, 'Readiness checklist before connecting', 'perm')
    s.note(840, 610, 720, ['☐ licence + redistribution terms re-verified', '☐ GPU sizing measured (quantised vs full)', '☐ native tool-calling tested; else json_schema', '☐ full-duplex behaviour vs our turn model', '☐ safety eval on prohibited-action prompts', '☐ conformance suite green · SLO baseline recorded'], 'Gate')
    return s

def vb16():
    s = Sheet('VB-16', 'App Navigation & Screens', 'A control centre around the character, not a chat client. Thirteen screens, four tabs, no deep stacks.', 'docs/14 · tokens VALIS Console')
    tabs = [('Home', ['presence preview', 'quick toggles · today']), ('Memory', ['mode · pending approvals', 'items · forget']), ('Activity', ['timeline of actions', 'evidence · why allowed']), ('Control', ['hub: permissions · character', 'voice · plugins · privacy …'])]
    for i, (t, l) in enumerate(tabs):
        s.node('t%d' % i, 60 + i * 375, 130, 340, 100, t, l, 'ink' if i == 0 else 'dev')
    s.text(60, 262, 'BOTTOM BAR (4 tabs) · workspace chip + avatar in every top bar', 11, 700, MUTE, mono=True)
    s.zone(30, 290, 1550, 590, 'Screens (numbering as in docs/14 and app.html)', 'plain')
    scr = [('1 Welcome', 'onboarding · hero disc'), ('2 Home', 'presence · today · health'), ('3 Permissions Center', 'truthful state per access'), ('4 Character', 'size · autonomy · sleep'), ('5 Voice', 'wake phrase · test · voice'), ('6 Memory', 'mode · approve · forget'),
           ('7 Services & plugins', 'scopes · managed locks'), ('8 Activity', 'timeline · evidence'), ('9 Privacy', 'what leaves the phone'), ('10 Security', 'devices · confirmations'), ('11 Plan & billing', 'usage meters · plans'), ('12 Workspace', 'switch · members · policy'), ('13 Confirmation card', 'overlay-native · device-rendered')]
    for i, (t, d) in enumerate(scr):
        x = 50 + (i % 5) * 304
        y = 330 + (i // 5) * 160
        s.node('s%d' % i, x, y, 280, 120, t, [d], 'perm' if i == 12 else 'pearl')
    s.note(50, 810, 1480, ['Flow: Welcome → Overlay access → Microphone → Meet VALIS → Home. Screens 3–5, 7, 9–12 are Control sub-pages.', 'Screen 13 is NOT an app screen: it is the device-rendered confirmation on the overlay (VB-10).'], None)
    return s

def vb17():
    s = Sheet('VB-17', 'Dependency-Aware Roadmap', 'M0–M7 build everything up to the model; M8 connects it. Critical path ≈ 24 weeks; ≈ 35 engineer-weeks total.', 'docs/12 · estimates are planning ranges')
    ms = [('M0', 'Foundations', 0, 2, 'ext'), ('M1', 'Character in overlay', 2, 5, 'dev'), ('M2', 'Voice loop', 7, 4, 'dev'), ('M3', 'Cloud core', 2, 6, 'cloud'), ('M4', 'Vision & actions', 11, 5, 'dev'),
          ('M5', 'Plugins · orgs · billing', 8, 5, 'cloud'), ('M6', 'Companion UI', 14, 5, 'dev'), ('M7', 'Hardening & release', 19, 4, 'perm'), ('M8', 'Model integration', 24, 3, 'model')]
    x0, pw = 150, 52
    for i in range(0, 28, 2):
        s.back.append('<line x1="%d" y1="110" x2="%d" y2="760" stroke="%s" stroke-width=".7"/>' % (x0 + i * pw / 1.0 * 0.9, x0 + i * pw * 0.9, DOT))
        s.text(x0 + i * pw * 0.9 + 3, 106, 'w%d' % i, 9.5, 400, MUTE, mono=True)
    for i, (m, t, st, d, k) in enumerate(ms):
        y = 124 + i * 70
        s.text(36, y + 30, m, 16, 700, mono=True)
        s.node(m, x0 + st * pw * 0.9, y, d * pw * 0.9, 56, t, [], k, tsize=12)
    s.note(36, 770, 700, ['Spikes first: S1 Filament in a translucent overlay · S2 Android 14/15 FGS + MediaProjection rules.', 'M3 runs in parallel with M1/M2 against the mock provider; M5 in parallel with M4.'], 'Order')
    s.note(760, 770, 520, ['M2 needs M1 (character events) + M3 (gateway)', 'M4 needs M2 + M3 · M6 needs M1,M3,M4 contracts', 'M8 is out of scope of this plan'], 'Dependencies')
    return s

def vb18():
    s = Sheet('VB-18', 'Cloud Deployment', 'Small, boring, replaceable: Render + Supabase + one GPU host. Scale by role, not by service count.', 'docs/13 · D12 D20 D21')
    s.zone(30, 92, 520, 380, 'Delivery (from Termux, mobile-first)', 'plain')
    s.node('t', 50, 130, 220, 80, 'Termux · git', ['commit · push on request'], 'ext'); s.node('gh', 290, 130, 240, 80, 'GitHub', ['monorepo · LFS for GLB'], 'store')
    s.node('ci', 50, 260, 220, 90, 'Actions CI', ['lint · test · RLS check', 'contract tests · APK'], 'dev'); s.node('apk', 290, 260, 240, 90, 'Signed APK / AAB', ['artifact · Play internal'], 'dev')
    s.edge('t', 'gh', None, 'data'); s.edge('gh', 'ci', None, 'ctrl', 'b.3', 't.8', via=[(360, 235), (230, 235)]) if False else s.edge('gh', 'ci', None, 'ctrl', 'b.2', 'r.5', via=[(338, 235), (338, 305)]) if False else None
    s.edge('ci', 'apk', None, 'data')
    s.edge('gh', 'ci', 'push', 'ctrl', 'b.3', 't.5', via=[(362, 232), (160, 232)], lw=40)
    s.node('rel', 50, 390, 480, 60, 'Environments: dev · staging · prod (separate DB + keys)', [], 'pearl')
    s.zone(580, 92, 1000, 380, 'Runtime', 'cloud')
    s.node('rn', 600, 130, 300, 90, 'Render', ['api · realtime · worker (3 services)', 'autoscale on CPU + WS count'], 'cloud')
    s.node('sb', 940, 130, 300, 90, 'Supabase', ['Postgres 16 + pgvector + Auth'], 'store')
    s.node('gp', 1280, 130, 280, 90, 'GPU host', ['inference service (private)', 'scale-to-zero off in prod'], 'model')
    s.node('vc', 600, 270, 300, 90, 'Vercel', ['admin console (Next.js)'], 'ext')
    s.node('ob', 940, 270, 300, 90, 'Object storage', ['S3 API · TTL · org keys'], 'store')
    s.node('km', 1280, 270, 280, 90, 'KMS', ['KEK · per-org DEK'], 'perm')
    s.edge('rn', 'sb', None, 'data'); s.edge('rn', 'gp', 'private link', 'data', 'b.5', 'b.5', via=[(750, 245), (1420, 245)], lw=86) if False else s.edge('sb', 'gp', None, 'data') if False else None
    s.edge('rn', 'gp', 'mTLS', 'data', 't.5', 't.5', via=[(750, 112), (1420, 112)], lw=60)
    s.edge('vc', 'rn', 'API', 'data', 't.5', 'b.5', lw=34)
    s.zone(30, 500, 1550, 380, 'Operations', 'plain')
    s.node('ot', 50, 540, 360, 110, 'Telemetry', ['OpenTelemetry · pino JSON', 'Sentry (app + backend)', 'ids only, no content'], 'dev')
    s.node('sl', 440, 540, 360, 110, 'SLOs', ['first audio p50 ≤ 1.2 s', 'API p95 ≤ 300 ms · 99.5% avail', 'crash-free ≥ 99.5%'], 'ok')
    s.node('al', 830, 540, 360, 110, 'Alerts', ['burn-rate pages · queue depth', 'RLS drift · GPU saturation'], 'perm')
    s.node('bk', 1220, 540, 340, 110, 'Backups & DR', ['PITR ≥ 7 d · restore drill/qtr', 'RPO 5 min · RTO 2 h'], 'store')
    s.note(50, 690, 1000, ['Release: staging soak → canary 5% → 50% → 100% · DB migrations expand/contract only', 'Feature flags per org · kill switches for vision, actions, plugins'], 'Rollout')
    s.note(1080, 690, 470, ['Costs watched: GPU hours, STT/TTS, storage', 'Meters per org feed usage limits'], 'Cost')
    return s
