C='assets/char/'
CSS="""
:root{--co:#1B55FF;--co7:#123BB8;--co1:#E3EAFF;--ink:#0E0E19;--i7:#2B2D45;--i5:#5A5D7A;--i4:#8A8DA6;--p5:#F6F6FB;--p1:#ECEDF6;--p2:#E3E4F1;--am:#C77700;--am1:#FFF1D6;--rd:#C62F2F;--rd1:#FFE3E3;--gr:#12805C;--gr1:#DDF5EA}
*{box-sizing:border-box}body{margin:0;background:#D9DAE6;font-family:'DM Sans',system-ui,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.top{padding:22px 16px 6px;max-width:900px;margin:auto}.top h1{margin:0;font-size:22px}.top p{margin:4px 0 0;color:var(--i5);font-size:14px;line-height:1.45}
.wrap{display:flex;flex-wrap:wrap;gap:28px;justify-content:center;padding:18px 12px 60px}
.fig{width:390px;max-width:100%}.cap{font:600 12px 'DM Mono',monospace;color:var(--i5);margin:0 0 8px 4px}
.ph{width:390px;max-width:100%;background:var(--p5);border-radius:32px;border:6px solid var(--ink);overflow:hidden;display:flex;flex-direction:column;min-height:760px;box-shadow:0 10px 30px #0e0e1933}
.sb{display:flex;justify-content:space-between;padding:12px 22px 4px;font-size:12px;font-weight:700;color:var(--ink)}
.bar{display:flex;align-items:center;gap:10px;padding:10px 20px}.bar h2{margin:0;font-size:20px;flex:1}
.chip{background:var(--p2);border-radius:999px;padding:6px 12px;font-size:12px;font-weight:700;color:var(--i7);white-space:nowrap}
.av{width:32px;height:32px;border-radius:50%;background:var(--ink);color:#fff;display:grid;place-items:center;font-size:12px;font-weight:700;flex:none}
.body{flex:1;padding:6px 20px 20px;display:flex;flex-direction:column;gap:14px}
.card{background:#fff;border-radius:20px;padding:16px}.card.p{background:var(--p1)}.card.d{background:var(--ink);color:#fff}
h3{margin:0 0 4px;font-size:16px}.s{font-size:14px;color:var(--i5);line-height:1.4}.d .s{color:#B9BBD3}.xs{font-size:12px;color:var(--i4)}
.row{display:flex;align-items:center;gap:12px;padding:12px 0;border-top:1px solid var(--p2);min-height:56px}.row:first-child{border-top:0}
.row .t{flex:1;min-width:0}.row .t b{display:block;font-size:15px}.row .t span{font-size:13px;color:var(--i5);line-height:1.35;display:block}
.peb{width:40px;height:40px;border-radius:50%;background:var(--co1);display:grid;place-items:center;flex:none;font-size:17px;color:var(--co)}
.peb.a{background:var(--am1);color:var(--am)}.peb.g{background:var(--gr1);color:var(--gr)}.peb.r{background:var(--rd1);color:var(--rd)}.peb.k{background:var(--p2);color:var(--i7)}
.pill{font-size:12px;font-weight:700;border-radius:999px;padding:5px 10px;white-space:nowrap;flex:none}
.pill.g{background:var(--gr1);color:var(--gr)}.pill.a{background:var(--am1);color:var(--am)}.pill.r{background:var(--rd1);color:var(--rd)}.pill.b{background:var(--co1);color:var(--co7)}.pill.k{background:var(--p2);color:var(--i7)}
.tg{width:48px;height:28px;border-radius:999px;background:var(--p2);position:relative;flex:none}.tg:after{content:"";position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;background:#fff}
.tg.on{background:var(--co)}.tg.on:after{left:23px}
.btn{display:block;text-align:center;border-radius:14px;padding:15px;font-weight:700;font-size:16px;min-height:48px}
.btn.p{background:var(--co);color:#fff}.btn.s2{background:var(--co1);color:var(--co7)}.btn.o{background:#fff;color:var(--ink);border:2px solid var(--p2)}.btn.r{background:var(--rd1);color:var(--rd)}
.btns{display:flex;gap:10px}.btns .btn{flex:1}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--co);margin-right:8px;vertical-align:middle}
.disc{width:200px;height:200px;border-radius:50%;background:var(--ink);display:grid;place-items:center;margin:0 auto;overflow:hidden}.disc img{width:170px;height:auto;display:block;margin-top:14px}
.disc.sm{width:112px;height:112px}.disc.sm img{width:96px;margin-top:8px}
.nav{display:flex;border-top:1px solid var(--p2);background:#fff;padding:8px 8px 14px}.nav div{flex:1;text-align:center;font-size:11px;font-weight:700;color:var(--i4);display:flex;flex-direction:column;align-items:center;gap:3px;min-height:48px;justify-content:center}.nav div i{font-style:normal;font-size:18px}.nav div.on{color:var(--co)}
.seg{display:flex;background:var(--p2);border-radius:14px;padding:4px;gap:4px}.seg div{flex:1;text-align:center;padding:10px 4px;border-radius:11px;font-size:13px;font-weight:700;color:var(--i5)}.seg div.on{background:#fff;color:var(--ink)}
.chips{display:flex;gap:8px;flex-wrap:wrap}.chips .chip.on{background:var(--ink);color:#fff}
.meter{height:10px;border-radius:999px;background:var(--p2);overflow:hidden;position:relative}.meter i{display:block;height:100%;background:var(--co);border-radius:999px}.meter i.w{background:var(--am)}
.sl{height:8px;border-radius:999px;background:var(--p2);position:relative;margin:16px 10px}.sl i{position:absolute;left:0;top:0;bottom:0;background:var(--co);border-radius:999px}.sl b{position:absolute;top:-8px;width:24px;height:24px;border-radius:50%;background:#fff;border:3px solid var(--co);margin-left:-12px}
.lbls{display:flex;justify-content:space-between;font-size:12px;color:var(--i5);font-weight:700}
.ban{border-radius:16px;padding:14px;font-size:14px;line-height:1.4;display:flex;gap:10px}.ban.a{background:var(--am1);color:#6b4100}.ban.r{background:var(--rd1);color:#7d1c1c}.ban.b{background:var(--co1);color:var(--co7)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.tile{background:#fff;border-radius:16px;padding:12px}.tile b{display:block;font-size:24px;font-variant-numeric:tabular-nums}.tile span{font-size:12px;color:var(--i5)}
.day{font:700 12px 'DM Mono',monospace;color:var(--i5);letter-spacing:.5px;margin:4px 0 -4px}
.overlay-bg{background:linear-gradient(#cfd2e6,#e4e6f2);flex:1;padding:20px;display:flex;flex-direction:column;gap:14px;position:relative}
.fake{height:12px;border-radius:6px;background:#bfc2d8}
.pad{height:8px}
.mem{display:flex;gap:10px;align-items:flex-start;padding:12px 0;border-top:1px solid var(--p2)}.mem:first-child{border-top:0}
.av2{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;color:#fff;font-weight:700;font-size:13px;flex:none}
"""
def ph(title,inner,nav=None,bar=True,wsp=True,extra=''):
    n=''
    if nav is not None:
        items=[('Home','⌂'),('Memory','◔'),('Activity','≡'),('Control','⚙')]
        n='<div class="nav">'+''.join('<div class="%s"><i>%s</i>%s</div>'%('on' if i==nav else '',g,t) for i,(t,g) in enumerate(items))+'</div>'
    b='<div class="bar"><h2>%s</h2>%s<div class="av">PU</div></div>'%(title,'<span class="chip">Personal ▾</span>' if wsp else '') if bar else ''
    return '<div class="ph"><div class="sb"><span>9:41</span><span>5G ▮▮▮</span></div>%s<div class="body">%s</div>%s</div>'%(b,inner,n)
