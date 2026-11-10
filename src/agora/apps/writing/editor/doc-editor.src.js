// The Writing window's editor. Builder draft by Claude, 4 Nov 2026, from Alex: "make it so its a continous document
// ... get rid of rectangles around text ... I should be able to highlight over sections, put my cursor anywhere ... I
// need it to work about as well as obsidian". CodeMirror 6 (what Obsidian's editor is built on) with a live preview:
// Markdown marks are hidden except where the caret is, headings are drawn large, lists get bullets, tasks get boxes,
// tables are drawn as tables until the caret enters them, and [[links]] show their title.
// Built into one script by build.mjs; writing-components.js reads it as WR_CM. Knows nothing of Agora: the page passes
// in what to do with links, saves, comments and menus.
import {EditorState, StateField, StateEffect, Compartment, RangeSetBuilder, ChangeSet, Text, Transaction, EditorSelection, Prec} from '@codemirror/state';
import {EditorView, keymap, Decoration, ViewPlugin, WidgetType, drawSelection, placeholder, dropCursor, highlightSpecialChars} from '@codemirror/view';
import {defaultKeymap, history, historyKeymap, indentMore, indentLess, insertTab, undo, redo, selectAll} from '@codemirror/commands';
import {markdown, markdownLanguage, markdownKeymap} from '@codemirror/lang-markdown';
import {syntaxTree, HighlightStyle, syntaxHighlighting, indentUnit, ensureSyntaxTree} from '@codemirror/language';
import {search, searchKeymap, openSearchPanel, highlightSelectionMatches} from '@codemirror/search';
import {autocompletion, completionKeymap, startCompletion, acceptCompletion} from '@codemirror/autocomplete';
import {tags as t} from '@lezer/highlight';

// ---- how it looks -------------------------------------------------------------------------------------------------
const look = HighlightStyle.define([
  {tag: t.heading1, fontSize: '1.7em', fontWeight: '700', lineHeight: '1.3'},
  {tag: t.heading2, fontSize: '1.36em', fontWeight: '680', lineHeight: '1.3'},
  {tag: t.heading3, fontSize: '1.15em', fontWeight: '650'},
  {tag: [t.heading4, t.heading5, t.heading6], fontWeight: '650'},
  {tag: t.strong, fontWeight: '700'},
  {tag: t.emphasis, fontStyle: 'italic'},
  {tag: t.strikethrough, textDecoration: 'line-through', color: 'var(--ag-ink-muted,#7b847f)'},
  {tag: t.link, color: 'var(--ag-accent,#4f7a6c)'},
  {tag: t.url, color: 'var(--ag-ink-muted,#7b847f)'},
  {tag: t.monospace, fontFamily: 'var(--ag-font-mono,ui-monospace,monospace)', fontSize: '.9em'},
  {tag: [t.processingInstruction, t.meta, t.contentSeparator], color: 'var(--ag-ink-faint,#a8b0ab)'},
  {tag: t.quote, color: 'var(--ag-ink-muted,#5f6b66)'},
]);

