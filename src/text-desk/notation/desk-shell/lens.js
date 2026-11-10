// lens.js : the generic painter, by paint kind. OWNER: Pike (OWNERS.md, 25 Sep).
// LINE BUDGET (Wren's rule, counted apart from continuity since a361): 150 lines of vocabulary, a guard against growing
// into a worse HTML. Under review: the codex team reports Alex rejected the cap [read: their BRIDGE-NOTES], and pike-8
// proposes admission tests in its place (a general scene contract, an honest text account, one addressed action path,
// preserved viewer state, performance, reuse across unlike tasks, not composable from existing kinds, semantics and
// look only through paint.semantic and style roles). Until Alex decides, lines over 150 are named here: the send's
// in-flight token and lost-answer handling (4 lines). viewer.js holds continuity.
// It paints the scene's painter contract (pike-7 section 6: key, paint, acts, fence, kids) and sends gestures back as
// desk command lines. It knows paint kinds, roles and interaction primitives, and nothing else: no app, no kind, no
// colour, no size. `fence` is opaque: returned with a gesture, never drawn, never compared.
//
// BEFORE YOU ADD TO THE PAINTER OR THE COMPILER (Alex, 14 Oct: "make those changes more general purpose", and leave
// guidance where you and workers will read it; drafted by Claude). This applies to scene.py, lens_ir.py and world.py too.
//  1. Behaviour lives in the world. What Alex asks for should end as words in a lens, a style, a verb or a help note that
//     a resident can change without source. Source adds vocabulary; it never answers one lens's need directly.
//  2. Name the missing word, not the case. If your comment names one lens, one role, one document kind or one chat, the
//     change is bespoke: find the capability underneath (a gesture, a field, a test) and add that instead.
//     Seen 13-14 Oct: `$quoted` (the last words highlighted anywhere) became `on select`, which writes the highlight
//     where the lens says; a chat line's about/quote/mark became any field on any line; `when` on menu entries became
//     `when` on every gesture.
//  3. Shared state is world data. What more than one viewer, or an agent, might read (a highlight, a choice, a mode)
//     belongs in props, lines or things, read by ordinary $reads. The painter keeps only this viewer's hands: caret,
//     draft, scroll, fold, the menu that is open.
//  4. One rule that holds everywhere beats a guess. "The list nearest the sender scrolls" was a guess; "a list that
//     keeps to its end goes there when this viewer's own gesture grows it" is a rule anyone can predict.
//  5. Widen a word's shape before adding a sibling. A special case for one gesture or one field is a second grammar.
//  6. The world judges only what it must (an id names a thing). What a value means (mark=ask) is the lens's and the
//     help's to say; enumerating a lens's values in source fixes one design into the engine.
//  7. Every new word gets a test from an imagined real use, its row in docs/Current Implementation.md, and a Rough
//     spots note (f747) naming what was missing. Try it in a scratch lens before a shared one.
//  Smells: a lens or role name in source; behaviour that depends on DOM nearness; a fix to your own fix within a day;
//  a painter global that two parts read; a default filled in by the compiler read as if the lens had said it (14 Oct:
//  "a text whose lens says commit enter" read every editable text, and documents stopped saving on leaving).
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  document.body.dataset.inspector = q.get("inspect") === "0" ? "off" : "on";   // codex team: inspect=0 gives the painter the full width
  // F7: the style is world data. The lens names it (def.style_name); the painter installs it from the world and again
  // whenever its revision changes, so restyling is a desk edit and repaints live. calm, the seed file, until a lens says.
  let styled = "";
  async function restyle(name, rev) {
    if (styled === name + "@" + rev) return;
    // 8 Oct: the server reads the style once (style.py) and answers with its looks; a text it refuses comes with the
    // refusal and no looks, and this page keeps the last style that read
    const st = await (await fetch(`/api/style?session=${encodeURIComponent(session)}&name=${encodeURIComponent(name)}&theme=${encodeURIComponent(q.get("theme") || "")}`)).json();
    if (st.looks) { Style.install(st.looks); styled = name + "@" + rev; }
    else if (st.refusal || st.refused) V.show("style " + name + " refused: " + (st.refusal || st.refused));
    // Alex, 30 Sep (scrollbars that fit the theme): a style with a `scrollbar` token draws its own bars (lens.html)
    document.documentElement.toggleAttribute("data-bars", !!Style.token("scrollbar"));
    // Alex, 7 Oct ('not everything should be highlighted text boxes'): a style with a `focus` token (a colour) draws
    // the ring round the text being written in that colour; the sheet's own colour makes it nothing
    document.documentElement.toggleAttribute("data-focus", !!Style.token("focus"));
  }
  const V = Viewer(session, who, lens, said, document.getElementById("status"));
  let last = "", sceneAt = 0, def = null;

  // a key's gesture (TEXT.key): sent as the text's own, and the answer comes back so the caret can follow what was made
  async function sendKey(n, line, consume) {
    const observed = { ...(n.fence || {}), at: sceneAt, def }, gesture = V.gesture(n.key, false);
    let r;
    try { r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed, gesture }) })).json(); }
    catch (e) { last = ""; await refresh(true); V.notify(`the answer was lost (${e.message}); your draft is kept`); return null; }
    const t = r.error || r.text || "", failed = r.error || /(^|\n)ERR\b/.test(t);
    if (!failed) { if (consume) V.drop(consume.key); V.hold = null; }
    else if (consume) V.answered(consume.key, t, consume.text);
    last = ""; await refresh(true);
    if (failed) V.notify(t);               // a refresh must not erase the refusal
    return r;
  }

  // a5300: a host verb goes to the program that holds this page (the home base gives it window.pywebview.api.host), which
  // answers "ok ..." or "ERR ..."; a refusal shows as the desk's do. A page in a plain browser has no host and says so.
  async function host(words) {
    const sp = words.indexOf(" "), verb = sp < 0 ? words : words.slice(0, sp), rest = sp < 0 ? "" : words.slice(sp + 1);
    const api = window.pywebview && window.pywebview.api;
    // a5941: `window <lens>` from a page with no home base (an Agora window, a browser tab) opens the lens as a window
    // of this page's own browser, as the home base's verb opens one in Edge: the same painter, person and world
    if ((!api || typeof api.host !== "function") && verb === "window" && /^[a-z][a-z0-9-]*$/.test(rest.trim())) {
      const u = `lens.html?${new URLSearchParams({ session, as: who, lens: rest.trim(), inspect: "0" })}`;
      return window.open(u, "agora-" + rest.trim(), "popup,width=1280,height=760") ? "ok opened" : V.notify(`the browser did not open ${rest.trim()} as a window (a pop-up blocker?)`);
    }
    if (!api || typeof api.host !== "function") return V.notify(`'${verb}' asks the home base, and this page is not in it (open the home base: Ctrl+Alt+J)`);
    let r;
    try { r = await api.host(verb, rest); } catch (e) { return V.notify(`the home base did not answer ${verb}: ${e.message || e}`); }
    if (typeof r === "string" && r.startsWith("ERR")) V.notify(r);
    return r;
  }

  // a8901: `on spoken` acts when its part is painted with words it has not acted on in this page (once per distinct
  // filled line), and only inside the home base, whose voice heard them (src/desktop/voice.py). A desk line
  // goes with a gesture id made from the filled line, so a second page or a reload is answered 'already done'
  const SPOKEN = new Set();
  function idOf(s) {           // two FNV-1a hashes of the line: the same words make the same id in every page
    let a = 0x811c9dc5, b = 0x01000193;
    for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); a = Math.imul(a ^ c, 16777619) >>> 0; b = Math.imul(b ^ c, 2246822519) >>> 0; }
    return "spoken-" + a.toString(16) + b.toString(16);
  }
  function spoken(el, n, a, p) {
    const words = String(p.text != null ? p.text : el.textContent || "").trim();
    if (!words) return;
    const line = a.line.replace(/\$value\b/g, () => TEXT.esc(words)), key = (n.key || "") + "|" + line;
    if (SPOKEN.has(key)) return;
    const api = window.pywebview && window.pywebview.api;
    if (!api || typeof api.host !== "function") return;     // not the home base (or its bridge not ready: the next paint)
    SPOKEN.add(key);
    if (line.startsWith("host ")) host(line.slice(5));
    else send(n, line, undefined, undefined, { gesture: idOf(line) });
  }

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line, draft, more, attachment) {
    const token = V.beginSend(n.key); if (!token) return;       // one send per part at a time (viewer.js)
    // a6010: the pressed part says at once that it was heard (data-sending, drawn by lens.html), until the answer is
    // painted: a press that waits on the world is seen on the next frame, not ~300 ms later
    const pressed = kept.get(n.key) && kept.get(n.key).el;
    if (pressed) pressed.dataset.sending = "1";
    try { return await sendNow(n, line, draft, more, attachment, token); }
    finally { if (pressed) delete pressed.dataset.sending; }
  }
  async function sendNow(n, line, draft, more, attachment, token) {
    const observed = { ...(n.fence || {}), at: sceneAt, def, ...more }, gesture = attachment?.gesture || V.gesture(n.key, draft !== undefined);
    let r;
    try { r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed, gesture, image_context: attachment?.image,
      source_quote: attachment?.quote }) })).json(); }
    catch (e) {      // a1008: the next scene is painted even if it is unchanged, so the kept draft can be sent again (same id)
      last = ""; V.answered(n.key, `the answer was lost (${e.message}); whether it was done is unknown until the view repaints`, draft, token); return refresh(true);
    }
    const t = r.text || r.error || ""; V.answered(n.key, r.error || t.startsWith("ERR") ? t : null, draft, token);
    // 14 Oct (Alex: 'the conversation should also scroll automatically when i send'): a list that keeps to its end
    // (scroll end) and grows by this viewer's own gesture goes to its end, wherever the reader had scrolled it
    const had = new Map([...paint.querySelectorAll('[data-scroll="end"]')].map(f => [f.dataset.key, new Set([...f.children].map(c => c.dataset.key))]));
    await refresh(true);
    if (!r.error) for (const f of paint.querySelectorAll('[data-scroll="end"]')) {
      const was = had.get(f.dataset.key);
      if (was && [...f.children].some(c => c.dataset.key && !was.has(c.dataset.key))) f.scrollTop = f.scrollHeight;
    }
    // a1008, the cause of e1851/e1852: typed words live in the element, not in its signature, so a composer whose
    // line was sent was reused still showing it, and its next blur sent it again. Once no draft holds them, they go.
    const k = kept.get(n.key), p = k && k.el._n.paint;
    if (k && k.el._composer) k.el._composer.sync();
    else if (p && p.text != null && !p.markdown && !p.media && draft !== undefined && !V.drafts.has(n.key) && k.el.textContent !== (p.runs ? p.runs.map(x => x.text).join("") : p.text)) {
      if (p.runs) runs(k.el, p.runs); else k.el.textContent = p.text; V.mark(k.el, n.key);
    }
    return r;
  }
  let imageCommentsBusy = () => false;
  let resizing = false;
  const dividers = window.Dividers?.install(paint, {
    send, refresh: () => refresh(true), busy: () => !!carrying || resizing,
    hold: held => { resizing = held; }
  });
  const partitions = window.PartitionUI?.install(paint, {
    send, refresh: () => refresh(true), busy: () => !!carrying || resizing,
    hold: held => { resizing = held; }
  });
  async function startImageComments() {
    try {
      // A retained HTML page can meet newer JS during a live update. An optional
      // interaction must never stop the entire lens from painting.
      if (typeof ImageComments !== "function") await new Promise((resolve, reject) => {
        const script = document.createElement("script"); script.src = "image-comments.js";
        const timer = setTimeout(() => reject(new Error("image comment controls did not load")), 5000);
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = () => { clearTimeout(timer); reject(new Error("image comment controls did not load")); };
        document.head.append(script);
      });
      imageCommentsBusy = ImageComments(paint, (n, line, observed, attachment) => send(n, line, undefined, observed, attachment),
        () => ({ at: sceneAt, def }), () => V.show("Image selection could not be captured. Please try again."));
    } catch (e) { V.show(`The document is available, but ${e.message}. Reload to retry image comments.`); }
  }

  // Iris, Astra: a part whose painting did not change keeps its element; only what changed is made again. Pike (run 1):
  // the signature is what is drawn (paint, the shapes of the acts, the kids' keys), never the fence.
  let kept = new Map(), next = new Map();
  function make(n) {
    const old = kept.get(n.key), p = n.paint || {};
    // a6067: a document is one element for as long as its key and its lens's words for it stand (rule 1): the desk's new
    // words go INTO it (textedit.js fits them over what this window has not sent), never a new element under the caret
    if (old && old.el._te && p.markdown && old.el._teConf === textConf(n, p)) {
      try { textFresh(old.el, n, p); old.sig = null; next.set(n.key, old); return old.el; }
      catch (e) { console.warn("a document could not take the desk's new words; it is drawn again", e); }   // a6452
    }
    // Keep the person's DOM and original gesture provenance. A newer scene can
    // update read-only wait status, never substitute another action or fence.
    if (old && V.hold === n.key) { old.el._next = n; next.set(n.key, old); return old.el; }
    const sig = JSON.stringify([p, n.acts.map(a => [a.on, a.line, a.part, a.label]), n.kids.map(k => k.key), V.drafts.get(n.key)]);
    // a6431: a page in a frame is one element for as long as it shows the same page: a new size, turn or toggle changes
    // the frame where it stands (a new element would load the page again)
    if (old && old.el._page && p.page && old.el._page.src === p.page.src) {
      old.el._n = n; old.sig = sig; old.el.className = (p.role ? Style.roleClass(p.role) + " " : "") + "t-page";
      old.el._page.update(p.page); next.set(n.key, old); return old.el;
    }
    if (old && old.el._composer && old.el._composer.config === JSON.stringify([p, n.acts])) {
      old.el._n = n; old.sig = sig; old.el._composer.sync(); next.set(n.key, old); return old.el;
    }
    if (old && old.sig === sig) { old.el._n = n; if (V.reuse(old.el, n.kids.map(make), p.text != null)) { tracks(old.el); next.set(n.key, old); return old.el; } }
    const el = document.createElement("div");
    // A bounded partition's changing children must not change its ancestors'
    // intrinsic size/baseline (and therefore the desk frame) on focus exit.
    if (p.partition) el.style.contain = "size layout";
    el._n = n; el.hidden = !!p.absent; el.dataset.key = n.key;   // Iris: with the key on the paint, agreement is a join
    if(n.tiling_list)el.dataset.tilingList='true';
    el.id = "part:" + n.key;  // stable native part identity for platform accessibility clients
    next.set(n.key, { el, sig }); if (p.why) el.dataset.why = p.why;
    const role = p.role || (p.state || p.cut ? "cut" : null);    // a bind that is not live, or a clamp's leaf, says so in `cut`
    if (role) el.className = Style.roleClass(role);
    if (p.kind === "frame") el.classList.add("l-" + p.flow);
    if (p.box) { el.classList.add("boxed"); Object.assign(el.style, { left: p.box[0] + "px", top: p.box[1] + "px", width: p.box[2] + "px", height: p.box[3] + "px" }); }
    // a6431: `page`: the page the words name, the real painter at a device's size (page.js); `on pick` names a part of it
    if (p.text != null && p.page && window.Page) Page.draw(el, p.page, { session, who,
      canPick: () => el._n.acts.some(a => a.on === "pick"),
      pick: async (name, key) => { for (const a of el._n.acts.filter(a => a.on === "pick")) await send(el._n, a.line.replace(/\$value\b/g, () => TEXT.esc(name)).replace(/\$part\b/g, () => TEXT.esc(key))); } });
    else if (p.text != null && p.markdown) markdown(el, n, p);
    else if (p.text != null && p.picture) { picture(el, p.text); pictureRegions(el, p.regions || []); }
    // `wave` (14 Oct): a role that waves draws each character as its own span, each a beat after the one before
    else if (p.text != null && role && ((Style.style || {}).roles || {})[role] && Style.style.roles[role].look.wave)
      el.replaceChildren(...[...p.text].map((ch, i) => Object.assign(document.createElement("span"), { className: "t-wave", textContent: ch, style: `--i:${i}` })));
    else if (p.text != null) {
      const words = V.words(n.key, p.text, n.fence);
      if (p.runs && words === p.text) runs(el, p.runs); else el.textContent = words;
      if (p.light && words === p.text) light(el, p.light);
      V.mark(el, n.key);
      if (p.wrap === "verbatim") el.classList.add("t-verbatim");
      if (p.clamp) {
        el.classList.add("clamp"); el.style.webkitLineClamp = p.clamp;
        // 13 Oct (Alex: a long comment 'can get truncated with a see more type thing'): a clamped text that is cut and
        // has no press of its own opens on a press and closes on the next. This viewer's own, as a fold is; no event.
        if (!n.acts.some(a => a.on === "click" || a.on === "edit")) {
          el.dataset.clamped = "1";
          if (V.folded("open:" + n.key, false)) { el.classList.remove("clamp"); el.dataset.opened = "1"; }
          el.addEventListener("click", () => {
            if (String(getSelection())) return;                 // highlighting words is not a press
            if (el.closest("[data-fold-inline] > [data-peek]")) return;   // a5359: in an inline fold's peek, the press opens the fold
            // the cut texts of one part open and close together: a comment and the replies under it (Alex, 13 Oct)
            const group = [...el.parentElement.querySelectorAll(":scope > [data-clamped]")];
            const open = !group.some(g => g.dataset.opened === "1");
            if (open && !group.some(g => g.scrollHeight > g.clientHeight + 1)) return;        // nothing is cut
            for (const g of group) { g.classList.toggle("clamp", !open); g.dataset.opened = open ? "1" : ""; V.fold("open:" + g._n.key, open); }
            settle();
          });
        }
      }
    }
    if (p.live && p.text != null) live(el, n, p);
    // a5941: `media`: the films and pictures the words name, drawn by media.js; Pop out sends the part's `on pop` acts
    // in order, desk lines and host verbs alike, with $value the path as written
    // a6452: in a Markdown text, a picture the document drew in its place is not drawn again under the words
    const inline = p.media && el._te ? new Set([...el.querySelectorAll("img.md-img[data-media]")].map(i => i.dataset.media)) : null;
    const media = inline && inline.size ? { ...p.media, items: p.media.items.filter(i => !inline.has(i.src)) } : p.media;
    if (media && window.Media) Media.draw(el, media, n.acts.some(a => a.on === "pop") ? item => popMedia(el, item) : null);
    if (p.semantic) semantic(el, p.semantic);                 // before frames: a fold's own state wins over the default
    if (p.kind === "frame") frames(el, n, p);
    // a weight, as a track is; in a row, a share also fills the row's height (lens.html: .l-row > [data-share]). 1 Oct:
    // Sable's a1266 made the Board's lanes a row of shares (was grid 1 1 1), rows align on baselines, and every lane
    // shrank to its title, so each lane's scrolling list was 0 high and Alex's Board looked empty
    if (p.share != null) { el.style.flex = `${p.share} 1 0`; el.style.minWidth = el.style.minHeight = "0"; el.dataset.share = "1"; }
    // a grid given a share is bounded, so it divides its height among its rows and its cells fill them; a cell with
    // `scroll` then scrolls inside the window instead of the page growing (Alex, 29 Sep: the window is bounded)
    if (p.share != null && p.tracks && !/^fill /.test(p.tracks[0])) { el.dataset.bounded = "1"; el.style.gridAutoRows = "minmax(0, 1fr)"; el.style.alignItems = "stretch"; }
    if (p.lines && p.commit !== "explicit") { el.style.minHeight = p.lines[0] + "lh"; if (p.lines[1]) el.style.maxHeight = p.lines[1] + "lh"; el.style.overflowY = "auto"; }
    if (p.hint) el.dataset.hint = p.hint;       // Juniper: what an empty input is for; paint only, never content
    if (p.caret) el.dataset.caret = p.caret.join(" ");    // a6642: what brings the caret here from anywhere (caretKeys)
    if (p.arrows) arrows(el);
    if (p.tip && p.tip[0]) { el._tip = p.tip; el.dataset.tip = p.tip[0]; el.setAttribute("aria-label", p.tip.join(": ")); }   // a6271
    if (p.peek) el.dataset.peek = "1";          // a1032: stays shown while its parent is folded (lens.html)
    if (Number.isInteger(p.peek)) { el.dataset.peekLines = p.peek; el.style.setProperty("--peek-lines", p.peek); }
    for (const a of n.acts) {
      // Alex, 7 Oct (buttons on top of a document): a button that presses a key, or names $focus, acts on the text the
      // caret is in. It must not take the caret, and its gesture is the text's own: sent with what that text showed.
      const onText = a.on === "click" && (a.line.startsWith("press ") || a.line.includes("$focus"));
      if (onText) { el.dataset.tool = "1"; el.addEventListener("mousedown", e => e.preventDefault()); }
      if (onText) el.addEventListener("click", () => {
        const t = TEXT.last && TEXT.last.isConnected ? TEXT.last : null;
        if (!t && /^press Ctrl\+[ES]$/.test(a.line)) return TEXT.press(el, a.line.slice(6));   // a5820: the page's document
        if (!t) return V.show("put the caret in a text first: this button acts on the text being written");
        if (a.line.startsWith("press ")) { t.focus(); return TEXT.press(t, a.line.slice(6)); }
        TEXT.wait(TEXT.tool(t, a.line));
      });
      // a5300: `on click host <verb> [words]` asks the program the page is painted in (the home base's bridge), never the desk
      else if (a.on === "click" && a.line.startsWith("host ")) { el.dataset.host = a.line.slice(5); el.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); host(a.line.slice(5)); }); }
      else if (a.on === "click") el.addEventListener("click", e => {     // a click knows where it landed: $x $y in this part's own space
        if (e.target !== el && a.line.includes("$x")) return;
        const r = el.getBoundingClientRect();
        // 13 Oct (Alex: 'clicking this checkbox takes too long, i want instant response'): the press shows at once, on
        // the part itself, while the desk answers; the world's answer still decides what is drawn after
        el.dataset.pressed = "1";
        send(el._n, a.line.replace("$x", Math.round(e.clientX - r.left + el.scrollLeft)).replace("$y", Math.round(e.clientY - r.top + el.scrollTop)))
          .finally(() => { delete el.dataset.pressed; });
      });
      if (a.on === "spoken") spoken(el, n, a, p);
      if (a.on === "edit" && !p.markdown) edits(el, n, a);
      if (a.on === "drag" && p.box) drags(el, n, a);
      if (a.on === "carry") carries(el, n);
      if (a.on === "drop") { el.dataset.drop = a.part; (el._drops = el._drops || []).push(a); }
      if (a.on === "click") el._clicks = true;
      // a5994: `on double` is a double-click on the part; one on a button inside it is that button's (two presses)
      if (a.on === "double") el.addEventListener("dblclick", e => {
        for (let t = e.target; t && t !== el; t = t.parentElement) if (t._clicks || t._drops || t.isContentEditable || /^(BUTTON|INPUT|TEXTAREA|A)$/.test(t.tagName)) return;
        e.preventDefault(); getSelection().removeAllRanges(); send(el._n, a.line);
      });
      if (a.on === "menu") el.dataset.menu = "1";                 // its entries are read from el._n when the menu opens
    }
    for (const k of n.kids) el.appendChild(make(k));
    if (p.tracks) tracks(el);
    return el;
  }

  // pike-7 section 9, lowered by Jeff (5bb7f7f): a grid's tracks hold its direct children in fixed slots, and a folded
  // child's track shrinks to its handle; gap, scroll and measure on any frame; fold is the lens's default, overridden by
  // this viewer only, never an event. The fold handle is the one control the painter draws itself (role tool).
  function frames(el, n, p) {
    if (p.remember) el.dataset.remember = p.remember;
    if (p.gap != null) el.style.gap = typeof p.gap === "number" ? p.gap + "px" : p.gap[0] === "/" ? `calc(var(--t-gap) / ${p.gap.slice(1)})` : `calc(${p.gap.slice(1)} * var(--t-gap))`;   // F10: steps of the style's gap
    if (p.scroll && p.scroll !== "none" && p.scroll !== "none end") { el.style.overflow = "auto"; el.dataset.scroll = p.scroll; }
    // a5496 (Alex, 15 Oct: 'I don't want the interface to scroll'): `scroll none` never scrolls; what does not fit is
    // cut, and a cut part fades at its foot (lens.html), so the eye knows there is more (settle marks data-cut).
    // `scroll none end` is cut at its head instead, its end always in view: a chat's newest lines
    // a5736: clip, not hidden: a hidden box still scrolls by a drag that selects text, the keys or scrollIntoView
    if (p.scroll === "none" || p.scroll === "none end") { el.style.overflow = "clip"; el.dataset.scroll = "none"; }
    if (p.scroll === "none end") el.dataset.atEnd = "1";
    if (p.measure) { el.style.maxWidth = p.measure; el.style.marginInline = "auto"; }
    if (!n.acts.some(a => a.on === "fold")) return;
    // Alex, 29 Sep: a floating fold is a menu. Its open contents are drawn over the page below the handle, it opens for
    // a moment (not remembered), and Escape or a press outside closes it. Its handle's look is role `menu`, a plain
    // fold's is `fold`, each over `tool`, so a style that names neither keeps the tool look.
    const float = !!(p.fold && p.fold.float);
    const h = document.createElement("button"); h.type = "button";
    h.className = Style.roleClass("tool") + " " + Style.roleClass((p.fold && p.fold.handle) || (float ? "menu" : "fold"));
    h.setAttribute("aria-label", (p.fold && p.fold.label) || n.part || "section");
    const dflt = p.fold ? p.fold.folded : !!p.folded;          // Jeff 75e39d8: fold is {folded, label}; 5bb7f7f emitted folded: true
    const lab = (p.fold && p.fold.label) || "";                  // the lens's handle label is drawn, not only announced
    const set = f => { el.dataset.folded = f ? "1" : ""; el.setAttribute("aria-expanded", String(!f)); h.textContent = (f ? "▸" : "▾") + (lab ? " " + lab : ""); h.setAttribute("aria-expanded", String(!f)); if (el.parentElement) tracks(el.parentElement); };
    if (float) { el.classList.add("l-float"); el._close = () => set(true); }
    // a5359 (Alex c5367: a card opens in place on a press on its title): `fold ... inline` draws the handle beside the
    // part's peek on one line (lens.html), and a press anywhere on the peek is a press on the handle, unless it lands on
    // a control of the peek's own (a part with a click or an edit, a link, a button) or ends a highlight
    if (p.fold && p.fold.inline) {
      el.dataset.foldInline = "1";
      el.addEventListener("click", e => {
        if (h.contains(e.target) || String(getSelection())) return;
        const peek = e.target.closest && e.target.closest("[data-peek]");
        if (!peek || peek.parentElement !== el) return;
        for (let t = e.target; t && t !== el; t = t.parentElement)
          if (t.matches("a, button, input, textarea, [contenteditable='true']") || (t._n && t._n.acts.some(a => a.on === "click" || a.on === "edit"))) return;
        h.click();
      });
    }
    el._fold = f => { V.fold(n.key, f); set(f); };
    const group = p.fold && p.fold.group;
    if (group) el.dataset.foldGroup = group;
    const opened = () => { for (const a of el._n.acts.filter(a => a.on === "open")) send(el._n, a.line); };
    h.addEventListener("click", () => {
      if (float) { const f = el.dataset.folded !== "1"; set(f); placeFloat(el); settle(); if (!f) opened(); return; }
      const f = !V.folded(n.key, dflt); V.fold(n.key, f); set(f);
      // `fold ... group <name>` (Alex, 30 Sep): opening one folds its open siblings in the same group, an accordion
      if (!f && group && el.parentElement)
        [...el.parentElement.children].forEach(s => { if (s !== el && s.dataset.foldGroup === group && s.dataset.folded !== "1" && s._fold) s._fold(true); });
      settle();
      if (!f) opened();
    });
    // a6265: a float open when its part is made again (its words or acts changed: a popover's feed lines arriving, the
    // press that opened it recorded) stays open; it still closes only by Escape, a press outside, or its handle
    const prev = float && kept.get(n.key);
    const stay = !!(prev && prev.el !== el && prev.el.classList.contains("l-float") && prev.el.dataset.folded === "");
    el.prepend(h); set(float ? (stay ? false : dflt) : V.folded(n.key, dflt));
  }
  // a6265: an open float inside a part that never scrolls (`scroll none` clips) was cut at that part's edge and lay under
  // the next column (a popover from a line of At work, in a narrow column): it is lifted into the page's top layer (a
  // manual popover, which no clip or later sibling covers), under its line, or above it when the page has no room below.
  // Closed, it goes back to the page's flow (lens.html's .l-float).
  // a7544 (the Tabs menu ran off an 800 px page): a lifted float is also sized to the page. It opens on the side of its
  // line with room for it, or else the side with more room, and is no taller than that room; the rest scrolls inside it
  // (lens.html gives it overflow auto), so every row stays reachable by wheel and keys. Placed again on each settle
  // (repaint, scroll, resize).
  function placeFloat(el) {
    if (!el.parentElement || !el.parentElement.closest('[data-scroll="none"]')) return;
    const r = el.getBoundingClientRect();
    for (const c of el.querySelectorAll(":scope > [data-key]:not([data-peek])")) {
      if (el.dataset.folded === "1") {
        if (c.popover && c.matches(":popover-open")) c.hidePopover();
        c.style.position = c.style.left = c.style.top = c.style.maxHeight = ""; continue;
      }
      if (c.showPopover && !c.popover) c.popover = "manual";
      if (c.popover && !c.matches(":popover-open")) try { c.showPopover(); } catch (e) {}
      c.style.position = "fixed"; c.style.maxHeight = "";
      const w = c.offsetWidth, h = c.offsetHeight, edge = 4;
      const below = innerHeight - r.bottom - edge, above = r.top - edge;
      const up = h > below && above > below, room = Math.max(0, up ? above : below);
      if (h > room) c.style.maxHeight = room + "px";
      c.style.left = Math.max(0, Math.min(r.left, innerWidth - w)) + "px";
      c.style.top = (up ? r.top - Math.min(h, room) : r.bottom) + "px";
    }
  }
  // a6642 (Alex, 20 Oct: search results chosen with the arrow keys and Enter): `arrows` on a frame. Its stops are the
  // texts being written and the presses inside it, in the order drawn (a float lifted into the top layer is still
  // inside it). Up and Down go from stop to stop; Down past the last opens a closed float inside it. A press in hand
  // takes Enter as a button does (semantic); Enter in a text whose words are unchanged presses the first press after
  // it, so a search sent once is opened by Enter again. The viewer's hands only: nothing is sent until a press
  const writes = t => t.isContentEditable || t.tagName === "TEXTAREA";
  function arrows(el) {
    el.dataset.arrows = "1";
    const stops = () => [...el.querySelectorAll("[data-key], textarea")].filter(t => (writes(t) || t._clicks) && t.getClientRects().length);
    el.addEventListener("keydown", e => {
      if (e.altKey || e.ctrlKey || e.metaKey || e.isComposing) return;
      const t = e.target, all = stops(), i = all.indexOf(t);
      if (i < 0) return;
      const lines = t._n && t._n.paint && t._n.paint.lines;
      if ((e.key === "ArrowDown" || e.key === "ArrowUp") && !(writes(t) && lines && (lines[1] == null || lines[1] > 1))) {
        const down = e.key === "ArrowDown";
        let to = all[i + (down ? 1 : -1)];
        if (!to && down) {
          const h = [...el.querySelectorAll('.l-float[data-folded="1"] > button')][0];
          if (h) { h.click(); const again = stops(); to = again[again.indexOf(t) + 1]; }
        }
        if (!to) return;
        e.preventDefault();
        if (!writes(to) && to.tabIndex < 0) to.tabIndex = -1;
        to.focus();
        if (writes(to) && to.isContentEditable) getSelection().selectAllChildren(to), getSelection().collapseToEnd();
        return;
      }
      if (e.key === "Enter" && !writes(t)) { e.preventDefault(); e.stopPropagation(); t.click(); return; }   // a press that is a frame has no button keys of its own
      if (e.key === "Enter" && !e.shiftKey && writes(t)) {
        const said = ((t._n && t._n.paint && t._n.paint.text) || "").trim();
        if (!said || (t.isContentEditable ? t.innerText : t.value).trim() !== said) return;
        const first = all.slice(i + 1).find(s => !writes(s));
        if (!first) return;
        e.preventDefault(); e.stopPropagation(); first.click();
      }
    }, true);
  }
  // a6642: `caret <key>|typing` on a text. A key it names (Ctrl+K, ...) pressed anywhere that no text took (a document's
  // own Ctrl+K stays the document's), or a letter typed while no text has the caret (`typing`), brings the caret to the
  // first such text drawn, at its end; a typed letter lands in it
  document.addEventListener("keydown", e => {
    if (e.defaultPrevented || e.isComposing || e.altKey || document.getElementById("menu-pop")) return;
    const a = document.activeElement, busy = a && a !== document.body && (writes(a) || /^(INPUT|SELECT)$/.test(a.tagName));
    const ctrl = e.ctrlKey || e.metaKey, combo = (ctrl ? "Ctrl+" : "") + (e.key.length === 1 ? e.key.toUpperCase() : e.key);
    const letter = !ctrl && e.key.length === 1 && e.key.trim() !== "";
    if (busy && !ctrl) return;
    const want = t => { const ks = t.dataset.caret.split(" "); return ks.includes(combo) || (letter && !busy && ks.includes("typing")); };
    const to = [...paint.querySelectorAll("[data-caret]")].find(t => t.getClientRects().length && want(t));
    if (!to || to === a) return;
    e.preventDefault();
    to.focus(); getSelection().selectAllChildren(to); getSelection().collapseToEnd();
    if (letter && !to.dataset.caret.split(" ").includes(combo)) document.execCommand("insertText", false, e.key);
  });
  const closeFloats = keep => document.querySelectorAll('.l-float:not([data-folded="1"])').forEach(m => { if (!m.contains(keep)) { m._close(); placeFloat(m); } });
  document.addEventListener("pointerdown", e => closeFloats(e.target));
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeFloats(null); });

  // Alex, 29 Sep ("native right click behavior"): a part's own menu, from its `on menu "<label>" do ...` entries, opened
  // by a right-click or the menu key anywhere on it (the innermost part that has entries), including editable words.
  // Input composers, a part with no entries, and Shift-right-click keep the browser's menu.
  let pop = null;
  const menuDrafts = new Map();
  function placeMenuDrafts() {
    for (const d of menuDrafts.values()) {
      const anchor = paint.querySelector(`[data-key="${CSS.escape(d.anchor)}"]`);
      if (!anchor || !anchor.getClientRects().length) { d.box.hidden = true; continue; }
      const r = anchor.getBoundingClientRect(), view = paint.getBoundingClientRect();
      d.box.hidden = r.bottom < view.top || r.top > view.bottom;
      d.box.style.left = Math.max(4, Math.min(r.left + d.dx, innerWidth - d.box.offsetWidth - 4)) + "px";
      d.box.style.top = (r.top + d.dy) + "px";
    }
  }
  function menuComposer(box, el, action, fill, x, y) {
    const key = el._n.key + "/composer/" + action.label;
    closeMenu();
    if (menuDrafts.has(key)) { menuDrafts.get(key).input.focus(); return; }
    const n = { key, fence: el._n.fence }, r = el.getBoundingClientRect();
    if (!x && !y) { x = r.left + 8; y = r.top + 8; }
    box.removeAttribute("id"); box.classList.add("menu-draft"); box.setAttribute("role", "group");
    box.setAttribute("aria-label", action.label + " draft");
    const input = document.createElement("textarea"); input.rows = 4; input.placeholder = action.label;
    input.setAttribute("aria-label", action.label); input.className = Style.roleClass("menu.ask");
    const bar = document.createElement("div"); bar.className = "composer-actions";
    const post = document.createElement("button"), discard = document.createElement("button");
    post.type = discard.type = "button"; post.textContent = "Send"; discard.textContent = "Discard";
    post.className = Style.roleClass("button"); discard.className = Style.roleClass("tool");
    const state = document.createElement("span"); state.className = Style.roleClass("meta"); state.textContent = "Unsent";
    bar.append(post, discard, state);
    // 14 Oct (Alex: the box grew as wide as the words it quoted; they are highlighted right above it): no copy of them here
    box.replaceChildren(input, bar);
    const d = { box, input, anchor: el._n.key, dx: x - r.left, dy: y - r.top };
    menuDrafts.set(key, d); document.body.append(box); placeMenuDrafts();
    const drop = () => { box.remove(); menuDrafts.delete(key); };
    input.addEventListener("input", () => { V.typed(key, input.value, n); post.disabled = !input.value.trim(); });
    // a6067: its keys, undo and composition are the continuous-text module's, as every typed text's are
    if (window.TextEdit) TextEdit.attach(input, { text: "", hooks: { notify: t => V.notify(t),
      changed: st => { if ((V.drafts.get(key) || {}).text !== st.text) { V.typed(key, st.text, n); post.disabled = !st.text.trim(); } } } });
    post.disabled = true;
    post.onclick = async () => {
      if (!input.value.trim() || post.disabled) return;
      const raw = input.value; post.disabled = discard.disabled = true; state.textContent = "Sending…";
      // The command and quotation belong to the place where composition began, never the latest selection.
      const line = fill(action.line, TEXT.esc(raw));
      if (line == null) { post.disabled = discard.disabled = false; state.textContent = "Not sent — the words you selected changed; select them again"; return; }
      await send(n, line, raw);
      if (!V.drafts.has(key)) drop();
      else { post.disabled = !input.value.trim(); discard.disabled = false; state.textContent = "Not sent — retry or discard"; }
    };
    discard.onclick = () => { if (V.drop(key)) drop(); };
    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); post.click(); }
      if (e.key === "Escape") { e.preventDefault(); input.blur(); }
    });
    input.focus();
  }
  // a7625: a menu that closes without an action puts back the words that were selected when it opened
  function closeMenu(refocus) {
    if (!pop) return; const back = pop._from, snap = pop._snap; pop.remove(); pop = null;
    if (refocus && back && back.focus) back.focus();
    if (snap && !snap.spent) SEL.restore(snap);
  }
  // a7625 (Alex, 20 Oct: 'I should be able to highlight and then right click to get options ... comment on it, copy,
  // cut, etc. Short list of relevant verbs'). Words deliberately selected in the painted page get a short menu of their
    // own: explicit world-authored prepare entries (never `on select`),
  // the part's own `on menu` entries, Copy, and Cut only in words being written. A right-click inside the selection never
  // replaces it (it is kept from the press, before the browser moves it); outside it, the menu is the part's as before.
  // `$quoted` and `$quoted_in` (reserved since 13 Oct) are the selected words exactly as the source has them, and the
  // thing they are in: a Markdown text gives its source's own slice (TextEdit's anchor), any other text its drawn words
  // only when the source holds them as they are. An entry naming them is refused when the thing changed since the words
  // were selected (its fence: the same item at the same revision), never by what is merely still on the screen.
  // Text inside something that carries has no press-selection of its own (the carry owns the press): its menu offers
  // "Select text". Shift+right-click, and words in an input or a textarea, keep the browser's menu.
  const SEL = {
    press: null,
    part(node) {
      let k = node && (node.nodeType === 1 ? node : node.parentElement);
      k = k && k.closest ? k.closest("[data-key]") : null;
      while (k && !(k._n && (k._n.paint.source || (k._n.fence || {}).item))) k = k.parentElement && k.parentElement.closest("[data-key]");
      return k && paint.contains(k) ? k : null;
    },
    inside(range, x, y) {
      for (const r of range.getClientRects()) if (x >= r.left - 2 && x <= r.right + 2 && y >= r.top - 2 && y <= r.bottom + 2) return true;
      return false;
    },
    norm: s => String(s).replace(/\s+/g, " ").trim(),
    snapshot(range) {
      const words = String(range), k = SEL.part(range.commonAncestorContainer);
      const binding = k && k._n.paint.source;
      const snap = { range: range.cloneRange(), words, key: k && k.dataset.key, item: binding?.item, rev: binding?.rev,
        field: binding?.field, start: null, end: null,
        quoted: null, why: "", editable: false, md: null };
      if (!k) { snap.why = "these words are not one thing's"; return snap; }
      const at = range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement;
      const md = at && at.closest(".md-part");
      if (md && md._md && md.contains(range.endContainer)) {
        snap.md = md; snap.localSource = md._md.src();
        const ed = at.closest('[contenteditable="true"]');
        snap.editable = !!ed && ed.contains(range.endContainer);
        const s = getSelection(); s.removeAllRanges(); s.addRange(range);       // the module reads the live selection
        const an = md._md.anchor && md._md.anchor();
        if (binding && an && an.quote && !an.unsent) {
          snap.quoted = an.quote; snap.start = an.start; snap.end = an.end;
        }
        else snap.why = "these words could not be found in the document's source";
      } else {
        const source = (k._n.paint && k._n.paint.text) || "";
        // DOM offsets distinguish repeated words; transformed labels fail closed.
        const prefix = document.createRange(); prefix.selectNodeContents(k); prefix.setEnd(range.startContainer, range.startOffset);
        const start = String(prefix).length, end = start + words.length;
        if (binding && k.textContent === source && source.slice(start, end) === words) {
          snap.quoted = words; snap.start = start; snap.end = end;
        }
        else snap.why = "these words are drawn differently from their source; select them in its source (Ctrl+E) to quote them";
      }
      return snap;
    },
    fresh(snap) {
      const now = snap.key && paint.querySelector(`[data-key="${CSS.escape(snap.key)}"]`), f = now && now._n && now._n.paint.source;
      return !!f && f.item === snap.item && f.rev === snap.rev;
    },
    restore(snap) {
      if (!snap.range.startContainer.isConnected || !snap.range.endContainer.isConnected) return false;
      const s = getSelection(); s.removeAllRanges(); s.addRange(snap.range); return true;
    },
    async copy(snap) {
      let ok = SEL.restore(snap) && String(getSelection()) === snap.words && document.execCommand("copy");
      if (!ok && navigator.clipboard) ok = await navigator.clipboard.writeText(snap.words).then(() => true, () => false);   // write only, never a read
      V.notify(ok ? "copied" : "Copy did not happen: the browser refused it (Shift+right-click gives its own menu)");
    },
    cut(snap) {
      snap.spent = true;
      const why = !SEL.fresh(snap) ? "the text changed since you selected it"
        : snap.md?._md.src() !== snap.localSource ? "the unsaved text changed since you selected it"
        : !SEL.restore(snap) ? "the words were drawn again" : String(getSelection()) !== snap.words ? "the selection moved" : "";
      if (why) { snap.spent = false; return V.notify(`Cut did not happen: ${why}; the words are still there — select them again`); }
      const sc = snap.range.startContainer, ed = (sc.nodeType === 1 ? sc : sc.parentElement).closest('[contenteditable="true"]');
      if (ed) ed.focus({ preventScroll: true });
      SEL.restore(snap);
      const before = snap.md._md.src(), ok = document.execCommand("cut"), after = snap.md._md.src();
      if (!ok || after === before) { snap.spent = false; V.notify("Cut did not happen: the browser refused it; the words are still there"); }
    },
  };
  // Private to this page, never URLs/reports/writer props. A destination must be
  // an existing explicit composer, named exactly by the authored menu.
  const quoteDrafts = new Map();
  async function checkQuote(selection) {
    const r = await (await fetch("/api/selection", { method: "POST",
      body: JSON.stringify({ session, as: who, selection }) })).json();
    if (r.error || !r.selection) throw new Error(r.error || "The source could not be checked");
    return r.selection;
  }
  async function prepareQuote(words, snap, origin) {
    const [target, ...args] = words.split(/\s+/), context = {};
    for (const arg of args) {
      const [name, item] = arg.split("=");
      const binding = (origin.fence?.reads || []).find(r => r[0] === item);
      const rev = binding ? binding[1] : origin.fence?.item === item ? origin.fence.rev : null;
      if (!["context", "destination"].includes(name) || !Number.isInteger(rev))
        return V.notify("Comment: the authored context has no revision; nothing changed");
      context[name === "context" ? "item" : name] = { item, rev };
    }
    const el = paint.querySelector(`[data-key="${CSS.escape(target)}"]`);
    if (!el?._composer) return V.notify("Comment: the destination composer is not open");
    if (!/\$quote_text\b/.test(el._composer.quotedLine || el._composer.line))
      return V.notify("Comment: this composer has no authored quote consumer");
    for (const line of [el._composer.line, el._composer.quotedLine || ""]) {
      const about = line.match(/(?:^|\s)about=(?:"([^"]*)"|(\S+))/);
      const existing = about && (about[1] ?? about[2]);
      if (existing && !existing.startsWith("$quote_") && context.item && existing !== context.item.item)
        return V.notify("Comment: the draft already has another topic; keep it or clear that topic first");
    }
    if (!snap?.quoted || !SEL.fresh(snap)) return V.notify("Comment: select the current source words again");
    const previous = quoteDrafts.get(target);
    try {
      const selection = await checkQuote({ item: snap.item, rev: snap.rev, field: snap.field,
        start: snap.start, end: snap.end, quote: snap.quoted, context });
      // Recheck after the asynchronous read: never replace another preparation.
      if (quoteDrafts.get(target) !== previous || (previous && JSON.stringify(previous) !== JSON.stringify(selection)))
        return V.notify("Comment: a quote is already attached; remove it before choosing another");
      if (!el.isConnected || el._composer.busy()) return V.notify("Comment: the composer changed or is sending; try again");
      quoteDrafts.set(target, selection); el._composer.sync();
      V.notify("Quote prepared; your words are kept");
    } catch (e) { V.notify(`Comment: ${e.message}; your draft is kept`); }
  }
  // the selection as it was at the right button's press, before the browser can move it
  document.addEventListener("pointerdown", e => {
    if (e.button !== 2) return;
    const s = getSelection();
    SEL.pressAt = performance.now();
    SEL.press = s.rangeCount && !s.isCollapsed ? { range: s.getRangeAt(0).cloneRange(), at: SEL.pressAt } : null;
  }, true);
  function menuButton(label, run, why) {
    const b = document.createElement("button"); Object.assign(b, { type: "button", textContent: label });
    b.className = Style.roleClass("tool") + " " + Style.roleClass("menu.item"); b.setAttribute("role", "menuitem");
    // an entry that cannot run now stays in the list (the keys reach it) and says why when pressed
    if (why) { b.title = why; b.setAttribute("aria-disabled", "true"); b.addEventListener("click", () => { closeMenu(true); V.notify(`${label}: ${why}`); }); }
    else b.addEventListener("click", run);
    b.addEventListener("pointerdown", ev => ev.preventDefault());       // pressing an entry does not take the words' selection away
    return b;
  }
  document.addEventListener("contextmenu", e => {
    const t = e.target instanceof Element ? e.target : null;
    if (e.shiftKey || !t || t.closest("input, textarea")) return;
    // the words: those kept at the press, if this right-click is inside them; for the menu key, what is selected now
    // no right press just before: the menu key or Shift+F10 opened it
    const keyed = !(SEL.pressAt && performance.now() - SEL.pressAt < 1500), s = getSelection();
    SEL.pressAt = 0;
    let range = null;
    if (!keyed && SEL.press && performance.now() - SEL.press.at < 1500 && SEL.inside(SEL.press.range, e.clientX, e.clientY)) range = SEL.press.range;
    else if (keyed && s.rangeCount && !s.isCollapsed) range = s.getRangeAt(0);
    SEL.press = null;
    // words of no one thing (a tile, a label) still get Copy; only the entries that quote them need a thing
    const snap = range && paint.contains(range.commonAncestorContainer) ? SEL.snapshot(range) : null;
    const host0 = snap && snap.key ? paint.querySelector(`[data-key="${CSS.escape(snap.key)}"]`) : t;
    const el = host0 && host0.closest("[data-menu]");
    const entries = el && paint.contains(el) && el._n ? el._n.acts.filter(a => a.on === "menu") : [];
    // text in something that carries, with nothing selected: a way to select it
    const leaf = t.closest("[data-key]");
    const carried = !snap && leaf && paint.contains(leaf) && leaf.closest("[data-carry]") && (leaf.textContent || "").trim() ? leaf : null;
    // 26 Oct (Alex): every right-click ends with a box to ask, in your own words, for a change to what you clicked.
    // The world's `ask` word decides where it goes (the kernel desk: a request relayed into the Conversation).
    const askAt = el && paint.contains(el) ? el : leaf && paint.contains(leaf) ? leaf : null;
    const askItem = askAt && askAt._n ? ((askAt._n.paint && askAt._n.paint.source && askAt._n.paint.source.item)
      || (askAt._n.fence && askAt._n.fence.item) || "") : "";
    if (!snap && !entries.length && !carried && !askAt) return;
    e.preventDefault(); closeMenu();
    if (snap) SEL.restore(snap);
    const box = document.createElement("div"); box.id = "menu-pop"; box.setAttribute("role", "menu");
    box.className = Style.roleClass("sheet") + " " + Style.roleClass("popup");
    // 13 Oct: an entry's line may name $selected (the words highlighted in this part's thing, in quotation marks) and
    // $value (words the entry asks for: pressed, it becomes a box to type in); a7625: $quoted, $quoted_in. One pass, so
    // words filled in are never read again as names
    const picked = el ? TEXT.selected(el._n) : "";
    const fill = (l, value) => {
      if (/\$quoted/.test(l) && (!snap || !snap.quoted || !SEL.fresh(snap))) return null;
      return l.replace(/\$(value|selected|quoted_in|quoted)\b/g, (m, k) => k === "value" ? (value ?? m) : k === "selected" ? picked
        : k === "quoted" ? TEXT.esc(snap.quoted) : snap.item);
    };
    for (const a of entries) {
      if (a.line.startsWith("prepare ")) {
        box.append(menuButton(a.label, () => { closeMenu(); prepareQuote(a.line.slice(8), snap, el._n); },
          snap?.quoted ? "" : snap?.why || "select the source words first"));
        continue;
      }
      const stale = /\$quoted/.test(a.line) && (!snap || !snap.quoted) ? (snap ? snap.why : "select the words first") : "";
      box.append(menuButton(a.label, () => {
        if (!a.line.includes("$value")) {
          closeMenu(); const line = fill(a.line);
          if (line == null) return V.notify(`${a.label}: the words changed since you selected them; select them again`);
          return line.startsWith("host ") ? host(line.slice(5)) : send(el._n, line);
        }
        menuComposer(box, el, a, fill, e.clientX, e.clientY);
      }, stale));
    }
    if (snap) {
      box.append(menuButton("Copy", () => { snap.spent = true; closeMenu(); SEL.copy(snap); }));
      if (snap.editable) box.append(menuButton("Cut", () => { snap.spent = true; closeMenu(); SEL.cut(snap); }));
    }
    if (carried) box.append(menuButton("Select text", () => {
      closeMenu(); const r = document.createRange(); r.selectNodeContents(carried);
      const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
    }));
    if (askAt) {
      const ask = document.createElement("input"); ask.type = "text"; ask.placeholder = "Ask for a change…";
      ask.className = Style.roleClass("menu.ask"); ask.setAttribute("aria-label", "Ask for a change to this, in your own words");
      ask.style.cssText = "display:block;box-sizing:border-box;width:100%;min-width:16em;margin-top:6px;padding:6px 8px;font:inherit";
      ask.addEventListener("keydown", async ev => {
        ev.stopPropagation();                                             // arrows and letters are the box's, not the menu's
        if (ev.key === "Escape") { ev.preventDefault(); closeMenu(true); return; }
        if (ev.key !== "Enter" || ev.isComposing || !ask.value.trim()) return;
        ev.preventDefault();
        const raw = ask.value.trim(), where = lens + " · " + askAt._n.key;
        closeMenu();
        await send({ key: askAt._n.key + "/ask", fence: askAt._n.fence },
          `ask ${askItem || "-"} text="${TEXT.esc(raw)}" where="${TEXT.esc(where)}"`, raw);
      });
      box.append(ask);
    }
    document.body.append(box);
    let x = e.clientX, y = e.clientY;
    if (keyed) {                                                                    // the menu key: at the words, or at the part
      const r = (snap ? snap.range : (el || t)).getBoundingClientRect(); x = r.left + 8; y = (snap ? r.bottom : r.top + 8);
    }
    box.style.left = Math.max(0, Math.min(x, innerWidth - box.offsetWidth - 4)) + "px";
    box.style.top = Math.max(0, Math.min(y, innerHeight - box.offsetHeight - 4)) + "px";
    box._from = document.activeElement; box._snap = snap; pop = box;
    const first = box.querySelector('button:not([aria-disabled="true"])') || box.querySelector("button"); if (first) first.focus({ preventScroll: true });
  });
  document.addEventListener("pointerdown", e => { if (pop && !pop.contains(e.target)) closeMenu(); }, true);
  // a scroll of the page closes the menu; a scroll inside it does not (Alex, 13 Oct: a comment longer than the box
  // scrolled the box, and the box and its words were gone)
  document.addEventListener("scroll", e => { placeMenuDrafts(); if (pop && e.target instanceof Node && pop.contains(e.target)) return; closeMenu(); }, true);
  addEventListener("resize", placeMenuDrafts);
  addEventListener("blur", () => closeMenu());
  document.addEventListener("keydown", e => {
    if (!pop) return;
    if (e.key === "Escape") { closeMenu(true); e.preventDefault(); e.stopPropagation(); return; }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      const bs = [...pop.querySelectorAll("button")], i = bs.indexOf(document.activeElement);
      if (!bs.length) return;                                    // an entry that is asking for words: the arrows are the text's
      bs[(i + (e.key === "ArrowDown" ? 1 : -1) + bs.length) % bs.length].focus(); e.preventDefault();
    }
  }, true);
  // paint.semantic (pike-8 section 4): what assistive technology is told, on the node's one element. A press leaf is a
  // button: a Tab stop that Enter and Space activate (the codex team's finding: a clickable div is not a control).
  function semantic(el, s) {
    el.setAttribute("role", s.role);
    if (s.label) el.setAttribute("aria-label", s.label);
    for (const k of ["expanded", "value", "min", "max"]) if (s[k] != null) el.setAttribute(k === "expanded" ? "aria-expanded" : `aria-value${k === "value" ? "now" : k}`, String(s[k]));
    if (s.role === "button") {
      el.tabIndex = 0;
      el.addEventListener("keydown", e => { if ((e.key === "Enter" || e.key === " ") && e.target === el) { e.preventDefault(); el.click(); } });
    }
  }
  function tracks(el) {
    const p = el._n && el._n.paint; if (!p || !p.tracks) return;
    const kids = [...el.children].filter(c => c.dataset.key);
    // a10637: `grid fill <min>`: as many equal columns as this part's own width holds, each at least <min> (never wider
    // than the part), children flowing into rows in order; counted by the browser, so a resize writes nothing
    if (/^fill /.test(p.tracks[0])) {
      const pack = p.tracks[0].endsWith(" pack"), m = p.tracks[0].slice(5).replace(/ pack$/, "");
      const least = /gap$/.test(m) ? `calc(${parseFloat(m)} * var(--t-gap))` : m;
      el.style.gridTemplateColumns = `repeat(auto-fill, minmax(min(${least}, 100%), 1fr))`;
      el.dataset.fill = "1";
      if (pack) window.GridPack?.attach(el);
      return;
    }
    el.style.gridTemplateColumns = p.tracks.map((t, i) => kids[i] && kids[i].dataset.folded ? "auto" : t === "fit" ? "max-content" : /gap$/.test(t) ? `calc(${parseFloat(t)} * var(--t-gap))` : `minmax(0, ${t})`).join(" ");
    kids.forEach((c, i) => { if (i < p.tracks.length) c.style.gridColumn = String(i + 1); });
  }

  const openComposers = new Set();
  // a10486: the part as the latest scene has it. A held part keeps its element and the newer scene beside it (make); a
  // part let go is the kept element's own. Only the wait status is read here;
  // the original action and fence remain the user's Send provenance.
  function latest(key, el) {
    const k = kept.get(key), e = k ? k.el : el;
    return (V.hold === key && e._next) || e._n;
  }
  // a10486: `waits "<words>" ["<what>"]`: Send waits while the words are not empty (what is still arriving), a few
  // seconds at most, then tries the original action; native admission selects
  // current attachments. Past the deadline it sends nothing and the words stay.
  const waiting = new Map(), WAIT_MS = 6000;
  async function waitUntilClear(read, update, ms = WAIT_MS) {
    let stopped = false, deadline, pause;
    try {
      return await Promise.race([
        (async () => {
          while (read()) {
            await new Promise(resolve => { pause = setTimeout(resolve, 250); });
            if (stopped) return false;
            await update();           // shared refresh can stall; deadline still settles the wait
            if (stopped) return false;
          }
          return true;
        })(),
        new Promise(resolve => { deadline = setTimeout(() => resolve(false), ms); })
      ]);
    } finally {
      stopped = true; clearTimeout(deadline); clearTimeout(pause);
    }
  }
  function composer(el, n, a) {
    el.replaceChildren(); el.classList.add("explicit-composer");
    const input = document.createElement("textarea"), actions = document.createElement("div");
    input.setAttribute("aria-label", n.paint.hint || "Draft"); input.placeholder = n.paint.hint || "Write…";
    actions.className = "composer-actions";
    const post = document.createElement("button"), discard = document.createElement("button"), recover = document.createElement("button"), status = document.createElement("span");
    post.type = discard.type = "button"; post.textContent = "Send"; discard.textContent = "Discard";
    recover.type = "button"; recover.textContent = "Use current version"; recover.className = Style.roleClass("button");
    post.className = Style.roleClass("button"); discard.className = Style.roleClass("tool"); status.className = Style.roleClass("meta");
    const quotation = document.createElement("div"), source = document.createElement("a"), removeQuote = document.createElement("button");
    quotation.hidden = true; removeQuote.type = "button"; removeQuote.textContent = "Remove quote";
    quotation.append(source, removeQuote);
    removeQuote.onclick = () => { if (!busy) { quoteDrafts.delete(n.key); sync(); } };
    actions.append(post, discard, recover, status); el.append(quotation, input, actions);
    let busy = false, picked = TEXT.selected(n), why = "";
    const sync = () => {
      // Reused elements must observe the refreshed value too. Otherwise a refused draft
      // never gets `shown`, and the next keystroke loses its origin while keeping its text.
      const words = V.words(n.key, el._n.paint.text || "", el._n.fence);
      const d = V.drafts.get(n.key);
      const quote = quoteDrafts.get(n.key);
      quotation.hidden = !quote;
      if (quote) {
        source.textContent = `${quote.label}: “${quote.quote.slice(0, 240)}${quote.quote.length > 240 ? "…" : ""}”`;
        source.href = "lens.html?" + new URLSearchParams({ session, as: who, lens, on: quote.item, inspect: "0" });
      }
      removeQuote.disabled = busy;
      if (document.activeElement !== input && input.value !== words) { input.value = words; if (te) te.reset(words); }
      const open = openComposers.has(n.key) || !!d;
      el.dataset.composing = String(open);
      const bounds = el._n.paint.lines;
      input.rows = bounds ? bounds[0] : open ? 4 : 1;
      actions.hidden = !open && !bounds;
      if (bounds) {
        const line = parseFloat(getComputedStyle(input).lineHeight) || parseFloat(getComputedStyle(input).fontSize) * 1.5;
        input.style.height = "auto";
        input.style.height = Math.max(line * bounds[0], Math.min(input.scrollHeight, line * (bounds[1] || 30), innerHeight * .4)) + "px";
        input.style.overflowY = "auto";
      }
      const unknown = !!d && !d.seen && !d.shown;
      const awaits = waiting.get(n.key);
      post.disabled = busy || !!awaits || !input.value.trim() || unknown; discard.disabled = busy || !!awaits;
      recover.hidden = !unknown; recover.disabled = busy || !!awaits;
      status.textContent = awaits ? `Waiting for the ${awaits}…` : busy ? "Sending…" : why || (unknown ? "Draft kept — review this version" : d && d.refused ? "Not sent — " + (d.why || "review and send again") : d ? "Unsent" : "");
      status.setAttribute("aria-live", "polite");
      V.mark(el, n.key);
      // An empty composer has no saved current text to compare with a refused draft.
      if (!el.dataset.now) delete el.dataset.now;
      settle();
    };
    const quotedLine = n.acts.find(x => x.on === "edit-quoted")?.line;
    el._composer = { config: JSON.stringify([n.paint, n.acts]), sync, busy: () => busy, line: a.line, quotedLine };
    input.value = V.words(n.key, n.paint.text || "", n.fence);
    // a6067: the box's keys, undo and composition are the continuous-text module's (textedit.js), as a document's are;
    // the draft rules here stay this composer's (Codex): what is unsent, its origin, Send, Discard, Use current version
    let te = null;
    input.addEventListener("focus", () => { if (!openComposers.has(n.key) && !V.drafts.has(n.key)) picked = TEXT.selected(el._n); openComposers.add(n.key); V.hold = n.key; sync(); });
    input.addEventListener("blur", () => { if (!V.repainting) { V.hold = null; sync(); } });
    // a10486: a send lets go of the box (V.hold), yet its caret stays; words typed after it hold it again, or the next
    // scene (a capture landing on the draft) made the composer again and the caret fell to the page mid-word
    input.addEventListener("input", () => { if (document.activeElement === input && V.hold !== n.key) { el._next = null; V.hold = n.key; } why = ""; V.typed(n.key, input.value, { key: n.key, fence: el._n.fence }); sync(); });
    // a5588 (a5581: a click in the box's middle missed its one-row textarea, and the keys went nowhere): the whole
    // composer is its hit area, so a press on its padding, the actions row or the status gives the words the caret
    el.addEventListener("mousedown", e => {
      if (e.button !== 0 || e.target === input || e.target.closest("button, a, input, select")) return;
      e.preventDefault(); input.focus();
    });
    // Enter that cannot send says why on the page, instead of pressing a disabled Send
    const trySend = () => {
      if (busy || waiting.has(n.key)) return;
      const d = V.drafts.get(n.key);
      why = te && te.composing() ? "Not sent — the input method is still writing; finish it first"
        : !input.value.trim() ? "Nothing to send — write something first"
        : d && !d.seen && !d.shown ? "Not sent — this draft was typed against a version not shown here: Use current version, or Discard"
        : "";
      if (why) return sync();
      post.click();
    };
    post.onclick = async () => {
      if (busy || waiting.has(n.key) || !input.value.trim()) return;
      if (te && te.composing()) { why = "Not sent — the input method is still writing; finish it first"; return sync(); }   // Codex, a6067 c6120
      const seen = V.editOrigin(n.key, el._n); if (!seen) return;
      const quote = quoteDrafts.get(n.key);
      // Freeze the chosen authored branch at the press, with the original
      // audience/topic/generation/fence. Only pending status may refresh.
      const action = quote ? quotedLine || a.line : a.line;
      if (quote && !/\$quote_text\b/.test(action)) { why = "This composer has no authored quote consumer"; return sync(); }
      if (/\$quote_\w+\b/.test(action) && !quote) { why = "Prepare a source quote first"; return sync(); }
      const raw = input.value; let submitted = false, delivered = false; busy = true; why = ""; sync();
      const shown = () => { const k = kept.get(n.key); if (k && k.el._composer && k.el !== el) k.el._composer.sync(); sync(); };
      try {
        const cur = latest(n.key, el);
        if (cur.paint.waits) {
          const what = cur.paint.waits_for || "attachment";
          waiting.set(n.key, what); shown();
          const arrived = await waitUntilClear(() => !!latest(n.key, el).paint.waits, () => refresh());
          if (!arrived) {
            why = `Not sent — the ${what} did not arrive; your words are kept`;
            V.notify(why);
            return;
          }
        }
        if (quote) await checkQuote(quote);
        if (input.value !== raw) { why = "Not sent — your words changed while waiting; review and send again"; return; }
        const values = quote ? { item: quote.item, rev: quote.rev, field: quote.field, start: quote.start, end: quote.end,
          text: quote.quote, before: quote.before, after: quote.after, context: quote.context.item?.item || "",
          destination: quote.context.destination?.item || "" } : {};
        // One substitution pass: selected/typed words never become command tokens.
        const line = action.replace(/\$(value|selected|quote_(?:item|rev|field|start|end|text|before|after|context|destination))\b/g,
          (m, key) => key === "value" ? TEXT.esc(raw) : key === "selected" ? picked : TEXT.esc(String(values[key.slice(6)] ?? "")));
        // Native context_from admission selects current captures atomically.
        // Comment's source_quote travels through that same fenced dispatch.
        submitted = true;
        const answer = await send(seen, line, raw, undefined, quote ? { quote } : undefined);
        delivered = !!answer && !answer.error && !/^(ERR|!!)/.test(answer.text || "");
        if (delivered && !V.drafts.has(n.key)) quoteDrafts.delete(n.key);
        if (delivered && !V.drafts.has(n.key)) { input.value = ""; if (te) te.reset(""); openComposers.delete(n.key); }
      } catch (e) {
        why = submitted ? "Send outcome unknown — check the feed before sending again"
          : `${e.message}; your draft and quote are kept`;
        V.notify(why);
      } finally {
        waiting.delete(n.key); busy = false; shown();
      }
    };
    discard.onclick = () => { if (V.drop(n.key)) { input.value = n.paint.text || ""; if (te) te.reset(input.value); openComposers.delete(n.key); sync(); } };
    recover.onclick = () => {
      if (V.useCurrent(n.key, { key: n.key, fence: el._n.fence, text: el._n.paint.text || "" })) { sync(); input.focus(); }
    };
    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); trySend(); }
      if (e.key === "Escape") { e.preventDefault(); input.blur(); }
    });
    if (window.TextEdit) te = TextEdit.attach(input, { text: input.value, key: n.key, item: (n.fence || {}).item,
      // an undo sets the box's words without an input event: the draft follows them
      hooks: { notify: t => V.notify(t), changed: st => {
        const d = V.drafts.get(n.key);
        if ((d ? d.text : (el._n.paint.text || "")) === st.text) return;
        why = "";
        if (st.text === (el._n.paint.text || "")) V.drop(n.key); else V.typed(n.key, st.text, { key: n.key, fence: el._n.fence });
        sync();
      } } });
    el._te = te;
    sync();
  }
  function edits(el, n, a) {
    if (n.paint.commit === "explicit") return composer(el, n, a);
    el.contentEditable = "plaintext-only";
    // Juniper a559 (870ec2d): a part with runs is read as runs and edited as its source, so what is written is what is
    // drawn. Pike (S28): swapping on focus put the caret at the end, because focus comes before the click places it, and
    // the delimiters appearing moved the words under the pointer. So the swap waits for the first change (a key that
    // writes, a paste, a cut), and maps the caret and selection the browser has already placed to the same characters.
    el.addEventListener("focus", () => { TEXT.last = el; if (!V.repainting) V.hold = n.key; });
    const toSource = () => { if (el._runs) source(el); };
    el._toSource = toSource;
    el.addEventListener("keydown", e => TEXT.key(el, e));
    el.addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.length === 1) MARKS.key(el, e, toSource); });
    el.addEventListener("keydown", e => { if (!e.ctrlKey && !e.metaKey && (e.key.length === 1 || /^(Backspace|Delete|Enter)$/.test(e.key))) toSource(); });
    const multi = () => { const pp = el._n.paint; return pp.commit ? pp.commit === "ctrl-enter" : !!pp.lines && (pp.lines[1] == null || pp.lines[1] > 1); };
    // Pike (S29): a pasted line break showed on screen and vanished from what was sent ("CampgroundHighway"). The value is
    // read as it is drawn (innerText), and a one-line part takes a paste as one line, which it shows before it is sent.
    el.addEventListener("paste", e => {
      toSource(); if (multi()) return;
      e.preventDefault(); document.execCommand("insertText", false, (e.clipboardData.getData("text/plain") || "").split(String.fromCharCode(10)).map(l => l.trim()).join(" "));
    });
    el.addEventListener("cut", toSource);
    el.addEventListener("input", () => V.typed(n.key, el.innerText, { key: n.key, fence: el._n.fence }));
    el.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey && (!multi() || e.ctrlKey || e.metaKey)) { e.preventDefault(); el._committing = true; el.blur(); }   // commit is emitted (75e39d8)
      if (e.key === "Escape") { e.preventDefault(); if (!V.drop(n.key)) return; V.mark(el, n.key); el.textContent = el._n.paint.text; el.blur(); }
    });
    el.addEventListener("blur", () => {
      if (V.repainting || el._ahead) return;      // a repaint moved it (the person is still editing it), or a split shown ahead took the caret
      // 14 Oct (Pike: a lone '@' was sent twice from Alex's composer): the window losing focus (a key that opens the
      // window's menu, another program) blurs the text too, and is not the person putting it down. A text whose lens
      // says `commit enter only` (a message) is sent by that key only, and leaving it keeps the draft; any other text
      // is saved on leaving, as an editor does. (From 09:26 to the fix the first rule held for every text, and words
      // edited in a document were not saved on leaving: a fix that read a default as a lens's word.)
      const committing = el._committing; el._committing = false;
      if (!document.hasFocus() || (el._n.paint.commit_only && !committing)) { V.hold = null; return; }
      // Focusing rendered marks without changing them is not an edit. Their
      // visible text omits the source delimiters, so saving it would strip marks.
      if (!V.drafts.has(n.key)) { V.hold = null; return; }
      // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
      const raw = el.innerText.trim(), v = raw.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
      const seen = V.editOrigin(n.key, el._n); if (!seen) { V.hold = null; return; }   // pike-8: never a fresher fence than was shown
      // a6642: sent by Enter inside an `arrows` frame (a search box), the caret comes back once the answer is painted,
      // so Down reaches what the words found; only if nothing else took the keyboard meanwhile. a5994 (found by the
      // playtest): a press anywhere closes an open float, the frame's own list too while it was empty, so the words'
      // answer filled a closed list and nothing showed: sending them is asking for that list, so a closed float in the
      // frame opens again
      const back = committing && el.closest("[data-arrows]") ? n.key : null;
      if (raw !== (el._n.paint.text || "").trim()) send(seen, a.line.replace("$value", () => v).replace("$selected", () => TEXT.selected(el._n)), raw).then(() => {
        const k = back && kept.get(back);
        if (!k || !k.el.isConnected) return;
        const frame = k.el.closest("[data-arrows]");
        if (frame) frame.querySelectorAll('.l-float[data-folded="1"] > button').forEach(h => h.click());
        if (document.activeElement && document.activeElement !== document.body) return;
        k.el.focus(); getSelection().selectAllChildren(k.el); getSelection().collapseToEnd();
      }); else { V.hold = null; V.drop(n.key); if (el._n.paint.runs) runs(el, el._n.paint.runs); }
    });
  }

  // a5820, a6067: a text that says `markdown` is a document, written through textedit.js (the continuous-text module:
  // caret, selection, composition, undo, keys) and drawn by markdown.js. Its `on edit` is the seam: sent as the person
  // pauses (and on Ctrl+S, Ctrl+Enter, before a [[link]] is followed) with $value the whole Markdown text, fenced by the
  // version the module fitted it to; the desk's new words are fitted over what this window has not sent (a4865's small
  // edits wait on Alex's choice; they would replace this one function). `on link` is sent with $value the id a
  // [[wikilink]] or ![[embed]] names; `on capture` with $value what a dropped capture carries. Without `on edit` it is
  // drawn only.
  // a6452: and the media it draws: those are drawn when the element is made, so new ones make a new element
  const textConf = (n, p) => JSON.stringify([n.acts.map(a => [a.on, a.line]), p.hint || "", p.media || null]);
  // the thing whose words a text shows: the read of its `text` (a lens that reads $d.text under another thing's part,
  // as doc-page does, is fenced on that part's thing, but its words are the document's subject), else the part's thing
  const textOf = n => { const f = n.fence || {}, r = (f.reads || []).find(e => Array.isArray(e[2]) && e[2].includes("text")); return (r && r[0]) || f.item || null; };
  // the module's keeper is the viewer's (Sable c5977: one keeper of a viewer's values): the unsent words, with the
  // words and version they were typed on, are the person's draft; the caret is this window's
  const textKeeper = (key, nOf) => ({
    load: () => { const st = V.textState(key) || {}, d = V.drafts.get(key); return { text: d ? d.text : undefined, base: d ? d.base : undefined, sel: st.sel }; },
    save: st => {
      const dirty = st.text !== st.base || !!st.conflict;
      V.textState(key, { sel: st.sel });
      if (dirty) V.rebased(key, st.text, { key, fence: st.version || (nOf().fence || null) }, st.base);
      else if (V.drafts.has(key) && !V.busy(key)) V.drop(key);
    },
  });
  // another window of this person changed a draft: a document shows the same unsent words, a composer draws again
  V.onDrafts(keys => {
    for (const k of keys) {
      const el = kept.get(k) && kept.get(k).el, d = V.drafts.get(k);
      if (el && el._composer) el._composer.sync();
      else if (el && el._te && el._teConf && d) el._te.adopt(d.text, d.base, d.seen && d.seen.fence);
    }
  });
  async function sendEdit(el, out) {
    const n = el._n, a = n.acts.find(x => x.on === "edit");
    if (!a) return { ok: false, error: "this text has no `on edit`" };
    const r = await send({ key: n.key, fence: out.version }, a.line.replace("$value", () => TEXT.esc(out.text)).replace("$selected", () => ""), out.text);
    const t = r ? (r.error || r.text || "") : "the answer was lost";
    const ok = !!r && !r.error && !/(^|\n)ERR\b/.test(t);
    return { ok, error: ok ? null : t, event: ok ? (r.events || []).slice(-1)[0] : null };
  }
  // a6452: Markdown the drawing cannot take still shows its words, as plain text: never an empty part, never a stopped page
  async function popMedia(el, item) {
    for (const a of el._n.acts.filter(a => a.on === "pop")) {
      const line = a.line.replace(/\$value\b/g, () => TEXT.esc(item.path));
      if (line.startsWith("host ")) await host(line.slice(5)); else await send(el._n, line);
    }
  }
  function markdown(el, n, p) {
    try { document_(el, n, p); }
    catch (e) {
      console.warn("a Markdown text could not be drawn; its words are shown as written", e);
      delete el._te; delete el._md; delete el._teConf; el.classList.remove("md-part");
      el.textContent = p.text; el.dataset.mdFailed = "1"; el.classList.add("t-verbatim");
    }
  }
  function document_(el, n, p) {
    if (!window.TextEdit || !window.Markdown) { el.textContent = p.text; return; }
    const a = n.acts.find(x => x.on === "edit");
    const te = TextEdit.create({
      text: p.text, version: n.fence, editable: !!a, key: n.key, item: textOf(n),
      links: p.wikilinks, things: p.things, titles: p.titles, hint: p.hint, media: (p.media && p.media.items) || [],
      light: p.light, lightClass: Style.roleClass("light"),        // a5949: `light` on a document lights its quoted words
      keep: a ? textKeeper(n.key, () => el._n) : null,
      seam: a ? { send: out => sendEdit(el, out) } : null,
      hooks: {
        notify: t => V.notify(t),
        pop: n.acts.some(x => x.on === "pop") ? item => popMedia(el, item) : null,
        follow: async id => {
          const at = linkFor(el);                                   // a6109: its own `on link`, or the nearest above it
          if (!at) return V.show("this document's links open nowhere here (no `on link` on it or above it)");
          if (a) await te.flush();
          send(at._n, at._n.acts.find(x => x.on === "link").line.replace(/\$value\b/g, () => TEXT.esc(id)));
        },
        // the world's undo of this window's sent edit; its answer says which undo this was, and a refusal says why
        undoSent: async ev => {
          const r = await send(el._n, `undo ${ev}`), t = r ? (r.error || r.text || "") : "the answer was lost";
          V.notify(r && !r.error && !/(^|\n)ERR\b/.test(t) ? `undid ${ev}, your last sent edit, through the desk (the world's undo: it shows for everyone)`
            : `the desk did not undo ${ev}: ${t.split("\n").find(l => l.trim()) || t}`);
        },
        // Pike (a6067 c6122): "Keep mine" set someone's landed change aside: said on the thing, so they learn it did not stand
        overrode: (changes, ev) => {
          const item = textOf(el._n); if (!item) return;
          const what = changes.slice(0, 3).map(c => `“${c.was.slice(0, 80)}” → “${c.now.slice(0, 80)}”`).join("; ");
          send(el._n, `do comment ${item} line="${TEXT.esc(`${who} kept their own words over a change that landed while they were typing (${ev || "their edit"}); set aside: ${what}`)}"`);
        },
        capture: (anchor, data) => {
          const c = el._n.acts.find(x => x.on === "capture");
          if (!c) return V.notify("this text takes no capture here (its lens has no `on capture`)");
          send(el._n, c.line.replace(/\$value\b/g, () => TEXT.esc(data)).replace("$selected", () => TEXT.esc(anchor.quote || "")));
        },
      },
    });
    el._te = el._md = te; el._teConf = textConf(n, p); el._mdLinks = JSON.stringify([p.wikilinks || {}, p.things || {}]);
    el.classList.add("md-part"); el.append(te.el);
    if (!a && p.text.trim() && !drawsSomething(te.el)) throw new Error("its marks hide every word");   // a lone ``` (a6452)
    if (!a) return;
    const root = te.el.querySelector(".md-doc");
    root.addEventListener("focus", () => { TEXT.last = el; if (!V.repainting) V.hold = n.key; });
    root.addEventListener("blur", () => {
      if (V.repainting || !document.hasFocus()) return;        // the window losing focus is not the person putting it down
      te.flush(); V.hold = null;
    });
  }
  // a read document shows something when a word outside its hidden marks, or a drawn rule, box, table or picture, is in it
  function drawsSomething(root) {
    if (root.querySelector("img, table, .md-hr, .md-check, .md-embed")) return true;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let t = w.nextNode(); t; t = w.nextNode()) if (t.data.trim() && !t.parentElement.closest(".md-syn")) return true;
    return false;
  }
  function textFresh(el, n, p) {
    el._n = n;
    const l = JSON.stringify([p.wikilinks || {}, p.things || {}]);
    if (l !== el._mdLinks) { el._mdLinks = l; el._te.links(p.wikilinks, p.things); }
    el._te.lights(p.light);                                     // a5949: a new comment's words light at once
    el._te.titles(p.titles);
    el._te.receive(p.text, n.fence);                            // a6067: the desk's words, at this version
    if (!n.acts.some(a => a.on === "edit") && p.text.trim() && !drawsSomething(el._te.el)) throw new Error("its marks hide every word");
  }

  // a text's keys (Alex, 7 Oct: 'Enter should create a new line, tab should indent'). A lens gives a text `on key
  // Enter|Tab|Shift+Tab|Backspace do ...`; the command may name $head and $tail, the words either side of the caret.
  // The words typed and not yet sent go with it (the command is told them), so nothing is sent twice. Afterwards the
  // caret follows the text: into the same part of a thing the command made, or onto the end of the one above when
  // this one is gone, or it stays.
  const TEXT = {
    last: null,
    esc: v => v.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n"),
    caret(el) {                               // the caret as a count of characters of the source
      const sel = getSelection(); if (!sel.rangeCount || !el.contains(sel.anchorNode)) return null;
      const r = document.createRange(); r.selectNodeContents(el); r.setEnd(sel.focusNode, sel.focusOffset);
      return { at: r.toString().length, wide: !sel.isCollapsed };
    },
    put(el, at) {                             // the caret at a count of characters (past the end: the end)
      el.focus(); if (el._toSource) el._toSource();
      const t = el.firstChild, sel = getSelection();
      if (t && t.nodeType === 3) sel.setBaseAndExtent(t, Math.min(at, t.data.length), t, Math.min(at, t.data.length)); else sel.selectAllChildren(el), sel.collapseToStart();
    },
    // a button's command on the text being written (Alex's page, 7 Oct: a heading typed and then made H2 lost its
    // words and the caret). Words typed and not yet sent are sent first, as the text's own edit; then the command;
    // then the caret goes back where it was, in the text as it was painted again.
    async tool(el, line) {
      const n = el._n, key = n.key, c = this.caret(el) || { at: 0 }, edit = n.acts.find(x => x.on === "edit");
      if (el._toSource) el._toSource();
      const raw = el.innerText.replace(/\n$/, ""), seen = V.editOrigin(key, n) || n;
      V.drop(key); V.hold = null;
      if (edit && raw !== (n.paint.text || "")) await sendKey(seen, edit.line.replace("$value", () => this.esc(raw)));
      const now = paint.querySelector(`[data-key="${CSS.escape(key)}"]`) || el;
      await sendKey(now._n, line.replace("$focus", () => (n.fence || {}).item || "").replace("$selected", () => this.selected(n)));
      const after = paint.querySelector(`[data-key="${CSS.escape(key)}"]`);
      if (after) this.put(after, c.at);
    },
    // A person types on while Enter is still on its way to the desk (seen live, 7 Oct: the next words landed in the
    // paragraph above). Keys pressed meanwhile are kept, in order, and given to the text the caret lands in.
    // $selected (Alex, c3669: 'I should be able to hilight text'): the words last highlighted in a text of the same
    // thing this gesture is about, kept when the caret leaves for a comment box, written in quotation marks with a space after; nothing when none were
    sel: null,
    selected(n) { const it = (n.fence || {}).item; return this.sel && it && this.sel.item === it ? "“" + this.esc(this.sel.text.trim()) + "” " : ""; },
    queue: null,
    ghost: null,                              // the text of a split shown ahead of the desk (ahead), while it is on its way
    ahead(el, src, at) {
      const item = (el._n.fence || {}).item; if (!item) return null;
      // the instance this text stands in: the outermost element above it whose key is this thing's
      let inst = null;
      for (let x = el; x && x !== paint; x = x.parentElement) if ((x.dataset.key || "").endsWith("/" + item)) inst = x;
      if (!inst) return null;
      const path = []; for (let x = el; x !== inst; x = x.parentElement) path.unshift([...x.parentElement.children].indexOf(x));
      const copy = inst.cloneNode(true);
      for (const x of [copy, ...copy.querySelectorAll("[data-key]")]) { x.dataset.key = "ahead:" + x.dataset.key; x.removeAttribute("id"); }
      copy.dataset.ahead = "1";
      let twin = copy; for (const i of path) twin = twin && twin.children[i];
      if (!twin) return null;
      el._ahead = true;                        // its leaving is not an edit: the split carries its words
      el.textContent = src.slice(0, at);
      twin.textContent = src.slice(at);
      inst.after(copy);
      this.ghost = twin; this.put(twin, 0);
      return copy;
    },
    wait(done) {
      if (!this.queue) this.queue = [];
      Promise.resolve(done).catch(() => {}).then(async () => {
        const keys = this.queue || []; this.queue = null;
        for (let i = 0; i < keys.length; i++) {
          const k = keys[i], el = document.activeElement;
          if (!el || !el.isContentEditable) break;
          if (k.key.length === 1) { document.execCommand("insertText", false, k.key); continue; }
          let stopped = false;
          this.key(el, { key: k.key, shiftKey: k.shiftKey, preventDefault() { stopped = true; }, stopImmediatePropagation() {} });
          if (stopped) { this.queue.push(...keys.slice(i + 1)); return; }      // that key began another wait: the rest follow it
          if (k.key === "Backspace") document.execCommand("delete");
          if (k.key === "Delete") document.execCommand("forwardDelete");
        }
      });
    },
    press(el, key) {
      // a5820: Source (Ctrl+E) and Save (Ctrl+S) belong to the document on the page, wherever the caret was last
      const md = el._md ? el : /Ctrl\+[ES]$/.test(key) && [...paint.querySelectorAll(".md-part")].find(m => m._md);
      if (md) return md._md.press(key);
      if (el._toSource) MARKS.key(el, { key: key.split("+").pop().toLowerCase(), preventDefault() {} }, el._toSource); },
    key(el, e) {
      if (e.ctrlKey || e.metaKey || e.altKey || e.isComposing) return;
      const name = (e.shiftKey ? "Shift+" : "") + e.key, a = el._n.acts.find(x => x.on === "key" && x.label === name);
      if (!a) return;
      el._toSource(); const c = this.caret(el); if (!c) return;
      if (name === "Backspace" && (c.at > 0 || c.wide)) return;
      if (name === "Delete" && (c.at < el.innerText.replace(/\n$/, "").length || c.wide)) return;
      e.preventDefault(); e.stopImmediatePropagation();
      const src = el.innerText.replace(/\n$/, ""), seen = V.editOrigin(el._n.key, el._n) || el._n, key = el._n.key, item = (el._n.fence || {}).item;
      const before = [...paint.querySelectorAll("[contenteditable]")].filter(x => x._n && x._n.part === el._n.part && x._n.fence?.bind?.parent === el._n.fence?.bind?.parent);
      const prev = before[before.indexOf(el) - 1], prevLen = prev ? (prev._n.paint.text || "").length : 0, prevKey = prev && prev._n.key;
      const whole = /[$](head|tail|value)\b/.test(a.line);
      const line = a.line.replace(/\$(head|tail|value)\b/g, (_, word) => this.esc(word === "head" ? src.slice(0, c.at) : word === "tail" ? src.slice(c.at) : src));
      // Snappy Desk stage 3 (14 Oct, hands go first): a key whose command splits the text at the caret ($head stays,
      // $tail goes on) is shown split now, before the desk answers: a copy of this text's instance stands after it
      // with the tail, the caret at its start, and keys typed meanwhile appear in it. It is only a picture: the keys
      // are still kept and given to the text the desk made, and the next paint replaces the copy (or, refused, takes
      // it away and says why). Read from the verb, which means the same in every lens, never from a lens's names.
      const ghost = whole && /^\s*(do\s+)?split\s/.test(a.line) && /[$]head\b/.test(a.line) && /[$]tail\b/.test(a.line) ? this.ahead(el, src, c.at) : null;
      // Keep the draft and its original fence until the command succeeds.
      // A refused split/join must never discard words that exist only here.
      this.wait(sendKey(seen, line, whole ? { key, text: src } : null).then(r => {
        if (ghost) { ghost.remove(); this.ghost = null; el._ahead = false; }
        if (!r || r.error || /(^|\n)ERR\b/.test(r.text || "")) return;
        const made = r && (r.created || [])[0], find = k => paint.querySelector(`[data-key="${CSS.escape(k)}"]`);
        const same = find(key), born = made && item && find(key.split(item).join(made));
        if (born) this.put(born, 0);
        else if (!same && prevKey && find(prevKey)) this.put(find(prevKey), prevLen);
        else if (same) this.put(same, name === "Backspace" ? 0 : c.at);
      }));
    },
  };

  // marks (Editor board a3486, 7 Oct): the words a text part carries marks in, when its lens says `marks`. One table
  // holds each mark's element, the source written around it and its key, so a new mark is one more line here and one
  // more arm in scene.marks_of. Read, a mark is drawn; edited, it is its source, as a code run is.
  const MARKS = {
    kinds: { strong: { tag: "strong", wrap: ["**", "**"], key: "b" }, stress: { tag: "em", wrap: ["*", "*"], key: "i" },
             both: { tag: "strong", look: "t-mark-strong t-mark-stress" }, link: { tag: "a", wrap: ["[", "](https://)"], key: "k" },
             thing: { tag: "a" } },          // a6109: an id in the words, drawn as the name of what it names (scene.things_of)
    draw(r) {
      const m = document.createElement(this.kinds[r.mark].tag); m.className = "t-mark " + (this.kinds[r.mark].look || "t-mark-" + r.mark); m.textContent = r.text;
      if (r.mark === "link") { m.dataset.href = r.href; m.title = r.href + "  (Ctrl+click opens it)"; }
      if (r.mark === "thing") { m.dataset.thing = r.open || ""; m.dataset.id = r.id; m.dataset.kind = r.kind || ""; m.title = (window.Markdown ? Markdown.fullName({ title: r.title, name: r.text }) : r.title) + (r.open ? "  (click opens it)" : ""); }   // a6460: never the id, on hover either
      return m;
    },
    // Ctrl+B and the like, in the source: wrap what is selected, or take the mark off when it is already there
    key(el, e, toSource) {
      const kind = Object.values(this.kinds).find(k => k.key === e.key.toLowerCase());
      if (!kind || !el._n.paint.marks) return false;
      e.preventDefault(); toSource();
      const sel = getSelection(), t = el.firstChild;
      if (!t || t.nodeType !== 3 || !sel.rangeCount || !el.contains(sel.anchorNode)) return true;
      const a = Math.min(sel.anchorOffset, sel.focusOffset), f = Math.max(sel.anchorOffset, sel.focusOffset), src = t.data, [w0, w1] = kind.wrap;
      const count = (i, d) => { let c = 0; while (src[i] === "*") { c++; i += d; } return c; };
      const stars = Math.min(count(a - 1, -1), count(f, 1));   // the stars around the words: 1 stress, 2 strong, 3 both
      const on = kind.tag !== "a" && (w0 === "**" ? stars >= 2 : stars % 2 === 1);
      if (on) sel.setBaseAndExtent(t, a - w0.length, t, f + w1.length);
      const words = src.slice(a, f) || (kind.tag === "a" ? "link" : "");
      document.execCommand("insertText", false, on ? words : w0 + words + w1);
      // the words stay selected, so the same key again takes the mark off; a new link leaves its address selected to type over
      el.normalize(); const t2 = el.firstChild, from = on ? a - w0.length : a + w0.length;
      if (t2 && t2.nodeType === 3) {
        if (kind.tag === "a") sel.setBaseAndExtent(t2, a + words.length + 3, t2, a + words.length + 3 + "https://".length);
        else sel.setBaseAndExtent(t2, from, t2, from + words.length);
      }
      return true;
    },
  };
  document.addEventListener("keydown", e => {
    if (!TEXT.queue || e.ctrlKey || e.metaKey || e.altKey || e.isComposing) return;
    if (e.key.length === 1 || /^(Enter|Tab|Backspace|Delete)$/.test(e.key)) {
      e.preventDefault(); e.stopImmediatePropagation(); TEXT.queue.push({ key: e.key, shiftKey: e.shiftKey });
      // a split shown ahead: what is typed shows in it at once (the keys themselves wait for the text the desk makes)
      if (TEXT.ghost && TEXT.ghost.isConnected && document.activeElement === TEXT.ghost) {
        if (e.key.length === 1) document.execCommand("insertText", false, e.key);
        else if (e.key === "Backspace") document.execCommand("delete");
      }
    }
  }, true);
  document.addEventListener("selectionchange", () => {
    const sel = getSelection(), el = sel.rangeCount && sel.anchorNode && (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement);
    const t = el && el.closest && el.closest("[contenteditable]");
    if (!t && el && el.closest && paint.contains(el)) {          // 13 Oct: words highlighted in a text that is only read, for its part's menu
      let k = el.closest("[data-key]"); while (k && !(k._n && (k._n.fence || {}).item)) k = k.parentElement && k.parentElement.closest("[data-key]");
      if (k) TEXT.sel = sel.isCollapsed ? null : { item: k._n.fence.item, text: String(sel) };
      return;
    }
    if (!t || !t._n || !t._n.paint.marks) return;                // only a text that carries marks is a document's words
    TEXT.sel = sel.isCollapsed ? null : { item: (t._n.fence || {}).item, text: String(sel) };
  });
  // Highlighting is local selection only. Legacy on-select acts remain readable
  // while world owners remove them; no pointer/key path executes them.
  // a6109 (Alex: 'names of things ... should ALL be clickable'): a name drawn for an id opens what it names, by the
  // nearest `on link` above it (the home base's root says where: its viewer), $value the id. With none above, the press
  // is the part's own, as a press on its words always was. Caught before the parts' own clicks, so a name on a card
  // opens the name, not the card. Words being highlighted are not a press.
  function linkFor(el) {
    let k = el.closest("[data-key]");
    while (k && !(k._n && k._n.acts.some(a => a.on === "link"))) k = k.parentElement && k.parentElement.closest("[data-key]");
    return k;
  }
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest(".t-mark-thing");
    if (!a || !paint.contains(a) || !a.dataset.thing || String(getSelection())) return;
    if (a.closest("[contenteditable]") && !(e.ctrlKey || e.metaKey)) return;
    const at = linkFor(a); if (!at) return;
    e.preventDefault(); e.stopPropagation();
    send(at._n, at._n.acts.find(x => x.on === "link").line.replace(/\$value\b/g, () => TEXT.esc(a.dataset.thing)));
  }, true);
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest(".t-mark-link");
    if (!a || !/^https?:/.test(a.dataset.href || "")) return;
    if (a.closest("[contenteditable]") && !(e.ctrlKey || e.metaKey)) return;     // in a text being written, a click places the caret
    e.preventDefault(); window.open(a.dataset.href, "_blank", "noopener");
  });

  // `live` (a5530, Alex: a clock top left, a pomodoro ring that visibly counts down): words this page keeps live from its
  // own clock, once a second, with no scene built. clock and date draw now; `until` reads the words as a moment
  // ("2026-10-15 17:05:12 of 1500") or as seconds left that stand still ("1453 of 1500") and draws the time left, `ring`
  // inside a ring that empties. At zero, a count this page watched move chimes softly, and the part's `on end` is sent
  // once (also when the page opens on a moment already past, so a timer that ended while no one looked is told).
  const LIVE = new Set(), ENDED = new Set();
  let liveTimer = 0, audio = null;
  addEventListener("pointerdown", () => { try { audio = audio || new AudioContext(); audio.resume(); } catch (e) { /* no sound here */ } }, true);
  function live(el, n, p) {
    el.classList.add("t-live"); el._live = { kind: p.live, src: p.text, was: null };
    LIVE.add(el); tick(el, false);
    liveTimer = liveTimer || setInterval(() => {
      for (const e of LIVE) if (e.isConnected) tick(e, true); else LIVE.delete(e);
      if (!LIVE.size) { clearInterval(liveTimer); liveTimer = 0; }
    }, 1000);
  }
  const clockOf = s => { const t = Math.max(0, Math.round(s)), h = Math.floor(t / 3600), m = Math.floor(t / 60) % 60, x = String(t % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${x}` : `${m}:${x}`; };
  function tick(el, watching) {
    const L = el._live, now = new Date();
    if (L.kind === "clock") { el.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); return; }
    if (L.kind === "date") { el.textContent = now.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" }); return; }
    const m = /^\s*(?:(\d{4})-(\d\d)-(\d\d)[ T](\d\d):(\d\d)(?::(\d\d))?|(-?\d+(?:\.\d+)?))(?:\s+of\s+(\d+(?:\.\d+)?))?\s*$/.exec(L.src);
    if (!m) { el.textContent = L.src; return; }
    const moving = m[7] == null, whole = m[8] ? +m[8] : 0;
    const left = moving ? Math.max(0, Math.ceil((new Date(+m[1], m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0)) - now) / 1000)) : Math.max(0, +m[7]);
    if (L.kind === "until ring") {
      if (!L.arc) {
        el.classList.add("t-ring");
        el.innerHTML = '<svg viewBox="0 0 100 100" aria-hidden="true"><circle class="ring-track" cx="50" cy="50" r="45" pathLength="1"/><circle class="ring-arc" cx="50" cy="50" r="45" pathLength="1"/></svg><span class="ring-time"></span>';
        L.arc = el.querySelector(".ring-arc"); L.time = el.querySelector(".ring-time");
      }
      L.arc.style.strokeDashoffset = String(1 - (whole ? Math.min(1, left / whole) : 1));
      L.time.textContent = clockOf(left);
    } else el.textContent = clockOf(left);
    el.toggleAttribute("data-ended", left === 0);
    if (moving && left === 0 && !ENDED.has(el.dataset.key + "|" + L.src)) {
      ENDED.add(el.dataset.key + "|" + L.src);
      if (watching && L.was > 0) chime();
      for (const a of el._n.acts.filter(a => a.on === "end")) send(el._n, a.line);
    }
    L.was = left;
  }
  function chime() {      // two soft notes, the second higher, each fading over a second
    try {
      audio = audio || new AudioContext(); const t = audio.currentTime;
      for (const [f, at] of [[660, 0], [880, 0.3]]) {
        const o = audio.createOscillator(), g = audio.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.setValueAtTime(0, t + at); g.gain.linearRampToValueAtTime(0.07, t + at + 0.05); g.gain.exponentialRampToValueAtTime(0.0001, t + at + 1.4);
        o.connect(g).connect(audio.destination); o.start(t + at); o.stop(t + at + 1.5);
      }
    } catch (e) { /* a page with no sound still shows the end */ }
  }

  // runs inside one text leaf: plain words as text, a code run in its role (a block run keeps its lines, verbatim)
  // `picture` (13 Oct): the part's text is a drawing written as SVG. Only shapes and words are drawn: an element or
  // attribute outside these lists is dropped (no script, no foreignObject, no link, no handler, no address), so a
  // drawing from the world can do nothing but be seen. Its colours may be the style's tokens: fill="var(--t-accent)".
  const PIC = { els: new Set("svg g path rect circle ellipse line polyline polygon text tspan title desc defs marker lineargradient radialgradient stop clippath".split(" ")),
    no: /^(on|href$|xlink:|src$|style$)/i };
  function picture(el, src) {
    el.classList.add("t-picture");
    if (!src.trim()) { el.replaceChildren(); return; }
    if (/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(src)) {
      const img = new Image(); img.src = src; img.alt = "Selected image region";
      img.draggable = false; img.style.width = "100%"; el.replaceChildren(img); return;
    }
    // a drawing written by hand rarely names its namespace, and without it the parser makes elements no browser draws
    if (!/^\s*<svg[^>]*\sxmlns=/.test(src)) src = src.replace(/^\s*<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    const doc = new DOMParser().parseFromString(src, "image/svg+xml"), root = doc.documentElement;
    if (!root || root.nodeName.toLowerCase() !== "svg" || doc.querySelector("parsererror")) { el.textContent = "this picture's text is not a drawing (SVG) the painter can read"; el.classList.add(Style.roleClass("cut")); return; }
    const clean = e => {
      for (const k of [...e.children]) { if (PIC.els.has(k.nodeName.toLowerCase())) clean(k); else k.remove(); }
      for (const a of [...e.attributes]) if (PIC.no.test(a.name) || /url\(\s*[^#]|javascript:/i.test(a.value)) e.removeAttribute(a.name);
    };
    clean(root);
    const t = root.querySelector(":scope > title, :scope > desc");
    root.setAttribute("role", "img"); if (t) root.setAttribute("aria-label", t.textContent.trim());
    el.replaceChildren(document.importNode(root, true));
  }
  function pictureRegions(el, regions) {
    const media = el.querySelector(":scope > svg, :scope > img");
    if (!media || !regions.length) return;
    const stage = document.createElement("div"); stage.className = "picture-stage";
    el.replaceChildren(stage); stage.append(media);
    for (const region of regions.filter(r => r.current)) {
      const box = document.createElement("div"); box.className = "picture-region " + Style.roleClass("region");
      const [x, y, w, h] = region.rect;
      Object.assign(box.style, { left: x * 100 + "%", top: y * 100 + "%", width: w * 100 + "%", height: h * 100 + "%" });
      box.setAttribute("role", "img"); box.setAttribute("aria-label", `Comment region by ${region.by}`);
      box.dataset.comment = region.id; stage.append(box);
    }
    if (regions.some(r => !r.current)) {
      const note = document.createElement("div"); note.className = Style.roleClass("meta");
      note.textContent = "An image comment refers to an earlier version; its region is not overlaid here.";
      el.append(note);
    }
  }
  // `light` (13 Oct; Alex: comments live on the text): each passage named is wrapped where it first stands in the
  // drawn words, in role `light`; a passage not found (the words changed since) is simply not lit
  function light(el, passages) {
    for (const want of passages) {
      const words = want.replace(/^[“"]|[”"]$/g, "").trim(); if (!words) continue;
      const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let node, done = false;
      while (!done && (node = walk.nextNode())) {
        if (node.parentElement && node.parentElement.closest("mark")) continue;
        const i = node.data.indexOf(words); if (i < 0) continue;
        const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + words.length);
        const m = document.createElement("mark"); m.className = Style.roleClass("light"); m.dataset.light = words;
        r.surroundContents(m); done = true;
      }
    }
  }
  function runs(el, rs) {
    el._runs = rs;
    // a6460: a name inside a sentence is drawn quiet, as a Markdown document draws it (markdown.js refDraw): first four
    // words, the whole on hover, an arrow for a comment, event or line, a number when named again; a text that is only
    // a name keeps it whole
    const M = window.Markdown, prose = M && rs.some(r => !r.mark && /[A-Za-z]{3,}/.test(r.text || ""));
    const refs = new Map(), n = new Map();
    if (prose) {
      for (const r of rs) if (r.mark === "thing" && r.kind !== "comment" && r.kind !== "event" && r.kind !== "line") n.set(r.id, (n.get(r.id) || 0) + 1);
      let k = 0; for (const [id, c] of n) if (c > 1) refs.set(id, { n: ++k, seen: false });
    }
    el.replaceChildren(...rs.map(r => {
      if (r.mark === "thing" && prose) {
        const m = MARKS.draw(r), full = M.fullName({ title: r.title, name: r.text });
        m.replaceChildren(...M.refDraw({ name: r.text, kind: r.kind }, refs.get(r.id), "t-"));
        m.title = full + (r.open ? "  (click opens it)" : "");
        return m;
      }
      if (r.mark) return MARKS.draw(r);
      if (!r.role) return document.createTextNode(r.text);
      const s = document.createElement(r.block ? "div" : "span"); s.className = Style.roleClass(r.role);
      if (r.block) s.classList.add("t-verbatim");
      s.textContent = r.text; return s;
    }));
  }
  function source(el) {
    const src = el._n.paint.text, rs = el._runs, kids = [...el.childNodes], sel = getSelection();
    let pos = 0; const starts = rs.map(r => { const i = src.indexOf(r.text, pos); pos = i + r.text.length; return i; });
    const map = (node, off) => {
      if (node === el) return off >= kids.length ? src.length : starts[off];
      const i = kids.findIndex(k => k === node || k.contains(node));
      return i < 0 ? src.length : starts[i] + (node.nodeType === 3 ? off : 0);
    };
    const inside = sel.rangeCount && el.contains(sel.anchorNode) && el.contains(sel.focusNode);
    const a = inside ? map(sel.anchorNode, sel.anchorOffset) : src.length, f = inside ? map(sel.focusNode, sel.focusOffset) : a;
    el._runs = null; el.textContent = src;
    const t = el.firstChild; if (t) sel.setBaseAndExtent(t, Math.min(a, src.length), t, Math.min(f, src.length));
  }

  // drag is geometry: $x $y in the free parent. Pointer and keys take, move and put through the same three steps (S9).
  function drags(el, n, a) {
    el.dataset.drag = "1"; el.tabIndex = 0;
    let m0 = null, x = 0, y = 0;
    const to = (nx, ny) => { x = Math.max(0, Math.round(nx)); y = Math.max(0, Math.round(ny)); el.style.left = x + "px"; el.style.top = y + "px"; };
    const take = () => { m0 = el._n; V.hold = n.key; x = m0.paint.box[0]; y = m0.paint.box[1]; };
    const put = back => {
      const m = m0; m0 = null; if (back) to(m.paint.box[0], m.paint.box[1]);
      if (!back && (x !== m.paint.box[0] || y !== m.paint.box[1])) send(m, a.line.replace("$x", x).replace("$y", y)); else V.hold = null;
    };
    el.addEventListener("pointerdown", e => {
      if (e.target.isContentEditable && e.target !== el) return;
      take(); el.setPointerCapture(e.pointerId);
      const x0 = e.clientX - x, y0 = e.clientY - y, move = m => to(m.clientX - x0, m.clientY - y0);
      const up = () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); put(false); };
      el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
    });
    el.addEventListener("keydown", e => {
      const d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key], step = e.shiftKey ? 40 : 8;
      if (e.target !== el || !(d || m0)) return;
      if (d) { e.preventDefault(); if (!m0) take(); to(x + d[0] * step, y + d[1] * step); }
      if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); put(e.key === "Escape"); }
    });
    el.addEventListener("blur", () => { if (m0 && !V.repainting) put(false); });
  }

  // carry is relation (pike-3): pick a thing up, put it down on a part that says `on drop <its part>`; the receiver says
  // what that means, and both are fenced. Pointer: press, move, release over a receiver. Keys: Space takes it, Tab
  // reaches the receivers that accept it, Enter puts it down, Escape cancels. Nothing is sent onto the receiver it came from.
  let carrying = null, carryFrom = null, carryHandoff = null;
  const receivers = part => [...paint.querySelectorAll("[data-drop]")].filter(r => CarryTargets.accepts(r, part));
  // a5994: a receiver may say an act per side (`on drop <part> at left`); the one taken is the side whose edge the
  // pointer is within a third of (nearest first), else the plain act, else the nearest side. On the receiver it came
  // from, only a left or right act (a panel set beside its own column); its middle would put it where it is.
  function landing(r, m) {
    return CarryTargets.plan(r, { el: carrying.el, part: carrying.n.part }, carrying.seen, m);
  }
  const over = (r, m) => {
    const c = Style.roleClass("tool.on"), l = r ? landing(r, m) : null;
    if (r && !l) r = null;
    if (carrying.over && carrying.over !== r) carrying.over.classList.remove(c);
    carrying.over = r; carrying.act = l && l.act; if (r) r.classList.add(c);
    // the landing box: where it will go, before the hand lets go
    if (!l) { carrying.drift?.move(null); if (carrying.box) carrying.box.hidden = true; return; }
    if (!carrying.box) { carrying.box = document.createElement("div"); carrying.box.className = "landing-box " + Style.roleClass("landing"); document.body.appendChild(carrying.box); }
    const [x, y, w, h] = l.box;
    Object.assign(carrying.box.style, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" }); carrying.box.hidden = false;
    if(carrying.drift && m) {
      const held=carrying;
      held.drift.move(r,{clientX:m.clientX,clientY:m.clientY,startX:held.startX,startY:held.startY},out=>{
        if(carrying!==held||!held.box)return;
        held.box.hidden=!out.allowed;
        if(out.allowed)Object.assign(held.box.style,out.landing.reduce((o,v,i)=>(o[["left","top","width","height"][i]]=v+"px",o),{}));
      });
    }
  };
  // a receiver is judged on what it meant at pick-up (pike-3), though the view keeps repainting while a card is in the air
  function take(el) { const rs = receivers(el._n.part); carrying = { el, n: el._n, over: null, seen: CarryTargets.snapshot(paint, el._n.part) }; V.hold = el._n.key; rs.forEach(r => { r.tabIndex = 0; }); }
  async function put(r, m) {
    const c = carrying; if (!c) return;
    if(c.releasing)return;c.releasing=true;
    if(c.drift && m)over(r,m);
    if(c.drift && r && !(await c.drift.flush())?.allowed)r=null;
    const l = r ? landing(r, m) : null;
    if(l&&c.ghost)carryFrom={key:thingOf(c.el),rect:c.ghost.getBoundingClientRect()};
    if(c.over)c.over.classList.remove(Style.roleClass("tool.on"));
    carrying = null; document.body.style.userSelect = "";
    const cleanup = immediate => {
      c.drift?.close(immediate);c.ghost?.remove();
      c.el.style.transform="";c.el.style.opacity="";c.el.style.animation="";
      if(c.box)c.box.remove();
    };
    cleanup.duration=c.drift?.duration;
    receivers(c.n.part).forEach(x => x.removeAttribute("tabindex"));
    if (!l) { cleanup(false); V.hold = null; return; }
    // Keep the direct placement preview until the answer is painted; no decorative fade.
    carryHandoff=cleanup;
    Promise.resolve(CarryTargets.submit(send, l, c.n.fence)).finally(() => {
      if(carryHandoff===cleanup){carryFrom=null;carryHandoff=null;cleanup(false);}
    });
  }
  // a copy of the card follows the pointer, fixed to the window, so a lane that scrolls (and so clips) can't hide it
  function ghost(el) {
    const b = el.getBoundingClientRect(), g = el.cloneNode(true);
    g.querySelectorAll("[data-key]").forEach(x => x.removeAttribute("data-key")); g.removeAttribute("data-key");
    Object.assign(g.style, { position: "fixed", left: b.left + "px", top: b.top + "px", width: b.width + "px", margin: 0,
      pointerEvents: "none", zIndex: 30, opacity: .92, animation: "none", boxShadow: "0 6px 18px rgba(0,0,0,.25)" });
    // a5994: a part with no ground of its own (a panel's title row) is carried on the ground it sits on, or its words
    // tangle with what it passes over
    const clear = c => !c || c === "transparent" || /rgba\(.*,\s*0\)$/.test(c);
    if (clear(getComputedStyle(el).backgroundColor)) {
      for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
        const s = getComputedStyle(a);
        if (!clear(s.backgroundColor)) { Object.assign(g.style, { background: s.backgroundColor, borderRadius: s.borderRadius, padding: "6px 10px", boxSizing: "border-box", backdropFilter: "blur(8px)" }); break; }
      }
    }
    document.body.appendChild(g); return g;
  }
  function carries(el, n) {
    el.tabIndex = 0; el.dataset.carry = n.part;
    el.addEventListener("pointerdown", e => {
      // 30 Sep (Alex: dragging cards didn't work): the card's title is its fold handle, a button covering most of the
      // card, and a press on a control was never a carry. Now a press becomes a carry only once it moves a few pixels,
      // from anywhere on the card, the title included; a press that doesn't move stays that control's click. The right
      // button opens the menu, and a press in text being typed stays typing.
      if (partitions?.carry(el, e)) return;
      if (e.target.isContentEditable || e.button !== 0) return;
      const x0 = e.clientX, y0 = e.clientY, pid = e.pointerId;
      let c = null;
      const at = m => carrying ? CarryTargets.at(document.elementsFromPoint(m.clientX, m.clientY),
        { el, part: n.part }, carrying.seen, m)?.receiver || null : null;
      const move = m => {
        if (m.pointerId !== pid) return;
        if (!c) {
          if (Math.hypot(m.clientX - x0, m.clientY - y0) < 5 || carrying) return;
          take(el); c = carrying; c.ghost = ghost(el); el.style.opacity = ".35"; el.style.animation = "none";   // a1140: the dim wins over a pulse
          c.startX=x0;c.startY=y0;c.drift=CarryTargets.drift(el);
          document.body.style.userSelect = "none"; getSelection().removeAllRanges();
        }
        c.ghost.style.transform = `translate(${m.clientX - x0}px, ${m.clientY - y0}px)`; over(at(m), m);
      };
      const up = m => {
        if (m.pointerId !== pid) return;
        document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up);
        document.removeEventListener("pointercancel", up);
        if (!c) return;
        // the release after a carry is not a click on the control it began on (it would fold or start the card)
        const eat = k => { k.stopPropagation(); k.preventDefault(); };
        window.addEventListener("click", eat, { capture: true, once: true });
        setTimeout(() => window.removeEventListener("click", eat, { capture: true }), 0);
        put(m.type === "pointercancel" ? null : at(m), m);
      };
      document.addEventListener("pointermove", move); document.addEventListener("pointerup", up);
      document.addEventListener("pointercancel", up);
    });
    el.addEventListener("keydown", e => {
      if (partitions?.key(el, e)) return;
      if (e.key === " " && e.target === el && !carrying) { e.preventDefault(); take(el); }
    });
  }
  document.addEventListener("keydown", e => {
    if (!carrying) return;
    const r = CarryTargets.accepts(document.activeElement, carrying.n.part) ? document.activeElement : null;
    if (e.key === "Escape") { e.preventDefault(); put(null); }
    else if (e.key === "Enter" && r) { e.preventDefault(); put(r); }
    else if (e.key === "Tab") setTimeout(() => { if (carrying) over(CarryTargets.accepts(document.activeElement, carrying.n.part) ? document.activeElement : null); });
  });

  let held = null;                               // the last scene answer painted, carried over a reload for new painter code
  // A frame following its end keeps doing so when its viewport or content is
  // resized, including line wrapping and a growing composer. Scrolling away
  // explicitly ends that following; the next resize must not pull the reader back.
  const followed = new Map();
  const endSizes = new ResizeObserver(entries => {
    const frames = new Set(entries.map(x => x.target.dataset.scroll === "end" ? x.target : x.target.parentElement));
    for (const frame of frames) {
      const state = followed.get(frame); if (!state) continue;
      if (state.end) frame.scrollTop = frame.scrollHeight;
      state.height = frame.clientHeight; state.width = frame.clientWidth;
    }
  });
  function followEnds() {
    for (const [frame, state] of followed) if (!frame.isConnected) {
      endSizes.unobserve(frame); state.kids.forEach(k => endSizes.unobserve(k)); followed.delete(frame);
    }
    for (const frame of paint.querySelectorAll('[data-scroll="end"]')) {
      let state = followed.get(frame);
      if (!state) {
        state = { end: frame.scrollHeight - frame.scrollTop - frame.clientHeight < 3,
          height: frame.clientHeight, width: frame.clientWidth, kids: new Set() };
        followed.set(frame, state); endSizes.observe(frame);
        frame.addEventListener("scroll", () => {
          if (state.height === frame.clientHeight && state.width === frame.clientWidth)
            state.end = frame.scrollHeight - frame.scrollTop - frame.clientHeight < 3;
        });
      }
      for (const child of state.kids) if (child.parentElement !== frame) { endSizes.unobserve(child); state.kids.delete(child); }
      for (const child of frame.children) if (!state.kids.has(child)) { state.kids.add(child); endSizes.observe(child); }
    }
  }
  // a6010 (a press fetched two whole scenes at once, its own and the stream's, each a build on the server): one scene
  // request at a time. An ask while one is out queues one more, which starts when it ends and so sees the world after
  // it; asks while one is queued join that one (forced if any of them was).
  let queued = null, chain = Promise.resolve();
  function refresh(force) {
    if (queued) { queued.force = queued.force || !!force; return queued.p; }
    const q = { force: !!force };
    q.p = chain.then(() => { queued = null; return fetchScene(q.force); });
    queued = q; chain = q.p.catch(() => {});
    return q.p;
  }
  async function fetchScene(force) {
    const have = !force && /^(\d+-\d+|g[0-9a-f]+)$/.test(last) ? `&have=${last}` : "";      // a build name, never the fallback text
    const keys = encodeURIComponent("Enter,Tab,Shift+Tab,Backspace,Delete");
    const on = q.get("on") ? `&on=${encodeURIComponent(q.get("on"))}` : "";   // a5949 (Sable's a4270): the thing the lens stands on
    // a6153: the scene's text is shown only in the inspector (#said); a page without it is not sent it (~400 KB and
    // ~25 ms of the home base's build at every press)
    const text = document.body.dataset.inspector === "on" ? "" : "&text=0";
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${encodeURIComponent(lens)}${on}&view=painter&keys=${keys}${text}${have}`)).json();
    if (r.same) return;                          // deskd: nothing changed since the build this page has
    return paintAnswer(r, force);
  }
  async function paintAnswer(r, force) {
    if (resizing) return;   // a divider owns both neighbours until its fenced answer
    const key = r.gen || JSON.stringify(r.scene || r.refused);      // deskd names each scene by its content (a1505); comparing 700 KB was the fallback
    if (key === last && !force) return;
    const incomingDef = (r.scene && r.scene.def) || r.def || null;
    await restyle((incomingDef && incomingDef.style_name) || "calm", (incomingDef && incomingDef.style_rev) || "seed");
    // A gesture can take the layout while a style request is outstanding.
    // Do not paint across that hold or acknowledge an answer we did not paint:
    // the post-gesture refresh must still be able to fetch this generation.
    if (resizing) return;
    last = key; sceneAt = r.events_total; def = incomingDef; if (r.scene) held = r;
    // 30 Sep (Alex: the Desktop kept going blank over the node budget): a refused scene keeps the last good paint on
    // screen and says why, as a refused style keeps the last good look; a page with nothing painted yet shows the reason
    if (r.refused) { V.show("refused: " + r.refused + (paint.firstChild ? "\n(showing the last good paint until the lens compiles again)" : "")); return; }
    V.recoverLayout(r.scene);
    const was = glideRects();
    if(carryHandoff){was.duration=carryHandoff.duration;carryHandoff(true);carryHandoff=null;}
    V.keep(() => { next = new Map(); const root = make(r.scene); kept = next; if (paint.firstChild !== root) paint.replaceChildren(root); });
    dividers?.sync();
    partitions?.sync();
    settle(); glideFrom(was); followEnds(); placeMenuDrafts(); V.show(r.text); report();
  }
  // a5504 (Alex: 'smooth movement when a card changes lane'): a part whose role says `glide` is known by its thing, not its
  // key, so a card that moved lane (a new key, a new element) is seen as the same card. Before a paint each one's place
  // is noted; after it, each travels from where its thing was (FLIP), and one that was not there before fades in.
  // Nothing moves for a viewer who asked for reduced motion, nor on the first paint.
  const thingOf = el => (el._n && el._n.fence && el._n.fence.item) || (el.dataset.key || "").split("/").pop();
  function glideRects() {
    const sel = [...(Style.glide || []), "[data-carry]"].join(",");
    const m = new Map(); for (const el of paint.querySelectorAll(sel)) if (!el.hidden && el.offsetParent
      && !el.closest("[data-partition]")) m.set(thingOf(el), el.getBoundingClientRect());
    if(carryFrom){m.set(carryFrom.key,carryFrom.rect);carryFrom=null;}
    return m;
  }
  function glideFrom(was) {
    if (!was || !was.size || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    for (const el of paint.querySelectorAll([...(Style.glide || []), "[data-carry]"].join(","))) {
      if (el.hidden || !el.offsetParent) continue;
      const a = was.get(thingOf(el)), b = el.getBoundingClientRect();
      if (!a) { el.animate([{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { duration: 360, easing: "ease-out" }); continue; }
      const dx = a.left - b.left, dy = a.top - b.top;
      if (Math.abs(dx) < 1 && Math.abs(dy) < 1) continue;
      el.animate([{ transform: `translate(${dx}px, ${dy}px)`, zIndex: 2 }, { transform: "none", zIndex: 2 }], { duration: was.duration??520, easing: "cubic-bezier(.2,.8,.2,1)" });
    }
  }
  // Alex, 7 Oct (c3674: comments must not push the paragraphs down): parts a style calls `afloat` take no room, so two
  // of them near each other would lie one on the other. After a paint each is slid down just far enough to clear the
  // one before it in the same column, as notes in a document's margin are.
  // 13 Oct follow-up: expanding cards overlapped until the next paint, and pointer-down anchoring could move a
  // displaced handle out from under its click. Keep document order, use each paragraph's position as a minimum,
  // and move neighbors synchronously after the gesture or a size change. The pressed part remains highlighted.
  let inHand = null;
  const floatSizes = new ResizeObserver(() => settle());
  const watchedFloats = new Set();
  const place = (el, side) => { let v = 0; for (let e = el; e; e = e.offsetParent) v += e[side]; return v; };
  function settle() {
    const sel = (Style.afloat || []).join(",");
    const cols = new Map();
    for (const el of watchedFloats) if (!el.isConnected) { floatSizes.unobserve(el); watchedFloats.delete(el); }
    for (const el of sel ? paint.querySelectorAll(sel) : []) {
      for (const child of el.children) if (!watchedFloats.has(child)) { watchedFloats.add(child); floatSizes.observe(child); }
      const h = el.scrollHeight;
      if (!h) { el.style.transform = ""; continue; }
      const c = Math.round(place(el, "offsetLeft"));
      if (!cols.has(c)) cols.set(c, []);
      cols.get(c).push({ el, at: place(el, "offsetTop"), h });
    }
    const gap = 8;
    for (const items of cols.values()) {
      let free = -Infinity;
      for (const it of items) { it.y = Math.max(it.at, free); free = it.y + it.h + gap; }
      for (const it of items) {
        const d = Math.round(it.y - it.at);
        // Height changes must move all neighbors in the same frame. Interpolating
        // only their positions leaves expanded text underneath a moving card.
        it.el.style.transition = "none";
        it.el.style.transform = d ? `translateY(${d}px)` : "";
        if (it.el.dataset.key === inHand) it.el.dataset.inhand = "1"; else delete it.el.dataset.inhand;
      }
    }
    for (const el of paint.querySelectorAll('.l-float:not([data-folded="1"])')) placeFloat(el);    // a6265: kept under its line
    // Cut attributes can affect styling. Read all overflow geometry first,
    // then publish the indicators, instead of invalidating layout per frame.
    const cuts = [...paint.querySelectorAll("[data-clamped]")].map(el =>
      [el, el.classList.contains("clamp") && el.scrollHeight > el.clientHeight + 1]);
    for (const el of paint.querySelectorAll('[data-scroll="none"]')) {
      // a hair is not more. Cut at the head (none end), the overflow is above the box, where scrollHeight does not count it
      const head = el.dataset.atEnd && el.firstElementChild ? el.getBoundingClientRect().top - el.firstElementChild.getBoundingClientRect().top : 0;
      cuts.push([el, el.scrollHeight > el.clientHeight + 8 || head > 8]);
    }
    for (const [el, cut] of cuts) el.dataset.cut = cut ? "1" : "";
  }

  // `tip` (a6271; Alex, 17 Oct: icons with 'no text. If I hover them it should say what they are'): a part's name and one
  // sentence, in one float laid over the page beside it while the pointer rests on it or it has focus, so it never moves
  // the layout: above the part in the lower half of the window, below it in the upper. It waits a moment before showing,
  // as a desktop's tooltips do, and shows at once when one was just showing (running the pointer along a bar). It wears
  // the style's role `tip` when the style has one. Known by key, so a repaint under the pointer keeps it.
  const TIP = { el: null, key: null, timer: 0, last: 0 };
  function tipShow(key) {
    TIP.timer = 0;
    const el = [...paint.querySelectorAll("[data-tip]")].find(e => e.dataset.key === key && e.getClientRects().length);
    if (!el) return tipHide();
    const t = TIP.el && TIP.el.isConnected ? TIP.el : (TIP.el = document.body.appendChild(document.createElement("div")));
    t.className = "lens-tip " + Style.roleClass("tip"); t.id = "lens-tip"; t.setAttribute("role", "tooltip");
    const line = (cls, words) => Object.assign(document.createElement("div"), { className: cls, textContent: words });
    t.replaceChildren(line("lens-tip-name", el._tip[0]), ...(el._tip[1] ? [line("lens-tip-about", el._tip[1])] : []));
    t.dataset.shown = "1"; TIP.key = key;
    const r = el.getBoundingClientRect(), w = t.offsetWidth, h = t.offsetHeight, gap = 8;
    const y = r.top > innerHeight / 2 ? r.top - h - gap : r.bottom + gap;
    t.style.left = Math.max(gap, Math.min(innerWidth - w - gap, r.left + r.width / 2 - w / 2)) + "px";
    t.style.top = Math.max(gap, Math.min(innerHeight - h - gap, y)) + "px";
  }
  function tipHide() {
    clearTimeout(TIP.timer); TIP.timer = 0;
    if (TIP.el && TIP.el.dataset.shown) { delete TIP.el.dataset.shown; TIP.last = Date.now(); }
    TIP.key = null;
  }
  function tipWant(el) {
    const key = el.dataset.key;
    if (key === TIP.key && (TIP.timer || (TIP.el && TIP.el.dataset.shown))) return;     // still on the same part
    const soon = !!(TIP.el && TIP.el.dataset.shown) || Date.now() - TIP.last < 600;
    tipHide(); TIP.key = key; TIP.timer = setTimeout(() => tipShow(key), soon ? 0 : 400);
  }
  const tipOf = e => e.target instanceof Element ? e.target.closest("[data-tip]") : null;
  paint.addEventListener("pointerover", e => { const el = tipOf(e); if (el && paint.contains(el)) tipWant(el); else if (TIP.key || TIP.timer) tipHide(); });
  paint.addEventListener("pointerleave", tipHide);
  paint.addEventListener("pointerdown", tipHide, true);
  paint.addEventListener("focusin", e => { const el = tipOf(e); if (el && e.target.matches(":focus-visible")) tipShow(el.dataset.key); });
  paint.addEventListener("focusout", tipHide);

  // which floating part is in hand: the one pressed, else the one beside what was pressed (the smallest part around
  // the press that holds exactly one), else none
  paint.addEventListener("pointerdown", e => {
    const sel = (Style.afloat || []).join(","); if (!sel || !(e.target instanceof Element)) return;
    let f = e.target.closest(sel);
    for (let k = e.target.closest("[data-key]"); !f && k && paint.contains(k); k = k.parentElement && k.parentElement.closest("[data-key]")) {
      const inside = [...k.querySelectorAll(sel)].filter(x => x.scrollHeight);
      if (inside.length === 1) f = inside[0];
      if (inside.length) break;
    }
    const key = f ? f.dataset.key : null;
    if (key !== inHand) inHand = key;
  }, true);
  addEventListener("resize", settle);
  // what floats moves when its own words grow: the faces arriving, a reply being typed (13 Oct)
  if (document.fonts) document.fonts.ready.then(settle);
  paint.addEventListener("input", settle);
  paint.addEventListener("click", settle);
  paint.addEventListener("load", settle, true);

  const report = () => V.report(paint, sceneAt, carrying ? { [carrying.n.key]: "carried" + (carrying.over ? " over " + carrying.over.dataset.key : "") } : {}, q.get("share") === "attention",
    def && { frame: def.frame, style: def.style_rev || "seed" });
  // a1473: boxes change without a new scene (a fold, the window, the fonts arriving), so those report too
  let scrolling; const later = () => { clearTimeout(scrolling); scrolling = setTimeout(report, 400); };
  paint.addEventListener("scroll", later); addEventListener("resize", later); paint.addEventListener("click", later);
  if (document.fonts) document.fonts.ready.then(later);

  // 30 Sep: a page that loads while deskd restarts (it reloads itself for new code, just as the keeper restarts the
  // server) got a failed first fetch; unguarded, it threw before the repaint loop below was set, and stayed blank
  // a1505: a page reloaded for new painter code (Alex pressed the quiet line, or the scene shape changed) carries its
  // view: the scene it showed (painted at once, before anything is fetched), each frame's scroll, focus and caret, and
  // the floats that were open. Only this tab reads it.
  const carryKey = `lens-carry:${session}:${who}:${lens}`;
  let carried = null; try { carried = JSON.parse(sessionStorage.getItem(carryKey) || "null"); sessionStorage.removeItem(carryKey); } catch (e) { carried = null; }
  if (carried && carried.answer) {
    await paintAnswer(carried.answer, true).catch(() => {});
    const q = k => paint.querySelector(`[data-key="${CSS.escape(k)}"]`);
    (carried.floats || []).forEach(k => { const el = q(k), h = el && el.querySelector(":scope > button"); if (h && el.dataset.folded === "1") h.click(); });
    if (carried.places) V.place(carried.places);
    const f = carried.focus && q(carried.focus.key);
    if (f && f.matches(".explicit-composer")) { const t = f.querySelector("textarea"); if (t) t.focus(); }
    else if (f) { f.focus(); const t = f.firstChild; if (t && t.nodeType === 3 && carried.focus.caret != null) getSelection().collapse(t, Math.min(carried.focus.caret, t.length)); }
  }
  await refresh().catch(() => {});
  startImageComments();
  setInterval(() => refresh().catch(() => {}), 1500);   // the server restarting is not an error worth a console line
  // a1505: the door (door.py) holds one long connection per page. A world event repaints at once (the 1.5 s poll stays
  // for what changes without an event: the clock, the house); the door's news feeds the quiet line (door.js).
  if (window.EventSource) {
    let soon = null;
    const es = new EventSource(`/door/stream?session=${encodeURIComponent(session)}`);
    es.addEventListener("world", () => { clearTimeout(soon); soon = setTimeout(() => refresh().catch(() => {}), 60); });
    es.addEventListener("door", m => { try { if (window.DoorLine) DoorLine.show(JSON.parse(m.data)); } catch (e) {} });
    es.onerror = () => { if (es.readyState === EventSource.CLOSED) es.close(); };   // no door (a bare deskd): the polls carry on
  }
  // live building (tier 2). a1505: a landing that changes only Python reloads nothing; deskd is swapped behind the door
  // and the next scene shows what it changed. When the PAINTER's own files change, the page keeps the painter it has
  // and the quiet line offers the new one ("new screen code: click to use it"); Alex chooses when (Juniper, e3746:
  // reading is not a keystroke, so no pause is safe to reload in). Only when deskd sends a scene shape this lens.js
  // can't read (scene.PAINTER_SHAPE) does the page reload on its own, and the line says why. Either way the reload
  // carries the view (above), and the terminal keeps its lines (term.js).
  const SHAPE = 1;                                  // the scene shape this file reads: scene.PAINTER_SHAPE
  let painter = null, leaving = false;
  function reloadKeeping() {
    const a = document.activeElement, s = getSelection();
    const c = a && a.closest && a.closest(".explicit-composer[data-key]");      // a5736: a composer's caret comes back too
    const focus = c ? { key: c.dataset.key, caret: null }
      : a && a.dataset && a.dataset.key ? { key: a.dataset.key, caret: s.rangeCount && a.contains(s.focusNode) ? s.focusOffset : null } : null;
    const floats = [...paint.querySelectorAll('.l-float:not([data-folded="1"])')].map(e => e.dataset.key);
    try { sessionStorage.setItem(carryKey, JSON.stringify({ answer: held, places: V.places(), focus, floats })); }
    catch (e) { try { sessionStorage.setItem(carryKey, JSON.stringify({ places: V.places(), focus, floats })); } catch (e2) {} }
    location.reload();
  }
  function versionIs(v) {
    if (v.shape != null && v.shape !== SHAPE) {
      if (leaving) return; leaving = true;
      if (window.DoorLine) DoorLine.note(`the new code sends screens this page can't read (shape ${v.shape}; it reads ${SHAPE}): reloading, keeping your view`);
      return setTimeout(reloadKeeping, 1500);
    }
    const p = v.painter || v.code; if (!p) return;
    if (painter === null) { painter = p; return; }
    if (p === painter) { if (window.DoorLine) DoorLine.note(""); return; }
    // Alex, 7 Oct: "I want painter edits live immediately, at least for now." New screen code loads on its own, keeping
    // the view (reloadKeeping), as soon as the person's hands are free: nothing carried, no part held, no composer with
    // the caret in it. While hands are busy the line says it is waiting, and the next tick asks again. (Until today the
    // line offered a click and the person chose when; Juniper's e3746 argued that reading has no safe pause.)
    // a5736: an empty composer that only has the caret is free hands. The home base keeps its chat's composer focused,
    // so it waited for ever and Alex's home base ran painter code three landings old (no `scroll none`: it scrolled)
    const empty = k => { const c = k && paint.querySelector(`.explicit-composer[data-key="${CSS.escape(k)}"]`), t = c && c.querySelector("textarea");
      return !!t && !t.value.trim() && !V.drafts.has(k); };
    const a = document.activeElement, idle = a && a.matches(".explicit-composer textarea") && empty(a.closest(".explicit-composer").dataset.key);
    const typing = a && !idle && (a.isContentEditable && paint.contains(a) || a.matches("input,textarea"));
    const composing = [...openComposers].some(k => !empty(k)), holding = V.hold && !empty(V.hold);
    if (resizing || carrying || holding || typing || imageCommentsBusy() || menuDrafts.size || composing) { if (window.DoorLine) DoorLine.note("new screen code: it will load when your hands are free"); return; }
    if (leaving) return; leaving = true;
    if (window.DoorLine) DoorLine.note("new screen code: loading it, keeping your view");
    setTimeout(reloadKeeping, 200);
  }
  setInterval(async () => {
    let v; try { v = await (await fetch("/api/version")).json(); } catch (e) { return; }
    versionIs(v);
  }, 5000);
})();
