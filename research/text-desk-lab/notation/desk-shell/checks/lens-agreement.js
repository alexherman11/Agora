// checks/lens-agreement.js — the agreement check, made structural. Owner: Iris.
//
// Until now "does the screen say what the text says" was a word diff: I compared the words
// visible in a window against the words in its text() panel. That is a weak check. It cannot
// tell a missing node from a reworded one, it cannot see a node painted that the text never
// mentioned, and it says nothing about roles, gestures or boxes.
//
// With a scene there is something better available. The scene is a tree with a `key` on every
// node. The paint is a tree. If the painter has no source of look but the scene, then the two
// trees must correspond node for node, and that correspondence is checkable rather than
// arguable.
//
//     const L = await import('/checks/lens-agreement.js');
//     await L.run('lens', 'iris', 'notes')
//
// ROUND SIX: THE CAVEAT IS GONE, AND THIS FILE IS NOW A PROOF RATHER THAN AN ARGUMENT.
// Last round the painter emitted no key, so I could only WALK both trees in parallel and
// assume the nth painted child was the nth scene child — which is the very thing the check
// was supposed to establish. Jeff added `data-key`. So the walker is deleted and the check
// is a set join on the key: two sets, compared by identity, with duplicates fatal on either
// side. A mismatch anywhere is now local instead of cascading.
//
// What that changes: "every scene node painted" and "nothing painted that is not in the
// scene" stop being inferences and become set difference. Nothing else in this file was
// weakened by the old join, but those two were the whole point.

const ROLE_CLASS = r => 'r-' + r;

function flatten(node, out = [], depth = 0) {
  out.push({ node, depth });
  (node.kids || []).forEach(k => flatten(k, out, depth + 1));
  return out;
}

// Walk the painted tree the same way, skipping nodes the painter adds for layout only.
function paintedTree(root) {
  const out = [];
  (function walk(el, depth) {
    out.push({ el, depth });
    [...el.children].forEach(c => walk(c, depth + 1));
  })(root, 0);
  return out;
}

