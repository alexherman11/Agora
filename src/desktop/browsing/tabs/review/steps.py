"""steps.py (a7544): the tabs acceptance journeys, run in order on one staged copy by tabs_review.py. Each leaves the
copy in the state the next one starts from (said in its docstring's last words)."""
import asyncio
import json
import re

V = "__tr.viewer()"
CHAT_TA = "[...document.querySelectorAll('textarea')].find(e => __tr.vis(e) && e.closest('[data-key*=\"lens:jeff-chat\"]'))"
DRAFT = (f"(() => {{ const t = {CHAT_TA}; if (!t) return null; const chat = t.closest('[data-key*=\"lens:jeff-chat\"]'); "
         "const top = [...document.querySelectorAll('[data-key*=\"lens:jeff-chat\"]')].filter(__tr.vis).sort((a, b) => a.dataset.key.length - b.dataset.key.length)[0] || chat; "
         "const s = top ? top.innerText.replace(/\\s+/g, ' ') : ''; const i = s.lastIndexOf('Attach open item'); "
         "return { v: t.value, s: t.selectionStart, e: t.selectionEnd, about: i < 0 ? '' : s.slice(i, i + 90) }; })()")


def chip(words):
    return f"__tr.leaf({json.dumps(words)}, {V})"


def pin(pid):
    return f"[...({V} || document).querySelectorAll('[data-key$=\"/bar/pins/{pid}\"]')].find(__tr.vis)"


TABS_HANDLE = f"(({V} || document).querySelector('[data-key$=\"/bar/tabs\"]') || {{}}).querySelector?.(':scope > button')"
TAB_ROWS = f"[...document.querySelectorAll('[data-key*=\"/bar/tabs/menu/\"]')].filter(e => /\\/menu\\/a\\d+\\/name$/.test(e.dataset.key) && __tr.vis(e))"


def tab_row(note, part="name"):
    return f"[...document.querySelectorAll('[data-key$=\"/bar/tabs/menu/{note}/{part}\"]')].find(__tr.vis)"


async def state(R):
    v = R.viewer()
    return {k: v.get(k, "") for k in ("viewing", "with", "back", "active_tab", "tab_count", "can_back", "can_forward", "find", "pins", "reading_key")}


async def page(R):
    return {"heading": await R.js("__tr.heading()"), "bar": await R.js("__tr.bar()"), "page": await R.js("__tr.page()")}


async def menu_open(R):
    if await R.js(f"{TAB_ROWS}.length"):
        return True
    await R.press(TABS_HANDLE, what="the Tabs handle")
    return await R.wait_for(f"{TAB_ROWS}.length > 0", 3)


async def menu_close(R):
    if await R.js(f"{TAB_ROWS}.length"):
        await R.press(TABS_HANDLE, what="the Tabs handle")
        await asyncio.sleep(0.4)


async def search_open(R, words, thing):
    box = "[...(document.querySelector('[data-key*=\"lens:home-search\"]') || document).querySelectorAll('[data-caret]')].find(__tr.vis)"
    await R.press(box, what="the search box")
    await R.w.type(words)
    await asyncio.sleep(0.3)
    await R.w.key("Enter")
    hit = f"[...document.querySelectorAll('[data-key*=\"lens:home-search\"]')].find(e => e.dataset.key.endsWith('/titles/{thing}') && __tr.vis(e))"
    if not await R.wait_for(hit, 4):
        raise LookupError(f"search for {words!r} did not list {thing}")
    await R.press(hit, what=f"result {thing}")
    await asyncio.sleep(0.8)


def columns(R):
    out = R.do("look f5664 :2")
    return len(re.findall(r"^\s+f\d+ surface ", out, re.M))


# ---- journeys --------------------------------------------------------------------------------------------------------

async def probe(R):
    """what the staged copy paints in the viewer"""
    facts = {"page": await R.js("__tr.page()"), "viewer": await R.js(f"(() => {{ const v = {V}; return v && {{key: v.dataset.key, r: __tr.R(v)}}; }})()"),
             "bar": await R.js("__tr.bar()"), "heading": await R.js("__tr.heading()"), "scrollers": await R.js("__tr.scrollers()"),
             "floats": await R.js("__tr.floats()"), "viewer_props": R.viewer(), "tabs": R.tabs(), "stage": R.stagelog, "made": R.made}
    print(json.dumps(facts, indent=1, ensure_ascii=False)[:6000])
    R.record("probe", probe.__doc__, "ran", "facts printed", facts, [await R.shot("probe")])


async def draft_start(R):
    """a synthetic unsent chat draft with a selected range, kept for the end (never sent)"""
    c = await R.js(f"(() => {{ const t = {CHAT_TA}; return t ? __tr.hit(t) : null; }})()")
    if not c or not c["ok"]:
        R.draft0 = None
        R.record("draft-start", draft_start.__doc__, "blocked", f"the chat composer cannot be pressed at this size ({c})", {}, [await R.shot("draft-cut")])
        return
    await R.w.click(c["x"], c["y"])
    await asyncio.sleep(0.3)
    if not await R.js(f"document.activeElement === {CHAT_TA}"):
        R.draft0 = None
        R.record("draft-start", draft_start.__doc__, "blocked", "the press did not give the composer the caret; nothing typed", {}, [await R.shot("draft-nofocus")])
        return
    if (await R.js(f"{CHAT_TA}.value")) != "unsent tabs review draft":      # the second start (after the last reload) only selects again
        await R.w.type("unsent tabs review draft")
    await asyncio.sleep(0.3)
    await R.js(f"{CHAT_TA}.setSelectionRange(7, 11)")
    await asyncio.sleep(1.2)
    R.draft0 = await R.js(DRAFT)
    R.draftline0 = R.lines("prop:role=conversation-draft,prop:actor=alex")
    R.record("draft-start", draft_start.__doc__, "ran" if R.draft0 and R.draft0["v"] == "unsent tabs review draft" else "fail",
             f"draft {R.draft0}", {"draft": R.draft0, "draft_note": R.draftline0}, [await R.shot("draft-start")])


async def migrate(R):
    """current view migrates into the first tab exactly once; pins, layout and draft untouched; a reload keeps it"""
    s, notes = await state(R), []
    base = R.base
    b = dict(re.findall(r"(\w+)=(\S*)", base["viewer"][0]))
    for k in ("viewing", "with", "pins", "find"):
        if s[k] != b.get(k, ""):
            notes.append(f"{k} {b.get(k)!r} -> {s[k]!r}")
    if s["tab_count"] != "1" or len(R.open_tabs()) != 1:
        notes.append(f"tabs {s['tab_count']} / notes {R.open_tabs()}")
    layout = [l.strip() for l in R.do("find prop:role=home-panel,prop:actor=alex").splitlines() if " note " in l]
    if layout != base["layout"]:
        notes.append("layout panels changed")
    again = R.do(f"do browse {R.vid} action=init", "alex")
    if "Already" not in again:
        notes.append("second init: " + again.strip()[-160:])
    h0 = await R.js("__tr.heading()")
    await R.reload()
    h1 = await R.js("__tr.heading()")
    if h0 != h1:
        notes.append(f"heading over reload {h0!r} -> {h1!r}")
    R.record("migrate", migrate.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"viewing {s['viewing']} with {s['with']!r} in tab-1, pins/find/layout unchanged; second init: Already; heading {h1!r} over reload",
             {"state": s, "second_init": again[-300:], "base_viewer": base["viewer"]}, [await R.shot("migrate")])


