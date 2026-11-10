/* page.js (a6431, 17 Oct; Alex: 'a webapp running in the middle the size of a phone'). A text that says `page` names a
   page in its words (a lens, or a /path on this server); the scene sends paint.page {src, w, h, touch, picks, safe,
   cutout, mark}. This draws it: the real painter (lens.html, the same person and world) in a same-origin frame of
   exactly w x h CSS pixels, scaled to fit the part and never above 1:1. The framed page keeps itself current as any
   painted page does, so a change to its lens or its data repaints it with no reload; a new size, a turn or a toggle
   changes the frame where it stands (only another src loads another page).
     touch   a drag inside scrolls what is under it (a carried or dragged part keeps its own drag), a click is a tap,
             the pointer is a fingertip and the scrollbars are a phone's (none)
     picks   a tap names the part under it instead of pressing it; a long press names it either way. Naming sends the
             part's `on pick` acts, $value its name (its part, its thing, its words, its lens) and $part its scene key,
             the key the control screen reads (id="part:<key>")
     safe    the insets the device keeps clear, drawn over the page, with its cutout (island, hole, notch)
     mark    a part of the page by its key, drawn round: what was picked is world data, so anyone can point
   What is drawn over the page is mechanics only; the frame's look is the role `pageframe` and the box's `pagemark`. */
