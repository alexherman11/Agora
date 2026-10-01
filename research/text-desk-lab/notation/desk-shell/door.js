// door.js : the quiet line that says what code changed under the page. OWNER: Claude (a1505, with the door).
// Pike c1534: an invisible swap that changes behaviour must not be a silence. The door (door.py) sends its news down the
// page's stream (lens.js); this draws one line from it, in the style's roles, never a banner: the last update today
// ("updated 08:54 · a1431: Views can show who made a thing · 3 today"), or, in role cut, that a new deskd was refused
// and the running code kept. Pressing it lists the day: every swap, its commits, and every refusal with its reason.
// A note from the painter rides beside it; one with an action is its own button ("new screen code: click to use it").
// In the terminal's head when the terminal is open (where Alex already looks), else at the page's bottom right.
const DoorLine = (() => {
  const R = n => (window.Style ? Style.roleClass(n) : "r-" + n);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const el = document.createElement("div"); el.id = "door"; el.hidden = true;
  const line = document.createElement("button"); line.type = "button"; line.className = "door-line";
  const act = document.createElement("button"); act.type = "button"; act.className = "door-act"; act.hidden = true;
  const list = document.createElement("div"); list.className = "door-list"; list.hidden = true; list.setAttribute("role", "list");
  el.append(line, act, list);
  let st = null, note = "", action = null;
  const today = () => { const d = new Date(), p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; };
  const what = n => (n.commits || []).map(c => c[1].replace(/^land /, "")).join("; ") || `deskd ${n.to}`;
  function place() {
    const head = document.querySelector("#term .term-head");
    const into = head && document.body.dataset.inspector === "term" ? head : document.body;
    if (el.parentElement !== into) into.prepend(el);
    el.classList.toggle("door-fixed", into === document.body);
  }
  function paint() {
    const mine = ((st && st.news) || []).filter(n => (n.at || "").startsWith(today()));
    const lastN = mine[mine.length - 1];
    el.hidden = !lastN && !note;
    if (el.hidden) return;
    place();
    const ok = mine.filter(n => n.ok);
    let text = "";
    if (lastN && !lastN.ok) {
      line.className = "door-line " + R("cut");
      text = `kept ${lastN.from || "the running code"} ${lastN.at.slice(11, 16)}: ${lastN.why}`;
    } else if (lastN) {
      line.className = "door-line " + R("meta");
      text = `updated ${lastN.at.slice(11, 16)} · ${what(lastN)}${lastN.painter ? " (the screen's own code too)" : ""}`;
    }
    if (ok.length > 1 || (lastN && !lastN.ok && ok.length)) text += ` · ${ok.length} update${ok.length === 1 ? "" : "s"} today`;
    if (note && !action) text = (text ? text + " · " : "") + note;
    line.hidden = !text;
    line.textContent = text; line.title = "what changed in the code today (press for the list)";
    act.hidden = !(note && action);
    act.textContent = note; act.className = "door-act " + R("tool");
    list.className = "door-list " + R("sheet") + " " + R("popup");
    list.innerHTML = mine.slice().reverse().map(n => `<div role="listitem" class="${R(n.ok ? "meta" : "cut")}">${esc(n.at.slice(11, 16))} `
      + (n.ok ? `${esc(n.from || "-")} → ${esc(n.to)}${n.painter ? " (screen code)" : ""}${n.dirty ? ` · uncommitted: ${esc(n.dirty.join(", "))}` : ""}`
              : `refused ${esc(n.to)}, kept ${esc(n.from || "-")}: ${esc(n.why || "")}`)
      + (n.commits || []).map(c => `<div>  ${esc(c[0])} ${esc(c[1])}</div>`).join("") + `</div>`).join("")
      || `<div class="${R("meta")}">nothing changed in the code today</div>`;
  }
  line.addEventListener("click", () => { list.hidden = !list.hidden; });
  act.addEventListener("click", () => { if (action) action(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") list.hidden = true; });
  document.addEventListener("pointerdown", e => { if (!el.contains(e.target)) list.hidden = true; });
  new MutationObserver(() => { if (!el.hidden) place(); }).observe(document.body, { attributes: true, attributeFilter: ["data-inspector"] });
  return {
    show(s) { st = s; paint(); },
    note(t, fn) { if (t === note && (fn || null) === action) return; note = t || ""; action = fn || null; paint(); },
    get status() { return st; },
  };
})();
window.DoorLine = DoorLine;      // a top-level const is not a property of window; lens.js and term.js ask window.DoorLine