const theme = EditorView.theme({
  '&': {background: 'transparent', color: 'var(--ag-ink,#2f3a35)', fontSize: '16.5px'},
  '&.cm-focused': {outline: 'none'},
  '.cm-scroller': {fontFamily: 'var(--ag-font-ui,system-ui,sans-serif)', lineHeight: '1.72', overflow: 'visible'},
  '.cm-content': {padding: '4px 0 40vh', caretColor: 'var(--ag-accent,#4f7a6c)', maxWidth: 'var(--wr-measure,780px)'},
  '.cm-line': {padding: '0'},
  '.cm-cursor, .cm-dropCursor': {borderLeftColor: 'var(--ag-accent,#4f7a6c)', borderLeftWidth: '2px'},
  '&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, ::selection':
    {background: 'color-mix(in srgb, var(--ag-accent,#4f7a6c) 26%, transparent) !important'},
  '.cm-placeholder': {color: 'var(--ag-ink-faint,#a8b0ab)', fontStyle: 'normal'},
  '.cm-wr-h1, .cm-wr-h2, .cm-wr-h3, .cm-wr-h4, .cm-wr-h5, .cm-wr-h6': {fontFamily: 'var(--ag-font-display,inherit)', letterSpacing: '-.005em'},
  '.cm-wr-h1': {paddingTop: '.7em !important', paddingBottom: '.1em !important'},
  '.cm-wr-h2': {paddingTop: '.6em !important', paddingBottom: '.05em !important'},
  '.cm-wr-h3, .cm-wr-h4, .cm-wr-h5, .cm-wr-h6': {paddingTop: '.4em !important'},
  '.cm-wr-quote': {borderLeft: '3px solid var(--ag-accent,#4f7a6c)', paddingLeft: '14px !important', color: 'var(--ag-ink-muted,#5f6b66)'},
  '.cm-wr-code': {fontFamily: 'var(--ag-font-mono,ui-monospace,monospace)', fontSize: '13.5px', lineHeight: '1.55',
    background: 'color-mix(in srgb, var(--ag-hover,#0000000d) 70%, transparent)', paddingLeft: '14px !important', paddingRight: '14px !important'},
  '.cm-wr-code-first': {borderTopLeftRadius: '10px', borderTopRightRadius: '10px', paddingTop: '6px !important'},
  '.cm-wr-code-last': {borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px', paddingBottom: '6px !important'},
  '.cm-wr-inline-code': {fontFamily: 'var(--ag-font-mono,ui-monospace,monospace)', fontSize: '.88em', padding: '.1em .32em', borderRadius: '5px',
    background: 'var(--ag-hover,#0000000d)'},
  '.cm-wr-bullet': {display: 'inline-block', width: '1.1em', color: 'var(--ag-ink-muted,#7b847f)', fontWeight: '700'},
  '.cm-wr-box': {verticalAlign: '-2px', margin: '0 .45em 0 0', accentColor: 'var(--ag-accent,#4f7a6c)', cursor: 'pointer'},
  '.cm-wr-done': {color: 'var(--ag-ink-muted,#7b847f)', textDecoration: 'line-through', textDecorationColor: 'var(--ag-ink-faint,#aab)'},
  '.cm-wr-hr': {display: 'block', height: '0', borderTop: '1px solid var(--ag-border,#e2dfd6)', margin: '.9em 0'},
  '.cm-wr-link': {color: 'var(--ag-accent,#4f7a6c)', textDecoration: 'underline', textDecorationColor: 'color-mix(in srgb, var(--ag-accent,#4f7a6c) 40%, transparent)',
    textUnderlineOffset: '3px', cursor: 'pointer'},
  '.cm-wr-link.cm-wr-missing': {color: 'var(--ag-ink-muted,#7b847f)', textDecorationStyle: 'dashed'},
  '.cm-wr-table': {margin: '.4em 0', overflowX: 'auto', cursor: 'text'},
  '.cm-wr-table table': {borderCollapse: 'collapse', width: '100%', fontSize: '14px', lineHeight: '1.5'},
  '.cm-wr-table th, .cm-wr-table td': {textAlign: 'left', verticalAlign: 'top', padding: '7px 10px', borderBottom: '1px solid var(--ag-border,#e2dfd6)'},
  '.cm-wr-table th': {fontWeight: '650', color: 'var(--ag-ink-muted,#5f6b66)', fontSize: '12.5px'},
  '.cm-wr-comment': {background: 'color-mix(in srgb, #f2c94c 32%, transparent)', borderBottom: '2px solid #e0b43a', cursor: 'pointer'},
  '.cm-wr-comment.cm-wr-hot': {background: 'color-mix(in srgb, #f2c94c 60%, transparent)'},
  '.cm-searchMatch': {background: 'color-mix(in srgb, #f2c94c 45%, transparent)'},
  '.cm-searchMatch-selected': {background: 'color-mix(in srgb, #f2994a 55%, transparent)'},
  '.cm-panels': {background: 'var(--ag-raised,#fff)', color: 'var(--ag-ink,#2f3a35)', borderColor: 'var(--ag-border,#e2dfd6)'},
  '.cm-panels.cm-panels-top': {position: 'sticky', top: '0'},
  '.cm-panel.cm-search': {padding: '8px 10px', fontSize: '13px'},
  '.cm-panel.cm-search input, .cm-panel.cm-search button': {fontSize: '13px', borderRadius: '6px'},
  '.cm-tooltip.cm-tooltip-autocomplete': {border: '1px solid var(--ag-border,#e2dfd6)', borderRadius: '10px', background: 'var(--ag-raised,#fff)',
    boxShadow: '0 10px 30px #0002', overflow: 'hidden'},
  '.cm-tooltip-autocomplete > ul > li': {padding: '5px 10px !important', fontFamily: 'var(--ag-font-ui,system-ui)'},
  '.cm-tooltip-autocomplete > ul > li[aria-selected]': {background: 'var(--ag-accent-soft,#e6efe9)', color: 'var(--ag-ink,#2f3a35)'},
  '.cm-completionDetail': {marginLeft: '10px', color: 'var(--ag-ink-muted,#7b847f)', fontStyle: 'normal', fontSize: '12px'},
});

// ---- live preview ---------------------------------------------------------------------------------------------------
const hide = Decoration.replace({});
const line = cls => Decoration.line({class: cls});

class Bullet extends WidgetType {
  eq() { return true }
  toDOM() { const s = document.createElement('span'); s.className = 'cm-wr-bullet'; s.textContent = '•'; return s }
}
class Box extends WidgetType {
  constructor(on, at) { super(); this.on = on; this.at = at }
  eq(o) { return o.on === this.on && o.at === this.at }
  toDOM(view) {
    const b = document.createElement('input'); b.type = 'checkbox'; b.className = 'cm-wr-box'; b.checked = this.on;
    b.setAttribute('aria-label', this.on ? 'Done' : 'Not done');
    b.addEventListener('mousedown', e => e.preventDefault());
    b.addEventListener('click', e => {
      e.preventDefault();
      const at = this.at, now = view.state.sliceDoc(at, at + 3);
      if (/^\[[ xX]\]$/.test(now)) view.dispatch({changes: {from: at + 1, to: at + 2, insert: now[1] === ' ' ? 'x' : ' '}, userEvent: 'input.tick'});
    });
    return b;
  }
  ignoreEvent() { return true }
}
class Rule extends WidgetType {
  eq() { return true }
  toDOM() { const s = document.createElement('span'); s.className = 'cm-wr-hr'; return s }
}

// Where the caret is: that line shows its marks. A selection shows marks only where its moving end is, so text does
// not shift under the mouse while dragging
function touched(state) {
  const lines = new Set();
  for (const r of state.selection.ranges) lines.add(state.doc.lineAt(r.head).number);
  return lines;
}
const nearSel = (state, from, to) => state.selection.ranges.some(r => r.head >= from && r.head <= to);
const near = nearSel;

const WIKI = /\[\[([^\]|\n]+)(?:\|([^\]\n]*))?\]\]/g;
const LinkMeta = StateEffect.define();      // the page says how links resolve now (titles change)

