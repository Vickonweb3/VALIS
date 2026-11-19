"""Blueprint sheet generator: nodes, zones, orthogonal edges, title block. Emits inline SVG."""
import html, re

INK = '#0F1433'; CO = '#1B55FF'; PAPER = '#F4F2EA'; DOT = '#DAD6C6'
AMB = '#C77700'; GRN = '#12805C'; RED = '#C62F2F'; MUTE = '#6B6E8A'
SANS = "'DM Sans','Inter',system-ui,sans-serif"; MONO = "'JetBrains Mono','DM Mono','DejaVu Sans Mono',monospace"
W, H = 1600, 1000
WARN = []

KIND = {  # fill, stroke, text, dash
    'dev':   ('#FFFFFF', CO,  INK, None),
    'cloud': ('#FFFFFF', INK, INK, None),
    'ext':   ('#FAF9F4', MUTE, INK, '5 4'),
    'model': (CO, CO, '#FFFFFF', None),
    'ink':   (INK, INK, '#FFFFFF', None),
    'store': ('#ECEDF6', INK, INK, None),
    'perm':  ('#FFF1D6', AMB, INK, None),
    'ok':    ('#DDF5EA', GRN, INK, None),
    'bad':   ('#FFE3E3', RED, INK, None),
    'pearl': ('#E9EEFF', CO, INK, None),
}
EDGE = {  # color, dash, label color
    'data':  (INK, None), 'ctrl': (CO, None), 'async': (INK, '6 4'),
    'perm':  (AMB, '6 4'), 'ev': (CO, '2 4'), 'deny': (RED, '6 4'), 'ok': (GRN, None),
}
ZONE = {
    'dev':   ('#EEF2FF', CO, '6 5'), 'cloud': ('#EFEDE3', INK, '6 5'),
    'ext':   ('none', MUTE, '3 5'),  'perm': ('#FFF8E8', AMB, '6 5'), 'plain': ('none', INK, '6 5'),
    'ink':   ('#E6E7F1', INK, None),
    'ok':    ('#EAF6F0', GRN, '6 5'),
}


def esc(s):
    return html.escape(str(s), quote=True)