async def show(R):
    """the Viewer is on the desk for the journeys (when the copy has it shelved, a search result brings it back)"""
    out = await R.js("!!__tr.viewer()")
    before = await state(R)
    # either way the journeys start on Long note A (a7544: a copy with the Viewer out on Board gave pins no first step)
    await search_open(R, "Long note A synthetic", R.made["Long note A (synthetic)"])
    after = await state(R)
    ok = await R.wait_for("!!__tr.viewer()", 4)
    R.record("show", show.__doc__, "pass" if ok and after["viewing"] == R.made["Long note A (synthetic)"] else "fail",
             f"Viewer {'out' if out else 'shelved'} in this copy (viewing {before['viewing']!r}); a search result opened {after['viewing']} in {after['active_tab']}",
             {"before": before, "after": after}, [await R.shot("show")])


async def pins_history(R):
    """pins open in the active tab (mouse); Back and Forward follow the tab's trail; a new page after Back drops Forward"""
    notes, seen = [], {}
    s_start = await state(R)
    start = s_start["viewing"]          # (with the migrated page before it, the start has its own Back: a7544 ran it)
    await R.press(pin("f155"), what="pin Board")
    seen["after Board"] = await state(R)
    await R.press(pin("a5202"), what="pin The lowdown")
    seen["after lowdown"] = await state(R)
    if seen["after lowdown"]["viewing"] != "a5202" or seen["after lowdown"]["can_back"] != "yes":
        notes.append(f"pins: {seen['after lowdown']}")
    shots = [await R.shot("pins")]
    await R.press(chip("Back"), what="Back")
    seen["back1"] = await state(R)
    if seen["back1"]["viewing"] != "f155" or seen["back1"]["can_forward"] != "yes":
        notes.append(f"Back: {seen['back1']}")
    if not await R.js(chip("Forward")):
        notes.append("no Forward chip after Back")
    shots.append(await R.shot("back"))
    await R.press(chip("Forward"), what="Forward")
    seen["fwd"] = await state(R)
    if seen["fwd"]["viewing"] != "a5202":
        notes.append(f"Forward: {seen['fwd']}")
    await R.press(chip("Back"), what="Back")
    await R.press(chip("Back"), what="Back")
    seen["back2"] = await state(R)
    if seen["back2"]["viewing"] != start or seen["back2"]["can_back"] != s_start["can_back"]:
        notes.append(f"Back twice: {seen['back2']} (start {start}, can_back {s_start['can_back']})")
    if s_start["can_back"] == "no" and await R.js(chip("Back")):
        notes.append("Back still shown at the first page")
    cols0 = columns(R)
    branch = R.made["long"][0]
    await search_open(R, "Synthetic tab 01", branch)
    seen["search"] = await state(R)
    cols1 = columns(R)
    R.tab1_page = branch
    if seen["search"]["viewing"] != branch or seen["search"]["can_forward"] != "no":
        notes.append(f"search/branch: {seen['search']}")
    if cols1 != cols0:
        notes.append(f"search made a column: {cols0} -> {cols1}")
    if await R.js(chip("Forward")):
        notes.append("Forward still shown after branching")
    shots.append(await R.shot("branch"))
    R.record("history", pins_history.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"pin, pin, Back, Forward, Back×2 to {start}, search opened {branch} in the same tab and dropped Forward; columns {cols0}={cols1}",
             seen, shots)


async def new_tab(R):
    """New tab makes a blank tab; search opens B there; the Tabs menu names both and selects between them (mouse)"""
    notes, seen = [], {}
    await R.press(chip("New tab"), what="New tab")
    seen["new"] = await state(R)
    blank = await R.js(f"!!__tr.leaf('Nothing open. Find it at the top, press a pin, or a name anywhere.', {V})")
    if seen["new"]["tab_count"] != "2" or seen["new"]["viewing"] != "" or not blank:
        notes.append(f"new tab: {seen['new']} blank hint {blank}")
    shots = [await R.shot("new-tab")]
    await search_open(R, "Long note B", R.made["Long note B (synthetic)"])
    seen["B"] = await state(R)
    if seen["B"]["viewing"] != R.made["Long note B (synthetic)"] or seen["B"]["tab_count"] != "2":
        notes.append(f"B: {seen['B']}")
    if not await menu_open(R):
        notes.append("the Tabs menu did not open")
    else:
        rows = await R.js(f"{TAB_ROWS}.map(e => [e.dataset.key.split('/menu/')[1], e.innerText.trim(), __tr.R(e)])")
        seen["rows"] = rows
        shots.append(await R.shot("tabs-menu"))
        if len(rows) != 2 or not rows[0][1].startswith("Synthetic tab 01") or rows[1][1] != "Long note B (synthetic)":
            notes.append(f"menu rows {[r[1] for r in rows]}")
        first = rows[0][0].split("/")[0]
        await R.press(tab_row(first), what="tab 1")
        seen["select 1"] = await state(R)
        if seen["select 1"]["viewing"] != R.tab1_page or seen["select 1"]["active_tab"] != "tab-1":
            notes.append(f"select tab 1: {seen['select 1']}")
        if seen["select 1"]["can_back"] != "yes":
            notes.append("tab 1 lost its Back")
    R.tabnote = {t["tab"]: t["id"] for t in R.tabs()}
    R.record("new-tab", new_tab.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"New tab blank, B opened in tab-2, menu rows {R.tab1_page}'s title and B; selecting tab 1 restored it with its Back", seen, shots)


async def search_dup(R):
    """the bar's search lists each page once: the tabs' projection notes do not stand beside the pages they name"""
    box = "[...(document.querySelector('[data-key*=\"lens:home-search\"]') || document).querySelectorAll('[data-caret]')].find(__tr.vis)"
    await R.press(box, what="the search box")
    await R.w.type("Synthetic tab 07")
    await R.w.key("Enter")
    hits = "[...document.querySelectorAll('[data-key*=\"lens:home-search\"]')].filter(e => /\\/(titles|hits)\\/[af]\\d+$/.test(e.dataset.key) && __tr.vis(e)).map(e => [e.dataset.key.split('/').pop(), e.innerText.replace(/\\s+/g, ' ').trim()])"
    await R.wait_for(f"{hits}.length > 0", 4)
    await asyncio.sleep(0.4)
    got = await R.js(hits)
    shot = await R.shot("search-dup")
    tabnotes = {t["id"] for t in R.tabs()}
    dup = [h for h in got if h[0] in tabnotes]
    await R.w.key("Escape")
    R.do(f"read {R.vid}", "alex")
    R.do(f"do prop {R.vid} find=\"\"", "alex")         # the box's words put back as they were
    await asyncio.sleep(0.6)
    R.record("search-dup", search_dup.__doc__, "fail" if dup else "pass",
             f"'Synthetic tab 07' lists {len(got)}: {got}; tab projection notes among them: {dup}" if dup else f"'Synthetic tab 07' lists {got}",
             {"hits": got, "tab_notes": sorted(tabnotes)}, [shot])