function preview(cfg) {
  return ViewPlugin.fromClass(class {
    // Until the editor is first pressed or focused, everything is drawn: no line shows its marks just because the
    // caret starts there
    constructor(view) { this.seen = view.hasFocus; this.decorations = this.build(view) }
    update(u) {
      if (u.focusChanged && u.view.hasFocus) this.seen = true;
      if (u.docChanged || u.viewportChanged || u.selectionSet || u.focusChanged || u.transactions.some(tr => tr.effects.some(e => e.is(LinkMeta) || e.is(SourceMode))) || syntaxTree(u.startState) !== syntaxTree(u.state))
        this.decorations = this.build(u.view);
    }
    build(view) {
      const {state} = view, source = state.field(sourceField, false);
      const seen = this.seen, near = (s, a, b) => seen && nearSel(s, a, b);
      const marks = [], active = seen ? touched(state) : new Set(), doc = state.doc;
      const add = (from, to, deco) => { if (to >= from) marks.push(deco.range(from, to)) };
      const lineOf = pos => doc.lineAt(pos).number;
      for (const {from, to} of view.visibleRanges) {
        syntaxTree(state).iterate({from, to, enter: node => {
          const n = node.name, ln = lineOf(node.from), on = active.has(ln);
          if (/^ATXHeading(\d)$/.test(n)) {
            const lvl = n.slice(-1);
            add(doc.lineAt(node.from).from, doc.lineAt(node.from).from, line('cm-wr-h' + lvl));
          } else if (/^SetextHeading(\d)$/.test(n)) {
            add(doc.lineAt(node.from).from, doc.lineAt(node.from).from, line('cm-wr-h' + n.slice(-1)));
          } else if (n === 'HeaderMark') {
            if (!source && !on && doc.sliceString(node.to, node.to + 1) === ' ') add(node.from, node.to + 1, hide);
            else if (!source && !on && node.from > doc.lineAt(node.from).from) add(node.from, node.to, hide);   // closing #s
          } else if (n === 'EmphasisMark' || n === 'StrikethroughMark') {
            const parent = node.node.parent;
            if (!source && parent && !near(state, parent.from, parent.to)) add(node.from, node.to, hide);
          } else if (n === 'InlineCode') {
            add(node.from, node.to, Decoration.mark({class: 'cm-wr-inline-code'}));
          } else if (n === 'CodeMark') {
            const parent = node.node.parent;
            if (!source && parent?.name === 'InlineCode' && !near(state, parent.from, parent.to)) add(node.from, node.to, hide);
          } else if (n === 'FencedCode' || n === 'CodeBlock') {
            const a = lineOf(node.from), b = lineOf(node.to);
            for (let i = a; i <= b; i++) {
              const l = doc.line(i);
              add(l.from, l.from, line('cm-wr-code' + (i === a ? ' cm-wr-code-first' : '') + (i === b ? ' cm-wr-code-last' : '')));
            }
            return false;
          } else if (n === 'Blockquote') {
            const a = lineOf(node.from), b = lineOf(node.to);
            for (let i = a; i <= b; i++) add(doc.line(i).from, doc.line(i).from, line('cm-wr-quote'));
          } else if (n === 'QuoteMark') {
            if (!source && !on) add(node.from, doc.sliceString(node.to, node.to + 1) === ' ' ? node.to + 1 : node.to, hide);
          } else if (n === 'ListMark') {
            const item = node.node.parent, mark = doc.sliceString(node.from, node.to);
            const task = item?.getChild('Task');
            if (source || on) return;
            if (task && /^[-*+]$/.test(mark)) add(node.from, Math.min(node.to + 1, task.from), hide);   // the box stands for the bullet
            else if (/^[-*+]$/.test(mark)) add(node.from, node.to, Decoration.replace({widget: new Bullet()}));
          } else if (n === 'TaskMarker') {
            const on2 = /x/i.test(doc.sliceString(node.from, node.to));
            if (!source && !near(state, node.from, node.to)) add(node.from, node.to, Decoration.replace({widget: new Box(on2, node.from)}));
            if (on2) { const task = node.node.parent; if (task && node.to + 1 < task.to) add(node.to + 1, task.to, Decoration.mark({class: 'cm-wr-done'})) }
          } else if (n === 'HorizontalRule') {
            if (!source && !on) add(node.from, node.to, Decoration.replace({widget: new Rule()}));
          } else if (n === 'Link') {
            // [words](address): show the words as a link; the marks and address come back where the caret is.
            // [[a link]] also parses as a Link; those are drawn below
            if (doc.sliceString(node.from - 1, node.from) === '[' || doc.sliceString(node.from, node.from + 2) === '[[') return false;
            const marks2 = node.node.getChildren('LinkMark'), url = node.node.getChild('URL');
            if (!source && marks2.length >= 2 && !near(state, node.from, node.to)) {
              const textTo = marks2[1].from;
              add(node.from, marks2[0].to, hide);
              add(marks2[0].to, textTo, Decoration.mark({class: 'cm-wr-link', attributes: {'data-url': url ? doc.sliceString(url.from, url.to) : ''}}));
              add(textTo, node.to, hide);
            }
            return false;
          } else if (n === 'Table') {
            return false;                    // drawn by tableField
          }
        }});
        // [[links]]: the title shows; [[ id| and ]] come back where the caret is
        const text = doc.sliceString(from, to);
        for (const m of text.matchAll(WIKI)) {
          const a = from + m.index, b = a + m[0].length;
          if (inCode(state, a)) continue;
          const ref = m[1].trim(), found = cfg.resolve?.(ref);
          const cls = 'cm-wr-link' + (found ? '' : ' cm-wr-missing');
          const attrs = found ? {'data-doc': found.id, title: found.title} : {'data-missing': ref, title: 'Nothing called “' + ref + '” yet: press to start it'};
          const label = m[2] != null ? a + 2 + m[1].length + 1 : a + 2;
          if (source) { add(a + 2, b - 2, Decoration.mark({class: cls, attributes: attrs})); continue }
          if (near(state, a, b)) {
            if (label > a + 2) add(a + 2, label, hide);                     // [[ and ]] show; the id does not
            add(label, b - 2, Decoration.mark({class: cls, attributes: attrs}));
            continue;
          }
          if (m[2] != null && !m[2].trim()) { add(a, b, Decoration.replace({widget: new LinkWord(found?.title || ref, cls, attrs)})); continue }
          add(a, label, hide);
          add(label, b - 2, Decoration.mark({class: cls, attributes: attrs}));
          add(b - 2, b, hide);
        }
      }
      return Decoration.set(marks, true);
    }
  }, {decorations: v => v.decorations});
}
class LinkWord extends WidgetType {
  constructor(word, cls, attrs) { super(); this.word = word; this.cls = cls; this.attrs = attrs }
  eq(o) { return o.word === this.word && o.cls === this.cls }
  toDOM() { const s = document.createElement('span'); s.className = this.cls; s.textContent = this.word; for (const [k, v] of Object.entries(this.attrs)) s.setAttribute(k, v); return s }
  ignoreEvent() { return false }
}
function inCode(state, pos) {
  for (let n = syntaxTree(state).resolveInner(pos, 1); n; n = n.parent)
    if (n.name === 'InlineCode' || n.name === 'FencedCode' || n.name === 'CodeBlock') return true;
  return false;
}

