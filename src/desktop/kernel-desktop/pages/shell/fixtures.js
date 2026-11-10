// fixtures.js: fake rows for the shell pages, used only when the URL says ?fixture=<name> (hidden renders and the proof).
// Shell builder, 26 Oct 2026. The window manager and the theme are other builders' work, so this stands in for both:
// `wm.windows` rows exactly as CONTRACTS.md section 2 describes them, and the words a bar speaks. The real pages ask
// the kernel's door the same questions through KD.see / KD.act; here they are answered from memory, and what they were
// told to do is kept in window.__acts for the proof to read back.
//
//   ?fixture=wm3 | wm8 | wm16     how many apps are running (3, 8 or 16)
//   ?focus=<n>                    which app is in front (default 1)
//   window.__FX_APPS = [{exe, app}, ...]   the proof may replace the app list with the PC's real programs
"use strict";
(() => {
  const q = new URLSearchParams(location.search);
  const name = q.get("fixture");
  if (!name) return;
  const SYS = "C:\\Windows\\System32\\", WIN = "C:\\Windows\\";
  const APPS = window.__FX_APPS || [
    { app: "Files", exe: WIN + "explorer.exe", titles: ["Downloads", "Pictures"] },
    { app: "Edge", exe: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", titles: ["Seabright Council - Agenda", "Tides - Seabright Harbor", "Inbox (3)"] },
    { app: "Notepad", exe: SYS + "notepad.exe", titles: ["notes.txt - Notepad"] },
    { app: "Paint", exe: SYS + "mspaint.exe", titles: ["wallpaper.png - Paint"] },
    { app: "Task Manager", exe: SYS + "Taskmgr.exe", titles: ["Task Manager"] },
    { app: "Command Prompt", exe: SYS + "cmd.exe", titles: ["Command Prompt"] },
    { app: "PowerShell", exe: SYS + "WindowsPowerShell\\v1.0\\powershell.exe", titles: ["Windows PowerShell"] },
    { app: "Control Panel", exe: SYS + "control.exe", titles: ["All Control Panel Items"] },
    { app: "Registry", exe: WIN + "regedit.exe", titles: ["Registry Editor"] },
    { app: "Magnifier", exe: SYS + "Magnify.exe", titles: ["Magnifier"] },
    { app: "Character Map", exe: SYS + "charmap.exe", titles: ["Character Map"] },
    { app: "Snipping", exe: SYS + "SnippingTool.exe", titles: ["Snipping Tool"] },
    { app: "Disk Cleanup", exe: SYS + "cleanmgr.exe", titles: ["Disk Cleanup"] },
    { app: "Resource Monitor", exe: SYS + "resmon.exe", titles: ["Resource Monitor"] },
    { app: "Windows Version", exe: SYS + "winver.exe", titles: ["About Windows"] },
    { app: "System Info", exe: SYS + "msinfo32.exe", titles: ["System Information"] },
  ];
  const count = { wm3: 3, wm8: 8, wm16: 16 }[name] || 8;
  const focus = +(q.get("focus") ?? 1);
  const rows = [];
  APPS.slice(0, count).forEach((a, i) => {
    const n = a.titles.length;
    for (let j = 0; j < n; j++) {
      rows.push({ key: `w${i}_${j}`, app: a.app, exe: a.exe, icon: a.icon || "exe:" + a.exe, agora: "", state: i === 3 ? "minimised" : (i === 6 && count > 6 ? "pinned" : "normal"),
        focused: i === focus && j === 0, rect: [0, 0, 100, 100], space: "", managed: true, why: "", title: a.titles[j] });
    }
  });
  const agora = [{ key: "dk4", name: "Task board", shows: "taskboard" }, { key: "dk7", name: "Lines", shows: "lines" }].slice(0, count > 3 ? 2 : 1);
  agora.forEach((w, i) => rows.push({ key: w.key, app: w.name, exe: "", icon: "agora:" + w.shows, agora: w.key, shows: w.shows, state: "normal", focused: false, managed: false, title: w.name }));
  const titles = Object.fromEntries(rows.map((r) => [r.key, r.title]));
  rows.forEach((r) => { delete r.title; });

  // a stand-in picture of a window, for the hover preview (the host draws a live DWM thumbnail over it in real use)
  const hue = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 360, 7);
  const preview = (title, app) => {
    const hh = hue(app);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200"><rect width="320" height="200" fill="hsl(${hh} 18% 96%)"/><rect width="320" height="22" fill="hsl(${hh} 30% 88%)"/>
<circle cx="12" cy="11" r="4" fill="hsl(${hh} 40% 60%)"/><rect x="26" y="8" width="90" height="6" rx="3" fill="hsl(${hh} 20% 55%)"/>
<rect x="0" y="22" width="74" height="178" fill="hsl(${hh} 28% 92%)"/><rect x="10" y="36" width="50" height="6" rx="3" fill="hsl(${hh} 20% 68%)"/><rect x="10" y="52" width="40" height="6" rx="3" fill="hsl(${hh} 20% 78%)"/><rect x="10" y="68" width="46" height="6" rx="3" fill="hsl(${hh} 20% 78%)"/>
<rect x="90" y="40" width="200" height="8" rx="4" fill="hsl(${hh} 25% 40%)"/><rect x="90" y="62" width="214" height="5" rx="2.5" fill="hsl(${hh} 15% 72%)"/><rect x="90" y="76" width="180" height="5" rx="2.5" fill="hsl(${hh} 15% 72%)"/><rect x="90" y="90" width="206" height="5" rx="2.5" fill="hsl(${hh} 15% 72%)"/>
<rect x="90" y="116" width="96" height="56" rx="6" fill="hsl(${hh} 55% 78%)"/><rect x="196" y="116" width="96" height="56" rx="6" fill="hsl(${(hh + 40) % 360} 45% 82%)"/></svg>`;
    return "data:image/svg+xml," + encodeURIComponent(svg);
  };
  const art = "data:image/svg+xml," + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6a35c"/><stop offset="1" stop-color="#7b3fa0"/></linearGradient></defs><rect width="64" height="64" fill="url(#g)"/><circle cx="40" cy="26" r="12" fill="#fff" opacity=".35"/><rect x="0" y="44" width="64" height="20" fill="#2a1a47" opacity=".4"/></svg>`);

  const state = { rows, acts: [], settings: {}, media: q.get("media") === "off" ? null : { player: "Spotify", title: "Harbor Lights", artist: "The Seabright Players", playing: true, art, position: 84, duration: 212 } };
  window.__acts = state.acts;
  window.__fxState = state;
  const pins = [
    { id: "p1", kind: "button", bar: "taskbar", label: "Files", path: WIN + "explorer.exe", does: "window.launch path=" + WIN + "explorer.exe" },
    { id: "p2", kind: "button", bar: "taskbar", label: "Edge", path: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", does: "window.launch path=C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" },
    { id: "p3", kind: "button", bar: "taskbar", label: "WordPad", path: "C:\\Program Files\\Windows NT\\Accessories\\wordpad.exe", does: "window.launch path=C:\\Program Files\\Windows NT\\Accessories\\wordpad.exe" },
  ];
  const sys = { cpu: { value: "14%", detail: "" }, memory: { value: "41%", detail: "13.1 of 32 GB" }, network: { value: "↓1.2 MB/s", detail: "↑300 KB/s" },
    volume: { value: q.get("volume") || "70%", detail: "" }, battery: q.get("battery") === "none" ? { value: "", detail: "no battery" } : { value: "86%", detail: "charging" } };
  const notes = q.get("notes") === "none" ? [] : [
    { id: "n1", text: "Maya replied on Harbor cleanup: \"Saturday at nine works.\"", at: "5 min", unread: "yes" },
    { id: "n2", text: "Three new posts in the Seabright feed", at: "32 min", unread: "yes" },
    { id: "n3", text: "JEFF finished the draft of the council summary", at: "1 h", unread: "no" } ];
  const ok = (rowsOut, text) => ({ ok: true, text: text || "", rows: rowsOut || [] });
  const wmOff = q.get("wm") === "off";

  const see = async (line) => {
    const w = line.trim().split(/\s+/);
    if (w[0] === "wm.windows") return wmOff ? { ok: false, text: "refused: no word wm.windows" } : ok(state.rows);
    if (w[0] === "window.list") return ok([...state.rows.filter((r) => r.agora).map((r) => ({ kind: "window", id: r.agora, name: r.app, shows: r.shows, shown: r.state !== "minimised", front: r.focused }))]);
    if (w[0] === "window.desktop") return ok(state.rows.filter((r) => !r.agora).map((r) => ({ handle: r.key, name: titles[r.key], program: r.exe.split("\\").pop().replace(/\.exe$/i, ""), path: r.exe, front: r.focused, shown: r.state !== "minimised" })));
    if (w[0] === "wm.title") { const r = state.rows.find((x) => x.key === w[1]); return ok(r ? [{ title: titles[r.key], hwnd: "", preview: preview(titles[r.key], r.app) }] : []); }
    if (line.startsWith("rows shell-settings")) return ok([state.settings]);
    if (line.startsWith("rows any bar=taskbar")) return ok(q.get("pins") === "none" ? [] : pins);
    if (line.startsWith("rows lens")) return ok(["feed", "board", "taskboard", "appearance"].map((n) => ({ name: n })));
    if (w[0] === "system.now") return ok(Object.entries(sys).map(([key, v]) => ({ key, ...v })));
    if (w[0] === "media.now") return ok(state.media ? [state.media] : []);
    if (line.startsWith("rows notification")) return ok(notes);
    if (line.startsWith("rows presence")) return ok([{ state: q.get("jeff") || "here", note: q.get("jeff") === "busy" ? "Drafting the weekly summary" : "" }]);
    return { ok: false, text: "refused: nothing here answers " + line, rows: [] };
  };
  const act = async (line) => {
    state.acts.push(line);
    const w = line.trim().split(/\s+/);
    const row = state.rows.find((r) => r.key === w[1]);
    if (w[0] === "wm.focus" && row) { state.rows.forEach((r) => (r.focused = false)); row.focused = true; row.state = "normal"; }
    if (w[0] === "wm.restore" && row) { state.rows.forEach((r) => (r.focused = false)); row.focused = true; row.state = "normal"; }
    if (w[0] === "wm.minimise" && row) { row.state = "minimised"; row.focused = false; }
    if (w[0] === "wm.pin" && row) row.state = "pinned";
    if (w[0] === "wm.unpin" && row) row.state = "normal";
    if (w[0] === "wm.close" && row) state.rows.splice(state.rows.indexOf(row), 1);
    if (w[0] === "window.focus" && row) { row.focused = !row.focused; }
    if (w[0] === "media.play" && state.media) state.media.playing = !state.media.playing;
    if (w[0] === "make" && /shell-settings/.test(line)) { for (const m of line.matchAll(/(show_\w+)=(\w+)/g)) state.settings[m[1]] = m[2]; }
    if (w[0] === "set" && /show_/.test(line)) { for (const m of line.matchAll(/(show_\w+)=(\w+)/g)) state.settings[m[1]] = m[2]; }
    return { ok: true, text: "ok (fixture)" };
  };
  window.__fx = { see, act, state, native: async (name, ...args) => { (window.__native = window.__native || []).push([name, ...args]); return true; } };
  if (typeof KD !== "undefined") KD.stream = () => {};
})();
