// Appearance: the window where people choose, make, import, export and share themes (src/agora/theme/THEMES.md).
// A reviewed component for the component painter. It reads the theme words (theme.list, theme.current, theme.options,
// theme.preview) and says them back through the arrangement's gestures (appearance.lens); it holds no power of its own.
// Everything it paints wears the viewer's own theme through the --ag-* variables, and each theme card is painted in *that*
// theme by setting the same variables on the card, so what you see on a card is what the desktop will wear.
const SLOT_NAMES = {
  base00: 'Background', base01: 'Raised surface', base02: 'Border and selection', base03: 'Quiet text', base04: 'Muted text',
  base05: 'Text', base06: 'Strong text', base07: 'Brightest', base08: 'Red', base09: 'Orange', base0A: 'Yellow', base0B: 'Green',
  base0C: 'Cyan', base0D: 'Blue', base0E: 'Purple', base0F: 'Brown'};
const ACCENT_SLOTS = ['base08', 'base09', 'base0A', 'base0B', 'base0C', 'base0D', 'base0E', 'base0F'];
const CSS = `
.ap{min-height:100%;padding:28px 32px 40px;color:var(--ag-ink,var(--ink));font:var(--ag-text,15px)/1.5 var(--ag-font-ui,system-ui);background:var(--ag-surface,var(--paper));box-sizing:border-box}
.ap *{box-sizing:border-box}
.ap>*{max-width:1240px;margin-left:auto;margin-right:auto}
.ap button{font:inherit;color:inherit;cursor:pointer}
.ap h1,.ap h2,.ap h3,.ap p{margin:0}
.ap-eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ag-ink-muted,var(--muted));font-weight:600}
.ap h1{font:600 clamp(26px,3.4vw,38px)/1.1 var(--ag-font-display,var(--ag-font-ui));letter-spacing:-.02em;margin:6px 0 8px}
.ap-lede{color:var(--ag-ink-muted,var(--muted));max-width:62ch}
.ap-head{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px 24px;margin-bottom:22px}
.ap-wear{display:flex;align-items:center;gap:14px;padding:10px 12px 10px 14px;border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:var(--ag-radius-pill,999px);background:var(--ag-raised,var(--card));min-height:52px}
.ap-wear-dots{display:flex;gap:4px}.ap-wear-dots i{width:12px;height:12px;border-radius:50%;display:block;box-shadow:inset 0 0 0 1px rgba(128,128,128,.25)}
.ap-wear b{font-weight:600}.ap-wear small{color:var(--ag-ink-muted,var(--muted));display:block;line-height:1.2}
.ap-wear-btns{display:flex;gap:8px;margin-left:6px}
.ap-trial{position:relative;overflow:hidden}.ap-trial::after{content:"";position:absolute;left:0;bottom:0;height:3px;width:var(--ap-left,100%);background:var(--ag-accent);transition:width .25s linear}
.ap-tabs{display:inline-flex;gap:4px;padding:4px;border-radius:var(--ag-radius-pill,999px);background:var(--ag-hover,rgba(128,128,128,.1));margin:0 0 22px}
.ap-tab{border:0;background:transparent;padding:8px 18px;border-radius:var(--ag-radius-pill,999px);color:var(--ag-ink-muted,var(--muted));font-weight:600}
.ap-tab[aria-selected=true]{background:var(--ag-accent);color:var(--ag-accent-ink,#fff);box-shadow:0 1px 6px rgba(0,0,0,.18)}
.ap-btn{border:var(--ag-border-w,1px) solid var(--ag-border);background:var(--ag-raised,var(--card));padding:7px 14px;border-radius:var(--ag-radius-m,10px);font-weight:600;transition:background var(--ag-dur-fast,.12s),border-color var(--ag-dur-fast,.12s),transform var(--ag-dur-fast,.12s)}
.ap-btn:hover{border-color:var(--ag-accent);background:var(--ag-accent-soft)}.ap-btn:active{transform:scale(.97)}
.ap-btn.primary{background:var(--ag-accent);border-color:var(--ag-accent);color:var(--ag-accent-ink,#fff)}.ap-btn.primary:hover{filter:brightness(1.08);background:var(--ag-accent)}
.ap-btn.quiet{background:transparent;border-color:transparent;color:var(--ag-ink-muted,var(--muted))}.ap-btn.quiet:hover{color:var(--ag-ink);background:var(--ag-hover);border-color:transparent}
.ap-btn[disabled]{opacity:.45;cursor:not-allowed}
.ap-btn:focus-visible,.ap-tab:focus-visible,.ap input:focus-visible,.ap select:focus-visible,.ap textarea:focus-visible{outline:2px solid var(--ag-focus,var(--accent));outline-offset:2px}
.ap-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:24px}
.ap-card{display:flex;flex-direction:column;border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:calc(var(--ag-radius-l,14px) + 2px);background:var(--ag-raised,var(--card));overflow:hidden;transition:transform var(--ag-dur-med,.2s) var(--ag-ease,ease),box-shadow var(--ag-dur-med,.2s)}
.ap-card:hover{transform:translateY(-2px);box-shadow:var(--ag-shadow,0 10px 30px rgba(0,0,0,.12))}
.ap-card.on{border-color:var(--ag-accent);box-shadow:0 0 0 1px var(--ag-accent)}
.ap-card-body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:10px}
.ap-card-top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.ap-card h3{font:600 17px/1.2 var(--ag-font-display,var(--ag-font-ui))}
.ap-meta{color:var(--ag-ink-muted,var(--muted));font-size:13px}
.ap-pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.04em;background:var(--ag-accent-soft);color:var(--ag-accent)}
.ap-pill.place{background:var(--ag-info-soft);color:var(--ag-info)}
.ap-swatches{display:flex;gap:5px}.ap-swatches i{flex:1;height:10px;border-radius:3px;display:block;box-shadow:inset 0 0 0 1px rgba(128,128,128,.22)}
.ap-actions{display:flex;flex-wrap:wrap;gap:8px}
.ap-desk{--ap-r:calc(var(--ag-radius-m,10px) * .55);container-type:inline-size;position:relative;aspect-ratio:16/10;overflow:hidden;background-color:var(--ag-bg,#222);background-repeat:no-repeat;font-family:var(--ag-font-ui);color:var(--ag-ink)}
.ap-desk::before{content:"";position:absolute;inset:0;background:var(--ag-wallpaper-dim,transparent)}
.ap-bar{position:absolute;left:0;right:0;top:0;height:var(--ap-bar,6.4cqw);display:flex;align-items:center;justify-content:space-between;padding:0 2.2cqw;background:var(--ag-bar-bg,var(--ag-bar));border-bottom:1px solid var(--ag-border);backdrop-filter:var(--ag-backdrop,none);font-size:2.3cqw}
.ap-bar .ws{display:flex;gap:1cqw;align-items:center}.ap-bar .ws i{width:1.5cqw;height:1.5cqw;border-radius:50%;background:var(--ag-ink-faint)}.ap-bar .ws i.a{width:4.4cqw;border-radius:99px;background:var(--ag-accent)}
.ap-bar .clock{font-weight:600;letter-spacing:.02em}.ap-bar .st{display:flex;gap:1.1cqw}.ap-bar .st i{width:1.8cqw;height:1.8cqw;border-radius:30%;background:var(--ag-ink-muted);opacity:.75}
.ap-wins{position:absolute;left:var(--ag-gap-outer-s,3.4cqw);right:var(--ag-gap-outer-s,3.4cqw);top:calc(var(--ap-bar,6.4cqw) + var(--ag-gap-outer-s,3.4cqw));bottom:calc(var(--ap-dock,5.2cqw) + 6.4cqw);display:grid;grid-template-columns:1.12fr 1fr;grid-template-rows:1fr 1fr;gap:var(--ag-gap-inner-s,1.6cqw)}
.ap-win{display:flex;flex-direction:column;min-width:0;overflow:hidden;background:var(--ag-window-bg,var(--ag-surface));border:var(--ag-border-w,1px) solid var(--ag-win-unfocused);border-radius:var(--ap-r);box-shadow:var(--ag-shadow);backdrop-filter:var(--ag-backdrop,none)}
.ap-win.f{border-color:var(--ag-win-focused);grid-row:1/3}
.ap-win .tb{display:flex;align-items:center;gap:1.1cqw;padding:1.1cqw 1.6cqw;border-bottom:1px solid var(--ag-border);background:var(--ag-raised);font-size:2cqw}
.ap-win .tb i{width:1.4cqw;height:1.4cqw;border-radius:50%;background:var(--ag-ink-faint)}.ap-win .tb i:first-child{background:var(--ag-danger)}
.ap-win .tb span{margin-left:.8cqw;color:var(--ag-ink-muted);white-space:nowrap}
.ap-win .bd{padding:1.8cqw 2cqw;display:flex;flex-direction:column;gap:1.2cqw;flex:1;min-height:0}
.ap-win .ln{height:1.2cqw;border-radius:99px;background:var(--ag-ink);opacity:.82}.ap-win .ln.m{background:var(--ag-ink-muted);opacity:.6}.ap-win .ln.h{height:1.8cqw;width:46%;background:var(--ag-ink);opacity:1;margin-bottom:.4cqw}
.ap-win .sel{height:3cqw;border-radius:calc(var(--ap-r) * .6);background:var(--ag-select);display:flex;align-items:center;padding:0 1.2cqw;font-size:1.9cqw;color:var(--ag-ink)}
.ap-win .btn{align-self:flex-start;padding:.7cqw 2.2cqw;border-radius:calc(var(--ap-r) * .8);background:var(--ag-accent);color:var(--ag-accent-ink);font-size:1.9cqw;font-weight:700}
.ap-win .tag{display:inline-block;padding:.3cqw 1.2cqw;border-radius:99px;font-size:1.6cqw;font-weight:700;margin-right:1cqw}
.ap-win .code{font-family:var(--ag-font-mono);font-size:1.8cqw;color:var(--ag-ink-muted);line-height:1.5}.ap-win .code b{color:var(--ag-ok);font-weight:400}.ap-win .code u{color:var(--ag-warn);text-decoration:none}.ap-win .code s{color:var(--ag-info);text-decoration:none}
.ap-dock{position:absolute;left:50%;bottom:2.2cqw;transform:translateX(-50%);display:flex;gap:1.4cqw;padding:1.3cqw 1.9cqw;background:var(--ag-bar-bg,var(--ag-bar));border:1px solid var(--ag-border);border-radius:calc(var(--ap-r) * 1.7);box-shadow:var(--ag-shadow);backdrop-filter:var(--ag-backdrop,none)}
.ap-dock i{display:block;width:var(--ap-dock,5.2cqw);height:var(--ap-dock,5.2cqw);border-radius:calc(var(--ap-r) * .9);position:relative}
.ap-dock i.r::after{content:"";position:absolute;left:50%;bottom:-1cqw;width:.9cqw;height:.9cqw;border-radius:50%;background:var(--ag-accent);transform:translateX(-50%)}
.ap-edit{display:grid;grid-template-columns:minmax(300px,1.05fr) minmax(300px,1fr);gap:28px;align-items:start}
@media(max-width:880px){.ap-edit{grid-template-columns:1fr}.ap{padding:20px 16px 32px}}
.ap-stick{position:sticky;top:12px;display:flex;flex-direction:column;gap:14px}
.ap-stick .ap-desk{border-radius:calc(var(--ag-radius-l,14px) + 2px);border:var(--ag-border-w,1px) solid var(--ag-border)}
.ap-panel{border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:var(--ag-radius-l,14px);background:var(--ag-raised,var(--card));padding:16px 18px;margin-bottom:16px}
.ap-panel>h3{font:700 12px/1 var(--ag-font-ui);letter-spacing:.14em;text-transform:uppercase;color:var(--ag-ink-muted,var(--muted));margin-bottom:14px}
.ap-row{display:grid;grid-template-columns:128px 1fr auto;gap:10px 12px;align-items:center;margin-bottom:10px}.ap-row:last-child{margin-bottom:0}
.ap-row label{font-size:14px;color:var(--ag-ink)}.ap-row output{font-variant-numeric:tabular-nums;color:var(--ag-ink-muted);font-size:13px;min-width:46px;text-align:right}
.ap input[type=range]{width:100%;accent-color:var(--ag-accent)}
.ap input[type=color]{width:36px;height:28px;padding:0;border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:6px;background:var(--ag-surface);cursor:pointer}
.ap input[type=text],.ap select,.ap textarea{width:100%;font:inherit;color:var(--ag-ink);background:var(--ag-surface,var(--paper));border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:var(--ag-radius-m,10px);padding:8px 11px}
.ap textarea{min-height:120px;resize:vertical;font-family:var(--ag-font-mono);font-size:13px}
.ap-pal{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.ap-pal label{display:flex;flex-direction:column;gap:5px;font-size:11px;color:var(--ag-ink-muted);line-height:1.15}
.ap-pal input[type=color]{width:100%;height:34px}
.ap-seg{display:inline-flex;border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:var(--ag-radius-m,10px);overflow:hidden}
.ap-seg button{border:0;background:transparent;padding:6px 12px;font-size:13px;font-weight:600;border-right:var(--ag-border-w,1px) solid var(--ag-border)}.ap-seg button:last-child{border-right:0}
.ap-seg button[aria-pressed=true]{background:var(--ag-accent);color:var(--ag-accent-ink,#fff)}
.ap-walls{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:10px}
.ap-wall{aspect-ratio:16/10;border-radius:var(--ag-radius-m,10px);border:2px solid var(--ag-border);background-size:cover;background-position:center;padding:0;position:relative;overflow:hidden}
.ap-wall[aria-pressed=true]{border-color:var(--ag-accent);box-shadow:0 0 0 2px var(--ag-accent-soft)}
.ap-wall span{position:absolute;left:0;right:0;bottom:0;font-size:10px;font-weight:700;padding:3px 6px;background:rgba(0,0,0,.55);color:#fff;text-align:left}
.ap-note{padding:12px 14px;border-radius:var(--ag-radius-m,10px);background:var(--ag-warn-soft);color:var(--ag-ink);font-size:14px;margin-bottom:14px}
.ap-note.err{background:var(--ag-danger-soft)}.ap-note.ok{background:var(--ag-ok-soft)}
.ap-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}
.ap-empty{padding:30px;text-align:center;color:var(--ag-ink-muted);border:1px dashed var(--ag-border);border-radius:var(--ag-radius-l,14px)}
.ap-hint{font-size:13px;color:var(--ag-ink-muted)}
.ap-list{display:flex;flex-direction:column;gap:8px}.ap-item{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 12px;border:var(--ag-border-w,1px) solid var(--ag-border);border-radius:var(--ag-radius-m,10px)}
`;
const FIELD = /^[a-z][\w.-]*$/;