// Tables are drawn as tables (a block, so from a state field) until the caret or a selection enters them
class TableWidget extends WidgetType {
  constructor(src, from, draw) { super(); this.src = src; this.from = from; this.draw = draw }
  eq(o) { return o.src === this.src && o.from === this.from }
  toDOM(view) {
    const box = document.createElement('div'); box.className = 'cm-wr-table';
    try { const el = this.draw?.(this.src); if (el) box.append(el); else box.textContent = this.src } catch { box.textContent = this.src }
    box.addEventListener('mousedown', e => {
      if (e.target.closest('a,[data-doc],[data-url],[data-missing]')) return;
      e.preventDefault();
      view.dispatch({selection: {anchor: this.from}, scrollIntoView: false}); view.focus();
    });
    return box;
  }
  ignoreEvent(e) { return e.type !== 'mousedown' }
}
function tables(state, draw) {
  if (state.field(sourceField, false)) return Decoration.none;
  const b = new RangeSetBuilder(), tree = ensureSyntaxTree(state, state.doc.length, 200) || syntaxTree(state);
  tree.iterate({enter: node => {
    if (node.name !== 'Table') return;
    const from = state.doc.lineAt(node.from).from, to = state.doc.lineAt(node.to).to;
    if (!near(state, from, to)) b.add(from, to, Decoration.replace({widget: new TableWidget(state.sliceDoc(from, to), from, draw), block: true}));
    return false;
  }});
  return b.finish();
}
const SourceMode = StateEffect.define(), Redraw = StateEffect.define();
// the first parse may finish after the table field was made: draw once more on the next frame
const redrawSoon = ViewPlugin.fromClass(class {
  constructor(view) { requestAnimationFrame(() => { if (view.dom.isConnected || true) try { view.dispatch({effects: Redraw.of(null)}) } catch {} }) }
});
const sourceField = StateField.define({
  create: () => false,
  update: (v, tr) => { for (const e of tr.effects) if (e.is(SourceMode)) v = e.value; return v },
});
function tableField(draw) {
  return StateField.define({
    create: s => tables(s, draw),
    update: (deco, tr) => (tr.docChanged || tr.selection || tr.effects.some(e => e.is(SourceMode) || e.is(Redraw)) || syntaxTree(tr.startState) !== syntaxTree(tr.state)) ? tables(tr.state, draw) : deco,
    provide: f => EditorView.decorations.from(f),
  });
}

