// apps/third.js : TOGETHER. OWNER: Lark. The studio's third application.
//
// Chosen because the thing this desk has that no other desktop has is the other inhabitant.
// The objection to it was "a dashboard is what you build when you cannot think of an app", so the
// rule I built it under is: EVERY LINE IS A VERB YOU CAN RUN. If it is only a list of facts, it failed.
//
// Contract note (this is the part I own across all three apps): text() is NOT written separately from
// the screen. Both are projections of ONE row model, so they cannot drift. The app then checks its own
// coverage — every row the model holds must appear in both — and prints the mismatches as ! lines.
// See the "contract" section: it calls every registered app's text() and reports which ones are silent.
(() => {
  const ME = Desk.actor;
  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const RECENT = 5;                 // "recent" is measured in ACTS, not seconds: see §limits below.

  // ---------------------------------------------------------------- the model
  // A row is { mark, text, acts: [commandline] }. mark is one of = ~ ? ! or "".
  // A section may declare a cut; a cut is never silent.
  const S = (title, rows, note) => ({ title, rows, note: note || "" });

  function ownerOf(id) {              // walk up to the nearest surface carrying owner=
    let n = Desk.node(id);
    while (n) { const o = n.props && n.props.owner; if (o) return o; n = n.parent ? Desk.node(n.parent) : null; }
    return null;
  }
  const where = id => { const n = Desk.node(id); return n && n.parent ? Desk.title(n.parent) : "desk"; };
  // Desk.title resolves nodes; an event's `changed` may also name a subject. Never print a bare id as a name.
  const name = id => {
    const n = Desk.node(id); if (n) return Desk.title(id);
    const s = Desk.snapshot.subjects[id]; if (s) return s.title;
    return `${id} (gone — nothing by that id is in the world now)`;
  };

  function model(view) {
    const snap = Desk.snapshot, ev = view.events, sections = [];
    if (!snap) return { sections: [S("Together", [{ mark: "?", text: "no snapshot yet", acts: [] }])] };

    // --- presence. Two different facts, deliberately not merged into one word.
    //   HANDS: where each actor last ACTED (from the event log).
    //   EYES : how far each actor has READ (snapshot.readers, which Jeff built after my round-four ask).
    // readers is a reading position, NOT attendance: someone caught up may have closed the tab a second
    // ago, and someone far behind may be sitting there thinking. So it never prints "here". It prints
    // "caught up" or "N behind", which is what it actually measures.
    const byActor = {};
    ev.forEach((e, i) => { (byActor[e.by] = byActor[e.by] || []).push(i); });
    const readers = snap.readers || {};
    const everyone = [...new Set([...Object.keys(byActor), ...Object.keys(readers)])].sort();
    const presence = everyone.map(a => {
      const acts = byActor[a] || [];
      const ago = acts.length ? ev.length - 1 - acts[acts.length - 1] : null;
      const at = readers[a];
      const behind = at === undefined ? null : snap.events_total - at;
      const hands = ago === null ? "has not acted" : ago === 0 ? "acted just now" : `acted ${ago === 1 ? "1 act" : ago + " acts"} ago`;
      const eyes = behind === null ? "?not a reader of this world"
                 : behind <= 1 ? "=read up to now"
                 : `=${behind} behind`;
      return { mark: "=", text: `${a}${a === ME ? " (you)" : ""} · ${hands} · ${eyes}`,
               acts: a === ME ? [] : [`find ?${a}`] };
    });
    presence.push({ mark: "?", text: "none of this is attendance. the desk knows who ACTED and how far each has READ; " +
      "it does not know who is sitting there. a reader caught up may have closed the tab a second ago", acts: [] });
    // A version stamp, so an observer's report can name the world it was true of. Iris, a447: "until a
    // request can name a version, my answers are true of a page that may no longer exist." events_total
    // is that version, it is free, and a window that does not print it cannot be quoted safely.
    presence.unshift({ mark: "=", text: `this window is true of ${Desk.session} at events_total=${snap.events_total} · ${ev.length} acts read`, acts: [] });
    sections.push(S("Who is here", presence));

    // --- elsewhere: worktrees. A worktree is an ELECTED ABSENCE - not the veil (which hides a place)
    // and not the bench (which shares one); it forks TIME, and what returns is a signed sequence.
    const wt = snap.worktree;
    const elsewhere = [];
    if (wt) {
      elsewhere.push({ mark: "=", text: `you are in a worktree · forked from ${wt.base} at event ${wt.base_events} by ${wt.by}` +
        ` · ${wt.journal} command${wt.journal === 1 ? "" : "s"} journalled`, acts: [`worktree`] });
      elsewhere.push({ mark: "!", text: `nothing you do here is visible in ${wt.base}. the others cannot collide with you ` +
        `and cannot see you working. when you merge, all ${wt.journal} land at once, signed by you`,
        acts: [`worktree diff ${Desk.session.split("@")[1] || ""}`.trim()] });
    } else {
      elsewhere.push({ mark: "?", text: `this snapshot does not list the worktrees of ${Desk.session}, so I cannot tell you ` +
        `whether anyone is working elsewhere right now, nor how much they have journalled. the desk knows: ` +
        `the 'worktree' command prints it. to-jeff: put the list in the snapshot`, acts: [`worktree`] });
    }
    sections.push(S("Elsewhere", elsewhere,
      "a worktree is the only way to be absent on purpose here, and it is the one absence this window cannot see"));

    // --- bursts: a merge lands as N events by one actor at one moment and is INDISTINGUISHABLE from
    // N minutes of steady work, because a merged event carries no provenance (via says 'retitle', never
    // 'worktree:name'). So this is ~ my reading of the shape, never = a fact. to-jeff: via=worktree:<name>.
    const bursts = [];
    let run = [];
    const flush = () => {
      if (run.length >= 4 && run[0].by !== ME)
        bursts.push({ mark: "~", text: `${run[0].by} · ${run.length} acts in a row, no other hand between them ` +
          `(${[...new Set(run.map(e => e.verb))].join(", ")}) — this is the SHAPE of a worktree merge, but the events ` +
          `do not say, so it may equally be ${run.length} ordinary acts`,
          acts: [`history`, `why ${(run[run.length - 1].changed || [])[0] || run[run.length - 1].target}`] });
      run = [];
    };
    ev.forEach(e => { if (run.length && run[0].by !== e.by) flush(); run.push(e); });
    flush();
    if (bursts.length) sections.push(S("Bursts", bursts.slice(-3),
      "a merge is a bulk act wearing ordinary clothes. until an event says it was replayed, nobody can tell one from an afternoon"));

    // --- needs you: never folded. Anything by someone else that touches what I touched FIRST.
    // Bug found by running this against the real log from a terminal: I was matching any event by anyone
    // on any id I had ever touched, including events that happened BEFORE mine. A deed that preceded my
    // work cannot have invalidated a belief I did not yet hold. This section is the one that may never
    // fold, so a false entry in it is worse than a missing one: it teaches you to skim the only list
    // you must not skim. The order test is the whole fix.
    const firstTouch = {};              // id -> index of MY earliest event on it
    ev.forEach((e, i) => { if (e.by === ME) (e.changed || []).forEach(id => { if (!(id in firstTouch)) firstTouch[id] = i; }); });
    const affects = [];
    ev.forEach((e, i) => {
      if (e.by === ME) return;
      const hit = (e.changed || []).filter(id => id in firstTouch && firstTouch[id] < i);
      if (!hit.length) return;
      const loud = e.verb === "undo" || e.verb === "remove";
      affects.push({ mark: loud ? "!" : "=", i,
        text: `${e.by} ${e.verb} ${hit.map(name).join(", ")}${loud ? "  — this undoes or removes work of yours" : ""}`,
        acts: [`why ${hit[0]}`, `history ${hit[0]}`] });
    });
    sections.push(S("Needs you", affects.length ? affects
      : [{ mark: "=", text: "nothing of yours has been changed by anyone else", acts: [] }],
      "never folded: a deed that makes something of yours wrong is the one thing a digest may not summarise"));

    // --- since you looked: grouped by person and place
    const since = ev.slice(view.seen);
    const groups = {};
    since.forEach(e => {
      const place = where((e.changed || [])[e.changed.length - 1] || e.target);
      const k = `${e.by} @ ${place}`;
      (groups[k] = groups[k] || { by: e.by, place, verbs: {}, n: 0 });
      groups[k].verbs[e.verb] = (groups[k].verbs[e.verb] || 0) + 1; groups[k].n++;
    });
    const rows = Object.values(groups).sort((a, b) => b.n - a.n).map(g => ({
      mark: "=", text: `${g.by} · ${g.place} · ` + Object.entries(g.verbs).map(([v, n]) => `${n} ${v}`).join(", "),
      acts: [`look "${g.place}" :3`]
    }));
    sections.push(S(`Since you looked here`, rows.length ? rows
      : [{ mark: "=", text: `nothing since you opened this window (${since.length} acts)`, acts: [] }],
      `reading position is VIEW STATE, not a fact of the world — the desk knows what you have seen, this window does not. to-jeff: expose it`));

    // --- warm: measured in acts, because the log has a day but no time
    const lastBy = {};
    ev.forEach((e, i) => (e.changed || []).forEach(id => { lastBy[id] = { by: e.by, i }; }));
    const warm = Object.entries(lastBy)
      .filter(([id, v]) => v.by !== ME && ev.length - 1 - v.i < RECENT && Desk.node(id))
      .map(([id, v]) => ({ mark: "=", text: `${name(id)} (${id}) · ${v.by}'s hands, ${ev.length-1-v.i===1?'1 act':(ev.length-1-v.i)+' acts'} ago · in ${where(id)}${ownerOf(id) ? ` · ${ownerOf(id) === ME ? "your side" : ownerOf(id) + "'s side"}` : " · no side owns this"}`,
        acts: [`look ${id} :1`, `do comment ${id} line="mind if I take this?"`] }));
    sections.push(S("Warm", warm.length ? warm : [{ mark: "=", text: "nothing is warm", acts: [] }],
      `warm here = touched by someone else within the last ${RECENT} acts. NOT within 90 seconds: the event log carries a day, not a time. to-jeff: an event needs a clock time`));

    // --- house rules
    // I claimed in round two that the desk does not print firing counts. It does: rules carry `fired`.
    // A manners rule that has never fired is either unnecessary or broken, and either way we should know which.
    const rr = (snap.rules || []).map(r => ({
      mark: r.fired ? "=" : "~",
      text: `${r.id} · ${r.text} · =fired ${r.fired || 0}x` + (r.fired ? "" : "  — never fired: unnecessary, or broken"),
      acts: [`rules`, `rule drop ${r.id}`]
    }));
    sections.push(S("House rules", rr.length ? rr
      : [{ mark: "=", text: "=0 rules. this desk has no manners written down yet", acts: [`rule when tag:knock do tag add=needs-reply`] }],
      "no rule here carries an owner or a reach, so nothing can be signed and nothing is scoped to one side. to-jeff: rules need owner= and reach=mine|ours|world"));

    // --- the text() contract, across every app (my job this round)
    // Note on myself: calling my own text({}) would build a fresh empty view and report a length that is not
    // the one on screen. Reporting a number I know to be wrong about my own window would be exactly the
    // dishonesty I am here to catch, so I measure myself from the view in hand and say that I did.
    const contract = Desk.apps.map(a => {
      if (a.id === "third") {
        const mine = asText({ sections });
        return { mark: "=", text: `Together (this window): text() = ${mine.split("\n").length} lines, measured from the view in hand`, acts: [] };
      }
      if (!a.text) return { mark: "!", text: `${a.title}: no text() — a window a blind reader cannot read at all`, acts: [] };
      let out; try { out = a.text({}); } catch (err) { return { mark: "!", text: `${a.title}: text() threw — ${err.message}`, acts: [] }; }
      if (!out || !String(out).trim()) return { mark: "!", text: `${a.title}: text() returned nothing`, acts: [] };
      return { mark: "~", text: `${a.title}: text() = ${String(out).split("\n").length} lines, ${String(out).length} chars` +
        ` — measured with an empty context, so this is its length for a fresh window, not the one on screen`, acts: [] };
    });
    sections.push(S("The text() contract", contract,
      "every window must say what a blind reader gets. ! here is a defect in that app, filed by this one"));

    return { sections };
  }

  // ------------------------------------------------------- the two projections
  function asText(m) {
    const L = [];
    m.sections.forEach(s => {
      L.push(`## ${s.title}`);
      s.rows.forEach(r => L.push(`  ${r.mark || " "} ${r.text}` + (r.acts.length ? `\n      now: ${r.acts.join("   ·   ")}` : "")));
      if (s.note) L.push(`  ( ${s.note} )`);
      L.push("");
    });
    // Iris, c518: the screen projection ends with a "Screen vs text" section that this projection cannot
    // contain, because it is computed from the rendered DOM — so the old verdict was false about the row it
    // was written in. Rather than pretend the two views match everywhere, this projection declares the one
    // place they differ, by construction, and says neither view can verify it alone.
    L.push("## Screen vs text");
    L.push("  ! not comparable from here. The screen projection runs the check (it reads the rendered DOM)");
    L.push("    and prints the verdict in a section this projection does not have. The rows above are the");
    L.push("    ones compared; THIS section is the one place the two views differ, by construction, and");
    L.push("    neither view can verify it alone.");
    L.push("  ( an audit that counts itself is not an audit — Iris, c519 )");
    L.push("");
    return L.join("\n");
  }

  function asHTML(m, host) {
    host.innerHTML = `<style>
      .tg{padding:14px 18px 22px;font:14px/1.55 var(--font)}
      .tg h2{margin:18px 0 6px;font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--quiet)}
      .tg h2:first-child{margin-top:0}
      .tg .row{display:flex;gap:8px;align-items:baseline;padding:6px 0;border-top:1px solid var(--line)}
      .tg .row:first-of-type{border-top:0}
      .tg .mk{font:11px/1.4 ui-monospace,Consolas,monospace;width:11px;flex:none;color:var(--quiet)}
      /* Iris, a447: "an honesty mark has to be a property of the SURFACE, not a character in the text,
         because a character can always be made quiet and a surface cannot." She found this by measuring
         four of our pages independently and it is the best correction anyone has given me. So a ! row is
         not a red glyph: it is a hatched band the width of the row, sized to what it is warning about. */
      .tg .mk.bang{color:var(--accent);font-weight:700}
      .tg .row.loud{background-image:repeating-linear-gradient(135deg,transparent 0 5px,
        color-mix(in srgb,var(--accent) 34%,transparent) 5px 6px);
        border-left:3px solid var(--accent);padding-left:9px;margin-left:-12px}
      .tg .row.loud .what{background:var(--surface);box-shadow:0 0 0 4px var(--surface)}
      .tg .what{flex:1;min-width:0}
      .tg .row.loud .what{font-weight:500}
      .tg .acts{margin-top:4px;display:flex;flex-wrap:wrap;gap:6px}
      .tg button.act{font:11.5px ui-monospace,Consolas,monospace;color:var(--ink);background:var(--paper);
        border:1px solid var(--line);border-radius:5px;padding:2px 7px;cursor:pointer}
      .tg button.act:hover{border-color:var(--ink)}
      /* a declaration of incompleteness must be at least as loud as what it qualifies (Iris, c376) */
      .tg .note{margin:7px 0 0;font-size:12px;color:var(--ink);border-left:3px solid var(--accent);padding:3px 0 3px 9px;
        background-image:repeating-linear-gradient(135deg,transparent 0 5px,
          color-mix(in srgb,var(--accent) 20%,transparent) 5px 6px)}
      .tg .note span{background:var(--surface);box-shadow:0 0 0 3px var(--surface)}
    </style><div class="tg"></div>`;
    const root = host.querySelector(".tg");
    m.sections.forEach(s => {
      const h = document.createElement("h2"); h.textContent = s.title; root.appendChild(h);
      s.rows.forEach(r => {
        const d = document.createElement("div");
        d.className = "row" + (r.mark === "!" ? " loud" : "");
        d.innerHTML = `<span class="mk ${r.mark === "!" ? "bang" : ""}">${esc(r.mark || "")}</span>
          <span class="what">${esc(r.text)}<span class="acts"></span></span>`;
        const acts = d.querySelector(".acts");
        r.acts.filter(Boolean).forEach(line => {
          const b = document.createElement("button");
          b.className = "act"; b.textContent = line;        // the label IS the command it sends
          b.onclick = () => Desk.do(line);
          acts.appendChild(b);
        });
        root.appendChild(d);
      });
      if (s.note) { const p = document.createElement("p"); p.className = "note";
        const sp = document.createElement("span"); sp.textContent = s.note; p.appendChild(sp); root.appendChild(p); }
    });

    // self-check: every row of the model must be reachable in BOTH projections
    const screen = root.textContent, txt = asText(m);
    const missing = [];
    m.sections.forEach(s => s.rows.forEach(r => {
      if (!screen.includes(r.text)) missing.push(`screen is missing: ${r.text}`);
      if (!txt.includes(r.text)) missing.push(`text() is missing: ${r.text}`);
      r.acts.filter(Boolean).forEach(a => { if (!screen.includes(a)) missing.push(`screen omits the act: ${a}`); });
    }));
    // Iris, c518/c519: this section appeared on screen and NOT in text(), so "every row appears in both
    // projections" was false about the row it was written in — the self-check had exempted itself, which
    // she called "the commonest way an audit goes wrong". Her repair is better than adding the heading:
    // MAKE THE LINE STATE ITS SCOPE — what it compared, and what it did not.
    const rowCount = m.sections.reduce((n, s) => n + s.rows.length, 0);
    const h = document.createElement("h2"); h.textContent = "Screen vs text"; root.appendChild(h);
    const d = document.createElement("div"); d.className = "row" + (missing.length ? " loud" : "");
    d.innerHTML = `<span class="mk ${missing.length ? "bang" : ""}">${missing.length ? "!" : "="}</span><span class="what">${
      missing.length ? esc(missing.join(" · ")) : esc(`=${rowCount} model rows compared; all appear in both projections`)}</span>`;
    root.appendChild(d);
    const ex = document.createElement("div"); ex.className = "row loud";
    ex.innerHTML = `<span class="mk bang">!</span><span class="what">` + esc(
      "not compared: this section itself. It is written after the comparison and exists only in the screen " +
      "projection; text() carries its own statement of the same exemption. An audit that counts itself is " +
      "not an audit (Iris, c519).") + `</span>`;
    root.appendChild(ex);
  }

  // ---------------------------------------------------------------- the app
  const views = new Map();
  function ctxOf(ctx) {
    if (!views.has(ctx)) views.set(ctx, { seen: 0, events: [] });
    return views.get(ctx);
  }
  async function load(view) {
    const r = await fetch(`/api/events?session=${Desk.session}&as=${Desk.actor}&since=0`);
    const j = await r.json();
    view.events = j.events || [];
    if (view.seen === 0 && view.firstLoad !== true) { view.seen = view.events.length; view.firstLoad = true; }
  }
  const draw = async (host, ctx = {}) => {
    const view = ctxOf(ctx);
    host.innerHTML = `<div style="padding:18px;color:var(--quiet)">reading the log…</div>`;
    await load(view);
    asHTML(model(view), host);
  };

  Desk.registerApp({
    id: "third", title: "Together", glyph: "◐",
    open: draw, refresh: draw,
    text: (ctx = {}) => {
      const view = ctxOf(ctx);
      if (!view.events.length) return "Together\n  ? the event log has not been read yet — open the window first";
      return "Together · " + Desk.session + " · you are " + Desk.actor + "\n\n" + asText(model(view));
    }
  });
})();
