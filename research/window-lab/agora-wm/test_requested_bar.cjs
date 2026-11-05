// Exercise shipped bar methods with a fake world transport. No browser/native UI.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const calls = [];
let reply = () => ({ok: true});
const context = {
  document: {documentElement: {dataset: {}}, addEventListener() {}},
  getComputedStyle: () => ({getPropertyValue: () => ''}),
  addEventListener() {},
  MutationObserver: class { observe() {} },
  EventTarget,
  nativeTimers: {setTimeout() {}, clearTimeout() {}, setInterval() {}, requestAnimationFrame() {}, cancelAnimationFrame() {}},
  agora: {
    async do(line) { calls.push(line); return reply(line); },
    async see() { throw Error('unexpected observation'); },
    async native() { throw Error('native operation forbidden'); },
  },
  css() {},
  SHELL_CSS: '',
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../kernel-desktop/shell_parts/shell-kit.js'), 'utf8'), context);
const data = context.ShellKit.Data;
data.wmOK = true;

(async () => {
  await data.focus({key: 'game', state: 'minimised'});
  await data.focus({key: 'companion', state: 'normal'});
  assert.deepEqual(calls.splice(0), ['wm.restore game share=yes', 'wm.focus companion share=yes']);

  await data.launch('window.launch path="C:/Apps/Notes.exe"', 'C:/Apps/Notes.exe');
  assert.deepEqual(calls.splice(0), [
    'wm.arrange expect="C:/Apps/Notes.exe"', 'window.launch path="C:/Apps/Notes.exe"']);

  await data.launch('window.open notes');
  assert.deepEqual(calls.splice(0), ['wm.arrange expect="agora"', 'window.open notes']);

  reply = () => ({refused: 'desktop unavailable'});
  const result = await data.launch('window.launch path="C:/Apps/Notes.exe"', 'C:/Apps/Notes.exe');
  assert.ok(result.refused);
  assert.deepEqual(calls.splice(0), ['wm.arrange expect="C:/Apps/Notes.exe"']);
  console.log('Requested bar: 4 checks passed; shipped restore/focus, executable/Agora launch, refusal propagation; no native UI');
})().catch(error => { console.error(error); process.exitCode = 1; });
