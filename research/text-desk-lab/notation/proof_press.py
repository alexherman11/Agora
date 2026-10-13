"""proof_press: a proof of the screen kind for a4465 (Alex, 13 Oct: 'clicking this checkbox takes too long, i want
instant response for visuals and clicking'). OWNER: pike (asked), worker a4465 (wrote it).

Steps on a screen, and what must be true after each. It drives screen.py (a copy of a world, this checkout's painter,
headless Chrome) and reads back what the PAGE measured: every time below is the page's own clock (performance.now),
from the click event to the first frame after the wanted thing is in the page.

    python proof_press.py [world] [--as alex] [--lens design-review] [--times]

--times only measures the click (steps 1 and 2) and prints where the time went, leg by leg; it judges nothing.
Exit code 0 when every step is GREEN.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# What the page keeps while it is watched. `want` is a function of the page that is true once the wanted thing is drawn;
# from a press (pointerdown is kept too) the probe notes when it first became true in the page (`dom`), and the first
# and second animation frames after that (`frame`, `frame2`: the change is on the glass between those two).
PROBE = r"""(() => { if (window.__m) return 'probe already here';
  const now = () => performance.now(), m = window.__m = { f: [], want: null, t: {} }, f = window.fetch;
  window.fetch = (u, o) => { const rec = { u: String(u).split('?')[0].replace('/api/', ''), t0: now() }; m.f.push(rec);
    return f(u, o).then(r => { rec.head = now(); r.clone().text().then(t => { rec.body = now(); rec.bytes = t.length; }); return r; }); };
  const seen = () => { if (m.t.dom != null || !m.want || !m.want()) return; m.t.dom = now();
    requestAnimationFrame(() => { m.t.frame = now(); requestAnimationFrame(() => { m.t.frame2 = now(); }); }); };
  new MutationObserver(seen).observe(document.getElementById('paint'), { subtree: true, childList: true, attributes: true, characterData: true });
  m.arm = want => { m.want = want; m.t = {}; m.f.length = 0; };
  m.go = () => { if (m.t.go == null) { m.t.go = now(); queueMicrotask(seen); } };
  document.addEventListener('click', () => m.go(), true);
  document.addEventListener('keydown', e => { if (e.key === 'Enter') m.go(); }, true);
  m.read = () => { const z = m.t.go, r = x => x == null ? null : Math.round((x - z) * 10) / 10;
    return { dom: r(m.t.dom), frame: r(m.t.frame), frame2: r(m.t.frame2),
             fetches: m.f.map(x => ({ u: x.u, sent: r(x.t0), head: r(x.head), body: r(x.body), bytes: x.bytes })) }; };
  return 'probe'; })()"""

# the first check paragraph that is not ticked and is in view: its key, and its thing's id
BOX = r"""(() => { const b = [...document.querySelectorAll('#paint [data-key$="/line/box"]')].find(e => { const r = e.getBoundingClientRect();
    return !e.hidden && r.width && r.top > 0 && r.bottom < innerHeight; });
  return b ? { key: b.dataset.key, item: b._n.fence.item, line: b.dataset.key.slice(0, -4) } : null; })()"""
# the first reply box in view in the margin; and a watch, frame by frame from Enter, of where the typed words are
REPLY = r"""(() => { const e = [...document.querySelectorAll('#paint [data-key$="/answer"]')].find(e => { const r = e.getBoundingClientRect();
    return r.width && r.top > 0 && r.bottom < innerHeight && document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) === e; });   // one a press can reach
  return e ? { key: e.dataset.key, item: (e._n.fence || {}).item } : null; })()"""
WORDS = "zebra words"
WATCH = r"""((key, words) => { const now = () => performance.now(), m = window.__r = { log: [] }, q = () => document.querySelector(`[data-key="${key}"]`);
  const card = q().parentElement.dataset.key;
  const snap = () => { const box = q(), c = document.querySelector(`[data-key="${card}"]`);
    const inBox = !!box && box.innerText.includes(words), inThread = !!c && [...c.children].some(x => x !== box && x.innerText.includes(words));
    const s = (inBox || inThread ? 'on the glass' : 'NOT on the glass') + (inBox ? ', in the box' : '') + (inThread ? ', in the thread' : '') + (box && box.dataset.unsent ? ` (marked: ${box.dataset.unsent})` : '');
    if (m.last !== s) { m.last = s; m.log.push(Math.round(now() - m.go) + ' ms: ' + s); }
    if (now() - m.go < 2500) requestAnimationFrame(snap); };
  document.addEventListener('keydown', e => { if (e.key === 'Enter' && !m.go) { m.go = now(); queueMicrotask(snap); } }, true);
  return 'watching'; })"""
TICKED ="(line => () => { const e = document.querySelector(`[data-key=\"${line}\"]`); return !!e && e.innerText.trim().startsWith('☑'); })"


def screen(world, who, lens, steps):
    out = subprocess.run([sys.executable, str(HERE / "screen.py"), world, "--as", who, "--lens", lens, *steps],
                         capture_output=True, text=True, encoding="utf-8", cwd=HERE)
    if out.returncode:
        raise SystemExit(f"proof_press: screen.py failed\n{out.stdout}\n{out.stderr}")
    return out.stdout.splitlines()


def values(lines):
    """the JSON each `js` step printed, in order (screen.py prints other steps in words)"""
    got = []
    for l in lines:
        try:
            got.append(json.loads(l))
        except ValueError:
            pass
    return got


def main():
    a = sys.argv[1:]
    world = a[0] if a and not a[0].startswith("--") else "frontier-try"
    who = a[a.index("--as") + 1] if "--as" in a else "alex"
    lens = a[a.index("--lens") + 1] if "--lens" in a else "design-review"
    box = values(screen(world, who, lens, ["js", BOX]))[0]
    if not box:
        raise SystemExit(f"proof_press: {lens} as {who} in {world} shows no unticked check box in view")
    arm = f"(window.__m.arm({TICKED}({json.dumps(box['line'])})), 'armed')"
    if "--times" in a:
        for run in range(3):
            got = values(screen(world, who, lens, ["js", "document.querySelectorAll('#paint [data-key]').length", "js", PROBE, "js", arm,
                                                    "click", box["key"], "wait", "1500", "js", "window.__m.read()"]))
            parts, t = got[0], got[-1]
            print(f"run {run + 1}: {parts} painted parts; click -> tick in the page {t['dom']} ms, first frame after {t['frame']} ms, next {t['frame2']} ms")
            for f in t["fetches"]:
                print(f"    {f['u']:8} sent {f['sent']!s:>7} answered {f['head']!s:>7} read {f['body']!s:>7}  {f.get('bytes')} bytes")
        reply = values(screen(world, who, lens, ["js", REPLY]))[0]
        got = values(screen(world, who, lens, ["js", f"{WATCH}({json.dumps(reply['key'])}, {json.dumps(WORDS)})", "click", reply["key"],
                                                "type", WORDS, "key", "Enter", "wait", "2000", "js", "window.__r.log"]))
        print("a reply typed in the margin, from Enter:")
        for l in got[-1]:
            print("    " + l)
        return
    ok = []

    def judge(step, green, said):
        ok.append(green)
        print(f"{'GREEN' if green else 'RED  '} {step}: {said}")

    # 1-3: the click, the tick within 100 ms by the page's clock, and the world: checked=yes by one event
    got = values(screen(world, who, lens, ["js", "document.querySelectorAll('#paint [data-key$=\"/main\"]').length", "js", EVENTS_AT, "js", PROBE,
                                            "js", arm, "click", box["key"], "wait", "1500", "js", "window.__m.read()",
                                            "js", f"{EVENTS_SINCE}(window.__at)", "js", f"{TICKED}({json.dumps(box['line'])})()"]))
    paras, t, evs, still = got[0], got[-3], got[-2], got[-1]
    print(f"1. {lens} as {who} in a copy of {world}: {paras} paragraphs; the unticked box in view is {box['item']}'s")
    judge("2. the tick within 100 ms of the click", t["frame"] is not None and t["frame"] <= 100,
          f"in the page at {t['dom']} ms, the frame after at {t['frame']} ms")
    mine = [e for e in evs if e["target"] == box["item"]]
    judge("3. the world has it, by one event", len(mine) == 1 and mine[0]["args"].get("checked") == "yes" and still,
          f"{len(mine)} event(s) on {box['item']}: " + ", ".join(f"{e['id']} {e['verb']} {json.dumps(e['args'])}" for e in mine) + f"; the tick is {'still' if still else 'NOT'} drawn")
    # 4: the refusal. Someone else makes the paragraph a bullet, and the click lands before the page has heard of it
    got = values(screen(world, who, lens, ["js", PROBE, "js", f"{REFUSE}({json.dumps(box['key'])}, {json.dumps(box['item'])})", "wait", "2000",
                                            "js", f"{AFTER}({json.dumps(box['line'])}, {json.dumps(box['item'])})"]))
    r = got[-1]
    judge("4. a refused click: no tick is left, and the page says why", not r["ticked"] and "refused" in r["status"] and not r["world"],
          f"the desk answered {got[-2]!r}; the line now begins {r['begins']!r}; the status line says {r['status'][:140]!r}; "
          f"the world has checked={'yes' if r['world'] else 'nothing'}")
    # 5: a reply typed in the margin and sent: his words are on the glass in every frame from Enter, and end in the thread
    reply = values(screen(world, who, lens, ["js", REPLY]))[0]
    got = values(screen(world, who, lens, ["js", f"{WATCH}({json.dumps(reply['key'])}, {json.dumps(WORDS)})", "click", reply["key"],
                                            "type", WORDS, "key", "Enter", "wait", "2000", "js", "window.__r.log"]))[-1]
    judge("5. a reply typed in the margin: his words on the glass at once and after", bool(got) and got[0].startswith("0 ms: on the glass")
          and not any("NOT" in l for l in got) and "in the thread" in got[-1], "; ".join(got))
    print("every step GREEN" if all(ok) else f"{ok.count(False)} of {len(ok)} RED")
    sys.exit(0 if all(ok) else 1)


EVENTS_AT = "(async () => (window.__at = (await (await fetch(`/api/events?session=${new URLSearchParams(location.search).get('session')}&since=999999999`)).json()).total))()"
EVENTS_SINCE = "(async at => (await (await fetch(`/api/events?session=${new URLSearchParams(location.search).get('session')}&since=${at}`)).json()).events.map(e => ({ id: e.id, verb: e.verb, target: e.target, by: e.by, args: e.args || {} })))"
# the paragraph stops being a check (another person's act), and the box is pressed in the same turn of the page, so the
# press carries what was painted before; the page's own answer to it is what is judged
REFUSE = r"""(async (key, item) => { const q = new URLSearchParams(location.search);
  const r = await (await fetch('/api/do', { method: 'POST', body: JSON.stringify({ session: q.get('session'), as: 'pike', line: `read ${item}; do prop ${item} block=bullet` }) })).json();
  if (r.error) return 'the other act was itself refused: ' + r.error;
  window.__m.arm(() => false); const el = document.querySelector(`[data-key="${key}"]`); el.click();
  for (let k = 0; k < 40 && !window.__m.f.some(x => x.u === 'do' && x.body != null); k++) await new Promise(d => setTimeout(d, 50));
  return (document.getElementById('status') || {}).textContent || '(no status yet)'; })"""
AFTER = r"""(async (line, item) => { const q = new URLSearchParams(location.search), e = document.querySelector(`[data-key="${line}"]`), t = e ? e.innerText.trim() : '';
  const r = await (await fetch('/api/do', { method: 'POST', body: JSON.stringify({ session: q.get('session'), as: 'pike', line: `read ${item}` }) })).json();
  return { ticked: t.startsWith('☑'), begins: t.slice(0, 24), status: (document.getElementById('status') || {}).textContent || '', world: /checked=yes/.test(r.text || '') }; })"""


if __name__ == "__main__":
    main()
