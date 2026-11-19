import json
from bp import *

J = json.load(open('/home/claude/valis-blueprint/site/assets/joints.json'))


def img(href, x, y, w, h):
    return f'<image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>'


def vb01():
    s = Sheet('VB-01', 'VALIS Master Architecture', 'Device ⇄ Cloud ⇄ Inference. Every arrow is a named contract; every permission gate is amber.', 'docs/00, 01 · decisions D01–D30')
    s.zone(30, 92, 725, 788, 'Android device · trusted for UX, not for authority', 'dev')
    s.zone(775, 92, 805, 610, 'VALIS Cloud (Render) · RLS-enforced tenancy', 'cloud')
    s.zone(775, 716, 805, 164, 'External services', 'ext')
    rows = [120, 235, 350, 465, 580]
    gate = [('Mic access', ['RECORD_AUDIO','FGS: microphone']), ('Screen consent', ['MediaProjection','per session']),
            ('Device control', ['A11y · Intents','runtime perms']), ('Overlay access', ['SYSTEM_ALERT_','WINDOW']), ('Notifications', ['POST_NOTIFS','Keystore'])]
    for (t, l), y in zip(gate, rows):
        s.node('g' + str(y), 48, y, 160, 88, t, l, 'perm')
    mods = [('Voice system', ['wake · VAD · AEC/NS', 'Opus up · jitter down'], 'M2'),
            ('Vision system', ['capture · redact · mask', 'WebP ≤350 KB'], 'M4'),
            ('Action engine', ['ToolBroker · policy', 'executors · verify'], 'M4'),
            ('Character + overlay', ['Filament · PoseRuntime', 'behaviour · FSM · window'], 'M1'),
            ('Companion UI + data', ['Compose control centre', 'Room/SQLCipher · Keystore'], 'M6')]
    ids = ['voice', 'vision', 'act', 'char', 'ui']
    for (t, l, tg), y, i in zip(mods, rows, ids):
        s.node(i, 232, y, 215, 88, t, l, 'dev', tag=tg)
    for y in rows:
        s.edge('g' + str(y), ids[rows.index(y)], None, 'perm', 'r', 'l')
    s.node('sess', 570, 120, 160, 433, 'SessionClient', ['WSS /v1/realtime', 'JSON control +', 'binary media', '', 'AuthClient (JWT)', 'resume · backoff'], 'dev', tag='D07')
    s.edge('voice', 'sess', 'audio ⇄ Opus', 'data', 'r.3', 'l.08', both=True, lw=88)
    s.edge('vision', 'sess', 'vision.frame', 'data', 'r.5', 'l.3', lw=76)
    s.edge('act', 'sess', 'tool req ⇄ result', 'ctrl', 'r.5', 'l.55', both=True, lw=100)
    s.edge('sess', 'char', 'emotion·gesture·text', 'ev', 'l.75', 'r.5', lw=118, ld=0)
    # REST
    s.node('api', 800, 610, 170, 80, 'REST API /v1', ['identity · tenancy', 'memory · plugins'], 'cloud', tag='role=api')
    s.edge('ui', 'api', 'HTTPS REST', 'data', 'r.5', 'l.5', via=[(660, 624), (660, 650)], lp=.5, lw=80)
    # cloud
    s.node('gw', 800, 140, 170, 413, 'Realtime Gateway', ['auth · entitlement', 'session · turn', 'media relay', 'resume · limits', '', 'role=realtime', 'Fastify + ws'], 'cloud', tag='D10')
    s.edge('sess', 'gw', 'WSS', 'ctrl', 'r.28', 'l.28', both=True, lw=40, lp=.5)
    s.node('orch', 1020, 235, 200, 130, 'Orchestrator', ['context assembly', 'catalogue ∩ policy ∩ risk', 'claim guard · usage', 'memory proposals'], 'cloud', tag='D24')
    s.edge('gw', 'orch', 'Turn', 'data', 'r.45', 'l.5', lw=40)
    s.zone(1255, 100, 315, 300, 'Inference service (Python · GPU · private)', 'plain', 11)
    s.node('p1', 1275, 128, 275, 70, 'mock', ['scripted · conformance fixtures'], 'cloud')
    s.node('p2', 1275, 214, 275, 70, 'cascade', ['ASR → LLM → TTS (fallback path)'], 'cloud')
    s.node('p3', 1275, 300, 275, 70, 'minicpm-o  (M8, separate)', ['InferenceProvider adapter only'], 'model', tag='D16')
    s.edge('orch', 'p1', 'InferenceRequest/Event', 'data', 'r.2', 'l.5', mid=1245, lw=128)
    s.edge('orch', 'p2', None, 'data', 'r.5', 'l.5', mid=1245)
    s.edge('orch', 'p3', None, 'data', 'r.8', 'l.5', mid=1245)
    s.node('mem', 1020, 410, 200, 90, 'Memory service', ['pgvector + FTS', 'proposals · export · erase'], 'cloud')
    s.edge('orch', 'mem', 'query · propose', 'data', 'b.5', 't.5', both=True, lw=100)
    s.node('tb', 1275, 420, 275, 80, 'Cloud tool broker', ['catalogue · policy', 'plugin invoke (HTTPS, signed)'], 'cloud')
    s.edge('orch', 'tb', 'tool.call', 'ctrl', 'r.9', 'l.5', via=[(1232, 351), (1232, 460)], lw=62)
    s.node('plug', 1275, 520, 275, 62, 'Plugin services', ['3rd-party / org-hosted'], 'ext', tag='D15')
    s.edge('tb', 'plug', 'POST /invoke', 'perm', 'b.5', 't.5', lw=76)
    s.node('pg', 1020, 610, 200, 80, 'PostgreSQL 16', ['RLS · pgvector · pg-boss', 'audit append-only'], 'store', tag='D11')
    s.edge('mem', 'pg', 'SQL under RLS', 'data', 'b.5', 't.5', lw=92)
    s.edge('api', 'pg', None, 'data', 'r.5', 'l.5')
    s.node('wk', 1275, 610, 275, 80, 'Worker (pg-boss)', ['embed · summarise · retention', 'billing sync · notifications'], 'cloud', tag='role=worker')
    s.edge('wk', 'pg', None, 'data', 'l.5', 'r.5')
    s.node('idp', 800, 745, 170, 80, 'Supabase Auth', ['OIDC JWT · JWKS'], 'ext', tag='D13')
    s.edge('idp', 'api', 'JWKS', 'perm', 't.5', 'b.5', lw=40, lp=.5)
    s.node('bill', 1000, 745, 200, 80, 'Stripe · Play Billing', ['webhooks · RTDN'], 'ext', tag='D18')
    s.edge('bill', 'api', 'webhooks', 'async', 't.5', 'b.8', via=[(1100, 715), (936, 715)], lw=64)
    s.node('fcm', 1230, 745, 150, 80, 'FCM · Email', ['push · invites'], 'ext')
    s.node('obj', 1410, 745, 150, 80, 'Object storage', ['S3 API · org keys'], 'ext')
    s.edge('wk', 'fcm', None, 'async', 'b.15', 't.5')
    s.edge('wk', 'obj', None, 'async', 'b.9', 't.5')
    s.note(48, 706, 690, ['1  Model proposes, device disposes: tool calls pass the broker (VB-10).',
                          '2  Vision never implies control. Screen text is untrusted data.',
                          '3  No audio leaves the device before the wake word (VB-08).',
                          '4  Character events: voice, vision, actions and cloud all feed VB-06.'], 'Hard rules')
    return s