async def scrollpos(R, what):
    sc = await R.js("__tr.scrollers()")
    return [s for s in sc if s["scope"]]


async def reading(R):
    """per-tab reading position: A and B scrolled differently survive tab switches and a browser reload"""
    notes, seen, shots = [], {}, []
    a, b = R.made["Long note A (synthetic)"], R.made["Long note B (synthetic)"]
    await search_open(R, "Long note A synthetic", a)          # tab 1 (selected last) goes on to A
    sc = await scrollpos(R, "A")
    if not sc:
        R.record("reading", reading.__doc__, "blocked", f"no remembered scrolling frame under the viewer for A: {await R.js('__tr.scrollers()')}", {}, [await R.shot("reading-none")])
        return
    s = sc[0]
    box = await R.js(f"(() => {{ const e = document.querySelector('[data-key=\"{s['key']}\"]'); return __tr.R(e); }})()")
    x, y = box[0] + box[2] / 2, box[1] + box[3] / 2
    await R.w.wheel(x, y, 120 * 6)
    await asyncio.sleep(0.8)
    seen["A scrolled"] = await scrollpos(R, "A")
    await menu_open(R)
    await R.press(tab_row(R.tabnote["tab-2"]), what="tab B")
    await asyncio.sleep(0.6)
    sb = await scrollpos(R, "B")
    seen["B at open"] = sb
    if sb:
        box = await R.js(f"(() => {{ const e = document.querySelector('[data-key=\"{sb[0]['key']}\"]'); return __tr.R(e); }})()")
        await R.w.wheel(box[0] + box[2] / 2, box[1] + box[3] / 2, 120 * 15)
        await asyncio.sleep(0.8)
    seen["B scrolled"] = await scrollpos(R, "B")
    await menu_open(R)
    await R.press(tab_row(R.tabnote["tab-1"]), what="tab A")
    await asyncio.sleep(0.6)
    seen["A again"] = await scrollpos(R, "A")
    shots.append(await R.shot("reading-A"))
    await R.reload()
    seen["A after reload"] = await scrollpos(R, "A")
    await menu_open(R)
    await R.press(tab_row(R.tabnote["tab-2"]), what="tab B")
    await asyncio.sleep(0.6)
    seen["B after reload"] = await scrollpos(R, "B")
    shots.append(await R.shot("reading-B"))
    ta, tb = seen["A scrolled"][0]["top"], (seen["B scrolled"] or [{"top": None}])[0]["top"]
    if not ta or not tb or ta == tb:
        notes.append(f"wheel did not set two different positions (A {ta}, B {tb})")
    for k, want in (("A again", ta), ("A after reload", ta), ("B after reload", tb)):
        got = (seen[k] or [{"top": None}])[0]["top"]
        if got is None or abs(got - want) > 2:
            notes.append(f"{k}: top {got} (want {want})")
    if (seen["B at open"] or [{"top": 0}])[0]["top"] not in (0,):
        notes.append(f"B opened at {seen['B at open'][0]['top']} (a fresh page should start at the top)")
    seen["storage"] = await R.js("__tr.reading()")
    R.record("reading", reading.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"A {ta} px and B {tb} px kept through switches and a reload ({seen['storage']})", seen, shots)


async def lens(R):
    """Open with: a lens choice is a history entry in that tab only; Back returns to the page's own look"""
    notes, seen = [], {}
    s0 = await state(R)                      # on tab B
    await R.press(chip("design-review"), what="design-review")
    seen["lens"] = await state(R)
    if seen["lens"]["with"] != "design-review" or seen["lens"]["can_back"] != "yes":
        notes.append(f"lens: {seen['lens']}")
    shots = [await R.shot("lens")]
    await R.press(chip("Back"), what="Back")
    seen["back"] = await state(R)
    if seen["back"]["with"] != s0["with"] or seen["back"]["viewing"] != s0["viewing"]:
        notes.append(f"Back from the lens: {seen['back']} (was {s0})")
    await menu_open(R)
    await R.press(tab_row(R.tabnote["tab-1"]), what="tab A")
    seen["A"] = await state(R)
    if seen["A"]["with"] != "":
        notes.append(f"tab A took the lens: {seen['A']}")
    R.record("lens", lens.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or "design-review pushed an entry in B, Back gave its own look, tab A unchanged", seen, shots)


async def new_tab_menu(R):
    """'Open in new tab' from a pin's menu and from the page title's menu (right button)"""
    notes, seen, shots = [], {}, []
    n0 = int((await state(R))["tab_count"])
    await R.press(pin("f155"), right=True, what="pin Board (right)")
    seen["pin menu"] = await R.js("__tr.menu()")
    shots.append(await R.shot("pin-menu"))
    if not seen["pin menu"] or "Open in new tab" not in seen["pin menu"]:
        notes.append(f"pin menu: {seen['pin menu']}")
        await R.w.key("Escape")
    else:
        await R.choose("Open in new tab")
        seen["pin new"] = await state(R)
        if seen["pin new"]["tab_count"] != str(n0 + 1) or seen["pin new"]["viewing"] != "f155":
            notes.append(f"pin new tab: {seen['pin new']}")
    title = f"[...({V}).querySelectorAll('[data-key$=\"/head/title\"]')].find(__tr.vis)"
    await R.press(title, right=True, what="page title (right)")
    seen["title menu"] = await R.js("__tr.menu()")
    if not seen["title menu"] or "Open in new tab" not in seen["title menu"]:
        notes.append(f"title menu: {seen['title menu']}")
        await R.w.key("Escape")
    else:
        await R.choose("Open in new tab")
        seen["title new"] = await state(R)
        if seen["title new"]["tab_count"] != str(n0 + 2) or seen["title new"]["viewing"] != "f155":
            notes.append(f"title new tab: {seen['title new']}")
    shots.append(await R.shot("new-tab-menu"))
    R.tabnote = {t["tab"]: t["id"] for t in R.tabs()}
    R.record("open-new-tab", new_tab_menu.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"pin menu and title menu each opened Board in a new tab ({n0} -> {n0 + 2})", seen, shots)


