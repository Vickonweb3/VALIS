from bp import *
from sheets_a import img


def vb07():
    s = Sheet('VB-07', 'Floating Overlay Architecture', 'One small, repositioned overlay window; three single-purpose foreground services; honest about what Android allows.', 'docs/03 · decisions D05')
    # phone
    px, py, pw, ph = 50, 100, 330, 690
    s.back.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="34" fill="#FFFFFF" stroke="{INK}" stroke-width="2.4"/>')
    sx, sy, sw, sh = px + 14, py + 16, pw - 28, ph - 32
    s.back.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="22" fill="#F2F3F9" stroke="{DOT}"/>')
    # status bar, gesture zone, IME hint
    s.back.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="30" rx="22" fill="#E3E4F1"/>')
    s.text(sx + sw / 2, sy + 20, 'status bar · cutout inset', 10, 600, MUTE, 'middle', True, 'back')
    s.back.append(f'<rect x="{sx}" y="{sy+sh-34}" width="{sw}" height="34" fill="#FFF1D6" stroke="{AMB}" stroke-dasharray="4 3"/>')
    s.text(sx + sw / 2, sy + sh - 14, 'gesture zone · keep ≥ 24 dp above', 10, 600, AMB, 'middle', True, 'back')
    # fake app content
    for i, (yy, ww) in enumerate([(70, 220), (96, 170), (140, 250), (166, 200), (192, 230), (236, 180), (262, 240)]):
        s.back.append(f'<rect x="{sx+18}" y="{sy+yy}" width="{ww}" height="12" rx="6" fill="#D9DBEA"/>')
    s.back.append(f'<rect x="{sx+18}" y="{sy+310}" width="{sw-36}" height="120" rx="14" fill="#E3E4F1"/>')
    s.text(sx + sw / 2, sy + 375, 'foreground app content', 11, 500, MUTE, 'middle', True, 'back')
    # anchors
    anchors = {'TL': (sx + 14, sy + 44), 'TR': (sx + sw - 14 - 120, sy + 44), 'BL': (sx + 14, sy + sh - 34 - 160), 'BR': (sx + sw - 14 - 120, sy + sh - 34 - 160)}
    for k, (ax, ay) in anchors.items():
        s.front.append(f'<rect x="{ax}" y="{ay}" width="120" height="160" rx="12" fill="none" stroke="{CO}" stroke-width="1.2" stroke-dasharray="5 4"/>')
        s.text(ax + 8, ay + 14, k, 10, 700, CO, 'start', True)
    ax, ay = anchors['BR']
    s.front.append(img('assets/char/idle.webp', ax - 6, ay - 8, 132, 175))
    s.front.append(f'<rect x="{ax}" y="{ay}" width="120" height="160" rx="12" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    s.text(px + pw / 2, py + ph + 24, 'tight box 200×270 dp · 4 corner anchors', 10.5, 500, INK, 'middle', True)
    # callouts on right of phone
    s.node('c1', 410, 120, 270, 98, 'Window', ['TYPE_APPLICATION_OVERLAY', 'NOT_FOCUSABLE · NOT_TOUCH_MODAL', 'LAYOUT_NO_LIMITS · TRANSLUCENT'], 'dev')
    s.node('c2', 410, 240, 270, 98, 'Position score S(a)', ['.45 free + .25 prefer + .10 stable', '−.10 travel − .10 IME conflict', 'free ← a11y nodes | frame | 0.5'], 'dev')
    s.node('c3', 410, 360, 270, 112, 'Gestures', ['drag (8 dp slop) · fling → anchor', 'drop ≤24 dp edge → tuck · tap = PTT', 'double-tap sleep · long-press menu'], 'dev')
    s.node('c4', 410, 494, 270, 98, 'Safe area', ['systemBars|cutout|gestures', 'IME inset · fold bounds', 'API26-29 metrics fallback'], 'dev')
    s.node('c5', 410, 614, 270, 112, 'Known limits', ['no overlay on lock screen / secure', 'system dialogs & shade draw above', 'transparent corners eat touches'], 'perm')
    # services
    s.zone(710, 92, 870, 330, 'Foreground services (one purpose each)', 'dev')
    s.node('pc', 730, 128, 230, 112, 'PresenceCoordinator', ['single source of PresenceState', 'owns service lifecycles', 'emits CharacterEvent'], 'ink')
    s.node('os', 1020, 128, 250, 80, 'OverlayService', ['FGS specialUse · START_STICKY'], 'dev')
    s.node('vs', 1020, 222, 250, 80, 'VoiceService', ['FGS microphone · wake word'], 'dev')
    s.node('cs', 1020, 316, 250, 80, 'CaptureService', ['FGS mediaProjection · per session'], 'dev')
    s.node('n1', 1310, 128, 250, 80, 'Presence notification', ['Summon · Mute · Stop'], 'pearl')
    s.node('n2', 1310, 222, 250, 80, 'Quick tile · shortcuts', ['user-initiated start'], 'pearl')
    s.node('n3', 1310, 316, 250, 80, 'Capture notification', ['"VALIS can see your screen"'], 'perm')
    s.edge('pc', 'os', 'start/stop', 'ctrl', 'r.2', 'l.5', lw=64); s.edge('pc', 'vs', None, 'ctrl', 'r.5', 'l.5'); s.edge('pc', 'cs', None, 'ctrl', 'r.8', 'l.5')
    s.edge('n1', 'pc', 'actions', 'async', 't.5', 't.9', via=[(1435, 99), (918, 99)], lw=58)
    s.edge('n2', 'vs', None, 'async', 'l.5', 'r.5') if False else None
    s.edge('os', 'n1', None, 'data', 'r.5', 'l.5'); s.edge('vs', 'n2', None, 'data', 'r.5', 'l.5'); s.edge('cs', 'n3', None, 'data', 'r.5', 'l.5')
    # lifecycle
    s.zone(710, 440, 870, 190, 'Overlay lifecycle', 'plain')
    chain = [('NOT_ATTACHED', 730), ('ATTACHING', 900), ('VISIBLE', 1070), ('TUCKED', 1240), ('SUPPRESSED', 1400)]
    for i, (n, x) in enumerate(chain):
        s.node('lc' + str(i), x, 480, 150, 56, n, [], 'model' if n == 'VISIBLE' else 'dev')
    for i in range(4):
        s.edge('lc' + str(i), 'lc' + str(i + 1), None, 'ctrl')
    s.edge('lc3', 'lc2', 'untuck', 'ctrl', 'b.3', 'b.7', via=[(1275, 578), (1135, 578)], lw=48)
    s.node('det', 730, 584, 150, 40, 'DETACHED', [], 'bad')
    s.edge('lc2', 'det', 'disable · revoke', 'deny', 'b.5', 't.5', lw=96) if False else None
    s.text(730, 556, 'keyguard / secure window / screen off → SUPPRESSED · disable or permission revoked → DETACHED', 10, 400, MUTE, 'start', True)
    s.zone(710, 646, 870, 234, 'Permissions requested just-in-time (never all at once)', 'perm')
    perms = [('Overlay', 'first enable'), ('Notifications', 'first enable'), ('Microphone', 'turn on voice'), ('Screen sight', 'first look · per session'), ('Accessibility', 'first UI action'), ('Notif. access', 'opt-in'), ('Usage access', 'opt-in'), ('Runtime tools', 'at first use')]
    for i, (a, b) in enumerate(perms):
        x = 730 + (i % 4) * 212
        y = 684 + (i // 4) * 94
        s.node('pm' + str(i), x, y, 196, 78, a, [b], 'perm')
    s.node('r3', 730, 790, 820, 70, 'Android 14/15 constraints (verify in S2)', ['mic FGS must start from a visible moment · no mic arming at BOOT_COMPLETED · overlay + FGS-from-background needs a visible overlay'], 'ink') if False else None
    return s


def vb08():
    s = Sheet('VB-08', 'Voice System Architecture', 'Wake word never leaves the device. A separate tiny detector runs; the main model only runs inside a turn.', 'docs/05 Part A · D06 D07')
    s.zone(30, 92, 830, 300, 'On-device only · always while armed (screen on)', 'dev')
    s.node('mic', 48, 130, 120, 84, 'Mic', ['16 kHz mono', '20 ms hops'], 'ext')
    s.node('aec', 196, 130, 150, 84, 'AEC · NS', ['VOICE_COMMUNICATION', 'platform effects'], 'dev')
    s.node('ring', 374, 130, 150, 84, 'Ring buffer', ['≈ 4 s PCM', 'RAM only'], 'store')
    s.node('vad', 552, 130, 130, 84, 'Silero VAD', ['ONNX · gate'], 'dev')
    s.node('ww', 710, 130, 130, 84, 'Wake model', ['"Yo, VALIS"', 'INT8 ONNX'], 'dev', tag='D06')
    for a, b in [('mic', 'aec'), ('aec', 'ring'), ('ring', 'vad'), ('vad', 'ww')]:
        s.edge(a, b, None, 'data')
    s.node('wd', 552, 262, 288, 100, 'WakeDetected(confidence)', ['smooth 3-of-5 · keep prior 1.5 s of audio', 'optional verifier pass · earcon · Summoned'], 'pearl')
    s.edge('ww', 'wd', None, 'ctrl', 'b.5', 't.85', lw=1) if False else None
    s.edge('ww', 'wd', 'score ≥ thr', 'ctrl', 'b.5', 't.85', lw=72)
    s.node('perm', 48, 262, 250, 100, 'RECORD_AUDIO + FGS mic', ['started from a visible moment', 'screen-off listening = opt-in'], 'perm')
    s.node('pres', 330, 262, 190, 100, 'PresenceCoordinator', ['opens turn · summons', 'CharacterEvent'], 'ink')
    s.edge('wd', 'pres', None, 'ev', 'l.5', 'r.5')
    s.edge('perm', 'mic', None, 'perm', 't.5', 'b.5', via=[(108, 240), (108, 214)]) if False else None
    s.zone(30, 410, 1550, 300, 'Streamed only during a turn (Opus up · PCM/Opus down)', 'plain')
    s.node('tc', 48, 448, 180, 100, 'TurnCapture', ['endpointing 450 ms', 'max 30 s · no-speech 6 s'], 'dev')
    s.node('opus', 258, 448, 150, 100, 'Opus encode', ['20 ms frames', '≈16–24 kbps'], 'dev')
    s.node('sc', 438, 448, 160, 100, 'SessionClient', ['WSS binary frames', 'seq · turn_id'], 'dev')
    s.node('gw', 628, 448, 160, 100, 'Gateway', ['entitlement · relay'], 'cloud')
    s.node('pv', 818, 448, 200, 100, 'InferenceProvider', ['s2s (omni) | cascade', '| text → client TTS'], 'cloud', tag='D16')
    s.node('out', 1048, 448, 160, 100, 'audio.out', ['PCM16 24 kHz', '≤100 ms chunks'], 'cloud')
    s.node('jb', 1238, 448, 150, 100, 'Jitter buffer', ['target 120 ms', 'adaptive 80–300'], 'dev')
    s.node('at', 1418, 448, 150, 100, 'AudioTrack', ['USAGE_ASSISTANT', 'duck, no pause'], 'dev')
    for a, b in [('tc', 'opus'), ('opus', 'sc'), ('sc', 'gw'), ('gw', 'pv'), ('pv', 'out'), ('out', 'jb'), ('jb', 'at')]:
        s.edge(a, b, None, 'data')
    s.node('tap', 1238, 590, 330, 90, 'Playback tap → CharacterRuntime', ['RMS envelope · optional provider visemes', 'visemes aa oh ou ee ih fv'], 'pearl')
    s.edge('at', 'tap', 'rms', 'ev', 'b.5', 't.9', lw=36) if False else None
    s.edge('jb', 'tap', None, 'ev', 'b.5', 't.2')
    s.node('bi', 48, 590, 560, 100, 'Barge-in (≤ 150 ms local cut-off)', ['VAD ≥120 ms above barge threshold during SPEAKING/THINKING', 'AudioTrack.pause()+flush() → Interrupted event → send interrupt{turn_id}', 'late audio for that turn_id dropped · AEC required or threshold raised'], 'bad')
    s.edge('bi', 'sc', 'interrupt', 'deny', 't.9', 'b.5', lw=62, via=[(552, 560), (518, 560)]) if False else None
    s.edge('bi', 'sc', 'interrupt', 'deny', 't.75', 'b.5', lw=62)
    s.node('fb', 638, 590, 570, 100, 'Fallback ladder (negotiated in session.ready)', ['s2s → cascade → text + local TTS → local SpeechRecognizer/TTS', 'every step change is told to the user, never silently degraded'], 'perm')
    s.zone(30, 726, 1550, 154, 'Latency budget (targets; real-model values validated in M8)', 'ink')
    segs = [('wake → visible', '≤ 400 ms', 200), ('endpointing', '450 ms', 150), ('uplink + model first token', '≤ 500 ms', 250), ('first audio playable', '≤ 1.2 s p50 after end of speech', 360), ('barge-in cut', '≤ 150 ms', 140)]
    x = 52
    for lab, val, w in segs:
        s.back.append(f'<rect x="{x}" y="770" width="{w}" height="46" rx="6" fill="#fff" stroke="{CO}" stroke-width="1.4"/>')
        s.text(x + w / 2, 790, val, 11.5, 700, INK, 'middle', True, 'front')
        s.text(x + w / 2, 806, lab, 10, 400, MUTE, 'middle', True, 'front')
        x += w + 14
    s.text(52, 850, 'Every segment is recorded per turn (usage_events.latency_*) and feeds SLO dashboards.', 10.5, 400, MUTE, 'start', True)
    return s


def vb09():
    s = Sheet('VB-09', 'Vision Pipeline', 'Consent, then one on-demand, redacted, masked frame. Seeing the screen grants no ability to act on it.', 'docs/05 Part B · D08 D24')
    s.node('req', 40, 130, 200, 90, 'Look request', ['model vision.request', 'or user: "Look at…"'], 'pearl')
    s.node('pol', 290, 130, 230, 90, 'VisionPolicy', ['org: off/allowlist/choice', 'denylist · secure content'], 'perm')
    s.node('con', 570, 130, 230, 90, 'MediaProjection consent', ['system dialog · per session', 'A14+: app or full screen'], 'perm')
    s.node('cap', 850, 130, 220, 90, 'CaptureService', ['FGS mediaProjection', 'first · then projection'], 'dev')
    s.node('vd', 1120, 130, 200, 90, 'VirtualDisplay', ['one per projection', 'callback registered'], 'dev')
    s.node('ir', 1370, 130, 190, 90, 'ImageReader', ['RGBA_8888 · 2 bufs', 'acquireLatestImage'], 'dev')
    for a, b in [('req', 'pol'), ('pol', 'con'), ('con', 'cap'), ('cap', 'vd'), ('vd', 'ir')]:
        s.edge(a, b, None, 'perm' if a in ('pol',) else 'ctrl')
    s.node('deny', 290, 270, 230, 70, 'Explain + offer', ['character speaks / chip'], 'bad')
    s.edge('pol', 'deny', 'blocked', 'deny', 'b.5', 't.5', lw=58)
    s.zone(30, 380, 1550, 250, 'FramePipeline (on device, in this order)', 'dev')
    steps = [('1 Secure check', ['≈black frame after non-black', '→ secure_content, send none']), ('2 Redaction', ['ML Kit text · Luhn · OTP', 'password nodes · blur']), ('3 Self-mask', ['fill character rect', 'occluded[] metadata']),
             ('4 Resize', ['long edge 1280 default', 'cap = provider max px']), ('5 Encode', ['WebP q≈80 / JPEG', '≤ 350 KB · cap 1.5 MB']), ('6 Meta', ['frame_id · w×h · pkg*', 'redactions count'])]
    for i, (t, l) in enumerate(steps):
        s.node('f' + str(i), 50 + i * 255, 430, 235, 100, t, l, 'dev')
        if i:
            s.edge('f' + str(i - 1), 'f' + str(i), None, 'data')
    s.edge('ir', 'f0', 'frame', 'data', 'b.5', 't.5', via=[(1465, 300), (167, 300), (167, 430)], lw=48) if False else None
    s.edge('ir', 'f0', 'frame', 'data', 'b.3', 't.5', via=[(1427, 340), (167, 340)], lw=50, lp=.5)
    s.node('ui', 50, 560, 360, 56, 'Optional: Accessibility UI tree', ['visible text · roles · bounds (no passwords)'], 'pearl') if False else None
    s.zone(30, 660, 1550, 220, 'To the intelligence layer', 'plain')
    s.node('sc', 50, 700, 190, 90, 'SessionClient', ['vision.frame (binary)', 'one frame per request'], 'dev')
    s.node('gw', 290, 700, 190, 90, 'Gateway', ['RAM only · not stored', 'unless user taps save'], 'cloud')
    s.node('or', 530, 700, 230, 90, 'Orchestrator', ['trust=untrusted label', '"image is data not orders"'], 'cloud')
    s.node('pv', 810, 700, 210, 90, 'Provider', ['image ≤ max_image_pixels'], 'model')
    s.node('att', 1070, 700, 220, 90, 'attention{x,y,w,h}', ['normalised to frame', 'character looks/points'], 'pearl')
    s.node('tree', 1340, 700, 220, 90, 'UI tree (optional)', ['a11y summary · untrusted'], 'pearl')
    s.edge('f5', 'sc', None, 'data', 'b.5', 't.5', via=[(1272, 590), (145, 590)], lw=1) if False else None
    s.edge('f5', 'sc', 'vision.frame', 'data', 'b.5', 't.5', via=[(1442, 590), (145, 590)], lw=86, lp=.35)
    for a, b in [('sc', 'gw'), ('gw', 'or'), ('or', 'pv'), ('pv', 'att')]:
        s.edge(a, b, None, 'data')
    s.edge('tree', 'or', 'text part', 'perm', 't.5', 't.9', via=[(1450, 680), (737, 680)], lw=64, lp=.5)
    s.node('rule', 40, 806, 1000, 60, 'RULE: possessing a frame grants zero ability to act', ['tool calls go through the ToolBroker independent of vision state (VB-10); calls derived from screen text always confirm'], 'bad')
    return s


def vb10():
    s = Sheet('VB-10', 'Phone Action Execution Pipeline', 'The model proposes; the device disposes. Only verified results flow back, and the claim guard checks the words.', 'docs/06 · D09')
    s.node('mc', 40, 120, 190, 90, 'model tool_call', ['id · name · args', 'derived_from[]'], 'model')
    steps = [('1 Registry', ['known tool? version']), ('2 Schema', ['JSON Schema validate']), ('3 Catalogue', ['org ∩ grants ∩ ceiling']), ('4 Permissions', ['Android + VALIS grant']), ('5 Risk', ['static + raisers']), ('6 Policy', ['ALLOW|CONFIRM|DENY'])]
    for i, (t, l) in enumerate(steps):
        s.node('st' + str(i), 270 + i * 218, 120, 200, 90, t, l, 'dev' if i < 3 else 'perm')
    s.edge('mc', 'st0', None, 'ctrl')
    for i in range(5):
        s.edge('st' + str(i), 'st' + str(i + 1), None, 'ctrl')
    s.zone(30, 250, 1550, 300, 'Decision branches', 'plain')
    s.node('den', 60, 300, 230, 100, 'DENY', ['PROHIBITED set · over ceiling', 'denylisted app · no permission'], 'bad')
    s.node('res_d', 60, 440, 230, 80, 'result{denied, reason}', ['spoken reason'], 'bad')
    s.edge('den', 'res_d', None, 'deny', 'b.5', 't.5')
    s.node('conf', 360, 300, 330, 100, 'CONFIRM · device-rendered card', ['text from confirmationTemplate + validated args', 'CONSEQUENTIAL = tap/biometric · 20 s timeout'], 'perm')
    s.node('res_c', 360, 440, 330, 80, 'result{cancelled}', ['declined or timed out'], 'bad')
    s.edge('conf', 'res_c', 'no', 'deny', 'b.5', 't.5', lw=34)
    s.node('allow', 760, 300, 200, 100, 'ALLOW', ['SAFE · logged', 'SENSITIVE after first ok'], 'ok')
    s.edge('st5', 'den', 'DENY', 'deny', 'b.15', 't.5', via=[(3 * 0 + 1318 - 218 * 0 - 0, 235)], lw=1) if False else None
    s.edge('st5', 'den', 'DENY', 'deny', 'b.1', 't.5', via=[(1396, 235), (175, 235)], lw=40, lp=.12)
    s.edge('st5', 'conf', 'CONFIRM', 'perm', 'b.3', 't.5', via=[(1424, 244), (525, 244)], lw=62, lp=.45)
    s.edge('st5', 'allow', 'ALLOW', 'ok', 'b.5', 't.5', via=[(1468, 253), (860, 253)], lw=48, lp=.55)
    s.edge('conf', 'allow', 'yes', 'ok', 'r.5', 'l.5', lw=30)
    s.zone(1010, 280, 560, 250, 'Executors (stateless · cancellable · deadline)', 'dev')
    ex = [('IntentExecutor', ['open app · settings', 'web · dial']), ('AccessibilityExecutor', ['global + node actions', 'never password fields']), ('SystemExecutor', ['audio · download · media', 'usage · SAF files']), ('CloudExecutor', ['plugins via cloud broker'])]
    for i, (t, d) in enumerate(ex):
        s.node('ex' + str(i), 1030 + (i % 2) * 270, 312 + (i // 2) * 106, 250, 98, t, d, 'dev')
    s.edge('allow', 'ex0', 'execute', 'ctrl', 'r.5', 'l.5', via=[(985, 350), (985, 358)], lw=1) if False else None
    s.edge('allow', 'ex0', 'execute', 'ctrl', 'r.5', 'l.5', lw=56)
    s.zone(30, 566, 1550, 314, 'Result path (the model never sees success it did not earn)', 'ok')
    s.node('vf', 60, 612, 240, 100, 'Verify (postcondition)', ['foreground pkg · DownloadManager', 'PlaybackState · node text · file'], 'ok')
    s.node('lg', 340, 612, 200, 100, 'ActionLog (Room)', ['args hash · decision', 'status · evidence'], 'dev')
    s.node('tr', 580, 612, 250, 100, 'tool.result', ['verified | unverified | failed', 'denied | cancelled | timeout'], 'ok')
    s.node('or', 870, 612, 230, 100, 'Orchestrator', ['rebuilds result from device', 'no synthesised success'], 'cloud')
    s.node('cg', 1140, 612, 200, 100, 'Claim guard', ['completion words vs status', 'rewrite if unverified'], 'bad')
    s.node('say', 1380, 612, 180, 100, 'Spoken outcome', ['templates for', 'CONSEQUENTIAL'], 'pearl')
    s.edge('ex1', 'vf', None, 'ctrl', 'b.5', 't.5', via=[(1295, 548), (180, 548)]) if False else None
    s.edge('ex2', 'vf', 'observe', 'ok', 'b.2', 't.5', via=[(1080, 556), (180, 556)], lw=58, lp=.3)
    s.edge('vf', 'lg', None, 'data'); s.edge('lg', 'tr', None, 'data'); s.edge('tr', 'or', 'WSS', 'ctrl', lw=36); s.edge('or', 'cg', None, 'ctrl'); s.edge('cg', 'say', None, 'ok')
    s.node('raise', 60, 750, 740, 108, 'Dynamic raisers (never lower a class)', ['derived_from screen|plugin|memory → at least CONFIRM', 'first use this session (SENSITIVE+) · denylisted foreground → DENY', 'org risk_ceiling · repeated failures → throttle · quiet hours → chip only'], 'perm')
    s.node('proh', 840, 750, 720, 108, 'PROHIBITED (always refused)', ['payments/purchases · banking & wallet apps · password entry', 'security & device-admin settings · disabling VALIS safeguards', 'anything on org lock-lists · multi-step UI max 8 steps/turn'], 'bad')
    return s


def vb11():
    s = Sheet('VB-11', 'Backend Infrastructure', 'One TypeScript modular monolith, three process roles, one Python inference service. No Kubernetes, no Redis, no microservices at launch.', 'docs/07 Part A · D10 D11 D12')
    s.node('cl', 40, 120, 160, 80, 'Android app', ['HTTPS + WSS'], 'dev'); s.node('ad', 40, 230, 160, 80, 'Admin console', ['Next.js · Vercel'], 'ext')
    s.zone(230, 92, 1350, 560, 'valis monolith · one image · ROLE=api | realtime | worker', 'cloud')
    s.node('edge', 250, 130, 130, 200, 'Edge', ['TLS 1.3', 'WAF', 'rate limit', 'WS upgrade'], 'ext')
    s.edge('cl', 'edge', 'HTTPS/WSS', 'data', 'r.5', 'l.15', lw=74)
    s.edge('ad', 'edge', 'HTTPS', 'data', 'r.5', 'l.55', lw=56)
    s.node('api', 430, 130, 200, 90, 'role=api', ['REST /v1 · Fastify', 'TypeBox · problem+json'], 'cloud')
    s.node('rt', 430, 240, 200, 90, 'role=realtime', ['WSS gateway', 'session · turn · relay'], 'cloud')
    s.node('wk', 430, 350, 200, 90, 'role=worker', ['pg-boss queues', 'embed · retention · billing'], 'cloud')
    s.edge('edge', 'api', None, 'data', 'r.15', 'l.5'); s.edge('edge', 'rt', None, 'data', 'r.5', 'l.5'); s.edge('edge', 'wk', None, 'data', 'r.85', 'l.5') if False else None
    mods = [('identity', 'JWT · devices'), ('tenancy', 'orgs · roles · RBAC'), ('memory', 'pgvector · proposals'), ('sessions', 'conversations · turns'), ('tools', 'catalogue · relay'), ('orchestrator', 'context · claim guard'), ('plugins', 'registry · invoke'), ('files', 'presign · TTL'), ('billing', 'entitlements · ports'), ('usage', 'events · limits'), ('audit', 'append-only'), ('notifications', 'push · email'), ('admin', 'aggregates')]
    s.zone(660, 118, 560, 340, 'Modules (import only each other’s index.ts)', 'plain', 11)
    for i, (n, d) in enumerate(mods):
        x = 676 + (i % 3) * 180
        y = 150 + (i // 3) * 58
        s.node('m' + n, x, y, 168, 48, n, [], 'pearl', tsize=12)
    s.text(676, 440, 'tenancy.withOrgContext(orgId) wraps every handler → RLS session vars', 10.5, 600, CO, 'start', True)
    s.edge('api', 'mtenancy', None, 'ctrl', 'r.5', 'l.5', via=[(645, 154), (645, 208)]) if False else None
    s.node('inf', 1250, 130, 310, 130, 'Inference service', ['Python · FastAPI · private', 'providers: mock · cascade · minicpm-o', 'mTLS / signed JWT · no egress', 'no DB credentials'], 'model', tag='D16')
    s.edge('rt', 'inf', 'InferenceRequest', 'data', 'r.5', 'l.5', via=[(645, 285), (645, 480), (1230, 480), (1230, 195)], lw=100, lp=.5) if False else None
    s.edge('mmemory', 'inf', None, 'data', 'r.5', 'l.5') if False else None
    s.zone(230, 668, 1350, 212, 'Data & platform', 'plain')
    s.node('pg', 250, 706, 330, 140, 'PostgreSQL 16', ['RLS forced · app role no BYPASSRLS', 'pgvector HNSW · FTS · pg-boss', 'partitions: usage, audit (monthly)', 'PITR ≥ 7 d · field-level encryption'], 'store', tag='D11')
    s.node('os', 620, 706, 250, 140, 'Object storage', ['S3 API · key org/{org_id}/…', 'pre-signed ≤ 5 min', 'lifecycle TTL'], 'store')
    s.node('kms', 910, 706, 230, 140, 'KMS', ['KEK → per-org DEK', 'rotation job', 'crypto-erase on delete'], 'perm')
    s.node('obs', 1180, 706, 380, 140, 'Observability', ['OpenTelemetry traces/metrics', 'Sentry errors · pino JSON logs', 'ids only — no content in logs', 'audit log separate, append-only'], 'dev')
    s.edge('api', 'pg', None, 'data', 'b.3', 't.2', via=[(490, 224), (490, 640), (300, 640)]) if False else None
    s.edge('wk', 'pg', 'SQL under RLS', 'data', 'b.5', 't.5', via=[(530, 500), (415, 500)], lw=96) if False else None
    s.edge('wk', 'pg', 'SQL under RLS', 'data', 'b.3', 't.6', via=[(490, 470), (448, 470)], lw=1) if False else None
    s.edge('wk', 'pg', 'SQL under RLS', 'data', 'b.5', 't.5', via=[(530, 600), (415, 600)], lw=96)
    s.note(250, 470, 260, ['authenticate → resolveOrg →', 'validate → authorize →', 'withOrgContext(RLS) →', 'handler → audit'], 'Request lifecycle')
    s.note(660, 480, 560, ['Errors: RFC 9457 problem+json · stable codes (USAGE_LIMIT_REACHED…)', 'Idempotency-Key on POST · cursor pagination · X-Org-Id', 'Provider failure → fallback chain before erroring'], 'Conventions')
    s.edge('rt', 'inf', 'InferenceRequest/Event', 'data', 'b.9', 'b.1', via=[(610, 650), (1270, 650)], lw=140, lp=.5) if False else None
    s.edge('mod' if False else 'morchestrator', 'inf', 'request ⇄ events', 'data', 'r.5', 'l.5', via=[(1230, 254), (1230, 195)], lw=96) if False else None
    s.edge('mtools', 'inf', None, 'data') if False else None
    s.edge('morchestrator', 'inf', 'request ⇄ events', 'data', 'r.5', 'l.5', via=[(1235, 232), (1235, 195)], lw=104, lp=.5)
    s.edge('morchestrator', 'inf', 'request ⇄ events', 'data', 'r.5', 'l.5', via=[(1232, 350), (1232, 195)], lw=104, lp=.55) if False else None
    s.edge('mmemory', 'pg', None, 'data') if False else None
    return s


def vb12():
    s = Sheet('VB-12', 'Database Architecture · key entities', 'Every tag "org_id" table has forced RLS; composite FKs stop cross-tenant references. Full DDL in docs/07.', 'docs/07 Part B · D11 D14')
    X = [40, 350, 660, 970, 1280]
    W_ = 270

    def T(i, c, y, name, cols, tag='org_id', kind='cloud'):
        s.node(i, X[c], y, W_, 30 + 14 * len(cols) + 10, name, cols, kind, tag=tag)
    T('users', 0, 110, 'users', ['id PK · idp_subject UQ', 'email · display_name · locale'], None)
    T('devices', 0, 240, 'devices', ['id PK · user_id FK', 'platform · os_api · key_thumbprint', 'attestation · revoked_at'], None)
    T('consent', 0, 390, 'consent_records', ['org_id · user_id · kind', 'version · granted · at'])
    T('files', 0, 510, 'files', ['org_id · bucket_key · bytes', 'sha256 · purpose · expires_at'])
    T('models', 0, 640, 'model_endpoints', ['provider · model_id · version', 'capabilities · config jsonb', 'priority · plan_ids · enabled'], None, 'model')
    T('memb', 1, 110, 'memberships', ['PK(org_id, user_id)', 'role: owner|admin|billing_admin', '  |member|guest · status'])
    T('orgs', 1, 240, 'organizations', ['id PK · kind personal|company', 'name · slug · owner_user_id', 'plan_id · status'], None)
    T('osets', 1, 400, 'org_settings', ['org_id PK · risk_ceiling', 'vision_policy · memory_policy', 'retention_days · plugin_policy'])
    T('inv', 1, 560, 'invitations', ['org_id · email · role', 'token_hash · expires_at'])
    T('conv', 2, 110, 'conversations', ['org_id · user_id · device_id', 'provider · model_id · version', 'history_enabled · summary'])
    T('turns', 2, 260, 'turns', ['conversation_id · seq UQ', 'latency_first_audio_ms · tokens', 'claim_guard_triggered', 'content_enc (null by default)'])
    T('tcalls', 2, 430, 'tool_calls', ['turn_id · tool · risk', 'decision · confirmed_by · status', 'derived_from[] · args_hash'])
    T('mem', 2, 580, 'memory_items', ['org_id · user_id? · scope', 'text_enc · embedding vector(1024)', 'status pending|active|… · sensitivity'])
    T('mev', 2, 730, 'memory_events', ['memory_id · actor · event · at'])
    T('plug', 3, 110, 'plugins', ['id PK (reverse-DNS)', 'publisher · kind · status'], None)
    T('pver', 3, 230, 'plugin_versions', ['PK(plugin_id, version)', 'manifest jsonb · signature', 'min_platform · deprecated_at'], None)
    T('pins', 3, 380, 'org_plugin_installs', ['PK(org_id, plugin_id)', 'version FK · config · secret_ref', 'scopes_granted · enabled'])
    T('pcred', 3, 530, 'plugin_credentials', ['org · user · plugin UQ', 'token_enc · refresh_enc', 'scopes · expires_at'])
    T('plans', 4, 110, 'plans', ['id PK · kind', 'limits jsonb · features jsonb'], None)
    T('subs', 4, 230, 'subscriptions', ['org_id · plan_id FK', 'provider stripe|play|manual', 'status · seats · period'])
    T('ent', 4, 370, 'entitlements', ['PK(org_id, feature)', 'value jsonb · source'])
    T('lim', 4, 470, 'usage_limits', ['PK(org, meter, period)', 'soft_limit · hard_limit'])
    T('uev', 4, 580, 'usage_events', ['org_id · meter · quantity', 'partitioned by month', 'ref_turn_id · provider'])
    T('aud', 4, 710, 'audit_logs', ['org_id · actor · action', 'target · meta (no content)', 'append-only · partitioned'])
    e = s.edge
    e('users', 'memb', 'user', 'data', 'r.3', 'l.3', lw=36)
    e('users', 'devices', None, 'data', 'b.5', 't.5')
    e('memb', 'orgs', 'org', 'data', 'b.5', 't.5', lw=30)
    e('orgs', 'osets', '1:1', 'data', 'b.5', 't.5', lw=30)
    e('osets', 'inv', None, 'data', 'b.5', 't.5') if False else None
    e('conv', 'turns', None, 'data', 'b.5', 't.5')
    e('turns', 'tcalls', None, 'data', 'b.5', 't.5')
    e('mem', 'mev', None, 'data', 'b.5', 't.5')
    e('plug', 'pver', None, 'data', 'b.5', 't.5')
    e('pver', 'pins', None, 'data', 'b.5', 't.5')
    e('plans', 'subs', None, 'data', 'b.5', 't.5')
    s.note(40, 790, 570, ['org_id on every tenant table · FORCE ROW LEVEL SECURITY', 'policy: org_id = current_setting(\'app.org_id\')::uuid', 'extra restrictive policy for user-scope memory (owner only)', 'CI fails if any table with org_id lacks forced RLS'], 'Tenant isolation')
    s.note(660, 800, 300, ['field-level envelope encryption:', 'text_enc · content_enc · token_enc', 'DEK per org · KMS KEK'], 'Encryption')
    return s