class Sheet:
    def __init__(self, no, title, subtitle, ref):
        self.no, self.title, self.subtitle, self.ref = no, title, subtitle, ref
        self.back, self.mid, self.front = [], [], []
        self.nodes = {}
        self.edge_kinds = set()

    # ---------- primitives
    def text(self, x, y, t, size=12, weight=400, fill=INK, anchor='start', mono=False, layer='front', italic=False):
        fam = MONO if mono else SANS
        st = ' font-style="italic"' if italic else ''
        getattr(self, layer).append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{esc(t)}</text>')

    def zone(self, x, y, w, h, label, kind='dev', size=12):
        f, s, d = ZONE[kind]
        dash = f' stroke-dasharray="{d}"' if d else ''
        self.back.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{f}" stroke="{s}" stroke-width="1.4"{dash}/>')
        if label:
            self.back.append(f'<text x="{x+14}" y="{y+22}" font-family="{SANS}" font-size="{size}" font-weight="700" letter-spacing="1.2" fill="{s if s!=MUTE else INK}">{esc(label.upper())}</text>')

    def node(self, id, x, y, w, h, title, lines=(), kind='dev', tag=None, tsize=13):
        fill, stroke, tc, dash = KIND[kind]
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.nodes[id] = (x, y, w, h)
        o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>']
        sub = '#DCE4FF' if kind in ('model', 'ink') else MUTE
        # width checks
        if len(title) * tsize * 0.56 > w - 16:
            WARN.append(f'[{self.no}] title overflow: {title} ({w})')
        o.append(f'<text x="{x+10}" y="{y+19}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tc}">{esc(title)}</text>')
        yy = y + 36
        for ln in lines:
            if len(ln) * 6.35 > w - 14:
                WARN.append(f'[{self.no}] line overflow in {id}: "{ln}" len={len(ln)} w={w}')
            o.append(f'<text x="{x+10}" y="{yy}" font-family="{MONO}" font-size="10.5" fill="{sub if kind in ("model","ink") else INK}" opacity="{1 if kind in ("model","ink") else .82}">{esc(ln)}</text>')
            yy += 14
        if yy - 6 > y + h:
            WARN.append(f'[{self.no}] height overflow in {id}: need {yy-y+2} have {h}')
        if tag:
            tw = len(tag) * 6.2 + 10
            o.append(f'<rect x="{x+w-tw-6}" y="{y-8}" width="{tw}" height="15" rx="7.5" fill="{INK}"/><text x="{x+w-tw/2-6}" y="{y+3}" font-family="{MONO}" font-size="9.5" fill="#fff" text-anchor="middle">{esc(tag)}</text>')
        self.mid.append(''.join(o))

    def note(self, x, y, w, lines, title=None, kind='plain'):
        h = 16 + 14 * len(lines) + (18 if title else 0)
        self.back.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#FFFDF6" stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>')
        yy = y + 18
        if title:
            self.front.append(f'<text x="{x+10}" y="{yy}" font-family="{SANS}" font-size="11.5" font-weight="700" fill="{INK}">{esc(title)}</text>')
            yy += 17
        for ln in lines:
            if len(ln) * 6.1 > w - 16:
                WARN.append(f'[{self.no}] note overflow: "{ln}" w={w}')
            self.front.append(f'<text x="{x+10}" y="{yy}" font-family="{MONO}" font-size="10.5" fill="{INK}" opacity=".85">{esc(ln)}</text>')
            yy += 14
        return h

    # ---------- edges
    @staticmethod
    def _anchor(n, spec):
        x, y, w, h = n
        side = spec[0]
        f = float(spec[1:]) if len(spec) > 1 else .5
        return {'l': (x, y + h * f), 'r': (x + w, y + h * f), 't': (x + w * f, y), 'b': (x + w * f, y + h)}[side], side

    def edge(self, a, b, label=None, kind='data', sa='r', sb='l', via=None, mid=None, lp=.5, ld=0, both=False, lw=None):
        self.edge_kinds.add(kind)
        na = self.nodes[a] if isinstance(a, str) else a
        nb = self.nodes[b] if isinstance(b, str) else b
        p0, s0 = self._anchor(na, sa)
        p1, s1 = self._anchor(nb, sb)
        pts = [p0]
        if via:
            pts += via
        else:
            h0, h1 = s0 in 'lr', s1 in 'lr'
            if h0 and h1:
                mx = mid if mid is not None else (p0[0] + p1[0]) / 2
                pts += [(mx, p0[1]), (mx, p1[1])]
            elif not h0 and not h1:
                my = mid if mid is not None else (p0[1] + p1[1]) / 2
                pts += [(p0[0], my), (p1[0], my)]
            elif h0 and not h1:
                pts += [(p1[0], p0[1])]
            else:
                pts += [(p0[0], p1[1])]
        pts.append(p1)
        # dedupe
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > .01 or abs(p[1] - clean[-1][1]) > .01:
                clean.append(p)
        col, dash = EDGE[kind]
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in clean)
        da = f' stroke-dasharray="{dash}"' if dash else ''
        ms = f' marker-start="url(#as-{kind})"' if both else ''
        self.front.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.6"{da} marker-end="url(#ae-{kind})"{ms}/>')
        if label:
            # longest segment
            best, bl = None, -1
            for i in range(len(clean) - 1):
                (x1, y1), (x2, y2) = clean[i], clean[i + 1]
                l = abs(x2 - x1) + abs(y2 - y1)
                if l > bl:
                    best, bl = (clean[i], clean[i + 1]), l
            (x1, y1), (x2, y2) = best
            cx, cy = x1 + (x2 - x1) * lp, y1 + (y2 - y1) * lp
            if abs(y2 - y1) < abs(x2 - x1):
                cy += ld
            else:
                cx += ld
            tw = (lw or len(label) * 5.9 + 10)
            self.front.append(f'<rect x="{cx-tw/2:.1f}" y="{cy-8:.1f}" width="{tw:.1f}" height="15" rx="3" fill="{PAPER}"/>'
                              f'<text x="{cx:.1f}" y="{cy+3:.1f}" font-family="{MONO}" font-size="10" fill="{col}" text-anchor="middle" font-weight="600">{esc(label)}</text>')

    # ---------- output
    def legend(self, items=None):
        x, y = 36, 912
        self.front.append(f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="10.5" font-weight="700" letter-spacing="1" fill="{INK}">LEGEND</text>')
        names = {'data': 'data flow', 'ctrl': 'control / command', 'async': 'async / event', 'perm': 'permission gate', 'ev': 'character event', 'deny': 'blocked / error', 'ok': 'verified result'}
        yy = y + 16
        xx = x
        for k in [k for k in ['data', 'ctrl', 'async', 'ev', 'perm', 'ok', 'deny'] if k in self.edge_kinds]:
            col, dash = EDGE[k]
            da = f' stroke-dasharray="{dash}"' if dash else ''
            self.front.append(f'<line x1="{xx}" y1="{yy}" x2="{xx+34}" y2="{yy}" stroke="{col}" stroke-width="1.8"{da}/><text x="{xx+40}" y="{yy+4}" font-family="{MONO}" font-size="10" fill="{INK}">{names[k]}</text>')
            xx += 40 + len(names[k]) * 6.1 + 20
            if xx > 700:
                xx = x
                yy += 16
        # node kinds
        yy2 = 960
        kinds = [('dev', 'on-device'), ('cloud', 'cloud'), ('ext', 'external'), ('model', 'model'), ('perm', 'permission'), ('store', 'datastore')]
        xx = x
        for k, n in kinds:
            f, s, t, d = KIND[k]
            da = f' stroke-dasharray="{d}"' if d else ''
            self.front.append(f'<rect x="{xx}" y="{yy2-9}" width="20" height="12" rx="3" fill="{f}" stroke="{s}" stroke-width="1.4"{da}/><text x="{xx+26}" y="{yy2+1}" font-family="{MONO}" font-size="10" fill="{INK}">{n}</text>')
            xx += 26 + len(n) * 6.1 + 18

    def svg(self):
        defs = ['<defs>']
        for k, (col, _) in EDGE.items():
            defs.append(f'<marker id="ae-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{col}"/></marker>')
            defs.append(f'<marker id="as-{k}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M10,1 L0,5 L10,9 z" fill="{col}"/></marker>')
        defs.append(f'<pattern id="dots-{self.no}" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".9" fill="{DOT}"/></pattern></defs>')
        frame = (f'<rect width="{W}" height="{H}" fill="{PAPER}"/><rect width="{W}" height="{H}" fill="url(#dots-{self.no})"/>'
                 f'<rect x="12" y="12" width="{W-24}" height="{H-24}" fill="none" stroke="{INK}" stroke-width="2"/>'
                 f'<rect x="18" y="18" width="{W-36}" height="{H-36}" fill="none" stroke="{INK}" stroke-width=".7"/>')
        head = (f'<text x="36" y="52" font-family="{SANS}" font-size="26" font-weight="700" fill="{INK}">{esc(self.title)}</text>'
                f'<text x="36" y="72" font-family="{SANS}" font-size="13" fill="{MUTE}">{esc(self.subtitle)}</text>'
                f'<rect x="{W-150}" y="30" width="110" height="38" rx="6" fill="{INK}"/><text x="{W-95}" y="55" font-family="{MONO}" font-size="18" font-weight="700" fill="#fff" text-anchor="middle">{esc(self.no)}</text>')
        tb_x, tb_y = W - 440, H - 108
        tb = (f'<rect x="{tb_x}" y="{tb_y}" width="410" height="84" fill="#FFFDF6" stroke="{INK}" stroke-width="1.6"/>'
              f'<line x1="{tb_x}" y1="{tb_y+28}" x2="{tb_x+410}" y2="{tb_y+28}" stroke="{INK}" stroke-width=".8"/>'
              f'<line x1="{tb_x+250}" y1="{tb_y+28}" x2="{tb_x+250}" y2="{tb_y+84}" stroke="{INK}" stroke-width=".8"/>'
              f'<text x="{tb_x+12}" y="{tb_y+19}" font-family="{SANS}" font-size="13" font-weight="700" fill="{INK}">VALIS · TECHNICAL BLUEPRINT</text>'
              f'<text x="{tb_x+398}" y="{tb_y+19}" font-family="{MONO}" font-size="11" fill="{CO}" text-anchor="end" font-weight="700">{esc(self.no)}</text>'
              f'<text x="{tb_x+12}" y="{tb_y+48}" font-family="{SANS}" font-size="12.5" font-weight="700" fill="{INK}">{esc(self.title)}</text>'
              f'<text x="{tb_x+12}" y="{tb_y+66}" font-family="{MONO}" font-size="10" fill="{MUTE}">{esc(self.ref)}</text>'
              f'<text x="{tb_x+262}" y="{tb_y+46}" font-family="{MONO}" font-size="10" fill="{INK}">REV R1 · 2026-11-19</text>'
              f'<text x="{tb_x+262}" y="{tb_y+62}" font-family="{MONO}" font-size="10" fill="{INK}">SCALE: NTS</text>'
              f'<text x="{tb_x+262}" y="{tb_y+77}" font-family="{MONO}" font-size="10" fill="{INK}">STATUS: PLAN (NOT BUILT)</text>')
        self.legend()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(self.no+" "+self.title)}">'
                + ''.join(defs) + frame + head + ''.join(self.back) + ''.join(self.mid) + ''.join(self.front) + tb + '</svg>')
