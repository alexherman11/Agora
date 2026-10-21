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
    if await R.js("!!__tr.viewer()"):
        R.record("show", show.__doc__, "ran", "the Viewer was already out", {}, [])
        return
    before = await state(R)
    await search_open(R, "Long note A synthetic", R.made["Long note A (synthetic)"])
    after = await state(R)
    ok = await R.wait_for("!!__tr.viewer()", 4)
    R.record("show", show.__doc__, "pass" if ok and after["viewing"] == R.made["Long note A (synthetic)"] else "fail",
             f"Viewer shelved in this copy (viewing {before['viewing']!r}); a search result brought it out on {after['viewing']} in {after['active_tab']}",
             {"before": before, "after": after}, [await R.shot("show")])


async def pins_history(R):
    """pins open in the active tab (mouse); Back and Forward follow the tab's trail; a new page after Back drops Forward"""
    notes, seen = [], {}
    start = (await state(R))["viewing"]
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
    if seen["back2"]["viewing"] != start or seen["back2"]["can_back"] != "no":
        notes.append(f"Back twice: {seen['back2']} (start {start})")
    if await R.js(chip("Back")):
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
    card = "[...document.querySelectorAll('[data-key*=\"lens:home-board\"]')].filter(__tr.vis).find(e => e._n && (e._n.acts || []).some(a => a.on === 'click' && /viewing=/.test(a.line)))"
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
    if seen["after card"]["viewing"] != seen["before"]["viewing"]:
        tabs_after = R.viewer().get("tabs_state", "")
        if await R.js(chip("Back")):
            await R.press(chip("Back"), what="Back")
            seen["after Back"] = await state(R)
            shots.append(await R.shot("bypass-back"))
        note = (f"card {k[1]!r} set viewing {seen['before']['viewing']} -> {seen['after card']['viewing']} directly; "
                f"tab label/state not updated (active {seen['after card']['active_tab']}, can_back {seen['after card']['can_back']}); "
                f"Back then went to {seen.get('after Back', {}).get('viewing', '(no Back)')}")
        out = "fail"
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
       ("bypass", bypass), ("overflow", overflow), ("search-dup", search_dup), ("close", close), ("unview", unview), ("draft-end", draft_end)]
