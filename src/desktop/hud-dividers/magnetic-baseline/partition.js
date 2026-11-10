// A bounded slicing tree in a declared world property. No application names.
// Only a gesture preview is local; every durable change is one fenced prop act.
(function (host) {
  "use strict";
  const copy = x => JSON.parse(JSON.stringify(x));
  const ids = n => !n ? [] : n.id ? [n.id] : n.kids.flatMap(ids);
  const leaf = id => ({ id });
  const reference = value => typeof value === "string" ? value : value?.$ref;
  function encoded(tree) {
    function node(n) {
      if (!n) return null;
      if (n.id) return { ...n, id: { $ref: n.id } };
      return { ...n, kids: n.kids.map(node),
        ...(n.axis === "tabs" ? { active: { $ref: n.active } } : {}) };
    }
    return { v: 1, root: node(tree.root), ...(tree.focus_weights ? {
      focus_weights: Object.entries(tree.focus_weights).map(([id, members]) => ({
        panel: { $ref: id }, members: Object.entries(members).map(([id, weight]) => ({ panel: { $ref: id }, weight }))
      }))
    } : {}) };
  }
  function clean(n, allowed, seen = new Set(), depth = 0) {
    if (!n || depth > 32) return null;
    if (n.id && typeof n.id === "object") n = { ...n, id: reference(n.id) };
    if (typeof n.id === "string") {
      if (!allowed.has(n.id) || seen.has(n.id)) return null;
      seen.add(n.id);
      return { id: n.id, ...(["content","stretch"].includes(n.size) ? { size: n.size } : {}),
        ...(Array.isArray(n.extent) && n.extent.length === 2 && n.extent.every(x=>Number.isFinite(x)&&x>0)
          ? { extent: n.extent.slice() } : {}) };
    }
    if (!["x", "y", "tabs"].includes(n.axis) || !Array.isArray(n.kids)) return null;
    const pairs = n.kids.slice(0, 256).map((k, i) => [clean(k, allowed, seen, depth + 1), n.weights?.[i]])
      .filter(([k]) => k);
    if (!pairs.length) return null;
    if (pairs.length === 1) return pairs[0][0];
    const out = { axis: n.axis, kids: pairs.map(p => p[0]) };
    if (n.axis === "tabs") out.active = ids(out).includes(reference(n.active)) ? reference(n.active) : ids(out.kids[0])[0];
    else out.weights = pairs.map(p => Number.isFinite(p[1]) && p[1] > 0 ? p[1] : 1);
    return out;
  }
  function model(raw, members, preferences = {}) {
    let n;
    try { n = typeof raw === "string" ? JSON.parse(raw) : copy(raw); } catch (_) {}
    if (n?.v !== 1) n = null;
    // Guarded direct children still carry partition_item. They keep their
    // slots; things actually removed from the membership do not accumulate.
    const allowed = new Set(members), seen = new Set();
    let root = clean(n?.root, allowed, seen);
    for (const id of members) if (!seen.has(id)) {
      root = root ? { axis: "x", kids: [root, leaf(id)], weights: [1, 1] } : leaf(id);
    }
    function defaults(node) {
      if (!node) return;
      if (node.id) {
        if (!node.size && preferences[node.id] === "content") node.size = "content";
      } else node.kids.forEach(defaults);
    }
    defaults(root);
    const fw = Array.isArray(n?.focus_weights) ? Object.fromEntries(n.focus_weights
      .filter(f => allowed.has(reference(f.panel)) && Array.isArray(f.members))
      .map(f => [reference(f.panel), Object.fromEntries(f.members
        .filter(m => allowed.has(reference(m.panel)) && Number.isFinite(m.weight) && m.weight > 0)
        .map(m => [reference(m.panel), m.weight]))])) : n?.focus_weights;
    return { v: 1, root, ...(fw && typeof fw === "object" ? { focus_weights: fw } : {}) };
  }
  function prune(n, predicate) {
    if (!n) return null;
    if (n.id) return predicate(n) ? copy(n) : null;
    const pairs = n.kids.map((k, i) => [prune(k, predicate), n.weights?.[i]]).filter(p => p[0]);
    if (!pairs.length) return null;
    if (pairs.length === 1) return pairs[0][0];
    const out = { ...n, kids: pairs.map(p => p[0]) };
    if (n.axis !== "tabs") out.weights = pairs.map(p => p[1]);
    else if (!ids(out).includes(n.active)) out.active = ids(out.kids[0])[0];
    return out;
  }
  function replace(n, id, fn) {
    if (n.id) return n.id === id ? fn(n) : n;
    return { ...n, kids: n.kids.map(k => replace(k, id, fn)) };
  }
  function activate(n, id) {
    if (n.id) return n;
    return { ...n, ...(n.axis === "tabs" && ids(n).includes(id) ? { active: id } : {}),
      kids: n.kids.map(k => activate(k, id)) };
  }
  function project(n, visible, path = []) {
    if (!n) return null;
    if (n.id) return visible.has(n.id) ? n : null;
    const pairs = n.kids.map((k, i) => [project(k, visible, path.concat(i)), i]).filter(p => p[0]);
    if (!pairs.length) return null;
    if (pairs.length === 1) return pairs[0][0];
    const out = { ...n, kids: pairs.map(p => p[0]), _path: path, _indices: pairs.map(p => p[1]) };
    if (n.axis !== "tabs") out.weights = pairs.map(p => n.weights[p[1]]);
    else if (!ids(out).includes(n.active)) out.active = ids(out.kids[0])[0];
    return out;
  }
  function minimum(n, opt) {
    if (n.id) return opt.minimum;
    const sizes = n.kids.map(k => minimum(k, opt));
    if (n.axis === "tabs") return [Math.max(...sizes.map(s => s[0])), Math.max(...sizes.map(s => s[1])) + opt.tab];
    const a = n.axis === "x" ? 0 : 1, b = 1 - a, out = [];
    out[a] = sizes.reduce((s, x) => s + x[a], 0) + opt.gap * (sizes.length - 1);
    out[b] = Math.max(...sizes.map(s => s[b])); return out;
  }
  function fit(space, mins, weights) {
    space = Math.max(0, space);
    const total = mins.reduce((s, x) => s + x, 0);
    if (total >= space) return mins.map(x => total ? x * space / total : 0);
    const out = Array(mins.length).fill(0), free = new Set(mins.map((_, i) => i));
    let remain = space;
    while (free.size) {
      const sum = [...free].reduce((s, i) => s + weights[i], 0);
      const tight = [...free].filter(i => remain * weights[i] / sum < mins[i]);
      if (!tight.length) { for (const i of free) out[i] = remain * weights[i] / sum; break; }
      for (const i of tight) { out[i] = mins[i]; remain -= mins[i]; free.delete(i); }
    }
    return out;
  }
  function geometry(root, bounds, options = {}) {
    const opt = { minimum: [240, 140], gap: 16, tab: 28, ...options };
    if (opt.visible) root = project(root, opt.visible);
    const boxes = {}, splits = [], tabs = [];
    function walk(n, b, path) {
      if (!n) return;
      if (n.id) {
        const wanted = n.extent || opt.intrinsic?.[n.id];
        boxes[n.id] = n.size === "content" && wanted
          ? { ...b, w: Math.min(b.w, Math.max(Math.min(b.w, opt.minimum[0]), wanted[0])),
              h: Math.min(b.h, Math.max(Math.min(b.h, opt.minimum[1]), wanted[1])) }
          : b;
        return;
      }
      if (n.axis === "tabs") {
        const height = Math.min(opt.tab, b.h);
        tabs.push({ path: n._path || path, node: n, box: { ...b, h: height } });
        const active = n.kids.find(k => ids(k).includes(n.active)) || n.kids[0];
        walk(active, { ...b, y: b.y + height, h: Math.max(0, b.h - height) }, path.concat(n.kids.indexOf(active)));
        return;
      }
      const x = n.axis === "x", span = x ? b.w : b.h;
      const gap = Math.min(opt.gap, span / Math.max(1, n.kids.length - 1));
      const mins = n.kids.map(k => minimum(k, opt)[x ? 0 : 1]);
      const sizes = fit(span - gap * (n.kids.length - 1), mins, n.weights);
      let pos = x ? b.x : b.y;
      const children = n.kids.map((k, i) => {
        const box = x ? { x: pos, y: b.y, w: sizes[i], h: b.h } : { x: b.x, y: pos, w: b.w, h: sizes[i] };
        walk(k, box, path.concat(i)); pos += sizes[i] + gap; return box;
      });
      splits.push({ path: n._path || path, node: n, children, mins, gap, box: b });
    }
    walk(root, bounds, []); return { boxes, splits, tabs };
  }
  function drop(tree, dragged, target, side, global = false) {
    if (!ids(tree.root).includes(dragged) || (!global && (target === dragged || !ids(tree.root).includes(target)))) return null;
    const original = (function find(n) { return n.id ? (n.id === dragged ? n : null) : n.kids.map(find).find(Boolean); })(tree.root);
    const rest = prune(tree.root, n => n.id !== dragged);
    if (!rest) return null;
    const add = n => {
      if (side === "centre") {
        return { axis: "tabs", kids: [n, original], active: dragged };
      }
      const axis = ["left", "right"].includes(side) ? "x" : "y";
      // An edge drop deliberately fills the previewed split. Centre tabs keep
      // a content preference; ordinary app intent is otherwise unchanged.
      const placed = original.size === "content" ? { ...original, size: "stretch" } : original;
      return { axis, kids: ["left", "top"].includes(side) ? [placed, n] : [n, placed], weights: [1, 1] };
    };
    const root = global ? add(rest) : replace(rest, target, add);
    const depth = n => n.id ? 0 : 1 + Math.max(...n.kids.map(depth));
    // Never save a gesture the next bounded model read would truncate.
    return depth(root) <= 32 ? { ...tree, root } : null;
  }
  function nodeAt(root, path) { return path.reduce((n, i) => n.kids[i], root); }
  function resize(tree, path, index, delta, bounds, options) {
    const out = copy(tree), split = geometry(out.root, bounds, options).splits.find(s => JSON.stringify(s.path) === JSON.stringify(path));
    if (!split || index < 0 || index >= split.children.length - 1) return out;
    const axis = split.node.axis === "x" ? "w" : "h", a = split.children[index][axis], b = split.children[index + 1][axis];
    const sum = a + b, scale = Math.min(1, sum / (split.mins[index] + split.mins[index + 1]));
    const minA = split.mins[index] * scale, minB = split.mins[index + 1] * scale;
    if (sum - minA - minB < .01) return out;
    const first = Math.max(minA, Math.min(sum - minB, a + delta));
    // Convert displayed pixels to weights for all children, including previously
    // clamped ones. This prevents a jump when a minimum becomes unconstrained.
    const node = nodeAt(out.root, path), indices = split.node._indices || split.children.map((_, i) => i);
    const totalWeight = indices.reduce((s, i) => s + node.weights[i], 0);
    const totalPixels = split.children.reduce((s, c) => s + c[axis], 0);
    split.children.forEach((c, i) => {
      const pixels = i === index ? first : i === index + 1 ? sum - first : c[axis];
      node.weights[indices[i]] = Math.max(.000001, pixels * totalWeight / totalPixels);
    });
    if (Math.abs(first - a) > .001) for (const i of [index, index + 1]) {
      const child = node.kids[indices[i]];
      if (child.id && child.size === "content") child.size = "stretch";
    }
    return out;
  }
  function hit(bounds, boxes, point, dragged) {
    const d = { left: point.x - bounds.x, right: bounds.x + bounds.w - point.x,
      top: point.y - bounds.y, bottom: bounds.y + bounds.h - point.y };
    if (Math.min(...Object.values(d)) < 0) return null;
    const global = Object.keys(d).sort((a, b) => d[a] - d[b])[0];
    if (d[global] <= Math.min(40, bounds.w / 6, bounds.h / 6)) return { global: true, side: global };
    for (const [id, b] of Object.entries(boxes)) {
      if (id === dragged || point.x < b.x || point.y < b.y || point.x > b.x + b.w || point.y > b.y + b.h) continue;
      const dist = { left: (point.x - b.x) / b.w, right: (b.x + b.w - point.x) / b.w,
        top: (point.y - b.y) / b.h, bottom: (b.y + b.h - point.y) / b.h };
      const side = Object.keys(dist).sort((a, z) => dist[a] - dist[z])[0];
      return { target: id, side: dist[side] < .25 ? side : "centre", global: false };
    }
    return null;
  }
  function plan(tree, dragged, target, bounds, options) {
    if (!target) return null;
    const next = drop(tree, dragged, target.target, target.side, target.global);
    if (!next) return null;
    const projected = geometry(next.root, bounds, options);
    return { tree: next, box: projected.boxes[dragged], target };
  }
  function escape(value) { return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\$/g, "\\$").replace(/\n/g, "\\n"); }
  function command(n, tree, focus) {
    return n.acts.find(a => a.on === "arrange").line.replace(/\$(value|partition_focus)\b/g,
      (_, key) => escape(key === "value" ? JSON.stringify(encoded(tree)) : focus || ""));
  }
  const exports = { ids, model, encoded, prune, project, replace, activate, minimum, fit, geometry, drop, resize, hit, plan, nodeAt, command };
  if (typeof module !== "undefined") module.exports = exports;
  else host.Partition = exports;
})(typeof window !== "undefined" ? window : globalThis);