async def keyboard(R):
    """keyboard: in the open Tabs menu, arrow keys move between rows and Enter selects that tab"""
    notes, seen = [], {}
    focus = "(document.activeElement && (document.activeElement.closest('[data-key]') || {dataset: {}}).dataset.key || '').split('/menu/')[1] || document.activeElement.tagName"
    await menu_close(R)
    await menu_open(R)                       # the handle pressed: focus is on it
    rows = await R.js(f"{TAB_ROWS}.map(e => e.dataset.key.split('/menu/')[1].split('/')[0])")
    seen["rows"] = rows
    await R.w.key("ArrowDown")
    await asyncio.sleep(0.3)
    seen["Down from the handle"] = await R.js(focus)
    if not str(seen["Down from the handle"]).startswith("a"):
        seen["note"] = "Down on the Tabs handle does not enter the list (the handle is not one of the frame's stops)"
        await R.w.key("Tab")
        await asyncio.sleep(0.3)
        seen["Tab"] = await R.js(focus)
    seen["focus1"] = await R.js(focus)
    await R.w.key("ArrowDown")
    await asyncio.sleep(0.3)
    seen["focus2"] = await R.js(focus)
    await R.w.key("ArrowDown")
    await asyncio.sleep(0.3)
    seen["focus3"] = await R.js(focus)
    seen["focus2"] = seen["focus3"] if str(seen["focus3"]).endswith("/name") else seen["focus2"]
    shots = [await R.shot("keyboard-focus")]
    await R.w.key("Enter")
    await asyncio.sleep(1.0)
    seen["after Enter"] = await state(R)
    f2 = str(seen["focus2"])
    want = next((t for t, n in R.tabnote.items() if f2.startswith(n + "/")), None)
    if not want:
        notes.append(f"arrows did not reach a tab row (focus {seen['focus1']} then {seen['focus2']})")
    elif seen["after Enter"]["active_tab"] != want:
        notes.append(f"Enter on {f2} selected {seen['after Enter']['active_tab']} (want {want})")
    shots.append(await R.shot("keyboard-enter"))
    R.record("keyboard", keyboard.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"{'Tab' if 'Tab' in seen else 'Down'} entered the list at {seen['focus1']}, Down reached {f2}, Enter selected {want}"
             + (f" ({seen['note']})" if seen.get("note") else ""), seen, shots)


async def bypass(R):
    """routes that still write viewing= directly (a board card): what the tabs and Back do afterwards"""
    seen = {"before": await state(R), "tabs before": [(t["tab"], t.get("active")) for t in R.open_tabs()]}
    card = "[...document.querySelectorAll('[data-key*=\"lens:home-board\"]')].filter(__tr.vis).find(e => e._n && (e._n.acts || []).some(a => a.on === 'click' && /viewing=|do view /.test(a.line)))"
    k = await R.js(f"(() => {{ const e = {card}; return e ? [e.dataset.key, e.innerText.trim().slice(0, 60)] : null; }})()")
    if not k:                                  # the names that open things are inside an opened card: open one first
        row = ("[...document.querySelectorAll('[data-key*=\"lens:home-board\"] [data-fold-inline], [data-key*=\"lens:home-board\"] .l-fold-handle, [data-key*=\"lens:home-board\"] button')]"
               ".filter(__tr.vis).find(e => e.innerText.includes(\"A window's own values\")) || __tr.leaf(\"A window's own values\", document.querySelector('[data-key*=\"lens:home-board\"]'))")
        if await R.js(f"!!{row}"):
            await R.press(row, what="a board card")
            await asyncio.sleep(0.8)
            seen["opened card"] = True
            k = await R.js(f"(() => {{ const e = {card}; return e ? [e.dataset.key, e.innerText.trim().slice(0, 60)] : null; }})()")
    if not k:
        acts = await R.js("[...document.querySelectorAll('[data-key*=\"lens:home-board\"]')].filter(__tr.vis).filter(e => e._n && (e._n.acts || []).some(a => a.on === 'click')).slice(0, 25).map(e => [e.dataset.key.split('lens:home-board')[1], e.innerText.trim().slice(0, 30), e._n.acts.filter(a => a.on === 'click').map(a => a.line.slice(0, 90))])")
        R.record("bypass", bypass.__doc__, "blocked", f"no board press found that writes viewing=; presses: {acts[:6]}", {"acts": acts}, [await R.shot("bypass-none")])
        return
    await R.press(card, what="a board card")
    await asyncio.sleep(0.6)
    seen["pressed"] = k
    seen["after card"] = await state(R)
    seen["heading"] = await R.js("__tr.heading()")
    shots = [await R.shot("bypass-card")]
    seen["tab notes"] = [(t["tab"], t.get("active")) for t in R.open_tabs()]
    out = "ran"
    note = ""
    seen["press line"] = await R.js(f"(() => {{ const e = {card}; return e ? e._n.acts.filter(a => a.on === 'click').map(a => a.line.slice(0, 120)) : null; }})()")
    if seen["after card"]["viewing"] != seen["before"]["viewing"]:
        if await R.js(chip("Back")):
            await R.press(chip("Back"), what="Back")
            seen["after Back"] = await state(R)
            shots.append(await R.shot("bypass-back"))
        back_to = seen.get("after Back", {}).get("viewing", "(no Back)")
        routed = seen["after card"]["can_back"] == "yes" and back_to == seen["before"]["viewing"]
        note = (f"card {k[1]!r} ({seen['press line']}) moved viewing {seen['before']['viewing']} -> {seen['after card']['viewing']}; "
                f"tab {seen['after card']['active_tab']} can_back {seen['after card']['can_back']}; Back then went to {back_to}"
                + (" (the page before: the tab's own history)" if routed else " (NOT the page before)"))
        out = "pass" if routed else "fail"
    else:
        note = f"card {k[1]!r} did not change viewing (opens elsewhere?)"
    R.record("bypass", bypass.__doc__, out, note, seen, shots)


async def denied(R):
    """web, file, local, javascript, other-world, missing and deleted targets refuse, leaving the tabs as they were"""
    notes, seen = [], {}
    st0 = R.raw()
    tries = ["https://example.com/", "http://127.0.0.1:8794/", "file:///C:/Windows/win.ini", "local://selection/abc",
             "javascript:alert(1)", "agora://elsewhere/item/a1", "agora://current/item/a99999999", "No such page anywhere"]
    for t in tries:
        said = R.do(f"do browse {R.vid} action=open target=\"{t}\"", "alex")
        seen[t] = said.strip().splitlines()[-1][:160] if said.strip() else ""
        if "refused" not in said and not said.startswith("ERR"):
            notes.append(f"{t}: {seen[t]}")
    said = R.do("do view https://example.com/", "alex")
    seen["view https"] = said.strip()[-160:]
    if "refused" not in said and "stopped" not in said and not said.startswith("ERR"):
        notes.append(f"view https: {seen['view https']}")
    st1 = R.raw()
    if st0 != st1:
        notes.append(f"the viewer changed by a refused target: {st0[0][-200:]} -> {st1[0][-200:]}")
    # deleted page: open it in this tab, open another, remove it, press Back
    doomed = R.made["doomed"]
    R.do(f"do view {doomed}", "alex")
    R.do(f"do view {R.made['Long note A (synthetic)']}", "alex")
    await asyncio.sleep(1.0)
    R.do(f"look {doomed}")
    seen["remove"] = R.do(f"do remove {doomed}").strip()[-120:]
    await asyncio.sleep(1.0)
    before = await state(R)
    if await R.js(chip("Back")):
        await R.press(chip("Back"), what="Back to the removed page")
        await asyncio.sleep(0.6)
    seen["status"] = await R.js("((document.getElementById('status') || {}).textContent || '').slice(0, 600)")
    seen["after Back"] = await state(R)
    shots = [await R.shot("deleted-back")]
    if seen["after Back"]["viewing"] != before["viewing"]:
        notes.append(f"Back to a removed page moved to {seen['after Back']['viewing']}")
    if "unavailable" not in seen["status"] and "refused" not in seen["status"].lower():
        seen["note"] = "no refusal words in the status line"
    R.record("denied", denied.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"{len(tries)} targets and view https refused, tabs unchanged; Back to a removed page stayed on {before['viewing']}, status {seen['status']!r}",
             seen, shots)