def vb02():
    s = Sheet('VB-02', 'Character System Architecture', 'The real VALIS asset is frozen; a derived runtime asset feeds a layered runtime on Filament.', 'docs/02 · F1–F10 findings')
    s.zone(30, 92, 480, 612, 'Source asset · renders from VALIS_rigged.glb', 'ink')
    ims = [('ta_front', 'front', 52, 118), ('ta_34', '¾ right', 272, 118), ('ta_side', 'side', 52, 372), ('ta_back', 'back', 272, 372)]
    for n, lab, x, y in ims:
        s.mid.append(img(f'assets/char/{n}.webp', x, y, 176, 233))
        s.text(x + 88, y + 247, lab, 11, 600, anchor='middle', mono=True)
    s.note(48, 640, 444, ['cobalt shell · near-black face · pearl ear linings · chest "V"'], None)
    s.note(30, 722, 480, ['500,000 tris · 286,174 verts · 4096² + 2048² textures · 37 MiB',
                          '27 joints · 26 face morphs · 6 viseme morphs · 48 clips @30 fps',
                          'F2 too heavy for overlay → derived runtime asset (≤45k tris)',
                          'F4 every clip keys all 29 nodes → masks + custom blender',
                          'F9 head shell separates in droop/bow/expression_shy (TD fix)'], 'Measured facts')
    s.zone(530, 92, 1050, 218, 'Build time (tools/asset-pipeline)', 'plain')
    s.node('src', 550, 130, 190, 90, 'VALIS_rigged.glb', ['Git LFS · frozen', 'never edited'], 'store')
    s.node('pipe', 790, 130, 220, 90, 'Asset pipeline', ['T-ASSET: decimate, bake', 'face split, KTX2/ETC2'], 'cloud', tag='M0')
    s.node('rt', 1060, 130, 230, 90, 'VALIS_runtime.glb', ['≤45k tris · ≤12 MB', 'face primitive owns morphs'], 'ok')
    s.node('bake', 1060, 232, 230, 62, 'valis_anim.v1', ['masks · groups · loop flags'], 'ok')
    s.node('qa', 1340, 130, 220, 90, 'Golden renders', ['ΔE ≤ 6 · IoU ≥ 0.97', 'TD identity sign-off'], 'pearl')
    s.edge('src', 'pipe', None, 'data'); s.edge('pipe', 'rt', None, 'data'); s.edge('rt', 'qa', 'verify', 'ctrl', 'r', 'l', lw=48)
    s.edge('pipe', 'bake', 'T-BAKE', 'data', 'b.7', 'l.5', via=[(944, 263)], lw=54)
    s.zone(530, 328, 1050, 376, 'Runtime on device (core/character)', 'dev')
    s.node('ldr', 550, 366, 170, 84, 'AssetLoader', ['gltfio ubershader', 'IO thread'], 'dev')
    s.node('bind', 760, 366, 190, 84, 'RigBinder', ['27 joints + 32 morphs', 'by name · hard-fail'], 'dev')
    s.node('apply', 990, 366, 190, 84, 'PoseApplier', ['setTransform + bones', 'setMorphWeights'], 'dev', tag='D03')
    s.node('rend', 1220, 366, 170, 84, 'Filament Renderer', ['translucent · IBL+key'], 'dev', tag='D01')
    s.node('surf', 1420, 366, 140, 84, 'Overlay surface', ['SurfaceView'], 'dev')
    s.edge('ldr', 'bind', None, 'data'); s.edge('bind', 'apply', None, 'data'); s.edge('apply', 'rend', None, 'data'); s.edge('rend', 'surf', None, 'data')
    s.node('evt', 550, 560, 170, 90, 'CharacterEvent', ['voice · vision · tool', 'cloud · touch · env'], 'pearl')
    s.node('beh', 760, 560, 190, 90, 'BehaviourEngine', ['utility selector', 'scheduler · cooldowns'], 'dev', tag='D04')
    s.node('pose', 990, 560, 190, 90, 'PoseRuntime', ['layers L0–L6 · masks', 'blend-loop · visemes'], 'dev')
    s.node('fsm', 1220, 560, 170, 90, 'State machine', ['10 states', 'serialised transitions'], 'dev')
    s.node('clip', 1420, 560, 140, 90, 'clip data', ['valis_anim.v1'], 'ok')
    s.edge('evt', 'beh', None, 'ev'); s.edge('beh', 'pose', 'commands', 'ctrl', lw=70); s.edge('pose', 'apply', 'pose', 'ctrl', 'r.5', 'b.5', via=[(1180, 605), (1085, 605)], lw=1, ) if False else None
    s.edge('pose', 'apply', 'pose · morphs', 'ctrl', 't.5', 'b.5', lw=84)
    s.edge('fsm', 'beh', None, 'ev', 'l.3', 'r.3', via=[(1205, 580), (1205, 580)]) if False else None
    s.edge('fsm', 'pose', 'state', 'ev', 'l.5', 'r.5', lw=40)
    s.edge('clip', 'fsm', None, 'data', 'l.5', 'r.5') if False else None
    s.edge('clip', 'rend', None, 'data', 't.5', 'b.5', via=[(1490, 600), (1490, 450)]) if False else None
    s.note(1220, 664, 340, ['Renderer facade = existing CharacterRenderer', 'CharacterRuntime sits above it (doc 02 §5)'], None)
    return s