(() => {
  const roleClass = r => (window.Style && Style.roleClass ? Style.roleClass(r) : "r-" + r);
  const HOLD_MS = 550, SLOP = 6;
  const FINGER = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28'%3E%3Ccircle cx='14' cy='14' r='11' fill='%23888' fill-opacity='.35' stroke='%23fff' stroke-opacity='.8' stroke-width='1.5'/%3E%3C/svg%3E\") 14 14, pointer";

  function urlOf(src, hands) {
    if (src.startsWith("/")) return src;
    const m = src.match(/^([a-z][a-z0-9-]*)(?:\s+on\s+([afs]\d+))?$/);
    const q = new URLSearchParams({ session: hands.session, as: hands.who, lens: m[1], inspect: "0", framed: "1" });
    if (m[2]) q.set("on", m[2]);
    return "lens.html?" + q;
  }
  const idIn = key => (String(key).split("/").reverse().find(s => /^[afs]\d+$/.test(s)) || "");
  const partIn = key => (String(key).split("/").reverse().find(s => s && !/^[afs]\d+$/.test(s) && !/^\d+$/.test(s)) || "");

  // what a person would call the part: its name in its lens, the thing it shows, its words (an id is drawn as its name
  // wherever a lens prints it, so the thing stays an id here)
  function nameOf(part, lensName) {
    const n = part._n || {}, key = part.dataset.key || "";
    let item = (n.fence && n.fence.item) || idIn(key);
    for (let up = part.parentElement; !item && up; up = up.parentElement) if (up.dataset && up.dataset.key) item = (up._n && up._n.fence && up._n.fence.item) || idIn(up.dataset.key);
    const words = (part.innerText || "").replace(/\s+/g, " ").trim();
    return [n.part || partIn(key) || "part", item ? "of " + item : "", words ? "“" + (words.length > 48 ? words.slice(0, 47) + "…" : words) + "”" : "",
            lensName ? "in " + lensName : ""].filter(Boolean).join(" ");
  }

  function draw(el, spec, hands) {
    el.classList.add("t-page");
    el.replaceChildren();
    // the bezel is the role `pageframe` (its ground, padding, corner and edge) round the screen, which is scaled to fit
    const hold = document.createElement("div"); hold.className = "page-hold " + roleClass("pageframe");
    const dev = document.createElement("div"); dev.className = "page-device";
    const frame = document.createElement("iframe"); frame.className = "page-frame"; frame.title = spec.src;
    const over = document.createElement("div"); over.className = "page-over";
    const mark = document.createElement("div"); mark.className = "page-mark " + roleClass("pagemark"); mark.hidden = true;
    const aim = document.createElement("div"); aim.className = "page-aim"; aim.hidden = true;
    dev.append(frame, over, mark, aim); hold.append(dev); el.append(hold);
    let cur = null, doc = null, scale = 1;
    const ctl = { src: spec.src, el, frame, get spec() { return cur; }, get scale() { return scale; } };

    function fit() {
      if (!cur) return;
      const cs = getComputedStyle(hold), px = k => parseFloat(cs[k]) || 0;
      const bx = px("paddingLeft") + px("paddingRight") + px("borderLeftWidth") + px("borderRightWidth"),
            by = px("paddingTop") + px("paddingBottom") + px("borderTopWidth") + px("borderBottomWidth");
      const aw = el.clientWidth - 16 - bx, ah = el.clientHeight - 16 - by;
      scale = Math.max(0.05, Math.min(1, aw / cur.w, ah / cur.h));
      const r = Math.max(0, px("borderTopLeftRadius") - px("paddingLeft"));
      Object.assign(dev.style, { width: cur.w + "px", height: cur.h + "px", transform: `scale(${scale})`,
                                 left: px("paddingLeft") + "px", top: px("paddingTop") + "px", borderRadius: r / scale + "px" });
      Object.assign(hold.style, { width: cur.w * scale + "px", height: cur.h * scale + "px" });
      dev.dataset.scale = scale.toFixed(3);
    }
    new ResizeObserver(fit).observe(el);

    function safeArea() {
      over.replaceChildren();
      const s = cur.safe; if (!s) return;
      const [t, r, b, l] = s, band = (css) => { const d = document.createElement("div"); d.className = "page-inset"; Object.assign(d.style, css); over.append(d); };
      if (t) band({ left: 0, right: 0, top: 0, height: t + "px" });
      if (b) band({ left: 0, right: 0, bottom: 0, height: b + "px" });
      if (l) band({ left: 0, top: 0, bottom: 0, width: l + "px" });
      if (r) band({ right: 0, top: 0, bottom: 0, width: r + "px" });
      // the cutout sits in the widest inset that is a short side (top in portrait, left in landscape); the home bar in the bottom
      const side = t >= l && t >= r ? "top" : (l >= r ? "left" : "right"), depth = Math.max(t, l, r);
      if (cur.cutout && depth) {
        const c = document.createElement("div"); c.className = "page-cutout page-cutout-" + cur.cutout;
        const long = side === "top" ? cur.w : cur.h;
        const along = cur.cutout === "island" ? Math.round(long * 0.32) : cur.cutout === "notch" ? Math.round(long * 0.42) : Math.round(depth * 0.45);
        const across = cur.cutout === "island" ? Math.round(depth * 0.62) : cur.cutout === "notch" ? Math.round(depth * 0.55) : along;
        const off = cur.cutout === "notch" ? 0 : Math.round((depth - across) / 2);
        if (side === "top") Object.assign(c.style, { top: off + "px", left: `calc(50% - ${along / 2}px)`, width: along + "px", height: across + "px" });
        else Object.assign(c.style, { [side]: off + "px", top: `calc(50% - ${along / 2}px)`, width: across + "px", height: along + "px" });
        over.append(c);
      }
      if (b >= 14) {
        const bar = document.createElement("div"); bar.className = "page-homebar";
        Object.assign(bar.style, { bottom: Math.round(b * 0.25) + "px", width: Math.round(Math.min(cur.w, 600) * 0.34) + "px", left: `calc(50% - ${Math.round(Math.min(cur.w, 600) * 0.17)}px)` });
        over.append(bar);
      }
    }

    // the box round a part of the page, by its key: where the framed painter drew it now (it may scroll, repaint, move)
    function boxOver(box, part) {
      if (!part || !part.getClientRects().length) { box.hidden = true; return; }
      const r = part.getBoundingClientRect();
      box.hidden = false;
      Object.assign(box.style, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    }
    const partOf = t => (t && t.closest ? t.closest('[id^="part:"]') : null);
    function placeMark() {
      if (!cur || !cur.mark || !doc) { mark.hidden = true; return; }
      boxOver(mark, doc.getElementById("part:" + cur.mark));
    }
    let markQueued = false;
    const queueMark = () => { if (markQueued) return; markQueued = true; requestAnimationFrame(() => { markQueued = false; placeMark(); }); };

    function lensName() { const m = cur.src.match(/^([a-z][a-z0-9-]*)/); return m ? m[1] : ""; }
    function pick(target) {
      const part = partOf(target); if (!part || !hands.canPick()) return false;
      hands.pick(nameOf(part, lensName()), part.dataset.key);
      boxOver(mark, part);                    // shown at once; the world's mark keeps it there after the answer
      return true;
    }

    function hook() {
      let d; try { d = frame.contentDocument; } catch (e) { d = null; }
      if (!d || !d.documentElement || d === doc) return;
      doc = d;
      const win = frame.contentWindow, st = d.createElement("style"); st.id = "page-hands";
      d.head.append(st);
      d.documentElement.dataset.framed = "1";
      ctl.restyle = () => {
        st.textContent = [
          // a framed page is the app alone: no status row under it, no door line (lens.html's own, for a whole window)
          "body { grid-template-rows: minmax(0, 1fr) auto !important; } #status[hidden], #door, #term-open { display: none !important; }",
          cur.touch ? `html, body, body * { cursor: ${FINGER} !important; } ::-webkit-scrollbar { width: 0 !important; height: 0 !important; } * { scrollbar-width: none; }
            body :not(input):not(textarea):not([contenteditable="true"]) { user-select: none; -webkit-user-select: none; }` : "",
          cur.picks ? "html, body, body * { cursor: crosshair !important; }" : ""].join("\n");
      };
      ctl.restyle();
      let down = null, eatClick = false;
      const scroller = t => {
        for (let e = t; e && e !== d.documentElement; e = e.parentElement) {
          const cs = win.getComputedStyle(e);
          if (/(auto|scroll)/.test(cs.overflowY + cs.overflowX) && (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1)) return e;
        }
        return d.scrollingElement;
      };
      const own = t => t.closest && t.closest('[data-carry], [data-drag], [contenteditable="true"], textarea, input, select');
      win.addEventListener("pointerdown", e => {
        if (e.button !== 0) return;
        down = { x: e.clientX, y: e.clientY, t: e.target, moved: false, sc: null, held: false };
        if (cur.touch && !own(e.target)) { const s = scroller(e.target); down.sc = s; down.top = s.scrollTop; down.left = s.scrollLeft; }
        if (hands.canPick()) down.timer = setTimeout(() => { if (down && !down.moved) { down.held = pick(down.t); eatClick = down.held; } }, HOLD_MS);
      }, true);
      win.addEventListener("pointermove", e => {
        if (cur.picks && !down) { const p = partOf(e.target); if (p) boxOver(aim, p); else aim.hidden = true; }
        if (!down) return;
        const dx = e.clientX - down.x, dy = e.clientY - down.y;
        if (!down.moved && Math.hypot(dx, dy) > SLOP) { down.moved = true; clearTimeout(down.timer); }
        if (down.moved && down.sc) { down.sc.scrollTop = down.top - dy; down.sc.scrollLeft = down.left - dx; e.preventDefault(); }
      }, true);
      const up = () => { if (!down) return; clearTimeout(down.timer); if (down.moved && down.sc) eatClick = true; down = null; };
      win.addEventListener("pointerup", up, true);
      win.addEventListener("pointercancel", up, true);
      d.addEventListener("pointerleave", () => { aim.hidden = true; }, true);
      win.addEventListener("click", e => {
        if (eatClick) { eatClick = false; e.preventDefault(); e.stopImmediatePropagation(); return; }
        if (cur.picks && pick(e.target)) { e.preventDefault(); e.stopImmediatePropagation(); }
      }, true);
      win.addEventListener("scroll", queueMark, true);
      win.addEventListener("resize", queueMark);
      new win.MutationObserver(queueMark).observe(d.body, { childList: true, subtree: true });
      queueMark();
    }
    frame.addEventListener("load", hook);

    ctl.update = (s) => {
      const fresh = !cur;
      cur = s;
      dev.dataset.touch = s.touch ? "1" : ""; dev.dataset.picks = s.picks ? "1" : "";
      frame.width = s.w; frame.height = s.h;
      if (fresh) frame.src = urlOf(s.src, hands);
      safeArea(); fit();
      if (ctl.restyle && doc) ctl.restyle();
      if (!s.picks) aim.hidden = true;
      queueMark();
    };
    ctl.update(spec);
    el._page = ctl;
    return ctl;
  }

  window.Page = { draw, nameOf };
})();