async def overflow(R):
    """30 long-titled tabs: the menu scrolls inside itself, names clamp, the HUD never scrolls; the last one selects"""
    notes, seen = [], {}
    for pid in R.made["long"]:
        said = R.do(f"do browse {R.vid} action=new target={pid}", "alex")
        if "refused" in said:
            notes.append(f"new {pid}: {said.strip()[-120:]}")
            break
    await asyncio.sleep(1.5)
    seen["count"] = (await state(R))["tab_count"]
    await menu_close(R)
    await menu_open(R)
    await asyncio.sleep(0.5)
    m = await R.js(f"(() => {{ const rows = {TAB_ROWS}; if (!rows.length) return null; const menu = rows[0].closest('[data-key$=\"/bar/tabs/menu\"]') || rows[0].parentElement.parentElement; "
                   "const r = __tr.R(menu); const hs = rows.map(e => Math.round(e.getBoundingClientRect().height)); "
                   "return { rows: rows.length, r, sh: menu.scrollHeight, ch: menu.clientHeight, sw: menu.scrollWidth, cw: menu.clientWidth, "
                   "rowH: [Math.min(...hs), Math.max(...hs)], clipped: rows.filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).length, "
                   "inView: r[0] >= 0 && r[1] >= 0 && r[0] + r[2] <= innerWidth + 0.5 && r[1] + r[3] <= innerHeight + 0.5 }; })()")
    seen["menu"] = m
    seen["page"] = await R.js("__tr.page()")
    shots = [await R.shot("overflow-menu")]
    p = seen["page"]
    if p["sh"] > p["ih"] or p["sw"] > p["iw"] or p["sy"] or p["sx"]:
        notes.append(f"the HUD scrolls: {p}")
    if not m:
        notes.append("menu did not open")
    else:
        if not m["inView"]:
            notes.append(f"menu reaches outside the page: {m['r']}")
        if m["sh"] <= m["ch"] and m["rows"] < int(seen["count"]):
            notes.append(f"menu shows {m['rows']} of {seen['count']} rows and does not scroll")
        if m["sw"] > m["cw"] + 1:
            notes.append(f"menu scrolls sideways {m['sw']} > {m['cw']}")
        last = R.tabs()[-1]
        mr = m["r"]
        await R.w.wheel(mr[0] + mr[2] / 2, mr[1] + mr[3] / 2, 120 * 40)
        await asyncio.sleep(0.8)
        seen["after wheel"] = await R.js("__tr.page()")
        await R.press(tab_row(last["id"]), what="the last tab")
        seen["selected"] = await state(R)
        if seen["selected"]["active_tab"] != last["tab"]:
            notes.append(f"last row selected {seen['selected']['active_tab']} (want {last['tab']})")
        heading = await R.js(f"(() => {{ const h = [...({V}).querySelectorAll('[data-key$=\"/head/title\"]')].find(__tr.vis); return h ? [__tr.R(h), h.scrollHeight > h.clientHeight + 1] : null; }})()")
        seen["heading"] = heading
        shots.append(await R.shot("overflow-last"))
    R.record("overflow", overflow.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"{seen['count']} tabs; menu {m and m['r']} scrolls inside ({m and m['sh']}>{m and m['ch']}), rows {m and m['rowH']} px, {m and m['clipped']} clamped names, HUD still; last row selected",
             seen, shots)


async def order(R):
    """reused slots (c7704): close three middle tabs, open two new ones; the notes do not grow, the menu lists rows by their order (numbers past 9 too), the new tabs last"""
    notes, seen = [], {}
    all0 = R.tabs()
    open0 = [t for t in all0 if t.get("closed") == "no"]
    if len(open0) < 8:
        R.record("order", order.__doc__, "blocked", f"only {len(open0)} open tabs to work with", {}, [])
        return
    for t in open0[2:5]:
        R.do(f"do browse {R.vid} action=close tab={t['tab']}", "alex")
    for pid in (R.made["Long note A (synthetic)"], R.made["Long note B (synthetic)"]):
        R.do(f"do browse {R.vid} action=new target={pid}", "alex")
    await asyncio.sleep(1.5)
    all1 = R.tabs()
    open1 = [t for t in all1 if t.get("closed") == "no"]
    seen["notes"] = [len(all0), len(all1)]
    if len(all1) > len(all0):
        notes.append(f"tab notes grew {len(all0)} -> {len(all1)} (closed slots not reused)")
    await menu_close(R)
    await menu_open(R)
    await asyncio.sleep(0.5)
    rows = await R.js(f"{TAB_ROWS}.map(e => e.dataset.key.match(/menu\\/(a\\d+)\\/name$/)[1])")
    by_order = [t["id"] for t in sorted(open1, key=lambda t: int(t["order"]) if t["order"].isdigit() else 10 ** 9)]
    seen["menu ids"], seen["by order"] = rows, by_order
    seen["orders"] = [(t["id"], t["order"], t["tab"]) for t in open1]
    st = R.raw()[1]
    keys = re.findall(r'"key": ?"(tab-\d+)"', st) or re.findall(r'"(tab-\d+)"', st)
    seen["state tab keys"] = keys[:60]
    if rows != by_order:
        notes.append(f"menu rows are not in order: first differences {[(i, a, b) for i, (a, b) in enumerate(zip(rows, by_order)) if a != b][:4]}")
    newest = [t["id"] for t in open1 if t not in open0 and t["id"] not in {x["id"] for x in open0}]
    seen["reused/new notes"] = newest
    if newest and by_order[-len(newest):] != newest and set(by_order[-len(newest):]) != set(newest):
        notes.append(f"the new tabs are not last in order: {newest} vs tail {by_order[-len(newest):]}")
    shots = [await R.shot("order-menu")]
    await menu_close(R)
    R.record("order", order.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"notes {seen['notes'][0]} -> {seen['notes'][1]} (slots reused); menu lists {len(rows)} rows by order, new tabs {newest} last", seen, shots)