def vb03():
    s = Sheet('VB-03', '3D Rendering Pipeline', 'Asset → bound rig → per-frame pose → Filament → transparent overlay surface. One owner thread for GL.', 'docs/02 §2 · S1 spike validates D01/D03')
    lanes = [('IO thread · load', 100, 118), ('Behaviour coroutine · 5 Hz', 232, 118), ('Render thread', 364, 250), ('Main thread · window + touch', 628, 118)]
    for lab, y, h in lanes:
        s.zone(30, y, 1550, h, lab, 'dev' if 'Render' in lab else 'plain')
    s.node('a1', 60, 132, 190, 76, 'Read assets', ['VALIS_runtime.glb', 'valis_anim.v1'], 'store')
    s.node('a2', 290, 132, 190, 76, 'gltfio load', ['ubershader · no JIT', 'textures KTX2/ETC2'], 'dev')
    s.node('a3', 520, 132, 190, 76, 'Create entities', ['27 joint entities', 'face + body + mouth'], 'dev')
    s.edge('a1', 'a2', None, 'data'); s.edge('a2', 'a3', None, 'data')
    s.node('b1', 60, 266, 200, 76, 'Context vector', ['state · energy · mood', 'battery · thermal · quiet'], 'pearl')
    s.node('b2', 300, 266, 200, 76, 'Utility selector', ['filter → weight → sample'], 'dev')
    s.node('b3', 540, 266, 200, 76, 'PoseCommand', ['clip · mask · weight', 'immutable · queued'], 'ctrl' if False else 'dev')
    s.edge('b1', 'b2', None, 'data'); s.edge('b2', 'b3', None, 'data')
    s.node('r0', 60, 408, 170, 90, 'Bind rig', ['names → entities', 'RigMismatch → degrade'], 'dev')
    s.node('r1', 270, 408, 170, 90, 'FrameClock', ['Choreographer', 'throttled skip-vsync'], 'dev')
    s.node('r2', 480, 408, 180, 90, 'PoseRuntime.evaluate', ['L0 base → L1 gesture', '→ L2 look → L3 face', '→ L4 speech → L5 sec.'], 'dev')
    s.node('r3', 700, 408, 190, 90, 'PoseApplier', ['setTransform(joints)', 'updateBoneMatrices()', 'setMorphWeights()'], 'dev')
    s.node('r4', 930, 408, 190, 90, 'Renderer.render', ['View: TRANSLUCENT', 'MSAA4/FXAA · neutral', 'IBL 256² + key light'], 'dev')
    s.node('r5', 1160, 408, 180, 90, 'SwapChain', ['alpha surface', 'RenderStats → adapt'], 'dev')
    s.node('r6', 1380, 408, 170, 90, 'Composited', ['SurfaceFlinger over', 'foreground app'], 'ext')
    for a, b in [('r0', 'r1'), ('r1', 'r2'), ('r2', 'r3'), ('r3', 'r4'), ('r4', 'r5'), ('r5', 'r6')]:
        s.edge(a, b, None, 'data')
    s.edge('a3', 'r0', 'entities', 'ctrl', 'r.5', 't.9', via=[(790, 170), (790, 388), (213, 388)], lw=58, lp=.8)
    s.edge('b3', 'r2', 'queue', 'ctrl', 'b.5', 't.5', lw=44)
    s.node('r7', 270, 530, 380, 70, 'Degradation ladder (Frame time > 33 ms for 3 s)', ['res scale 1.0→0.75 · MSAA→FXAA · IDLE fps · static pose'], 'perm')
    s.node('r8', 700, 530, 420, 70, 'Thermal / battery policy', ['MODERATE: cap 15 fps · SEVERE: pause · saver: no big motions'], 'perm')
    s.node('m1', 60, 662, 200, 76, 'Overlay window', ['TYPE_APPLICATION_OVERLAY', 'tight box · 200×270 dp'], 'dev')
    s.node('m2', 300, 662, 220, 76, 'surfaceCreated/Destroyed', ['SwapChain lifecycle'], 'dev')
    s.node('m3', 560, 662, 200, 76, 'Touch', ['drag · tap · long-press', '→ CharacterEvent'], 'dev')
    s.node('m4', 800, 662, 230, 76, 'Dormant policy', ['120 s warm · then free', 'TRIM_MEMORY → drop engine'], 'perm')
    s.edge('m2', 'r5', 'surface', 'ctrl', 't.5', 'b.5', via=[(410, 614), (1250, 614)], lw=56) if False else None
    s.edge('m2', 'r5', 'surface', 'ctrl', 't.9', 'b.3', via=[(498, 620), (1214, 620)], lw=56)
    s.note(1060, 662, 500, ['Budgets (mid-range ref device): CPU ≤ 8% idle · GPU mem ≤ 80 MB', 'RSS ≤ 150 MB · cold load ≤ 1.5 s · warm summon ≤ 400 ms'], 'Targets')
    return s


