from playtest_steps import Step


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_glance():
        """What a glance at the whole home base meets, with the panels out: what is cut, squeezed or spills (a count,
        not a judgement: it fails only when a panel shows nothing but its title)."""
        g = await w.js(r"""(() => { const pt = window.__pt, out = { panels: [], cut: [], spill: [], tiny: [] };
          for (const t of document.querySelectorAll('#paint [data-key$="/grip/title"]')) { if (!pt.vis(t)) continue;
            const p = t.parentElement.parentElement, body = [...p.children].find(c => /\/body$/.test(c.dataset.key || ''));
            const name = t.textContent.trim(), r = p.getBoundingClientRect(); out.panels.push(name);
            if (p.dataset.cut || (body && body.dataset.cut) || [...p.querySelectorAll('[data-cut]')].length) out.cut.push(name);
            if (!body || !pt.vis(body) || body.getBoundingClientRect().height < 24) out.tiny.push(name); }
          for (const e of document.querySelectorAll('#paint [data-key]')) { if (!pt.vis(e) || e.querySelector('[data-key]')) continue;
            if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'visible' && !e.classList.contains('clamp')) out.spill.push(e.dataset.key.split('/').slice(-2).join('/')); }
          out.parts = document.querySelectorAll('#paint [data-key]').length; return out; })()""")
        note = (f"{len(g['panels'])} panels out ({', '.join(g['panels'])}); {g['parts']} painted parts; "
                f"cut at the foot: {', '.join(g['cut']) or 'none'}; words cut at the side: {len(g['spill'])}"
                + (f" ({', '.join(g['spill'][:4])})" if g["spill"] else "")
                + (f"; only a title showing: {', '.join(g['tiny'])}" if g["tiny"] else ""))
        bare = [t for t in g["tiny"] if t]
        if bare:
            raise AssertionError(note)
        return {"note": note}
    return s_glance


STEP = Step(name='glance', description='a glance with every panel out: what is cut or squeezed', order=2200,
            needs=(), script=bind, assertion='a glance with every panel out: what is cut or squeezed', budget=(100, 300))