MENU_BOX = (f"(() => {{ const rows = {TAB_ROWS}; if (!rows.length) return null; const m = rows[0].closest('[data-key$=\"/bar/tabs/menu\"]'); if (!m) return null; "
            "const h = (m.closest('.l-float') || m.parentElement).getBoundingClientRect(), r = __tr.R(m); "
            "return { r, handle: [h.top, h.bottom], sh: m.scrollHeight, ch: m.clientHeight, mh: m.style.maxHeight, rows: rows.length, ih: innerHeight, iw: innerWidth, "
            "up: r[1] + r[3] <= h.top + 1, inView: r[1] >= -0.5 && r[1] + r[3] <= innerHeight + 0.5 && r[0] >= -0.5 && r[0] + r[2] <= innerWidth + 0.5 }; })()")


async def floats(R):
    """the long Tabs menu as a lifted float: inside the page at either edge, scrolls inside, every row reachable by keys, Escape closes it; again after a resize and at 125% zoom"""
    notes, seen, shots, blocked = [], {}, [], []
    n = int((await state(R))["tab_count"])
    if n < 12:
        R.record("floats", floats.__doc__, "blocked", f"only {n} tabs: no long menu", {}, [])
        return
    page0 = await R.js("__tr.page()")

    async def look(tag):
        await menu_close(R)
        await menu_open(R)
        await asyncio.sleep(0.5)
        m = await R.js(MENU_BOX)
        seen[tag] = m
        if not m:
            panel = next((l for l in R.lines("prop:role=home-panel,prop:actor=alex") if "home-viewer" in l), "")
            handle = await R.js(f"(() => {{ const e = {TABS_HANDLE}; return e ? [__tr.vis(e), __tr.R(e), __tr.hit(e)] : null; }})()")
            seen[tag] = {"panel": panel[-60:], "tabs handle": handle, "page": await R.js("__tr.page()")}
            if handle and handle[2] and not handle[2]["ok"]:
                blocked.append(f"{tag}: the Tabs handle is covered by {handle[2]['at'][:40]} at this size (the HUD's layout, not the float)")
            else:
                notes.append(f"{tag}: menu did not open (Tabs handle {handle}; {panel[-30:]})")
            shots.append(await R.shot(f"floats-{tag}-shut"))
            return None
        if not m["inView"]:
            notes.append(f"{tag}: menu reaches outside the page {m['r']} on {m['iw']}x{m['ih']}")
        if m["rows"] > 6 and m["sh"] <= m["ch"] + 1 and m["r"][3] < m["rows"] * 18:
            notes.append(f"{tag}: rows cut and the menu does not scroll ({m['sh']}<={m['ch']})")
        shots.append(await R.shot(f"floats-{tag}"))
        return m

    await look("as-is")
    # keys: into the list, down to the last row; the focused row must be inside the menu's box
    await R.press(TABS_HANDLE, what="the Tabs handle (close)")
    await R.press(TABS_HANDLE, what="the Tabs handle (open)")
    await asyncio.sleep(0.4)
    for _ in range(3):
        await R.w.key("Tab")
        if await R.js(f"{TAB_ROWS}.some(e => e.contains(document.activeElement) || e === document.activeElement || (document.activeElement && document.activeElement.closest && document.activeElement.closest('[data-key*=\"/bar/tabs/menu/\"]')))"):
            break
    # Down until the focus stops moving (a row has two stops, its name and its ×)
    was, still = None, 0
    for _ in range(3 * n + 6):
        await R.w.key("ArrowDown")
        await asyncio.sleep(0.05)
        now = await R.js("(document.activeElement && document.activeElement.dataset && document.activeElement.dataset.key) || ''")
        still = still + 1 if now == was else 0
        was = now
        if still >= 3:
            break
    focus = await R.js("(() => { const a = document.activeElement; const row = a && a.closest && a.closest('[data-key*=\"/bar/tabs/menu/a\"]'); const m = row && row.closest('[data-key$=\"/bar/tabs/menu\"]'); "
                       "if (!row || !m) return {key: a && a.dataset && a.dataset.key}; const r = row.getBoundingClientRect(), b = m.getBoundingClientRect(); "
                       "return {key: row.dataset.key.split('/').slice(-2).join('/'), inside: r.top >= b.top - 1 && r.bottom <= b.bottom + 1, scrollTop: m.scrollTop}; })()")
    # the menu lists by order (slots are reused, so creation order is not menu order): its last row is the highest order
    last_open = sorted((t for t in R.tabs() if t.get("closed") == "no"), key=lambda t: int(t.get("order") or 0))
    seen["keys"] = focus
    if not focus or not focus.get("inside") or (last_open and last_open[-1]["id"] not in (focus.get("key") or "")):
        notes.append(f"keys: the last row was not reached and shown inside the menu ({focus}; last {last_open[-1]['id'] if last_open else None})")
    await R.w.key("Escape")
    await asyncio.sleep(0.4)
    seen["after Escape"] = {"rows": await R.js(f"{TAB_ROWS}.length"), "focus": await R.js("(document.activeElement && document.activeElement.dataset && document.activeElement.dataset.key || document.activeElement.tagName || '').slice(-60)")}
    seen["after Escape"]["panel"] = next((l for l in R.lines("prop:role=home-panel,prop:actor=alex") if "home-viewer" in l), "")[-60:]
    seen["after Escape"]["viewing"] = (await state(R))["viewing"]
    shots.append(await R.shot("floats-after-escape"))
    if seen["after Escape"]["rows"]:
        notes.append("Escape left the menu open")
    if "shelf=yes" in seen["after Escape"]["panel"]:
        notes.append("Escape on the menu also shelved the Viewer")
    # a shorter page (a resize), then 125% zoom: the menu is placed again inside it
    # the real (hidden) window resized through the browser's own window bounds, so posted presses still land: a short
    # page, then the CSS page 125% zoom would give (each side / 1.25; the layout is in CSS px, the DPR stays)
    iw, ih = page0["iw"], page0["ih"]
    win = await R.w.p.call("Browser.getWindowForTarget")
    wid, b0 = win["windowId"], dict(win["bounds"])

    async def size_to(w, h):
        b = dict(b0)
        for _ in range(3):
            pg = await R.js("[innerWidth, innerHeight]")
            if abs(pg[0] - w) <= 2 and abs(pg[1] - h) <= 2:
                break
            cur = (await R.w.p.call("Browser.getWindowBounds", windowId=wid))["bounds"]
            b = {"windowState": "normal", "width": int(cur["width"] + (w - pg[0]) * cur["width"] / max(pg[0], 1)),
                 "height": int(cur["height"] + (h - pg[1]) * cur["width"] / max(pg[0], 1))}
            await R.w.p.call("Browser.setWindowBounds", windowId=wid, bounds=b)
            await asyncio.sleep(1.2)
        return await R.js("__tr.page()")

    try:
        # (0.9: at 0.62 of 800 the HUD gives the viewer tile no room at all, a7544 ran it: its Tabs handle lies under the shelf)
        seen["resized page"] = await size_to(iw, int(ih * 0.9))
        await look("resized")
        seen["zoom-125 page"] = await size_to(int(iw / 1.25), int(ih / 1.25))
        await look("zoom-125")
        await menu_close(R)
    finally:
        await size_to(iw, ih)
    await menu_close(R)
    seen["page after"] = await R.js("__tr.page()")
    if seen["page after"]["sy"] or seen["page after"]["sx"]:
        notes.append(f"the HUD scrolled: {seen['page after']}")
    opened = [k for k in ("as-is", "resized", "zoom-125") if (seen.get(k) or {}).get("r")]
    R.record("floats", floats.__doc__, "fail" if notes else ("pass" if not blocked else "pass (part blocked)"),
             "; ".join(notes + blocked) if notes else "menu inside the page each time (" + ", ".join(f"{k} {seen[k]['iw']}x{seen[k]['ih']}: {seen[k]['r']} {'above' if seen[k]['up'] else 'below'} its handle, max-height {seen[k]['mh'] or 'none'}, scroll {seen[k]['sh']}>{seen[k]['ch']}" for k in opened)
             + f"); last row reached by keys {focus.get('key')}; Escape closed it, Viewer kept" + ("; " + "; ".join(blocked) if blocked else ""),
             seen, shots)