def vb04():
    s = Sheet('VB-04', 'Rig & Animation Architecture', 'Clips are primitives: masked, sampled or layered. Joints and morph names below are verified from the GLB.', 'docs/04 §1–3 · clip_inventory.csv')
    s.zone(30, 92, 470, 700, 'Rig overlay · 27 skin joints (rest pose)', 'ink')
    ox, oy, sc = 50, 112, 1.0
    s.mid.append(img('assets/char/ta_front.webp', ox, oy, 420, 557))
    order = ['root', 'hips', 'spine', 'chest', 'neck', 'head', 'shoulder_L', 'upperArm_L', 'lowerArm_L', 'hand_L', 'shoulder_R', 'upperArm_R', 'lowerArm_R', 'hand_R', 'upperLeg_L', 'lowerLeg_L', 'foot_L', 'upperLeg_R', 'lowerLeg_R', 'foot_R', 'tail_1', 'tail_2', 'tail_3', 'ear_1_L', 'ear_2_L', 'ear_1_R', 'ear_2_R']
    num = {n: i + 1 for i, n in enumerate(order)}
    for n, d in J.items():
        if d['parent'] and d['parent'] in J:
            p = J[d['parent']]
            s.front.append(f'<line x1="{ox+p["x"]:.1f}" y1="{oy+p["y"]:.1f}" x2="{ox+d["x"]:.1f}" y2="{oy+d["y"]:.1f}" stroke="{CO}" stroke-width="1.6" opacity=".85"/>')
    for n, d in J.items():
        x, y = ox + d['x'], oy + d['y']
        s.front.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="#fff" stroke="{INK}" stroke-width="1.2"/><text x="{x:.1f}" y="{y+3.4:.1f}" font-family="{MONO}" font-size="8.6" font-weight="700" fill="{INK}" text-anchor="middle">{num[n]}</text>')
    s.note(30, 802, 470, ['1 root 2 hips 3 spine 4 chest 5 neck 6 head 7-10 arm L (shoulder→hand)', '11-14 arm R · 15-17 leg L · 18-20 leg R · 21-23 tail', '24-27 ears (1_L 2_L 1_R 2_R)', 'No jaw · no eye bones: mouth and gaze are morph-only.'], 'Joint key')
    s.zone(520, 92, 520, 790, 'Pose runtime layers (evaluated each frame)', 'dev')
    L = [('L6 Locomotion', 'window velocity → posture_lean_* pose blend · hover bob', 'pearl'),
         ('L5 Secondary', 'spring chains: ears (4) · tail (3) · only if unmasked', 'dev'),
         ('L4 Speech', 'visemes aa oh ou ee ih fv · amplitude fallback', 'dev'),
         ('L3 Face (morph-only)', 'emotion pose · blink · gaze · brows · mouth', 'dev'),
         ('L2 Look (procedural)', 'neck/head solver ±35° · eye morphs · saccades', 'dev'),
         ('L1 Gesture (masked clips)', 'wave · nod · shrug · tilt · bow · reach · celebrate', 'dev'),
         ('L0 Base (full body)', 'idle (blend-loop) · weight_shift · sit · sleep · posture', 'model')]
    y = 124
    for t, d, k in L:
        s.node('l' + t[:2], 540, y, 480, 78, t, [d], k)
        y += 92
    s.text(780, 780, '▲ later layers override or add inside their masks', 11, 400, MUTE, 'middle', True)
    s.note(540, 800, 480, ['Layered: clip float and baked blink/gaze are dropped'], None)
    s.zone(1060, 92, 520, 790, 'Clip taxonomy (48 verified names)', 'plain')
    groups = [('Base loops / holds', 'idle · weight_shift · sit_swing_legs · posture_crouch · posture_lean_{left,right,forward,back}'),
              ('Face poses (loop-safe)', 'expression_{happy,excited,surprised,curious,sleepy,sad,angry,shy,wink}'),
              ('Gestures', 'wave_left/right · nod · shake_head · tilt_head · shrug · bow · wiggle · flap · reach_ik · peek · look_around · look_targets'),
              ('Reactions', 'startle · celebrate · jump · spin · turn_left'),
              ('Fidgets', 'stretch · yawn · tail_wag · ear_twitch · dance_{bounce,sway,twist}'),
              ('Transitions / speech', 'sit_down · stand_up · talk'),
              ('Reference only', 'multi_sit_swing_look · living_idle_showcase (45 s)')]
    y = 124
    for t, d in groups:
        words = d.split(' ')
        lines, cur = [], ''
        for w_ in words:
            if len(cur) + len(w_) + 1 > 52:
                lines.append(cur); cur = w_
            else:
                cur = (cur + ' ' + w_).strip()
        lines.append(cur)
        h = 36 + 14 * len(lines)
        s.node('c' + t[:3], 1080, y, 480, h, t, lines, 'pearl')
        y += h + 12
    s.node('bk', 1080, y + 6, 480, 98, 'Bake rules (valis_anim.v1)', ['30 fps · quantised quats · scale kept only if ≥0.02', 'morph keys split: BLINK GAZE BROW LID MOUTH VISEME', 'loopable if end≈start (≤5°,1 cm): only 14 of 48', 'meaningfulMask = joints >3° minus legs/ears/tail'], 'ok')
    return s


