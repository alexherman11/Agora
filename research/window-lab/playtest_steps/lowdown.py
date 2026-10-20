from playtest_steps import Step
from playtest_steps._support import open_panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_lowdown():
        r = await open_panel(play, "The lowdown", "home-lowdown")
        prose = await w.js("(() => { const pt = window.__pt, l = pt.part('lens:home-lowdown'); if (!l) return null;"
                           " const t = [...l.querySelectorAll('[data-key]')].filter(e => pt.vis(e) && !e.querySelector('[data-key]')).map(e => e.textContent.trim()).join(' ');"
                           " const cut = !!l.closest('[data-cut]') || [...l.querySelectorAll('*')].some(e => e.dataset && e.dataset.cut);"
                           " const r = l.getBoundingClientRect(); return { words: t.split(/\\s+/).length, cut, h: Math.round(r.height) }; })()")
        if not prose or prose["words"] < 12:
            raise AssertionError(f"the lowdown shows almost nothing ({prose})")
        r = r or {"note": "already out"}
        r["note"] = (r.get("note", "") + f"; {prose['words']} words shown in {prose['h']} px" + ("; CUT: some of it is hidden" if prose["cut"] else "")).lstrip("; ")
        return r
    return s_lowdown


STEP = Step(name='lowdown', description='read the lowdown (its chip on the shelf)', order=200,
            needs=(), script=bind, assertion='read the lowdown (its chip on the shelf)', budget=(100, 300))
