import sys, bp
sys.path.insert(0,'/home/claude/tools')
import sheets_a as A, sheets_b as B, sheets_c as C
fs=[A.vb01,A.vb02,A.vb03,A.vb04,A.vb05,A.vb06,B.vb07,B.vb08,B.vb09,B.vb10,B.vb11,B.vb12,C.vb13,C.vb14,C.vb15,C.vb16,C.vb17,C.vb18]
secs=[];
for f in fs:
    try:
        s=f(); secs.append((s.no,s.title,s.svg()))
    except Exception as e:
        import traceback; print('FAIL',f.__name__,e); traceback.print_exc()
css="""body{margin:0;background:#E9E6DA;font-family:'DM Sans',system-ui,sans-serif;color:#0F1433}
header{padding:20px 16px 8px}h1{font-size:22px;margin:0}p{color:#6B6E8A;margin:4px 0 0;font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:6px;padding:8px 16px}nav a{font:600 12px monospace;background:#0F1433;color:#fff;padding:5px 8px;border-radius:5px;text-decoration:none}
section{margin:14px 8px;background:#fff;border-radius:8px;overflow-x:auto;box-shadow:0 1px 4px #0002}section svg{min-width:1100px;display:block}
.b{font:600 12px monospace;padding:8px 12px;color:#1B55FF}"""
html='<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VALIS Blueprint Sheets</title><style>%s</style><header><h1>VALIS · 18 blueprint sheets</h1><p>Scroll sideways on a phone, pinch to zoom. Plan status: not built.</p></header><nav>%s</nav>%s'%(css,''.join('<a href="#%s">%s</a>'%(n,n) for n,_,_ in secs),''.join('<section id="%s"><div class=b>%s · %s</div>%s</section>'%(n,n,t,v) for n,t,v in secs))
open('/home/claude/valis-blueprint/site/blueprint.html','w').write(html)
print(len(secs),'sheets; WARN:',len(bp.WARN)); [print(' ',w) for w in bp.WARN[:40]]
