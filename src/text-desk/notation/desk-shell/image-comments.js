/* A picture's existing comment action, with a selected region as context.
   Capture is confined to the sanitized picture element, never the page. */
function ImageComments(paint, send, observed, failed) {
  let active = null;
  const style = document.createElement("style");
  style.textContent = `
    .t-picture { touch-action: none; }
    .image-region { position:fixed; pointer-events:none; border:2px solid #64aaff;
      background:#64aaff22; z-index:10000; box-sizing:border-box; }
    .image-comment { width:min(420px,calc(100vw - 40px)); max-height:85vh; overflow:auto;
      padding:20px; border:1px solid #75849b; border-radius:12px; background:#18202c;
      color:#f3f5fa; box-shadow:0 15px 70px #0009; }
    .image-comment::backdrop { background:#0005; }
    .image-comment h2 { font:600 18px system-ui; margin:0 0 12px; }
    .image-comment img { display:block; max-width:100%; max-height:230px; margin:12px auto; }
    .image-comment textarea { box-sizing:border-box; width:100%; min-height:100px;
      padding:10px; background:#0c131d; color:inherit; border:1px solid #75849b;
      border-radius:6px; font:14px system-ui; resize:vertical; }
    .image-comment p { font:13px system-ui; line-height:1.5; }
    .image-comment footer { display:flex; gap:10px; justify-content:flex-end; margin-top:12px; }
    .image-comment button { padding:8px 15px; border-radius:6px; border:1px solid #75849b;
      background:#24364e; color:inherit; cursor:pointer; }
    .image-comment button[type=submit] { background:#3769ba; }
  `;
  document.head.append(style);
  const clamp = (v, max) => Math.max(0, Math.min(max, v));
  function snapshot(media) {
    if (media.tagName === "IMG") return media.src;
    const clone = media.cloneNode(true), originals = [media, ...media.querySelectorAll("*")];
    [clone, ...clone.querySelectorAll("*")].forEach((node, i) => {
      const s = getComputedStyle(originals[i]);
      for (const prop of ["fill", "stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity",
        "font-family", "font-size", "font-weight", "font-style", "text-anchor", "letter-spacing"])
        node.setAttribute(prop, s.getPropertyValue(prop));
    });
    const r = media.getBoundingClientRect();
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", r.width); clone.setAttribute("height", r.height);
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
  }
  async function crop(src, r, box) {
    const img = new Image(); img.src = src; await img.decode();
    const scale = Math.min(devicePixelRatio || 1, 2048 / box[2], 2048 / box[3]);
    const c = document.createElement("canvas");
    c.width = Math.max(1, Math.round(box[2] * scale)); c.height = Math.max(1, Math.round(box[3] * scale));
    const ctx = c.getContext("2d");
    ctx.drawImage(img, box[0] / r.width * img.width, box[1] / r.height * img.height,
      box[2] / r.width * img.width, box[3] / r.height * img.height, 0, 0, c.width, c.height);
    const data = c.toDataURL("image/png");
    if (data.length > 2796300) throw new Error("The selected region is too large. Choose a smaller region.");
    return { data_url: data, width: c.width, height: c.height };
  }
  function compose(n, action, image, fence) {
    const d = document.createElement("dialog"); d.className = "image-comment";
    const title = Object.assign(document.createElement("h2"), { textContent: "Comment on this region", id: "image-comment-title" });
    d.setAttribute("aria-labelledby", title.id);
    const preview = Object.assign(new Image(), { src: image.data_url, alt: "Region attached to this comment" });
    const hint = Object.assign(document.createElement("p"), { textContent: "This crop will stay with your comment and be sent to the replying agent." });
    const input = document.createElement("textarea"); input.placeholder = "Your comment…"; input.setAttribute("aria-label", "Your comment");
    const status = document.createElement("p"); status.setAttribute("role", "status");
    const footer = document.createElement("footer"), cancel = document.createElement("button"), submit = document.createElement("button");
    cancel.type = "button"; cancel.textContent = "Cancel"; submit.type = "submit"; submit.textContent = "Send comment";
    footer.append(cancel, submit); d.append(title, preview, hint, input, status, footer); document.body.append(d);
    let pending = false, gesture = crypto.randomUUID();
    const close = () => { if (!pending) { d.close(); d.remove(); active = null; } };
    cancel.onclick = close; d.addEventListener("cancel", e => { e.preventDefault(); close(); });
    async function post() {
      if (pending || !input.value.trim()) return;
      pending = true; submit.disabled = cancel.disabled = input.disabled = true; status.textContent = "Sending…";
      const value = input.value.trim().replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
      const line = action.line.replace("$selected", "").replace("$value", () => value);
      let result;
      try { result = await send(n, line, fence, { image, gesture }); }
      catch (e) { status.textContent = e.message; }
      pending = false; submit.disabled = cancel.disabled = false;
      if (result && !result.error && !(result.text || "").split("\n").some(l => /^(ERR|MISS)/.test(l))) { close(); return; }
      if (result) { input.disabled = false; gesture = crypto.randomUUID(); }
      status.textContent = result?.error || result?.text || "The answer was lost. Retry sends the same comment once.";
      submit.textContent = "Retry";
    }
    submit.onclick = post;
    input.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); post(); } });
    d.showModal(); input.focus(); active = d;
  }
  paint.addEventListener("pointerdown", e => {
    if (active || e.button !== 0 || e.shiftKey || e.altKey) return;
    const pic = e.target.closest?.(".t-picture");
    // Annotated pictures keep the source media inside a stage with sibling overlays.
    // Crop only that media, so existing highlights never become part of the attachment.
    const media = pic?.querySelector(":scope > svg, :scope > img, :scope > .picture-stage > svg, :scope > .picture-stage > img");
    const host = pic?.closest("[data-menu]"), n = host?._n;
    const action = n?.acts.find(a => a.on === "menu" && /^do comment [as]\d+ line=/.test(a.line) && a.line.includes("$value"));
    if (!media || !action) return;
    const source = action.line.match(/^do comment ([as]\d+)/)[1];
    const r = media.getBoundingClientRect(), x = clamp(e.clientX - r.left, r.width), y = clamp(e.clientY - r.top, r.height);
    if (!r.width || !r.height) return;
    const sourceText = pic._n.paint.text, saved = snapshot(media), fence = { ...n.fence, ...observed() };
    const overlay = document.createElement("div"); overlay.className = "image-region"; document.body.append(overlay); active = overlay;
    let box = [x, y, 0, 0];
    const move = ev => {
      const xx = clamp(ev.clientX - r.left, r.width), yy = clamp(ev.clientY - r.top, r.height);
      box = [Math.min(x, xx), Math.min(y, yy), Math.abs(x - xx), Math.abs(y - yy)];
      Object.assign(overlay.style, { left: r.left + box[0] + "px", top: r.top + box[1] + "px", width: box[2] + "px", height: box[3] + "px" });
      ev.preventDefault(); ev.stopPropagation();
    };
    const cleanup = () => {
      document.removeEventListener("pointermove", move, true); document.removeEventListener("pointerup", up, true);
      document.removeEventListener("pointercancel", abort, true); document.removeEventListener("keydown", key, true);
      window.removeEventListener("blur", abort);
      document.removeEventListener("scroll", abort, true);
      overlay.remove(); active = null;
    };
    const abort = () => cleanup();
    const key = ev => { if (ev.key === "Escape") { ev.preventDefault(); ev.stopPropagation(); abort(); } };
    const up = async ev => {
      move(ev); cleanup();
      if (box[2] < 6 || box[3] < 6) return;
      active = true;
      try {
        const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(sourceText));
        const image = { ...await crop(saved, r, box), source, source_hash: [...new Uint8Array(hash)].map(v => v.toString(16).padStart(2, "0")).join(""),
          rect: [box[0] / r.width, box[1] / r.height, box[2] / r.width, box[3] / r.height] };
        compose(n, action, image, fence);
      } catch (_) { active = null; failed(); }
    };
    document.addEventListener("pointermove", move, true); document.addEventListener("pointerup", up, true);
    document.addEventListener("pointercancel", abort, true); document.addEventListener("keydown", key, true);
    window.addEventListener("blur", abort);
    document.addEventListener("scroll", abort, true);
    paint.setPointerCapture(e.pointerId);
    e.preventDefault(); e.stopPropagation();
  }, true);
  return () => !!active;
}