def vb05():
    s = Sheet('VB-05', 'Autonomous Behaviour Engine', 'Spontaneous, not random: weighted utility with cooldowns, caps, mood and repetition memory.', 'docs/04 §4–5')
    s.zone(30, 92, 330, 788, 'Inputs · context vector (5 Hz + events)', 'plain')
    ins = [('State + dialogue', 'FSM state · speaking/listening'), ('Time', 'idle seconds · since speech'), ('Energy', 'decays idle · recovers on use'), ('Emotion', 'label + intensity · decays'),
           ('Device', 'battery saver · charging · thermal'), ('Environment', 'rotation · quiet hours · screen'), ('Settings', 'autonomy Calm/Balanced/Playful'), ('Opt-in signals', 'notification · music · app category')]
    y = 124
    for t, d in ins:
        s.node('i' + t[:3], 50, y, 290, 74, t, [d], 'pearl')
        y += 92
    s.zone(390, 92, 560, 788, 'Selector', 'dev')
    s.node('f', 410, 130, 520, 90, '1  Candidate filter', ['state-allowed · priority ≥ current · not cooling down', 'hourly cap not exceeded · mask free · asset enabled (F9)'], 'dev')
    s.node('w', 410, 262, 520, 112, '2  Effective weight', ['w × moodAffinity × timeGrowth', '× repetition (0.15 last 3, 0.5 last 8, else 1)', '× cooldownGate × rateGate  · boredom growth ≤ ×6'], 'dev')
    s.node('p', 410, 416, 520, 90, '3  Weighted sample', ['seeded RNG (reproducible tests)', 'never same clip twice · same category ≤ 2 in a row'], 'dev')
    s.node('sch', 410, 548, 520, 90, 'Scheduler', ['spontaneous delay ~ lognormal: median 12 s (Balanced)', '20 s Calm · 8 s Playful · min 4 s · ×3 on saver'], 'dev')
    s.node('dis', 410, 680, 520, 96, 'Suppressors', ['quiet hours · THINKING/SPEAKING/ACTING/LISTENING', 'sleeping (only ambient) · thermal SEVERE · low-power'], 'perm')
    s.edge('iEmo', 'f', 'context', 'ev', 'r.5', 'l.5', via=[(365, 437), (365, 175)], lw=60, lp=.3)
    s.edge('f', 'w', None, 'data', 'b.5', 't.5'); s.edge('w', 'p', None, 'data', 'b.5', 't.5'); s.edge('sch', 'f', 'fire', 'ctrl', 'l.5', 'l.5', via=[(396, 593), (396, 175)], lw=30) if False else None
    s.edge('sch', 'p', 'fire', 'ctrl', 'r.5', 'r.5', via=[(944, 593), (944, 461)], lw=34)
    s.edge('dis', 'sch', 'gate', 'perm', 't.5', 'b.5', lw=36)
    s.edge('Time' if False else 'iTim', 'f', None, 'ev', 'r.5', 'l.5', via=[(375, 253), (375, 175)]) if False else None
    s.zone(980, 92, 600, 788, 'Outputs & companions', 'dev')
    s.node('beh', 1000, 130, 560, 104, 'Behaviour catalogue (≈30 entries)', ['id · clips/mask · states · weight · cooldown · max/h', 'idle.* · react.* · dialogue.* · error.* · sleep.*'], 'ink')
    s.node('pc', 1000, 276, 560, 76, 'PoseCommand → PoseRuntime', ['masked clip / pose slice / procedural target'], 'dev')
    s.node('emo', 1000, 394, 270, 112, 'Emotion model', ['10 labels · intensity', 'half-life 8 s (sleepy 20 s)', 'hints from model = requests'], 'dev')
    s.node('look', 1290, 394, 270, 112, 'Look-at solver', ['user > screen ROI > touch', '> idle wander · 70% head', '30% eye morphs'], 'dev')
    s.node('prio', 1000, 548, 560, 150, 'Priority ladder', ['P0 system: startle · error · forced sleep', 'P1 dialogue: summon · listen · think · speak · act', 'P2 reactive: touch · charger · low battery', 'P3 spontaneous: stretch · yawn · look_around …', 'P4 ambient: hover · blink · ears/tail'], 'perm')
    s.node('sl', 1000, 740, 560, 112, 'Sleep rule', ['energy < 0.15 or idle > sleepAfter (180 s default)', 'yawn → sit_down → expression_sleepy hold', 'wake: wake word · touch · stand_up → stretch'], 'dev')
    s.edge('p', 'beh', 'pick', 'ctrl', 'r.25', 'l.8', via=[(965, 438), (965, 213)], lw=34) if False else None
    s.edge('p', 'beh', 'pick', 'ctrl', 'r.2', 'l.5', via=[(960, 434), (960, 182)], lw=34)
    s.edge('beh', 'pc', None, 'ctrl', 'b.5', 't.5')
    return s


