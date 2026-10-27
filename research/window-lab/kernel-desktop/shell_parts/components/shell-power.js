// shell-power: turns the Agora desktop off, on a second press within four seconds. Gesture off (default
// `off window`); the window manager is told `wm.mode off` first when it is answering.
export default {mount(api) {
  const K = globalThis.ShellKit, { glyph, Data } = K;
  const body = api.part('body', 'button', { class: 'btn off', 'aria-label': 'Turn the desktop off (press twice)', 'aria-pressed': 'false' }, glyph('power'));
  let armed = false, timer = 0;
  const disarm = () => { armed = false; body.classList.remove('armed'); body.setAttribute('aria-pressed', 'false'); body.setAttribute('aria-label', 'Turn the desktop off (press twice)'); };
  body.addEventListener('click', async () => {
    if (!armed) {
      armed = true; body.classList.add('armed'); body.setAttribute('aria-pressed', 'true');
      body.setAttribute('aria-label', 'Press again to turn the desktop off');
      K.toast('Press the power button again to turn the Agora desktop off');
      clearTimeout(timer);
      timer = api.setTimeout(disarm, 4000);
      return;
    }
    clearTimeout(timer); disarm();
    if (Data.wmOK) await Data.act('wm.mode off');
    await K.fire(api, 'off', 'off window');
  });
  return body;
}};