def row(ic,t,s,right='',k=''):
    return '<div class="row"><div class="peb %s">%s</div><div class="t"><b>%s</b><span>%s</span></div>%s</div>'%(k,ic,t,s,right)
def pill(t,k='k'): return '<span class="pill %s">%s</span>'%(k,t)
def tg(on=True): return '<div class="tg%s"></div>'%(' on' if on else '')

S=[]
def add(n,title,html): S.append((n,title,html))

add(1,'Welcome',ph('',f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:22px;text-align:center">
<div class="disc"><img src="{C}ta_front.webp" alt="VALIS"></div>
<div><div style="font-size:40px;font-weight:700;letter-spacing:-1px">VALIS</div><p class="s" style="font-size:16px;margin:8px 10px 0">Your companion lives on your screen. Say “Yo, VALIS”, and it helps.</p></div></div>
<div class="btn p">Set up VALIS</div><div class="btn o">How VALIS handles your data</div>''',bar=False))
add(2,'Home',ph('Home',f'''<div class="card d" style="display:flex;gap:14px;align-items:center"><div class="disc sm"><img src="{C}idle.webp" alt=""></div><div><span class="pill b" style="background:#1B55FF33;color:#bcd0ff"><span class="dot" style="width:8px;height:8px;margin-right:6px"></span>Ready</span><h3 style="margin-top:10px;font-size:18px">Listening for “Yo, VALIS”</h3><div class="s">Nothing leaves your phone until then.</div></div></div>
<div class="btns"><div class="btn s2">Summon</div><div class="btn o">Sleep</div><div class="btn o">Mic</div></div>
<div class="ban a"><span>⚠</span><span><b>Accessibility was turned off.</b><br>VALIS can’t tap for you until it’s back on.</span></div>
<div class="day">TODAY</div><div class="grid3"><div class="tile"><b>7</b><span>chats</span></div><div class="tile"><b>4</b><span>verified actions</span></div><div class="tile"><b>12m</b><span>voice</span></div></div>
<div class="card">{row('↗','Opened Settings','2 min ago',pill('Verified','g'),'g')}{row('☎','Call Mum','Declined by you',pill('Declined','r'),'r')}{row('♪','Played focus mix','Yesterday',pill('Unverified','a'),'a')}</div>''',nav=0))
add(3,'Permissions Center',ph('Permissions','''<div class="card p"><h3 style="font-size:28px;letter-spacing:-.5px">5 of 7 ready</h3><div class="meter" style="margin-top:10px"><i style="width:71%"></i></div><div class="s" style="margin-top:8px">Only turn on what you want VALIS to do.</div></div>
<div class="card">'''+row('◉','Overlay','Show VALIS over other apps',pill('On','g'),'g')+row('🎤','Microphone','Hear the wake phrase and you',pill('On','g'),'g')+row('🔔','Notifications','Show the status chip',pill('On','g'),'g')+row('▣','Screen sight','Asked each time you use it',pill('Per use','b'))+row('☝','Accessibility','Needed to tap and scroll for you',pill('Lost','a'),'a')+'''<div class="ban a" style="margin:2px 0 10px"><span>⚠</span><span>Android turned this off after an update. Turn it back on to use device actions.</span></div>'''+row('✉','Notification access','Read incoming alerts (optional)',pill('Off','k'),'k')+row('◷','Usage access','Know which app is open (optional)',pill('Off','k'),'k')+'</div>',nav=3))
add(4,'Character',ph('Character',f'''<div class="card d" style="text-align:center"><div class="disc"><img src="{C}listening.webp" alt=""></div><div class="chips" style="justify-content:center;margin-top:14px"><span class="chip">Idle</span><span class="chip" style="background:var(--co);color:#fff">Listening</span><span class="chip">Thinking</span><span class="chip">Speaking</span></div></div>
<div class="card"><h3>Size</h3><div class="seg" style="margin-top:8px"><div>S</div><div class="on">M</div><div>L</div></div></div>
<div class="card"><h3>Autonomy</h3><div class="sl"><i style="width:50%"></i><b style="left:50%"></b></div><div class="lbls"><span>Calm</span><span>Balanced</span><span>Playful</span></div></div>
<div class="card">{row('☾','Sleep after','Tucks away when idle','<span class="pill k">3 min ▾</span>')}{row('⏾','Quiet hours','No random movement','<span class="pill k">23:00–07:00</span>')}{row('⌖','Remember position per app','',tg(True))}</div>''',nav=3))
add(5,'Voice',ph('Voice','''<div class="card"><h3>Wake phrase</h3><div style="font-size:28px;font-weight:700;margin:8px 0 14px;letter-spacing:-.5px">“Yo, VALIS”</div><div class="s">Sensitivity</div><div class="sl"><i style="width:60%"></i><b style="left:60%"></b></div><div class="lbls"><span>Fewer false wakes</span><span>Hears me easily</span></div></div>
<div class="card d"><div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0">Test it</h3><span class="pill b" style="background:#1B55FF33;color:#bcd0ff">Detected ✓</span></div><div style="display:flex;gap:4px;align-items:flex-end;height:44px;margin-top:14px">'''+''.join('<i style="flex:1;border-radius:3px;background:#1B55FF;height:%dpx"></i>'%h for h in [8,14,26,38,22,30,44,24,12,18,34,20,10,16])+'''</div></div>
<div class="card">'''+row('🔒','Listen with screen off','Uses more battery',tg(False))+row('✋','Let me interrupt','Talk while VALIS speaks',tg(True))+row('↺','Follow-up window','Keep listening after a reply','<span class="pill k">4 s ▾</span>')+row('♫','Voice','Preview before choosing','<span class="pill k">Nova ▾</span>')+'''</div>
<div class="xs" style="text-align:center">Nothing leaves your phone before the wake phrase.</div>''',nav=3))
add(6,'Memory',ph('Memory','''<div class="seg"><div class="on">Cloud</div><div>This phone</div><div>Off</div></div>
<div class="card" style="background:var(--co1)"><h3 style="color:var(--co7)">2 waiting for you</h3><div class="s" style="color:var(--i7);margin-bottom:10px">VALIS wants to remember:</div>
<div class="card" style="padding:12px;margin-bottom:8px"><b style="font-size:14px">You take the 07:40 bus to work</b><div class="btns" style="margin-top:10px"><div class="btn p" style="padding:10px;min-height:44px;font-size:14px">Remember</div><div class="btn o" style="padding:10px;min-height:44px;font-size:14px">No</div></div></div></div>
<div class="card" style="background:#fff"><div class="chips" style="margin-bottom:6px"><span class="chip on">All</span><span class="chip">Preferences</span><span class="chip">People</span><span class="chip">Facts</span></div>
<div class="mem"><div class="av2" style="background:var(--co)">P</div><div class="t"><b style="font-size:15px">Prefers short answers</b><div class="xs">Preference · from chat · 12 Nov</div></div></div>
<div class="mem"><div class="av2" style="background:var(--i7)">S</div><div class="t"><b style="font-size:15px">Sam is your brother</b><div class="xs">People · from chat · 3 Nov</div></div></div></div>
<div class="btns"><div class="btn o">Export</div><div class="btn r">Forget all</div></div>''',nav=1))
add(7,'Services & plugins',ph('Services','''<div class="day">INSTALLED</div><div class="card">'''+row('⚡','Device actions','Open apps, settings, media · built in',tg(True))+row('◔','Memory','Remember what you approve · built in',tg(True))+row('🗓','Acme Calendar','Read and add events',tg(True))+'''<div style="display:flex;gap:8px;flex-wrap:wrap;padding:0 0 12px 52px"><span class="pill k">read events</span><span class="pill k">create events</span><span class="pill a">🔒 Managed by Acme</span></div></div>
<div class="day">AVAILABLE</div><div class="card">'''+row('✉','Mail helper','Draft replies · 3rd party','<div class="btn s2" style="padding:8px 16px;min-height:40px;font-size:14px">Install</div>')+row('☰','Notes sync','Sync notes · Acme','<div class="btn s2" style="padding:8px 16px;min-height:40px;font-size:14px">Install</div>')+'</div>',nav=3))
add(8,'Activity',ph('Activity','''<div class="chips"><span class="chip on">All</span><span class="chip">Actions</span><span class="chip">Chats</span><span class="chip">Declined</span></div>
<div class="day">TODAY</div><div class="card">'''+row('↗','Opened Settings','Wi-Fi · 14:02 · fingerprint not needed',pill('Verified','g'),'g')+row('♪','Played focus mix','Spotify · 13:40',pill('Unverified','a'),'a')+row('☎','Call Mum','You tapped Deny · 09:12',pill('Declined','r'),'r')+'''</div><div class="day">YESTERDAY</div><div class="card">'''+row('💬','Chat · 6 turns','Trip ideas · 4 min',pill('Chat','k'),'k')+row('↗','Open Maps','21:03',pill('Failed','r'),'r')+'''</div>
<div class="card p"><h3>Why was “Opened Settings” allowed?</h3><div class="s">Safe action · foreground was <b>Settings</b> at 14:02:11 · you spoke the request.</div></div>''',nav=2))
add(9,'Privacy',ph('Privacy','''<div class="card d"><h3>What leaves your phone</h3>'''+'''<div class="row" style="border-color:#2B2D45"><div class="peb g">✓</div><div class="t"><b>Wake word</b><span style="color:#B9BBD3">Never. It runs on this phone.</span></div></div><div class="row" style="border-color:#2B2D45"><div class="peb">↑</div><div class="t"><b>Voice</b><span style="color:#B9BBD3">To your VALIS server, only after you wake it.</span></div></div><div class="row" style="border-color:#2B2D45"><div class="peb a">▣</div><div class="t"><b>Screen</b><span style="color:#B9BBD3">One blurred picture, only when allowed.</span></div></div></div>
<div class="card">'''+row('▣','Screen sight','Allow VALIS to look when asked',tg(True))+row('☰','Conversation history','Keep transcripts',tg(False))+row('◔','Analytics','Anonymous crash reports',tg(True))+row('⊘','Blocked apps','Banking, passwords · 6 apps','<span class="pill k">Edit</span>')+'''</div><div class="btns"><div class="btn o">Export my data</div><div class="btn r">Delete my data</div></div>''',nav=3))
add(10,'Security',ph('Security','''<div class="card">'''+row('📱','This phone','Pixel 8 · signed in today',pill('This device','b'))+row('💻','Old tablet','Last seen 41 days ago','<span class="pill r">Revoke</span>')+'''</div>
<div class="card"><h3>Confirm with fingerprint</h3><div class="seg" style="margin-top:8px"><div>Off</div><div class="on">Calls & msgs</div><div>All</div></div></div>
<div class="card"><h3>Always allowed</h3><div class="row"><div class="t"><b>Open apps</b><span>Safe action</span></div><span class="pill k">Revoke</span></div><div class="row"><div class="t"><b>Change volume</b><span>Safe action</span></div><span class="pill k">Revoke</span></div></div>
<div class="card" style="background:var(--rd1)"><h3 style="color:var(--rd)">VALIS never…</h3><div class="s" style="color:#7d1c1c;line-height:1.7">• makes payments or purchases<br>• types or reads your passwords<br>• changes security settings<br>• turns off its own safeguards</div></div>''',nav=3))
add(11,'Plan & billing',ph('Plan','''<div class="card d"><span class="pill b" style="background:#1B55FF33;color:#bcd0ff">Current plan</span><h3 style="font-size:28px;margin:10px 0 2px;letter-spacing:-.5px">Plus</h3><div class="s">Renews 4 Dec · $12 / month</div></div>
<div class="card"><h3>Usage this month</h3><div style="margin-top:12px"><div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px"><b>Voice minutes</b><span class="s">212 / 600</span></div><div class="meter"><i style="width:35%"></i></div></div><div style="margin-top:14px"><div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px"><b>Screen looks</b><span class="s">91 / 100</span></div><div class="meter"><i class="w" style="width:91%"></i></div><div class="xs" style="margin-top:4px;color:var(--am)">Soft limit reached soon</div></div><div style="margin-top:14px"><div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px"><b>Actions</b><span class="s">340 / 2000</span></div><div class="meter"><i style="width:17%"></i></div></div></div>
<div class="card">'''+row('★','Compare plans','Free · Plus · Team','<span class="pill k">›</span>')+row('▤','Next invoice','4 Dec','<span class="pill k">$12</span>')+'''</div><div class="btn s2">Manage billing</div>''',nav=3))
add(12,'Workspace',ph('Workspace','''<div class="card">'''+row('◉','Personal','You · owner',pill('Active','b'))+row('▦','Acme Ltd','Member · 24 people','<span class="pill k">Switch</span>')+'''</div>
<div class="card"><h3>Acme Ltd · members</h3><div style="display:flex;gap:-6px;margin:10px 0">'''+''.join('<div class="av2" style="background:%s;margin-right:-6px;border:2px solid #fff">%s</div>'%(c,l) for c,l in [('#1B55FF','A'),('#2B2D45','B'),('#12805C','C'),('#C77700','D'),('#8A8DA6','+20')])+'''</div><div class="s" style="margin-top:12px">Admins: 2 · Members: 22</div></div>
<div class="card"><h3>Managed by your admin</h3>'''+row('⚑','Risk ceiling','Highest action allowed','<span class="pill a">Confirm</span>')+row('▣','Screen sight','',pill('Choice','b'))+row('⌛','Data kept','','<span class="pill k">30 days</span>')+'''</div><div class="btns"><div class="btn s2">Invite</div><div class="btn o">Admin console ↗</div></div>''',nav=3))
add(13,'Confirmation card',f'''<div class="ph" style="background:#cfd2e6"><div class="sb"><span>9:41</span><span>5G ▮▮▮</span></div><div class="overlay-bg"><div class="fake" style="width:60%"></div><div class="fake" style="width:85%"></div><div class="fake" style="width:70%"></div><div class="pad"></div><div class="fake" style="width:45%"></div><div class="fake" style="width:80%"></div><div style="flex:1"></div>
<div style="background:var(--ink);color:#fff;border-radius:24px;padding:18px;display:flex;flex-direction:column;gap:14px;box-shadow:0 12px 30px #0e0e1955"><div style="display:flex;gap:14px;align-items:center"><div class="disc sm" style="background:#2B2D45"><img src="{C}acting.webp" alt=""></div><div><span class="pill" style="background:#C7770033;color:#FFD08A">Needs your OK</span><h3 style="margin-top:8px;font-size:18px">Call Mum?</h3></div></div>
<div style="background:#2B2D45;border-radius:14px;padding:12px;font-size:14px;line-height:1.5"><b>Mum</b><br><span style="color:#B9BBD3">+44 7700 900123 · mobile</span></div><div class="btns"><div class="btn" style="background:#2B2D45;color:#fff">Deny</div><div class="btn p">Allow once</div></div><div class="xs" style="text-align:center;color:#8A8DA6">Closes in 20 s · written by your phone, not the AI</div></div></div></div>''')

EXP=[('Floating','idle','VALIS rests in the corner while you use any app. Taps pass through everywhere else.','ready'),
('Listening','listening','“Yo, VALIS” — it turns, tilts and shows a quiet cobalt ring.','listen'),
('Thinking','thinking','Looks aside while the model works. A small chip says what it is doing.','think'),
('Speaking','speaking','Mouth follows the voice. A caption can show the words.','speak'),
('Acting','acting','Reaches toward what it is about to do. The phone shows the confirmation.','act'),
('Interrupted','interrupted','You talk over it: a small startle, then it listens.','int'),
('Sleeping','sleeping','Sits down, eyes soft, tucked to the edge. A tap wakes it.','sleep'),
('Error','error','A shrug and a plain sentence, never silence.','err')]
def exp_phone(i,name,img,desc,k):
    chip={'ready':'','listen':'<span class="pill b">● Listening</span>','think':'<span class="pill k">Checking your calendar…</span>','speak':'<div class="cap2">“You’re free at three. Want me to set a reminder?”</div>','act':'<span class="pill a">Waiting for your OK</span>','int':'<span class="pill k">Go ahead</span>','sleep':'<span class="pill k">Zzz · tap to wake</span>','err':'<span class="pill r">Couldn’t reach the server</span>'}[k]
    side='right:10px' if k!='sleep' else 'right:-26px'
    return f'''<div class="fig"><div class="cap">{i+1}/8 · {name}</div><div class="eph"><div class="sb"><span>9:41</span><span>5G ▮▮▮</span></div>
<div class="app"><div class="ah"><b>Roamly</b><span class="chip">Trips</span></div><div class="ac"><div class="ph1"></div><div><b>Lisbon, 3 days</b><div class="s">Flights · Hotels · Plan</div></div></div><div class="ac"><div class="ph1" style="background:#cfe3d4"></div><div><b>Porto weekend</b><div class="s">Draft</div></div></div><div class="ac"><div class="ph1" style="background:#e8d9c4"></div><div><b>Madeira hikes</b><div class="s">Saved</div></div></div></div>
<div class="ov"><div class="chipr">{chip}</div><img class="ch" src="{C}{img}.webp" alt="VALIS {name}" style="{'transform:rotate(0deg)' if k!='sleep' else ''}"></div>
<div class="cap3">{desc}</div></div></div>'''

ECSS=CSS+""".eph{width:390px;max-width:100%;background:#fff;border-radius:32px;border:6px solid var(--ink);overflow:hidden;display:flex;flex-direction:column;box-shadow:0 10px 30px #0e0e1933;position:relative;min-height:800px}
.app{padding:10px 18px;display:flex;flex-direction:column;gap:12px;background:#F4F5F7;flex:1}.ah{display:flex;justify-content:space-between;align-items:center;padding:6px 0}.ah b{font-size:20px}
.ac{background:#fff;border-radius:16px;padding:12px;display:flex;gap:12px;align-items:center}.ph1{width:64px;height:64px;border-radius:12px;background:#cfd8f0;flex:none}.ac b{font-size:15px}
.ov{position:absolute;right:8px;bottom:100px;display:flex;flex-direction:column;align-items:flex-end;gap:6px;width:240px}.ch{width:150px;height:auto;display:block}
.chipr{max-width:240px;display:flex;justify-content:flex-end}.cap2{background:var(--ink);color:#fff;border-radius:16px 16px 4px 16px;padding:10px 12px;font-size:13px;line-height:1.35}
.cap3{padding:14px 18px 20px;font-size:14px;color:var(--i7);line-height:1.45;background:#fff;border-top:1px solid var(--p2);min-height:92px}
"""
nav='<nav>'+''.join('<a href="#s%d">%d</a>'%(n,n) for n,_,_ in S)+'</nav>'
open('/home/claude/valis-blueprint/site/app.html','w').write('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VALIS companion app — 13 screens</title><style>'+CSS+'</style><div class="top"><h1>VALIS Console · 13 screens</h1><p>Companion app control centre, drawn at phone width. The character is the real VALIS asset; everything else is a design proposal (not built).</p></div><div class="wrap">'+''.join('<div class="fig" id="s%d"><div class="cap">%d · %s</div>%s</div>'%(n,n,t,h) for n,t,h in S)+'</div>')
open('/home/claude/valis-blueprint/site/experience.html','w').write('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VALIS in use</title><style>'+ECSS+'</style><div class="top"><h1>VALIS in use · 8 states</h1><p>The real character over a made-up third-party app (“Roamly”). Renders come from VALIS_rigged.glb; the app, chips and captions are design proposals.</p></div><div class="wrap">'+''.join(exp_phone(i,*e) for i,e in enumerate(EXP))+'</div>')
print('ok')