# the painter's acts carry the lines as said, with $names already filled in (do view a7466; do remove a7725)
# (the notices list last: open, it lies over the usage widget)
ROUTE_LENSES = [("home-work", "lens=home-feed"), ("home-house", "lens=home-feed"), ("home-usage", "lens=plan-usage-reader"),
                ("waiting-on-me", "^do view [af]\\d+"), ("home-surface", "^do view [af]\\d+"), ("home-notices", "^do view [af]\\d+; do remove [af]\\d+")]


def press_in(lens, pat):
    return (f"[...document.querySelectorAll('[data-key*=\"lens:{lens}\"]')].filter(__tr.vis).find(e => e._n && (e._n.acts || [])"
            f".some(a => a.on === 'click' && new RegExp({json.dumps(pat)}).test(a.line)) && __tr.hit(e) && __tr.hit(e).ok)")


async def routes(R):
    """every rerouted entry that is drawn: it moves the active tab's own history (Back returns), opens with its lens, unshelves the Viewer, and a notice is still removed"""
    notes, seen, shots, tried = [], {}, [], 0
    # open the notices list, so its rows are drawn
    nh = "[...document.querySelectorAll('[data-key*=\"lens:home-notices\"] .l-float > button, [data-key*=\"lens:home-notices\"] .l-fold-handle')].find(__tr.vis)"
    for lens, pat in ROUTE_LENSES:
        if lens == "home-notices" and await R.js(f"!!{nh}") and not await R.js(f"!!{press_in(lens, pat)}"):
            await R.press(nh, what="the notices list")
            await asyncio.sleep(0.6)
        el = press_in(lens, pat)
        k = await R.js(f"(() => {{ const e = {el}; return e ? [e.dataset.key.split('lens:{lens}')[1].slice(0, 80), e.innerText.trim().slice(0, 40), e._n.acts.filter(a => a.on === 'click').map(a => a.line.slice(0, 140))] : null; }})()")
        if not k:
            diag = await R.js(f"(() => {{ const all = [...document.querySelectorAll('[data-key*=\"lens:{lens}\"]')]; const v = all.filter(__tr.vis); "
                              f"const a = v.filter(e => e._n && (e._n.acts || []).some(a => a.on === 'click')); "
                              f"return {{drawn: all.length, visible: v.length, presses: a.slice(0, 4).map(e => [e.innerText.trim().slice(0, 24), (__tr.hit(e) || {{}}).ok, e._n.acts.filter(a => a.on === 'click').map(a => a.line.slice(0, 90))])}}; }})()")
            seen[lens] = f"no rerouted press to hit (blocked): {diag}"
            continue
        tried += 1
        # the Viewer shelved first where the clause unshelves it: the press must bring it back
        unshelves = "shelf=no" in " ".join(k[2]) or "do view" in " ".join(k[2])
        pre = dict(await state(R))                # the page Back must return to: the active tab's own entry (shelving keeps it)
        try:
            ts = json.loads(R.viewer().get("tabs_state", "") or "{}")
            t = next(t for t in ts["tabs"] if t["key"] == ts["active"])
            pre["viewing"] = t["entries"][t["index"]]["target"]["address"].rsplit("/", 1)[-1] if t["index"] >= 0 else ""
        except (ValueError, KeyError, StopIteration, IndexError):
            pass
        if unshelves:
            R.do("look " + R.vid, "alex")
            R.do(f"do unview {R.vid}", "alex")
            await asyncio.sleep(1.0)
        s0 = await state(R)
        gone = re.search(r"do remove ([af]\d+)", " ".join(k[2]))   # the pressed notice itself (find lists a capped few)
        await R.press(el, what=f"{lens} {k[1]!r}")
        await asyncio.sleep(1.2)
        s1 = await state(R)
        panel = next((l for l in R.lines("prop:role=home-panel,prop:actor=alex") if "home-viewer" in l), "")
        row = {"pressed": k, "before": {x: s0[x] for x in ("viewing", "with", "active_tab", "can_back")},
               "after": {x: s1[x] for x in ("viewing", "with", "active_tab", "can_back")}, "panel": panel[-80:]}
        bad = []
        if s1["viewing"] == s0["viewing"] and s1["with"] == s0["with"]:
            bad.append("nothing opened")
        if s1["active_tab"] != s0["active_tab"]:
            bad.append(f"tab changed {s0['active_tab']} -> {s1['active_tab']}")
        want_lens = re.search(r"lens=([\w-]+)", " ".join(k[2]))
        if want_lens and s1["with"] != want_lens.group(1):
            bad.append(f"lens {s1['with']!r}, want {want_lens.group(1)}")
        if unshelves and "shelf=yes" in panel:
            bad.append("the Viewer stayed shelved")
            # recorded; now bring it out by the copy's door (as alex, copy only) so the journeys after this one can run
            pid = panel.split()[0]
            R.do(f"look {pid}", "alex")
            R.do(f"do prop {pid} shelf=no", "alex")
            await asyncio.sleep(1.2)
        if gone:
            said = R.do(f"examine {gone.group(1)}").strip().splitlines()
            row["notice after"] = said[0][:120] if said else ""
            if "not in the world now" not in row["notice after"]:
                bad.append(f"the pressed notice {gone.group(1)} was not removed ({row['notice after']})")
        if pre["viewing"] and s1["can_back"] == "yes" and not await R.js(f"!!{chip('Back')}"):
            bad.append("no Back chip on the page after the press")
        elif pre["viewing"] and s1["can_back"] == "yes":
            await R.press(chip("Back"), what="Back")
            await asyncio.sleep(0.8)
            back = await state(R)
            row["after Back"] = {x: back[x] for x in ("viewing", "with")}
            if back["viewing"] != pre["viewing"]:
                bad.append(f"Back went to {back['viewing']}, want {pre['viewing']}")
        elif pre["viewing"]:
            bad.append("no Back after the press")
        row["problems"] = bad
        seen[lens] = row
        shots.append(await R.shot(f"route-{lens}"))
        notes += [f"{lens}: {b}" for b in bad]
    if await R.js("[...document.querySelectorAll('[data-key*=\"lens:home-notices\"] .l-float')].some(f => f.dataset.folded !== '1')"):
        await R.press(nh, what="the notices list (close)")
        await asyncio.sleep(0.4)
    out = "blocked" if not tried else ("pass" if not notes else "fail")
    if not tried:
        notes = [f"{l}: {seen[l]}" for l, _ in ROUTE_LENSES]
    R.record("routes", routes.__doc__, out, "; ".join(notes) or f"{tried} rerouted entries pressed; each moved the tab's own history with its lens and Back returned; "
             + "; ".join(f"{l}: {seen[l] if isinstance(seen[l], str) else seen[l]['after']}" for l, _ in ROUTE_LENSES if l in seen), seen, shots)


