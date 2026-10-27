// shell-spaces: one chip per window-manager space, shown only when there are two or more.
export default {mount(api) {
  const K = globalThis.ShellKit, { h, Data } = K;
  const body = api.part('body', 'div', { class: 'spaces', role: 'group', 'aria-label': 'Spaces' });
  body.hidden = true;
  K.watch(api, 'windows', 2500, (wins) => {
    const spaces = [...new Set(wins.map((w) => w.space).filter(Boolean))];
    body.hidden = spaces.length < 2;
    body.replaceChildren(...spaces.map((sp, i) => api.part('space', 'button', { class: 'btn chip', 'aria-label': `Space ${sp}`, on: { click: () => K.ran(Data.act(`wm.space ${sp}`)) } }, String(i + 1))));
  });
  return body;
}};
