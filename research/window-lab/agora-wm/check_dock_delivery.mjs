// House-only deterministic JS contract check. No browser, network, timer,
// native window or process lifecycle. Executes the shipped Data vocabulary and
// shipped dock-item mount/click; DOM and word transport are explicit stand-ins.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const parts = path.join(here, '../kernel-desktop/shell_parts');
const source = readFileSync(path.join(parts, 'shell-kit.js'), 'utf8');
const begin = source.indexOf('  const refused = ');
const end = source.indexOf('  // ------------------------------------------------------------------------------------------------ the reading hub', begin);
assert(begin >= 0 && end > begin, 'Data vocabulary source boundary changed');
const context = vm.createContext({});
vm.runInContext(source.slice(begin, end) + '\nglobalThis.Data=Data;', context);
const Data = context.Data;
let calls = [], reject = false;
Data.wmOK = true;
Data.act = async line => {
  calls.push(line);
  return reject ? {ok:false, refused:'fixture exclusive fullscreen'} : {ok:true};
};

const componentSource = readFileSync(path.join(parts, 'components/shell-dock-item.js'), 'utf8');
const component = (await import('data:text/javascript;base64,' +
  Buffer.from(componentSource).toString('base64'))).default;
function part(_name, _tag, _attrs, ..._children) {
  return {style:{}, firstChild:{style:{}}, events:{}, setAttribute(){},
    addEventListener(name, fn){this.events[name]=fn;}};
}
globalThis.ShellKit = {Data, Icon(){}, Pop:{}, dock:{state:{}, items:[]},
  ran: async r => r, poke(){}, h(){}, glyph(){}, Menu:{}};
const api = {part, cleanup(){}};
const exe = 'C:\\Fixture Apps\\music.exe';
async function click(wins, line) {
  calls = [];
  const button = component.mount(api, {group:{id:'music', app:'Music', exe, wins, line}});
  await button.events.click();
  return calls;
}
assert.deepEqual(await click([{key:'music', state:'minimised'}]),
  ['wm.restore music share=yes']);
assert.deepEqual(await click([{key:'music', state:'normal'}]),
  ['wm.focus music share=yes']);
assert.deepEqual(await click([{key:'music', state:'pinned'}]), ['wm.focus music']);
assert.deepEqual(await click([{key:'music', state:'normal', focused:true}]), ['wm.minimise music']);
assert.deepEqual(await click([]),
  [`wm.arrange expect=${JSON.stringify(exe)}`, `window.launch path=${JSON.stringify(exe)}`]);
reject = true;
assert.deepEqual(await click([]), [`wm.arrange expect=${JSON.stringify(exe)}`],
  'a refused sharing request must not launch or forward');
reject = false;
assert.deepEqual(await click([], 'window.open writing'), ['window.open writing']);
console.log('PASS: 7 production dock click/vocabulary cases; DOM/transport stand-ins, native outcome unverified');