async def close(R):
    """Close on the active tab moves to its neighbour; closing every tab leaves one blank tab"""
    notes, seen = [], {}
    s0 = await state(R)
    await menu_open(R)
    act = next(t for t in R.tabs() if t.get("active") == "yes" and t.get("closed") == "no")
    await R.press(tab_row(act["id"], "close"), what="Close on the active tab")
    seen["after close"] = await state(R)
    if int(seen["after close"]["tab_count"]) != int(s0["tab_count"]) - 1 or seen["after close"]["active_tab"] == act["tab"]:
        notes.append(f"close: {seen['after close']}")
    shots = [await R.shot("close-one")]
    for t in R.open_tabs():
        R.do(f"do browse {R.vid} action=close tab={t['tab']}", "alex")
    await asyncio.sleep(1.5)
    seen["after all"] = await state(R)
    seen["open notes"] = [(t["tab"], t.get("active")) for t in R.open_tabs()]
    seen["closed notes"] = len([t for t in R.tabs() if t.get("closed") == "yes"])
    if seen["after all"]["tab_count"] != "1" or seen["after all"]["viewing"] != "" or len(seen["open notes"]) != 1:
        notes.append(f"close all: {seen['after all']} {seen['open notes']}")
    shots.append(await R.shot("close-all"))
    R.record("close", close.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"Close moved to {seen['after close']['active_tab']}; all closed left one blank tab ({seen['open notes']}); {seen['closed notes']} closed notes stay in Home base",
             seen, shots)


async def unview(R):
    """× shelves the Viewer and shows the chat, keeping the tabs; the next view brings it back on that tab"""
    notes, seen = [], {}
    await search_open(R, "Long note A", R.made["Long note A (synthetic)"])
    await R.press(chip("New tab"), what="New tab")
    await search_open(R, "Long note B", R.made["Long note B (synthetic)"])
    s0 = await state(R)
    ts0 = R.raw()[1]
    x = f"[...({V}).querySelectorAll('[data-key$=\"/head/close\"]')].find(__tr.vis)"
    await R.press(x, what="×")
    await asyncio.sleep(0.8)
    seen["after x"] = await state(R)
    seen["panels"] = [l for l in R.lines("prop:role=home-panel,prop:actor=alex") if "home-viewer" in l or "jeff-chat" in l]
    shots = [await R.shot("unview")]
    if "shelf=yes" not in next((l for l in seen["panels"] if "home-viewer" in l), ""):
        notes.append("the Viewer panel was not shelved")
    if R.raw()[1] != ts0:
        seen["tabs_state changed by unview"] = True
    await search_open(R, "Long note A", R.made["Long note A (synthetic)"])
    seen["after view"] = await state(R)
    seen["panels after"] = [l for l in R.lines("prop:role=home-panel,prop:actor=alex") if "home-viewer" in l]
    if "shelf=no" not in (seen["panels after"] or [""])[0]:
        notes.append("view did not bring the Viewer back")
    if seen["after view"]["tab_count"] != s0["tab_count"] or seen["after view"]["active_tab"] != s0["active_tab"]:
        notes.append(f"tabs not kept: {s0['tab_count']}/{s0['active_tab']} -> {seen['after view']['tab_count']}/{seen['after view']['active_tab']}")
    if seen["after view"]["can_back"] != "yes":
        notes.append("the tab lost its Back over unview")
    shots.append(await R.shot("unview-restore"))
    R.record("unview", unview.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"× shelved it (viewing {seen['after x']['viewing']!r}), search brought it back on {s0['active_tab']} of {s0['tab_count']} with Back", seen, shots)


async def draft_end(R):
    """the unsent draft, its range and the chat's About row after every journey; nothing was sent"""
    if not getattr(R, "draft0", None):
        R.record("draft-end", draft_end.__doc__, "blocked", "no draft was started (composer cut at this size)", {}, [])
        return
    d = await R.js(DRAFT)
    line = R.lines("prop:role=conversation-draft,prop:actor=alex")
    sent = await R.js("[...document.querySelectorAll('[data-key*=\"lens:jeff-chat\"]')].some(e => e.innerText.includes('unsent tabs review draft') && e.tagName !== 'TEXTAREA' && !e.querySelector('textarea'))")
    notes = []
    if not d or d["v"] != R.draft0["v"]:
        notes.append(f"words {d and d['v']!r}")
    elif (d["s"], d["e"]) != (R.draft0["s"], R.draft0["e"]):
        notes.append(f"range {d['s']}-{d['e']} (was {R.draft0['s']}-{R.draft0['e']})")
    if line != R.draftline0:
        notes.append(f"draft note props {R.draftline0} -> {line}")
    if sent:
        notes.append("the draft text appears outside the composer (sent?)")
    about = (d or {}).get("about", "")
    R.record("draft-end", draft_end.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"words and range {d['s']}-{d['e']} kept, draft note unchanged, nothing sent; About row now {about!r} (was {R.draft0['about']!r})",
             {"start": R.draft0, "end": d, "note": line}, [await R.shot("draft-end")])


ALL = [("probe", probe), ("draft-start", draft_start), ("migrate", migrate), ("show", show), ("history", pins_history), ("new-tab", new_tab),
       ("reading", reading), ("draft-again", draft_start), ("lens", lens), ("open-new-tab", new_tab_menu), ("keyboard", keyboard), ("denied", denied),
       ("bypass", bypass), ("routes", routes), ("overflow", overflow), ("order", order), ("floats", floats), ("search-dup", search_dup), ("close", close), ("unview", unview), ("draft-end", draft_end)]