// ---- comments: marks on the words they are about, kept in place as the text changes ---------------------------------
const SetComments = StateEffect.define(), HotComment = StateEffect.define();
const commentField = StateField.define({
  create: () => ({list: [], hot: ''}),
  update(v, tr) {
    let list = v.list, hot = v.hot;
    if (tr.docChanged) list = list.map(c => ({...c, from: tr.changes.mapPos(c.from, 1), to: tr.changes.mapPos(c.to, -1)})).filter(c => c.to > c.from);
    for (const e of tr.effects) { if (e.is(SetComments)) list = e.value; if (e.is(HotComment)) hot = e.value }
    return list === v.list && hot === v.hot ? v : {list, hot};
  },
  provide: f => EditorView.decorations.from(f, v => Decoration.set(v.list.map(c =>
    Decoration.mark({class: 'cm-wr-comment' + (c.id === v.hot ? ' cm-wr-hot' : ''), attributes: {'data-comment': c.id}}).range(c.from, c.to)), true)),
});

// ---- keys -----------------------------------------------------------------------------------------------------------
function wrapWith(mark) {
  return view => {
    const {state} = view;
    view.dispatch(state.changeByRange(r => {
      const before = state.sliceDoc(r.from - mark.length, r.from), after = state.sliceDoc(r.to, r.to + mark.length);
      if (before === mark && after === mark)     // already marked: take the marks away
        return {changes: [{from: r.from - mark.length, to: r.from}, {from: r.to, to: r.to + mark.length}],
                range: EditorSelection.range(r.from - mark.length, r.to - mark.length)};
      return {changes: [{from: r.from, insert: mark}, {from: r.to, insert: mark}],
              range: EditorSelection.range(r.from + mark.length, r.to + mark.length)};
    }), {userEvent: 'input.format'});
    return true;
  };
}
function inList(state) {
  const n = syntaxTree(state).resolveInner(state.selection.main.head, -1);
  for (let x = n; x; x = x.parent) if (x.name === 'ListItem') return true;
  return /^\s*([-*+]|\d+[.)])\s/.test(state.doc.lineAt(state.selection.main.head).text);
}

