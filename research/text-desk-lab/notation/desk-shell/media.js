/* media.js (a5941, 16 Oct; Alex: 'can we get that video to be hyperlinked in chat and open in a native window here?
   I don't want to have to open a different application to look at a video'). A text that says `media` names films and
   pictures in its words; the scene sends the ones the desk may show as paint.media {mode, items: [{path, src, kind,
   name}]} (media_links.py decides, deskd serves /media/ with ranges and checks again). This draws them:
     embed   under the words, each a poster with a play button; a press plays it where it is (the browser's own
             controls then), and Pop out sends the part's `on pop` acts with $value the path as written
     player  the first fills the part: play/pause, seek, time, speed, full window (Space, arrows, F, Esc)
   What is playing, where it is and how fast are this viewer's hands, never the world's. The look is roles: media (the
   frame), tool (the buttons), meta (the name and time); only mechanics are written here. */
(() => {
  const roleClass = r => (window.Style && Style.roleClass ? Style.roleClass(r) : "r-" + r);
  const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}" fill="currentColor"/></svg>`;
  const ICON = { play: "M8 5v14l11-7z", pause: "M6 5h4v14H6zM14 5h4v14h-4z" };
  const clock = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
  function button(words, role, label) {
    const b = document.createElement("button"); b.type = "button"; b.className = roleClass(role || "tool") + " media-button";
    if (words.startsWith("<svg")) b.innerHTML = words; else b.textContent = words;
    if (label) b.setAttribute("aria-label", label);
    return b;
  }
  function stageOf(item) {
    const stage = document.createElement("div"); stage.className = "media-stage";
    if (item.kind === "video") {
      const v = document.createElement("video");
      v.preload = "metadata"; v.playsInline = true; v.src = item.src + "#t=0.1";     // the frame at 0.1 s is the poster
      v.setAttribute("aria-label", item.name); stage.append(v);
    } else {
      const img = document.createElement("img"); img.src = item.src; img.alt = item.name; img.loading = "lazy"; img.draggable = false;
      stage.append(img);
    }
    return stage;
  }

  // embed: each item under the words. `pop(item)` is the part's Pop out, or null when its lens has no `on pop`
  function embed(el, items, pop) {
    const box = document.createElement("div"); box.className = "t-media"; box.contentEditable = "false";
    for (const item of items) {
      const fig = document.createElement("figure"); fig.className = "media-item " + roleClass("media"); fig.dataset.media = item.src;
      const stage = stageOf(item); fig.append(stage);
      const v = stage.querySelector("video");
      if (v) {
        const play = button(svg(ICON.play), "tool", "Play " + item.name); play.classList.add("media-play"); stage.append(play);
        const start = e => { e.stopPropagation(); play.hidden = true; v.controls = true; v.play().catch(() => { play.hidden = false; }); };
        play.addEventListener("click", start);
        v.addEventListener("click", e => { if (!v.controls) start(e); });
      }
      const bar = document.createElement("figcaption"); bar.className = "media-bar";
      const name = document.createElement("span"); name.className = roleClass("meta") + " media-name"; name.textContent = item.name; name.title = item.path;
      bar.append(name);
      if (v) {
        const t = document.createElement("span"); t.className = roleClass("meta") + " media-time"; bar.append(t);
        v.addEventListener("loadedmetadata", () => { t.textContent = clock(v.duration); });
      }
      if (pop) {
        const out = button("Pop out", "tool", "Open " + item.name + " in its own window"); out.classList.add("media-pop");
        out.addEventListener("click", e => { e.stopPropagation(); if (v) v.pause(); pop(item); });
        bar.append(out);
      }
      fig.append(bar); box.append(fig);
    }
    el.append(box);
  }

  // player: the first item fills the part, with its own controls
  function player(el, items) {
    const item = items[0], box = document.createElement("div");
    box.className = "t-media media-player " + roleClass("media"); box.tabIndex = 0; box.dataset.media = item.src; box.title = item.path;
    const stage = stageOf(item); box.append(stage);
    const v = stage.querySelector("video"), bar = document.createElement("div"); bar.className = "media-bar";
    const name = document.createElement("span"); name.className = roleClass("meta") + " media-name"; name.textContent = item.name;
    const full = button("Full window", "tool", "Fill the window"); full.classList.add("media-full");
    const fill = on => { box.toggleAttribute("data-full", on); full.textContent = on ? "Leave full window" : "Full window"; };
    full.addEventListener("click", () => fill(!box.hasAttribute("data-full")));
    if (v) {
      const toggle = button(svg(ICON.play), "tool", "Play"); toggle.classList.add("media-toggle");
      const seek = document.createElement("input"); seek.type = "range"; seek.min = 0; seek.max = 1000; seek.value = 0; seek.step = 1;
      seek.className = "media-seek"; seek.setAttribute("aria-label", "Seek");
      const t = document.createElement("span"); t.className = roleClass("meta") + " media-time";
      const speeds = document.createElement("span"); speeds.className = "media-speeds";
      const show = () => {
        toggle.innerHTML = svg(v.paused ? ICON.play : ICON.pause); toggle.setAttribute("aria-label", v.paused ? "Play" : "Pause");
        if (!seeking) seek.value = v.duration ? Math.round(v.currentTime / v.duration * 1000) : 0;
        t.textContent = clock(v.currentTime) + " / " + clock(v.duration);
        for (const b of speeds.children) b.toggleAttribute("data-on", Number(b.dataset.rate) === v.playbackRate);
      };
      let seeking = false;
      const play = () => (v.paused ? v.play().catch(() => {}) : v.pause());
      toggle.addEventListener("click", play);
      v.addEventListener("click", play);
      seek.addEventListener("input", () => { seeking = true; if (v.duration) v.currentTime = seek.value / 1000 * v.duration; });
      seek.addEventListener("change", () => { seeking = false; });
      for (const r of [0.5, 1, 1.5, 2]) {
        const b = button(r + "×", "tool", "Speed " + r); b.dataset.rate = r;
        b.addEventListener("click", () => { v.playbackRate = r; show(); }); speeds.append(b);
      }
      for (const ev of ["play", "pause", "timeupdate", "loadedmetadata", "ratechange", "seeked"]) v.addEventListener(ev, show);
      box.addEventListener("keydown", e => {
        if (e.target.closest("input")) return;
        const k = e.key;
        if (k === " " || k === "k") { e.preventDefault(); play(); }
        else if (k === "ArrowRight" || k === "ArrowLeft") { e.preventDefault(); v.currentTime = Math.max(0, v.currentTime + (k === "ArrowRight" ? 5 : -5)); }
        else if (k === "f" || k === "F") fill(!box.hasAttribute("data-full"));
        else if (k === "Escape") fill(false);
      });
      bar.append(toggle, seek, t, speeds);
      show();
    } else box.addEventListener("keydown", e => { if (e.key === "Escape") fill(false); else if (e.key === "f" || e.key === "F") fill(!box.hasAttribute("data-full")); });
    bar.append(name, full); box.append(bar);
    el.replaceChildren(box);
  }

  window.Media = { draw(el, media, pop) { if (!media || !media.items || !media.items.length) return; (media.mode === "player" ? player : embed)(el, media.items, pop); } };
})();
