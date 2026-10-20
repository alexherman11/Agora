// Generic cross-lens receivers. Policy remains in each receiver's world gesture.
// A drag snapshots receivers at pickup: repainting cannot grant a new destination
// or silently substitute a newer fence. Also used by specialised carry adapters.
(function (root) {
  "use strict";
  function accepts(receiver, part) {
    return (receiver?._drops || []).some(a => a.part === part || a.part === "any");
  }
  function snapshot(paint, part) {
    return new Map([...paint.querySelectorAll("[data-drop]")]
      .filter(r => accepts(r, part))
      .map(r => [r.dataset.key, { fence: r._n.fence,
        acts: (r._drops || []).filter(a => a.part === part || a.part === "any")
          .map(a => ({ ...a })) }]));
  }
  function plan(receiver, source, seen, pointer) {
    const saved = seen.get(receiver?.dataset?.key);
    if (!saved || !accepts(receiver, source.part)) return null;
    const own = receiver.contains(source.el);
    const acts = saved.acts.filter(a => !own || a.side === "left" || a.side === "right");
    if (!acts.length) return null;
    const b = receiver.getBoundingClientRect();
    if (!(b.width > 0 && b.height > 0)) return null;
    const fx = pointer ? (pointer.clientX - b.left) / b.width : .5;
    const fy = pointer ? (pointer.clientY - b.top) / b.height : .5;
    const distance = { left: fx, right: 1 - fx, top: fy, bottom: 1 - fy };
    const sides = acts.filter(a => a.side).sort((a, b) => distance[a.side] - distance[b.side]);
    // A named receiver wins over the general receiver at the same location.
    const choices = acts.some(a => a.part === source.part) ?
      acts.filter(a => a.part === source.part) : acts;
    const edges = sides.filter(a => choices.includes(a));
    const act = edges.find(a => distance[a.side] < 1 / 3) ||
      choices.find(a => !a.side) || edges[0];
    if (!act) return null;
    const h = { left: [0, 0, .5, 1], right: [.5, 0, .5, 1],
      top: [0, 0, 1, .5], bottom: [0, .5, 1, .5] }[act.side] || [0, 0, 1, 1];
    return { key: receiver.dataset.key, fence: saved.fence, act,
      box: [b.left + h[0] * b.width, b.top + h[1] * b.height, h[2] * b.width, h[3] * b.height] };
  }
  function at(elements, source, seen, pointer) {
    // elementsFromPoint is front-to-back. A child receiver wins over its parent.
    for (const receiver of elements) {
      if (!receiver.dataset?.drop) continue;
      const p = plan(receiver, source, seen, pointer);
      if (p) return { receiver, ...p };
    }
    return null;
  }
  function submit(send, target, sourceFence) {
    if (!target || !sourceFence) return Promise.resolve(null);
    return send({ key: target.key, fence: target.fence }, target.act.line,
      undefined, { carried: sourceFence, receiver: target.fence });
  }
  function session(paint, source, send, exclude, doc = document) {
    const seen = snapshot(paint, source.n.part);
    let target = null, box = null;
    const cancel = () => { box?.remove(); box = null; target = null; };
    return {
      move(pointer) {
        const elements = doc.elementsFromPoint(pointer.clientX, pointer.clientY)
          .filter(el => !exclude?.contains(el));
        target = at(elements, { el: source.el, part: source.n.part }, seen, pointer);
        if (!target) { box?.remove(); box = null; return null; }
        if (!box) {
          box = doc.createElement("div"); box.className = "landing-box";
          Object.assign(box.style, { position: "fixed", pointerEvents: "none", zIndex: "45", transition: "none" });
          doc.body.appendChild(box);
        }
        ["left", "top", "width", "height"].forEach((k, i) => { box.style[k] = target.box[i] + "px"; });
        return target;
      },
      get target() { return target; },
      async release() {
        const chosen = target;
        try { return await submit(send, chosen, source.n.fence); }
        finally { cancel(); }
      },
      cancel
    };
  }
  const api = { accepts, snapshot, plan, at, submit, session };
  if (typeof module !== "undefined") module.exports = api;
  else root.CarryTargets = api;
})(typeof window === "undefined" ? globalThis : window);