// ---- the editor -----------------------------------------------------------------------------------------------------
export function createEditor(cfg) {
  const editable = new Compartment(), links = new Compartment();
  const view = new EditorView({
    state: EditorState.create({
      doc: cfg.doc || '',
      extensions: [
        highlightSpecialChars(), history({newGroupDelay: 600}), drawSelection(), dropCursor(),
        EditorView.lineWrapping, indentUnit.of('  '), EditorState.tabSize.of(4),
        markdown({base: markdownLanguage, addKeymap: true, completeHTMLTags: false}),
        syntaxHighlighting(look), theme,
        sourceField, preview(cfg), tableField(cfg.drawTable), commentField, redrawSoon,
        search({top: true}), highlightSelectionMatches({minSelectionLength: 3}),
        autocompletion({override: [ctx => linkCompletions(ctx, cfg)], icons: false, activateOnTyping: true, closeOnBlur: true}),
        placeholder(cfg.placeholder || 'Start writing…'),
        EditorView.contentAttributes.of({spellcheck: 'true', autocorrect: 'on', autocapitalize: 'sentences', 'aria-label': cfg.label || 'Document'}),
        editable.of([EditorView.editable.of(!cfg.readonly), EditorState.readOnly.of(!!cfg.readonly)]),
        Prec.high(keymap.of([
          {key: 'Mod-b', run: wrapWith('**')},
          {key: 'Mod-i', run: wrapWith('*')},
          {key: 'Mod-Shift-x', run: wrapWith('~~')},
          {key: 'Mod-`', run: wrapWith('`')},
          {key: 'Mod-s', run: () => { cfg.onSave?.(); return true }, preventDefault: true},
          {key: 'Mod-e', run: () => { cfg.onToggleSource?.(); return true }, preventDefault: true},
          {key: 'Mod-f', run: openSearchPanel, preventDefault: true},
          {key: 'Tab', run: v => acceptCompletion(v) || (inList(v.state) ? indentMore(v) : insertTab(v))},   // Tab stays in the text, as in Obsidian
          {key: 'Shift-Tab', run: v => inList(v.state) ? indentLess(v) : false},
          {key: 'Escape', run: () => { cfg.onEscape?.(); return false }},
        ])),
        keymap.of([...completionKeymap, ...searchKeymap, ...historyKeymap, ...defaultKeymap]),
        EditorView.updateListener.of(u => cfg.onUpdate?.(u)),
        EditorView.domEventHandlers({
          mousedown: (e, v) => linkPress(e, v, cfg),
          click: (e, v) => { const c = e.target.closest?.('[data-comment]'); if (c) cfg.onCommentPress?.(c.dataset.comment, e); return false },
          contextmenu: (e, v) => cfg.onContextMenu?.(e, v) || false,
          blur: () => { cfg.onBlur?.(); return false },
        }),
      ],
    }),
  });
  return {
    view,
    setSource: on => view.dispatch({effects: SourceMode.of(!!on)}),
    source: () => view.state.field(sourceField),
    relink: () => view.dispatch({effects: LinkMeta.of(null)}),
    setComments: list => view.dispatch({effects: SetComments.of(list)}),
    hotComment: id => view.dispatch({effects: HotComment.of(id || '')}),
    comments: () => view.state.field(commentField).list,
    setReadonly: ro => view.dispatch({effects: editable.reconfigure([EditorView.editable.of(!ro), EditorState.readOnly.of(!!ro)])}),
  };
}