def vb06():
    s = Sheet('VB-06', 'Character State Machine', 'Ten states; one at a time; transitions serialised and logged. P0 reactions can interrupt anything.', 'docs/04 §7 · adds SUMMONED, ERROR')
    st = lambda i, x, y, t, l, k='dev', w=200: s.node(i, x, y, w, 74, t, l, k)
    st('DORMANT', 40, 420, 'DORMANT', ['overlay detached', 'wake word armed'], 'ext')
    st('SUMMONED', 300, 420, 'SUMMONED', ['place window', 'wave_right / peek'], 'dev')
    st('IDLE', 560, 420, 'IDLE', ['idle (blend-loop)', 'spontaneous behaviours'], 'model')
    st('LISTENING', 820, 420, 'LISTENING', ['tilt_head + curious', 'gaze to user'], 'dev')
    st('THINKING', 1080, 420, 'THINKING', ['look_targets slice', 'curious α0.4'], 'dev')
    st('SPEAKING', 1340, 420, 'SPEAKING', ['visemes + talk body', 'beat gestures'], 'dev')
    st('ACTING', 1210, 230, 'ACTING', ['reach_ik toward target', 'confirm card open'], 'perm')
    st('SLEEPING', 300, 230, 'SLEEPING', ['sit_down · sleepy hold', 'window may tuck'], 'dev')
    st('INTERRUPTED', 1080, 640, 'INTERRUPTED', ['startle(0.5) · P0', '≤ 0.6 s'], 'bad')
    st('ERROR', 560, 640, 'ERROR', ['shrug + sad · 2.5 s', 'turn cancelled'], 'bad')
    e = s.edge
    e('DORMANT', 'SUMMONED', 'wake · tile · tap', 'ctrl', lw=96)
    e('SUMMONED', 'IDLE', 'no turn', 'ctrl', lw=52)
    e('SUMMONED', 'LISTENING', 'turn open', 'ctrl', 'b.3', 'b.3', via=[(360, 520), (880, 520)], lp=.5, lw=64)
    e('IDLE', 'LISTENING', 'wake · tap', 'ctrl', lw=62)
    e('LISTENING', 'THINKING', 'end of speech', 'ctrl', lw=84)
    e('THINKING', 'SPEAKING', 'first audio', 'ctrl', lw=70)
    e('THINKING', 'ACTING', 'tool.request', 'ctrl', 't.5', 'l.5', lw=76, lp=.5)
    e('ACTING', 'THINKING', 'verified result', 'ok', 'b.2', 't.8', lw=92)
    e('ACTING', 'SPEAKING', 'model resumes', 'ctrl', 'r.5', 't.35', lw=86)
    e('SPEAKING', 'IDLE', 'ended · no follow-up', 'ctrl', 't.5', 't.5', via=[(1440, 175), (660, 175)], lw=124)
    e('SPEAKING', 'LISTENING', 'follow-up 4 s', 'ctrl', 'b.15', 'b.7', via=[(1370, 552), (960, 552)], lw=88) if False else None
    e('IDLE', 'SLEEPING', 'energy · timeout', 'async', 't.1', 'r.5', lw=96, lp=.5)
    e('SLEEPING', 'SUMMONED', 'wake · touch', 'ctrl', 'b.5', 't.5', lw=76)
    e('SLEEPING', 'DORMANT', 'dismiss', 'async', 'l.5', 't.5', lw=56)
    e('THINKING', 'INTERRUPTED', 'user speech', 'deny', 'b.5', 't.5', lw=76)
    e('SPEAKING', 'INTERRUPTED', 'barge-in · tap', 'deny', 'b.3', 'r.5', lw=84)
    e('INTERRUPTED', 'LISTENING', 'after startle ≤ 0.4 s', 'ctrl', 'l.5', 'b.8', lw=118)
    e('THINKING', 'ERROR', 'timeout · provider error', 'deny', 'b.1', 't.5', via=[(1100, 600), (660, 600)], lw=140, lp=.4)
    e('ERROR', 'IDLE', 'reaction done', 'ctrl', 't.2', 'b.2', lw=84)
    s.note(40, 120, 640, ['Invariants:', ' • exactly one state; transitions serialised on one dispatcher',
                          ' • every transition logged with cause · INTERRUPTED never > 0.6 s',
                          ' • ERROR from THINKING/ACTING cancels the turn server-side (turn.cancel)',
                          ' • any state + Dismissed → DORMANT (250 ms scale-out)',
                          ' • any state + Error(kind) → ERROR (non-fatal) · fatal renderer loss → DORMANT'], None)
    s.note(40, 650, 470, ['SPEAKING → LISTENING (follow-up window 4 s) when allowed.', 'SPEAKING → IDLE when no follow-up. LISTENING → IDLE after 6 s of silence.', 'ACTING failed/denied → THINKING (model is told; short shrug).'], 'Additional transitions')
    return s