export default {css: CSS, mount(api) {
  const {P} = api;
  const el = api.el;
  const v = api.view();
  const tab = v.tab || 'gallery';
  const root = el('div', {class: 'ap'});
  const draft = api.draft;
  const h = (tag, attrs = {}, ...kids) => {
    const {vars, ...rest} = attrs;
    const node = el(tag, rest, ...kids);
    if (vars) for (const [k, val] of Object.entries(vars)) node.style.setProperty(k, val);
    return node;
  };
  const btn = (text, fn, cls = '', attrs = {}) => h('button', {type: 'button', class: 'ap-btn ' + cls, on: {click: api.guard(fn)}, ...attrs}, text);
  const safe = fn => async (...a) => { try { return await fn(...a); } catch (e) { api.tell(e); } };
  const say = (event, values) => api.fire(event, values);
  const first = stack => String(stack || '').split(',')[0].replace(/["']/g, '').trim();

  // ---- a theme painted in itself: the same variables the desktop will read, set on the card -------------------------
  function deskVars(card) {
    const vars = {...card.vars};
    const s = card.shape || {};
    vars['--ap-bar'] = (1.4 + 0.14 * (s.bar_height ?? 36)).toFixed(2) + 'cqw';
    vars['--ap-dock'] = (0.1 * (s.dock_size ?? 52)).toFixed(2) + 'cqw';
    vars['--ag-gap-inner-s'] = (0.2 * (s.gap_inner ?? 8)).toFixed(2) + 'cqw';
    vars['--ag-gap-outer-s'] = (0.3 * (s.gap_outer ?? 10) + .4).toFixed(2) + 'cqw';
    return vars;
  }
  function desk(card, extra = '') {
    const w = card.wallpaper || {};
    const node = h('div', {class: 'ap-desk ' + extra, vars: deskVars(card), 'aria-hidden': 'true'});
    const image = w.uri ? `url("${w.uri}")` : (w.background && w.background !== 'none' ? w.background : '');
    if (image) { node.style.backgroundImage = image; node.style.backgroundSize = w.fit === 'contain' ? 'contain' : w.fit === 'fill' ? '100% 100%' : 'cover'; node.style.backgroundPosition = 'center'; }
    const hue = ['base08', 'base09', 'base0B', 'base0D', 'base0E'];
    node.append(
      h('div', {class: 'ap-bar'}, h('div', {class: 'ws'}, h('i', {class: 'a'}), h('i'), h('i')), h('div', {class: 'clock'}, '10:42'), h('div', {class: 'st'}, h('i'), h('i'), h('i'))),
      h('div', {class: 'ap-wins'},
        h('div', {class: 'ap-win f'}, h('div', {class: 'tb'}, h('i'), h('i'), h('i'), h('span', {}, 'Notes')),
          h('div', {class: 'bd'}, h('div', {class: 'ln h'}), h('div', {class: 'ln'}), h('div', {class: 'ln m'}), h('div', {class: 'ln'}, ), h('div', {class: 'sel'}, 'Selected line'), h('div', {class: 'ln m'}), h('div', {class: 'btn'}, 'Save'))),
        h('div', {class: 'ap-win'}, h('div', {class: 'tb'}, h('i'), h('i'), h('i'), h('span', {}, 'Terminal')),
          h('div', {class: 'bd'}, h('div', {class: 'code'}, '$ agora ', h('b', {}, 'ok'), h('br'), h('u', {}, 'warn'), ' 2 ', h('s', {}, 'info')))),
        h('div', {class: 'ap-win'}, h('div', {class: 'tb'}, h('i'), h('i'), h('i'), h('span', {}, 'Board')),
          h('div', {class: 'bd'}, h('div', {}, ...['ok', 'warn', 'danger'].map(k => h('span', {class: 'tag', style: {background: `var(--ag-${k}-soft)`, color: `var(--ag-${k})`}}, k))), h('div', {class: 'ln'}), h('div', {class: 'ln m'})))),
      h('div', {class: 'ap-dock'}, ...hue.map((slot, i) => h('i', {class: i === 2 ? 'r' : '', style: {background: `var(--ag-${slot})`}}))));
    return node;
  }
  const swatchRow = card => h('div', {class: 'ap-swatches'}, ...['base00', 'base01', 'base05', 'base08', 'base09', 'base0B', 'base0D', 'base0E'].map(s => h('i', {style: {background: card.palette[s]}})));

  // ---- the status strip: what you wear, and a theme being tried ---------------------------------------------------------
  const strip = h('div', {class: 'ap-wear', role: 'status'});
  let skew = 0;                       // the kernel's clock minus this page's, so a countdown is right wherever the page's clock is
  function paintStrip(cards, now) {
    strip.replaceChildren();
    const wearing = cards.find(c => c.wearing) || cards.find(c => c.place) || cards[0];
    if (!wearing) { strip.hidden = true; return; }
    strip.append(h('div', {class: 'ap-wear-dots'}, ...['base00', 'base05', 'base08', 'base0B', 'base0D'].map(s => h('i', {style: {background: wearing.palette[s]}}))));
    const where = now.source === 'trial' ? 'trying it' : now.source === 'me' ? 'just for you' : now.source === 'place' ? 'the place’s theme' : 'the default look';
    const label = h('div', {}, h('b', {}, wearing.title), h('small', {}, where));
    strip.append(label);
    if (now.source === 'trial' && now.until) {
      strip.classList.add('ap-trial');
      const end = new Date(now.until).getTime();
      const tick = () => { const left = Math.max(0, end - (Date.now() + skew)); strip.style.setProperty('--ap-left', Math.min(100, left / 300) + '%'); label.querySelector('small').textContent = 'trying it · ' + Math.ceil(left / 1000) + ' s, then it goes back'; };
      tick(); api.setInterval(tick, 250);
      strip.append(h('div', {class: 'ap-wear-btns'}, btn('Keep', safe(() => say('keep', {})), 'primary'), btn('Go back', safe(() => say('revert', {})))));
    } else if (now.source === 'me') {
      strip.append(h('div', {class: 'ap-wear-btns'}, btn('Follow the place', safe(() => say('follow', {})), 'quiet')));
    }
  }

  // ---- the gallery ---------------------------------------------------------------------------------------------------------
  function card(c) {
    const node = h('article', {class: 'ap-card' + (c.wearing ? ' on' : ''), 'data-theme': c.id});
    const pills = [];
    if (c.wearing) pills.push(h('span', {class: 'ap-pill'}, c.source === 'trial' ? 'TRYING' : 'IN USE'));
    if (c.place && !c.wearing) pills.push(h('span', {class: 'ap-pill place'}, 'PLACE DEFAULT'));
    else if (c.place) pills.push(h('span', {class: 'ap-pill place'}, 'PLACE'));
    const actions = h('div', {class: 'ap-actions'},
      btn('Try 30 s', safe(() => say('try', {theme: c.id})), '', {'data-act': 'try'}),
      btn('Use just for me', safe(() => say('useme', {theme: c.id})), 'primary', {'data-act': 'use-me'}),
      ...(c.can_place ? [btn('Use for everyone', safe(() => say('use', {theme: c.id})), '', {'data-act': 'use'})] : []));
    const more = h('div', {class: 'ap-actions'},
      btn('Make my own from this', safe(() => say('make', {theme: c.id, name: 'My ' + c.title, select: {tab: 'make', editing: '', pending: 'My ' + c.title}})), 'quiet', {'data-act': 'make'}),
      btn('Export', safe(() => api.downloadReading('theme.export ' + c.id)), 'quiet', {'data-act': 'export'}));
    node.append(desk(c), h('div', {class: 'ap-card-body'},
      h('div', {class: 'ap-card-top'}, h('h3', {}, c.title), h('div', {}, ...pills)),
      h('div', {class: 'ap-meta'}, [c.author, c.variant, c.licence].filter(Boolean).join(' · ')),
      swatchRow(c), actions, more));
    return node;
  }
  function gallery(cards, now) {
    const box = h('div', {class: 'ap-grid'});
    for (const c of cards) box.append(card(c));
    if (!cards.length) box.replaceWith(h('div', {class: 'ap-empty'}, 'No themes yet. A steward can add the starters with theme.starters.'));
    return box;
  }

  // ---- make your own -----------------------------------------------------------------------------------------------------
  let previewSeq = 0;
  function editor(cards, now, options) {
    const mine = cards.filter(c => c.mine && !c.starter);
    const editing = cards.find(c => c.id === v.editing) || [...mine].reverse().find(c => c.title === v.pending) || mine[0];
    const wrap = h('div', {});
    if (!editing) {
      wrap.append(h('div', {class: 'ap-panel'}, h('h3', {}, 'Start from a theme'),
        h('p', {class: 'ap-hint', style: {marginBottom: '14px'}}, 'Pick any theme to copy. The copy is yours: change anything, and see the whole desktop in it before you use it.'),
        h('div', {class: 'ap-grid'}, ...cards.slice(0, 6).map(c => {
          const n = h('div', {class: 'ap-card'}, desk(c), h('div', {class: 'ap-card-body'}, h('h3', {}, c.title), btn('Copy and edit', safe(() => say('make', {theme: c.id, name: 'My ' + c.title, select: {tab: 'make', editing: '', pending: 'My ' + c.title}})), 'primary')));
          return n;
        }))));
      return wrap;
    }
    const patch = draft.patch = draft.patch || {};
    const preview = h('div', {class: 'ap-prev'}, desk(editing));
    const swap = card => { preview.replaceChildren(desk(card)); };
    async function refreshPreview() {
      const seq = ++previewSeq;
      const kv = Object.entries(patch).map(([k, val]) => k + '=' + api.Q(val)).join(' ');
      if (!kv) return swap(editing);
      try {
        const rows = await api.rows('theme.preview ' + editing.id + ' ' + kv);
        if (seq === previewSeq && rows[0]) swap(rows[0]);
      } catch (e) { note.textContent = String(e.message || e); note.className = 'ap-note err'; note.hidden = false; }
    }
    let timer;
    const later = () => { clearTimeout(timer); timer = api.setTimeout(refreshPreview, 90); };
    const note = h('div', {class: 'ap-note', hidden: ''});
    async function commit() {
      clearTimeout(timer);
      const fields = {...patch};
      if (!Object.keys(fields).length) return;
      try { await say('edit', {theme: editing.id, fields}); for (const k of Object.keys(patch)) delete patch[k]; note.hidden = true; }
      catch (e) { note.textContent = String(e.message || e); note.className = 'ap-note err'; note.hidden = false; }
    }
    const norm = path => path.startsWith('palette.') ? path.toLowerCase() : path;
    const set = (path, value, save) => { patch[norm(path)] = value; later(); if (save) commit(); };
    const cur = (path, fallback) => norm(path) in patch ? patch[norm(path)] : fallback;
    const row = (label, control, out) => h('div', {class: 'ap-row'}, h('label', {}, label), control, out || h('span'));
    const range = (path, label, min, max, step, value, unit = '') => {
      const out = h('output', {}, String(cur(path, value)) + unit);
      const input = h('input', {type: 'range', min, max, step, value: cur(path, value), 'aria-label': label, on: {
        input: e => { out.textContent = e.target.value + unit; set(path, e.target.value, false); }, change: e => set(path, e.target.value, true)}});
      return row(label, input, out);
    };
    const seg = (path, label, opts, value) => {
      const group = h('div', {class: 'ap-seg', role: 'group', 'aria-label': label});
      for (const o of opts) group.append(h('button', {type: 'button', 'aria-pressed': String(cur(path, value) === o), on: {click: () => { set(path, o, true); for (const b of group.children) b.setAttribute('aria-pressed', String(b.textContent === o)); }}}, o));
      return row(label, group);
    };
    const select = (path, label, opts, value, show = x => x) => {
      const sel = h('select', {'aria-label': label, on: {change: e => set(path, e.target.value, true)}});
      for (const o of (opts.includes(cur(path, value)) ? opts : [cur(path, value), ...opts])) sel.append(h('option', {value: o, ...(o === cur(path, value) ? {selected: ''} : {})}, show(o)));
      return row(label, sel);
    };
    const colour = slot => {
      const input = h('input', {type: 'color', value: cur('palette.' + slot, editing.palette[slot]), 'aria-label': SLOT_NAMES[slot], on: {
        input: e => set('palette.' + slot, e.target.value, false), change: e => set('palette.' + slot, e.target.value, true)}});
      return h('label', {title: slot}, SLOT_NAMES[slot], input);
    };
    const pal = (slots) => h('div', {class: 'ap-pal'}, ...slots.map(colour));
    const fonts = options?.fonts || {ui: [], mono: []};
    const name = h('input', {type: 'text', value: cur('meta.name', editing.title), maxlength: 60, 'aria-label': 'Theme name', on: {change: e => set('meta.name', e.target.value, true)}});
    const accentNow = editing.roles?.accent;
    const accentSlot = ACCENT_SLOTS.find(s => editing.palette[s] === accentNow) || 'base0D';
    const left = h('div', {class: 'ap-stick'}, preview,
      h('div', {class: 'ap-actions'},
        btn('Try on my desktop (30 s)', safe(() => say('try', {theme: editing.id})), 'primary'),
        btn('Use just for me', safe(() => say('useme', {theme: editing.id}))),
        btn('Share…', safe(() => api.select({tab: 'share', shareTheme: editing.id}))),
        btn('Export', safe(() => api.downloadReading('theme.export ' + editing.id)), 'quiet')),
      h('p', {class: 'ap-hint'}, 'Changes are saved as you make them and can be undone. The preview is this theme painted by itself; “Try” puts it on the real desktop.'));
    const right = h('div', {},
      note,
      ...(mine.length > 1 ? [h('div', {class: 'ap-panel'}, h('h3', {}, 'Your themes'), h('div', {class: 'ap-seg'}, ...mine.map(c => h('button', {type: 'button', 'aria-pressed': String(c.id === editing.id), on: {click: () => api.select({editing: c.id})}}, c.title))))] : []),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Name'), name),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Colours'),
        h('p', {class: 'ap-hint', style: {marginBottom: '10px'}}, 'Surfaces and text'), pal(['base00', 'base01', 'base02', 'base03', 'base04', 'base05', 'base06', 'base07']),
        h('p', {class: 'ap-hint', style: {margin: '16px 0 10px'}}, 'Colours'), pal(ACCENT_SLOTS),
        h('div', {style: {marginTop: '16px'}}, select('roles.accent', 'Accent colour', ACCENT_SLOTS, accentSlot, s => SLOT_NAMES[s]))),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Type'),
        select('type.ui', 'Interface font', fonts.ui, editing.type.ui, first), select('type.mono', 'Code font', fonts.mono, editing.type.mono, first),
        range('type.size', 'Text size', 12, 18, 0.5, editing.type.size, ' px')),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Shape'),
        seg('shape.radius', 'Corners', ['none', 'small', 'medium', 'large'], editing.shape.radius),
        range('shape.gap_inner', 'Gap between windows', 0, 32, 1, editing.shape.gap_inner, ' px'),
        range('shape.gap_outer', 'Gap at the edges', 0, 48, 1, editing.shape.gap_outer, ' px'),
        range('shape.border', 'Border width', 0, 4, 1, editing.shape.border, ' px'),
        range('shape.bar_height', 'Top bar height', 24, 64, 1, editing.shape.bar_height, ' px'),
        range('shape.dock_size', 'Dock icon size', 32, 96, 1, editing.shape.dock_size, ' px')),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Surfaces'),
        range('surface.bar_opacity', 'Bar opacity', 0.2, 1, 0.02, editing.surface.bar_opacity),
        range('surface.window_opacity', 'Window opacity', 0.5, 1, 0.02, editing.surface.window_opacity),
        seg('surface.shadow', 'Shadow', ['none', 'soft', 'deep'], editing.surface.shadow),
        seg('surface.blur', 'Glass blur', ['none', 'soft'], editing.surface.blur)),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Wallpaper'),
        h('div', {class: 'ap-walls'}, ...[{name: 'none', kind: 'none'}, ...(options?.wallpapers || [])].map(w => {
          const b = h('button', {type: 'button', class: 'ap-wall', 'aria-label': 'Wallpaper ' + w.name, 'aria-pressed': String(false), on: {click: () => set('wallpaper', w.name === 'none' ? 'none' : 'preset:' + w.name, true)}}, h('span', {}, w.name));
          if (w.uri) b.style.backgroundImage = `url("${w.uri}")`; else if (w.background && w.background !== 'none') b.style.backgroundImage = w.background; else b.style.background = 'var(--ag-hover)';
          return b;
        })),
        h('div', {style: {marginTop: '14px'}}, range('wallpaper.dim', 'Dim', 0, 0.8, 0.02, editing.wallpaper?.dim || 0))));
    wrap.append(h('div', {class: 'ap-edit'}, left, right));
    return wrap;
  }

  // ---- import, export and share -------------------------------------------------------------------------------------------
  function exchange(cards, channels) {
    const box = h('div', {});
    const msg = h('div', {class: 'ap-note', hidden: ''});
    const show = (text, cls = '') => { msg.textContent = text; msg.className = 'ap-note ' + cls; msg.hidden = !text; };
    const importText = async text => {
      if (!text.trim()) { show('Paste a scheme or choose a file first.', 'err'); return; }
      if (text.length > 60000) { show('That file is larger than this window can paste (60 KB). Themes with big pictures travel in a kit or on the board.', 'err'); return; }
      try { const out = await say('import', {fields: {text}}); show('Imported. It is in the gallery now: Try it, or make it your own.', 'ok'); draft.paste = ''; }
      catch (e) { show(String(e.message || e).replace(/^.*?: /, ''), 'err'); }
    };
    const area = h('textarea', {placeholder: 'system: "base16"\nname: "My scheme"\npalette:\n  base00: "#1e1e2e"\n  …', 'aria-label': 'Paste a base16 scheme or agora-theme.json', value: draft.paste || '', on: {input: e => { draft.paste = e.target.value; }}});
    const file = h('input', {type: 'file', accept: '.yaml,.yml,.json,.txt', hidden: '', on: {change: safe(async e => { const f = e.target.files[0]; if (f) { const text = await f.text(); area.value = text; draft.paste = text; await importText(text); } })}});
    const picked = cards.find(c => c.id === (v.shareTheme || draft.shareTheme)) || cards.find(c => c.mine && !c.starter) || cards[0];
    const themeSel = h('select', {'aria-label': 'Theme to share', on: {change: e => { draft.shareTheme = e.target.value; api.select({shareTheme: e.target.value}); }}}, ...cards.map(c => h('option', {value: c.id, ...(c.id === picked?.id ? {selected: ''} : {})}, c.title)));
    const exportSel = h('select', {'aria-label': 'Theme to export'}, ...cards.map(c => h('option', {value: c.id, ...(c.id === picked?.id ? {selected: ''} : {})}, c.title)));
    const chanSel = h('select', {'aria-label': 'Channel'}, ...channels.map(c => h('option', {value: c.group}, c.title)));
    const text = h('textarea', {'aria-label': 'Message', style: {minHeight: '84px', fontFamily: 'inherit', fontSize: '14px'}, value: draft.shareText ?? ''});
    if (picked && !draft.shareText) text.value = `I made a theme called ${picked.title}. Download the attached file and use Import in Appearance to try it.`;
    text.addEventListener('input', () => { draft.shareText = text.value; });
    const board = channels.length
      ? [h('div', {class: 'ap-row', style: {gridTemplateColumns: '90px 1fr auto'}}, h('label', {}, 'Theme'), themeSel), h('div', {class: 'ap-row', style: {gridTemplateColumns: '90px 1fr auto'}}, h('label', {}, 'Channel'), chanSel),
         text, h('div', {class: 'ap-actions', style: {marginTop: '12px'}}, btn('Share to the board', safe(() => shareToBoard(picked, chanSel.value, text.value, show)), 'primary', {'data-act': 'share'}))]
      : [h('p', {class: 'ap-hint'}, 'The board is not installed in this place yet, so there is nowhere to post a theme. Export the file and share it any way you like: anyone can import it here.')];
    box.append(msg, h('div', {class: 'ap-two'},
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Import a theme'),
        h('p', {class: 'ap-hint', style: {marginBottom: '10px'}}, 'Paste a base16 or base24 scheme (the tinted-theming YAML) or an agora-theme.json, or choose the file. It is checked first: no scripts, no addresses, fonts by name only.'),
        area, h('div', {class: 'ap-actions', style: {marginTop: '12px'}}, btn('Import', safe(() => importText(area.value)), 'primary', {'data-act': 'import'}), btn('Choose a file…', () => file.click()), file)),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Export a theme'),
        h('p', {class: 'ap-hint', style: {marginBottom: '12px'}}, 'One file, agora-theme.json, with the wallpaper inside it. A base16 file carries only the palette, for any other program that reads those.'),
        h('div', {class: 'ap-row', style: {gridTemplateColumns: '90px 1fr auto'}}, h('label', {}, 'Theme'), exportSel),
        h('div', {class: 'ap-actions'}, btn('Export agora-theme.json', safe(() => api.downloadReading('theme.export ' + exportSel.value)), 'primary', {'data-act': 'export-file'}),
          btn('Export base16 (.yaml)', safe(() => api.downloadReading('theme.export ' + exportSel.value + ' format=base16')), '', {'data-act': 'export-b16'}))),
      h('div', {class: 'ap-panel'}, h('h3', {}, 'Share on the board'), ...board)));
    return box;
  }
  async function shareToBoard(c, group, words, show) {
    if (!c) return;
    try {
      show('Drawing a preview…');
      const png = await new Promise(resolve => drawPreview(c).toBlob(resolve, 'image/png'));
      const slug = (c.name || c.title).replace(/[^a-z0-9-]+/gi, '-').toLowerCase();
      const exported = (await api.rows('theme.export ' + c.id))[0];
      show('Posting…');
      const post = await say('post', {fields: {text: words || ('A theme: ' + c.title), post_kind: 'discussion', in: group}});
      const target = post?.made?.[0];
      if (!target) throw new Error('The board did not make a post.');
      show('Attaching the preview and the theme file…');
      const image = await api.upload(new File([png], slug + '-preview.png', {type: 'image/png'}), group);
      const data = await api.upload(new File([exported.text], exported.filename, {type: 'application/json'}), group);
      const rev = async id => (await api.rows('look ' + id))[0]?.rev;
      for (const up of [image, data]) {
        const file = up?.made?.[0];
        if (file) await say('attach', {file, target, saw: {[file]: await rev(file), [target]: await rev(target)}});
      }
      show('Shared: the post carries a preview and the theme file. Neighbours use Import to try it.', 'ok');
    } catch (e) {
      show('Not shared: ' + String(e.message || e).replace(/^refused: /, ''), 'err');
    }
  }
  // a preview drawn straight onto a canvas, for the picture on a board post
  function drawPreview(c) {
    const W = 960, H = 600, cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const g = cv.getContext('2d'), pal = c.palette, r = c.roles, s = c.shape;
    const rr = (x, y, w, hh, rad, fill, stroke) => { g.beginPath(); g.roundRect(x, y, w, hh, rad); if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = s.border || 1; g.stroke(); } };
    const grad = c.wallpaper?.background;
    g.fillStyle = r.bg; g.fillRect(0, 0, W, H);
    const rad = ({none: 0, small: 6, medium: 14, large: 22})[s.radius] ?? 12;
    if (c.palette) {
      const lg = g.createLinearGradient(0, 0, 0, H); lg.addColorStop(0, pal.base01); lg.addColorStop(1, pal.base00); g.fillStyle = lg; g.fillRect(0, 0, W, H);
      if (c.variant === 'dark') { const rg = g.createRadialGradient(W * .2, 0, 10, W * .2, 0, W * .7); rg.addColorStop(0, r.accent + '55'); rg.addColorStop(1, r.accent + '00'); g.fillStyle = rg; g.fillRect(0, 0, W, H); }
    }
    rr(0, 0, W, 54, 0, r.bar); g.fillStyle = r.ink; g.font = '600 22px sans-serif'; g.fillText('10:42', W / 2 - 28, 35);
    rr(26, 20, 62, 16, 8, r.accent); for (const i of [1, 2]) { g.beginPath(); g.arc(100 + i * 22, 28, 6, 0, 7); g.fillStyle = r['ink-muted']; g.fill(); }
    const gap = Math.max(8, (s.gap_inner || 8) * 1.6), top = 54 + (s.gap_outer || 10) * 1.6, bottom = H - 120;
    const lw = (W - 2 * (s.gap_outer || 10) * 2.4 - gap) * .54, x0 = (s.gap_outer || 10) * 2.4;
    const win = (x, y, w, hh, focused, title) => {
      rr(x, y, w, hh, rad, r.surface, focused ? c.windows.focused : c.windows.unfocused);
      rr(x, y, w, 36, rad, r.raised); g.fillStyle = r.raised; g.fillRect(x, y + 20, w, 16);
      g.fillStyle = r.danger; g.beginPath(); g.arc(x + 18, y + 18, 5, 0, 7); g.fill();
      g.fillStyle = r['ink-muted']; g.font = '600 16px sans-serif'; g.fillText(title, x + 36, y + 24);
      for (let i = 0; i < 4; i++) { rr(x + 18, y + 56 + i * 24, w * (i % 2 ? .5 : .78), 9, 5, i % 2 ? r['ink-muted'] : r.ink); }
      rr(x + 18, y + hh - 54, 84, 30, Math.min(rad, 12), r.accent); g.fillStyle = r['accent-ink']; g.font = '700 15px sans-serif'; g.fillText('Save', x + 40, y + hh - 33);
    };
    win(x0, top, lw, bottom - top, true, 'Notes');
    win(x0 + lw + gap, top, W - x0 * 2 - lw - gap, (bottom - top - gap) / 2, false, 'Terminal');
    win(x0 + lw + gap, top + (bottom - top + gap) / 2, W - x0 * 2 - lw - gap, (bottom - top - gap) / 2, false, 'Board');
    const dw = 5 * 56 + 24 + 4 * 14; rr(W / 2 - dw / 2, H - 94, dw, 74, rad + 8, r.bar, r.border);
    ['base08', 'base09', 'base0B', 'base0D', 'base0E'].forEach((k, i) => rr(W / 2 - dw / 2 + 12 + i * 70, H - 82, 56, 50, rad, pal[k]));
    g.fillStyle = r.ink; g.globalAlpha = .9; g.font = '700 26px sans-serif'; g.fillText(c.title, 28, H - 22 - 78 + 78 - 2 + 0); g.globalAlpha = 1;
    return cv;
  }

  // ---- put it together -----------------------------------------------------------------------------------------------------
  const tabs = h('div', {class: 'ap-tabs', role: 'tablist'}, ...[['gallery', 'Gallery'], ['make', 'Make your own'], ['share', 'Import and share']].map(([id, label]) =>
    h('button', {type: 'button', class: 'ap-tab', role: 'tab', 'aria-selected': String(tab === id), 'data-tab': id, on: {click: () => api.select({tab: id})}}, label)));
  const body = h('div', {class: 'ap-body'});
  root.append(h('header', {class: 'ap-head'}, h('div', {}, h('div', {class: 'ap-eyebrow'}, 'Appearance'), h('h1', {}, 'One look for everything'),
    h('p', {class: 'ap-lede'}, 'A theme is one palette and one shape: the same in every window, the bar, the dock and your widgets. Try one for half a minute; keep it if it feels right.')), strip), tabs, body);
  Promise.all([api.read('theme.list'), api.read('theme.current'), api.read('theme.options'), api.read('rows board-channel').catch(() => []), api.read('clock').catch(() => [])]).then(api.guard(async ([cards, nowRows, optRows, channels, clockRows]) => {
    const now = nowRows[0] || {};
    if (clockRows[0]?.at) skew = Date.parse(clockRows[0].at) - Date.now();
    paintStrip(cards, now);
    if (tab === 'gallery') body.append(gallery(cards, now));
    else if (tab === 'make') {
      const mineNow = cards.filter(c => c.mine && !c.starter);
      const editing = cards.find(c => c.id === v.editing) || [...mineNow].reverse().find(c => c.title === v.pending) || mineNow[0];
      const options = editing ? (await api.rows('theme.options ' + editing.id))[0] : optRows[0];
      body.append(editor(cards, now, options));
    } else body.append(exchange(cards, channels));
    root.dataset.ready = 'true';
  })).catch(api.tell);
  return root;
}};