// A press on a drawn link opens it; with the caret already in it (marks showing), it only places the caret
function linkPress(e, view, cfg) {
  if (e.button !== 0) return false;
  const a = e.target.closest?.('.cm-wr-link[data-doc], .cm-wr-link[data-missing], .cm-wr-link[data-url]:not([data-url=""])');
  if (!a) return false;
  const pos = view.posAtDOM(a);
  const revealed = near(view.state, pos, pos + (a.textContent || '').length) && !(e.ctrlKey || e.metaKey);
  if (revealed) return false;
  e.preventDefault();
  cfg.onLink?.({doc: a.dataset.doc, missing: a.dataset.missing, url: a.dataset.url}, e);
  return true;
}

// [[ picks a document by its title
function linkCompletions(ctx, cfg) {
  const m = ctx.matchBefore(/\[\[[^\]\n|]{0,60}/);
  if (!m) return null;
  const q = m.text.slice(2).toLowerCase();
  const docs = (cfg.documents?.() || []).filter(d => !q || d.title.toLowerCase().includes(q) || d.id === q).slice(0, 30);
  const close = ctx.state.sliceDoc(ctx.pos, ctx.pos + 2) === ']]';
  return {
    from: m.from + 2, filter: false,
    options: docs.map(d => ({label: d.title, detail: d.detail || '', apply: (view, c, from, to) => {
      const ins = d.id + '|' + d.title + ']]';
      view.dispatch({changes: {from, to: to + (close ? 2 : 0), insert: ins}, selection: {anchor: from + ins.length}, userEvent: 'input.complete'});
    }})),
  };
}

// ---- helpers the page uses to keep its copy in step with the world ---------------------------------------------------
// The change from text a to text b, as one replacement (what the world's text did meanwhile)
export function diff(a, b) {
  let s = 0; const m = Math.min(a.length, b.length);
  while (s < m && a.charCodeAt(s) === b.charCodeAt(s)) s++;
  let e = 0;
  while (e < m - s && a.charCodeAt(a.length - 1 - e) === b.charCodeAt(b.length - 1 - e)) e++;
  return ChangeSet.of(s === a.length && s === b.length ? [] : [{from: s, to: a.length - e, insert: b.slice(s, b.length - e)}], a.length);
}
// [from, to, inserted] spans of a change set, in UTF-16 positions into the text before it (what `edit` takes)
export function spans(changes) {
  const out = [];
  changes.iterChanges((fromA, toA, fromB, toB, ins) => out.push([fromA, toA, ins.toString()]));
  return out;
}
// The same fingerprint as the kernel's bodies.fingerprint: length and FNV-1a over UTF-16 code units
export function fingerprint(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0 }
  return text.length + ':' + h.toString(16).padStart(8, '0');
}
export {ChangeSet, Text, Transaction, EditorSelection, EditorView, undo, redo, selectAll, startCompletion, openSearchPanel};