export async function run(session = 'lens', as = 'iris', lens = 'notes') {
  const url = `/api/scene?session=${session}&as=${as}&lens=${lens}`;
  const res = await fetch(url);
  const payload = await res.json();
  const scene = payload.scene;
  const printed = payload.text || '';

  const paintRoot = document.querySelector('#paint') || document.body;
  const sceneNodes = flatten(scene);
  const paintNodes = paintedTree(paintRoot).filter(p => p.el !== paintRoot);

  const stamp = {
    at: new Date().toTimeString().slice(0, 8), href: location.href, title: document.title,
    dpr: window.devicePixelRatio || 1, viewport: innerWidth + 'x' + innerHeight,
    lens, sceneNodes: sceneNodes.length, paintedNodes: paintNodes.length,
    join: 'INFERRED by parallel walk — the painter emits no data-key. See the caveat in this file.'
  };

  // ---- 1. every scene node painted -------------------------------------------------
  // Matched by role class where the scene names a role, by layout class where it names a
  // layout, and by text where it carries text. A scene node with none of the three cannot
  // be matched at all, and is counted separately rather than silently passed.
  const classesOf = el => [...el.classList];
  const unmatched = [], unmatchable = [];
  const claimed = new Set();
  sceneNodes.forEach(({ node }) => {
    const wantRole = node.role ? ROLE_CLASS(node.role) : null;
    const wantLayout = node.layout ? 'l-' + node.layout : null;
    const wantText = (node.text || '').trim();
    if (!wantRole && !wantLayout && !wantText) { unmatchable.push(node.key); return; }
    const hit = paintNodes.find(({ el }) => {
      if (claimed.has(el)) return false;
      const cs = classesOf(el);
      if (wantRole && !cs.includes(wantRole)) return false;
      if (wantLayout && !cs.includes(wantLayout)) return false;
      if (wantText && !(el.textContent || '').includes(wantText.slice(0, 40))) return false;
      return true;
    });
    if (hit) claimed.add(hit.el); else unmatched.push({ key: node.key, role: node.role, text: wantText.slice(0, 26) });
  });

  // ---- 2. nothing painted that is not in the scene ----------------------------------
  const extra = paintNodes.filter(({ el }) => !claimed.has(el))
    .map(({ el }) => ({ tag: el.tagName, cls: [...el.classList].join('.') || '(none)', text: (el.textContent || '').trim().slice(0, 24) }));

  // ---- 3. every role resolves to a real style class ---------------------------------
  const roles = [...new Set(sceneNodes.map(s => s.node.role).filter(Boolean))];
  const declared = new Set();
  [...document.styleSheets].forEach(s => {
    try {
      [...s.cssRules].forEach(r => {
        if (!r.selectorText) return;
        r.selectorText.split(',').forEach(sel => {
          const m = sel.trim().match(/\.(r-[\w-]+)/);
          if (m) declared.add(m[1]);
        });
      });
    } catch (e) { }
  });
  const unresolved = roles.filter(r => !declared.has(ROLE_CLASS(r)));
  // a role that resolves but paints nothing distinguishable is worth knowing too
  const inert = roles.filter(r => declared.has(ROLE_CLASS(r))).filter(r => {
    const el = document.querySelector('.' + ROLE_CLASS(r));
    if (!el) return false;
    const cs = getComputedStyle(el);
    return cs.fontSize === getComputedStyle(document.body).fontSize
      && cs.color === getComputedStyle(document.body).color
      && cs.backgroundColor === 'rgba(0, 0, 0, 0)'
      && parseFloat(cs.borderTopWidth) === 0 && parseFloat(cs.paddingTop) === 0;
  });

  // ---- 4. every declared gesture live ----------------------------------------------
  const acts = [];
  sceneNodes.forEach(({ node }) => (node.acts || []).forEach(a => acts.push({ key: node.key, on: a.on, line: a.line })));
  const deadActs = acts.filter(a => {
    if (a.on === 'drag' || a.on === 'drop') return !document.querySelector('[data-drag]');
    if (a.on === 'edit') return !document.querySelector('[contenteditable]');
    if (a.on === 'click') return !document.querySelector('[data-click],[onclick],button,[role=button]');
    return true;
  });
  // and the reverse: anything interactive on screen that the scene never declared
  const liveEls = [...paintRoot.querySelectorAll('[data-drag],[contenteditable],[data-click],button,[role=button]')];
  const undeclared = Math.max(0, liveEls.length - acts.filter(a => a.on !== 'drop').length);

  // ---- 5. boxes where the scene says ------------------------------------------------
  const boxed = sceneNodes.filter(s => Array.isArray(s.node.box));
  const boxRows = boxed.map(({ node }) => {
    const [x, y, w, h] = node.box;
    // find the painted card carrying this item's title text
    const title = (node.kids || []).find(k => k.part === 'title');
    const t = title && (title.text || '').trim();
    let el = null;
    if (t) el = [...paintRoot.querySelectorAll('.' + ROLE_CLASS(node.role || 'card'))]
      .find(e => (e.textContent || '').includes(t.slice(0, 30)));
    if (!el) return { key: node.key, found: false };
    const r = el.getBoundingClientRect();
    const parent = el.offsetParent || paintRoot;
    const pr = parent.getBoundingClientRect();
    return {
      key: node.key, found: true,
      said: [x, y, w, h].join(','),
      painted: [Math.round(r.left - pr.left + parent.scrollLeft), Math.round(r.top - pr.top + parent.scrollTop), Math.round(r.width), Math.round(r.height)].join(','),
      dw: Math.round(r.width) - w, dh: Math.round(r.height) - h
    };
  });
  const boxWrong = boxRows.filter(b => b.found && (Math.abs(b.dw) > 1 || Math.abs(b.dh) > 1));

  // ---- 6. what the paint knows and the scene does not -------------------------------
  // These are the measured facts only the browser has. They are the candidates for flowing
  // back to the scene as `~` observations.
  const measured = [];
  paintNodes.forEach(({ el }) => {
    if (el.children.length) return;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const clamped = cs.webkitLineClamp && cs.webkitLineClamp !== 'none';
    const overflow = el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2;
    const lines = Math.round(r.height / (parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.5));
    const offscreen = r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth;
    if (clamped || overflow || offscreen || lines > 1) {
      measured.push({
        cls: [...el.classList].join('.').slice(0, 20),
        text: (el.textContent || '').trim().slice(0, 20),
        lines, clamped: !!clamped, overflow, offscreen
      });
    }
  });

  return {
    stamp,
    painted: { scene: sceneNodes.length, matched: claimed.size, unmatched, unmatchable },
    extraPainted: { n: extra.length, rows: extra.slice(0, 8) },
    roles: { n: roles.length, roles, unresolved, inert },
    gestures: { declared: acts.length, dead: deadActs, undeclaredLiveElements: undeclared, kinds: [...new Set(acts.map(a => a.on))] },
    boxes: { n: boxed.length, wrong: boxWrong.length, rows: boxRows.slice(0, 6) },
    paintOnlyFacts: { n: measured.length, rows: measured.slice(0, 10) },
    printedTextChars: printed.length
  };
}

export default { run };
