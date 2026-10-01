// style-read.js: what the painter's own style.js makes of a style text, for test_scene's check of scene.style_check (a1101).
//   node style-read.js < some.style   ->  {"refusal": "line N" | null, "unread": [[role, prop], ...]}
const fs = require("fs"), path = require("path");
global.document = { createElement: () => ({}), head: { appendChild() {} } };
const Style = new Function(fs.readFileSync(path.join(__dirname, "..", "style", "style.js"), "utf8") + "\nreturn Style;")();
const src = fs.readFileSync(0, "utf8");
let out;
try {
  const st = Style.install(src);
  const unread = [];
  for (const role of Object.keys(st.roles)) for (const u of Style.look({ as: role }).unreadable) unread.push([role, u.prop]);
  out = { refusal: null, unread };
} catch (e) {
  if (!(e instanceof Style.Refusal)) throw e;
  out = { refusal: `line ${e.line}`, unread: [] };
}
process.stdout.write(JSON.stringify(out));
