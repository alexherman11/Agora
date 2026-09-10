/* A shared text-editor contract. Extensions consume this API, never another app's DOM. */
(() => {
  'use strict';
  const textOf = object => object.facets['core.text']?.text || '';
  const titleOf = object => object.facets['core.title']?.text || '';
  const signature = object => JSON.stringify([titleOf(object), textOf(object)]);
  const digest = async text => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(x => x.toString(16).padStart(2, '0')).join('');
  const node = (tag, cls, text) => { const el = document.createElement(tag); if (cls) el.className = cls; if (text !== undefined) el.textContent = text; return el; };
  class ObjectEditor {
    constructor(root, options = {}) {
      this.root = root; this.options = options; this.listeners = new Set(); this.extensions = {};
      this.dirty = false; this.conflict = ''; this.saving = null; this.stateQueue = Promise.resolve(); this.refreshing = false;
      this.root.className = 'object-editor ' + (options.preview ? 'document-editor' : 'note-editor');
      const toolbar = node('div', 'editor-toolbar');
      this.title = node('input', 'editor-title'); this.title.setAttribute('aria-label', 'Title'); this.title.maxLength = 500;
      this.saveButton = node('button', 'save', 'Save'); this.saveButton.type = 'button'; this.saveButton.onclick = () => this.save().catch(() => {});
      this.format = node('select', 'format'); this.format.setAttribute('aria-label', 'Text format');
      this.format.append(new Option('Plain text', 'plain'), new Option('Markdown', 'markdown'));
      this.format.onchange = async () => { try { await this.save(); await this.updateFacet('text.format', {kind: this.format.value}); } catch (error) { this.showError(error); } };
      toolbar.append(this.title, this.saveButton); if (options.preview) toolbar.append(this.format);
      const body = node('div', 'editor-body');
      this.input = node('textarea', 'editor-input'); this.input.setAttribute('aria-label', 'Text'); this.input.maxLength = 100000; this.input.spellcheck = true;
      body.append(this.input);
      if (options.preview) { this.preview = node('article', 'editor-preview'); this.preview.setAttribute('aria-label', 'Preview'); body.append(this.preview); }
      this.status = node('div', 'editor-status', 'Opening…'); this.status.setAttribute('role', 'status');
      this.error = node('div', 'editor-error'); this.error.hidden = true; this.error.setAttribute('role', 'alert');
      this.extensionRoot = node('div', 'editor-extensions');
      this.root.append(toolbar, body, this.status, this.error, this.extensionRoot);
      for (const field of [this.title, this.input]) {
        field.disabled = true;
        field.addEventListener('input', () => this.edited());
      }
      this.input.addEventListener('select', () => this.scheduleState());
      this.input.addEventListener('scroll', () => this.scheduleState(), {passive: true});
      this.root.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); this.save().catch(() => {}); }
        if (options.preview && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b' && event.target === this.input) {
          event.preventDefault(); const a = this.input.selectionStart, b = this.input.selectionEnd;
          this.input.setRangeText('**' + (this.input.value.slice(a,b) || 'bold text') + '**', a, b, 'select'); this.edited();
        }
      });
      this.ready = this.initialize();
      AgoraApp.onChange(() => this.refresh());
      AgoraApp.onFlush(async () => { await this.ready; try { await this.save(); } catch (error) { if (!this.conflict) throw error; } await this.persistState(); });
      this.timer = setInterval(() => this.refresh(), 2500);
    }
    async initialize() {
      try {
        this.context = await AgoraApp.ready;
        const [object, retained] = await Promise.all([AgoraApp.request('read'), AgoraApp.request('state.get')]);
        this.object = object; this.base = object;
        const state = retained.state.editor;
        this.extensions = retained.state.extensions || {};
        this.title.value = titleOf(object); this.input.value = textOf(object);
        if (state?.dirty && state.subject === object.id) {
          this.title.value = state.title; this.input.value = state.text; this.dirty = true;
          this.base = {...object, facets: {...object.facets, 'core.title': {text: state.baseTitle}, 'core.text': {text: state.baseText}}};
          if (signature(this.base) !== signature(object)) this.conflict = 'This object changed while the view was closed. Your draft is retained.';
        }
        if (state?.subject === object.id) { this.input.setSelectionRange(state.start || 0, state.end || 0); this.input.scrollTop = state.scroll || 0; }
        this.title.disabled = false; this.input.disabled = false; this.loaded = true;
        this.render(); this.emit();
        if (this.dirty && !this.conflict) this.saveTimer = setTimeout(() => this.save().catch(() => {}), 600);
        return this;
      } catch (error) { this.showError(error); throw error; }
    }
    snapshot() { return {object: this.object, subject: this.context?.subject, dirty: this.dirty, text: this.input.value, title: this.title.value}; }
    subscribe(handler) { this.listeners.add(handler); if (this.loaded) handler(this.snapshot()); return () => this.listeners.delete(handler); }
    emit() { for (const handler of this.listeners) handler(this.snapshot()); }
    addPanel(label) { const details = node('details', 'extension-panel'); details.append(node('summary', '', label)); const content = node('div', 'extension-content'); details.append(content); this.extensionRoot.append(details); return {details, content}; }
    extensionState(key, value) { if (arguments.length === 2) { this.extensions[key] = value; this.scheduleState(); } return this.extensions[key]; }
    scheduleState() { if (!this.loaded) return; clearTimeout(this.stateTimer); this.stateTimer = setTimeout(() => this.persistState().catch(error => this.showError(error)), 150); }
    persistState() {
      clearTimeout(this.stateTimer);
      if (!this.loaded) return this.stateQueue;
      const state = {version: 1, editor: {subject: this.context.subject, dirty: this.dirty,
        title: this.title.value, text: this.input.value, baseTitle: titleOf(this.base), baseText: textOf(this.base),
        start: this.input.selectionStart, end: this.input.selectionEnd, scroll: this.input.scrollTop}, extensions: structuredClone(this.extensions)};
      this.stateQueue = this.stateQueue.catch(() => {}).then(() => AgoraApp.request('state.set', {state}));
      return this.stateQueue;
    }
    edited() { this.dirty = true; clearTimeout(this.saveTimer); this.scheduleState(); this.render(); this.emit(); if (!this.conflict) this.saveTimer = setTimeout(() => this.save().catch(() => {}), 550); }
    async save() {
      await this.ready; clearTimeout(this.saveTimer);
      if (this.saving) { await this.saving; if (this.dirty) return this.save(); return; }
      if (!this.dirty) return;
      if (this.conflict) throw new Error(this.conflict);
      const text = this.input.value, title = this.title.value, baseSignature = signature(this.base);
      this.saving = (async () => {
        const latest = await AgoraApp.request('read');
        if (signature(latest) !== baseSignature) throw new Error('Conflict: this text changed in another view. Your draft is retained.');
        const result = await AgoraApp.request('transact', {changes: [{id: latest.id, expected_revision: latest.revision,
          facets: {'core.title': {text: title}, 'core.text': {text}}}]});
        this.object = result.items[0]; this.base = this.object;
        this.dirty = this.input.value !== text || this.title.value !== title;
        this.conflict = ''; await this.persistState(); this.emit();
      })().catch(async error => { this.conflict = error.message; await this.persistState().catch(() => {}); throw error; })
        .finally(() => { this.saving = null; this.render(); });
      this.render(); await this.saving; if (this.dirty) return this.save();
    }
    async refresh() {
      if (!this.loaded || this.refreshing) return;
      this.refreshing = true;
      try {
        const latest = await AgoraApp.request('read');
        if (latest.revision < this.object.revision) return;
        this.object = latest;
        if (!this.dirty && !this.saving) {
          this.base = latest;
          const start = this.input.selectionStart, end = this.input.selectionEnd, scroll = this.input.scrollTop;
          if (this.title.value !== titleOf(latest)) this.title.value = titleOf(latest);
          if (this.input.value !== textOf(latest)) { this.input.value = textOf(latest); this.input.setSelectionRange(start,end); this.input.scrollTop = scroll; }
        }
        this.render(); this.emit();
      } catch (error) { this.showError(error); } finally { this.refreshing = false; }
    }
    async captureSelection() {
      const start = this.input.selectionStart, end = this.input.selectionEnd, text = this.input.value;
      if (start === end) throw new Error('Select some text first.');
      await this.save();
      if (text !== this.input.value || text !== textOf(this.base)) throw new Error('Selection changed during save. Select the text again.');
      return {subject: this.context.subject, revision: this.base.revision, start, end, quote: text.slice(start,end), text, text_hash: await digest(text)};
    }
    async updateFacet(name, value, expectedRevision) {
      await this.save();
      const object = this.object;
      const result = await AgoraApp.request('transact', {changes: [{id: object.id,
        expected_revision: expectedRevision ?? object.revision, facets: {[name]: value}}]});
      this.object = result.items[0]; this.base = this.object; this.render(); this.emit(); return this.object;
    }
    selectRange(start, end) { this.input.focus(); this.input.setSelectionRange(start,end); this.scheduleState(); }
    render() {
      const format = this.object?.facets['text.format']?.kind || 'plain';
      this.format.value = format;
      this.status.textContent = this.conflict ? 'Draft retained · conflict needs review' : this.saving ? 'Saving…' : this.dirty ? 'Saving soon…' : 'Saved · ' + (format === 'markdown' ? 'Markdown' : 'plain text');
      this.error.hidden = !this.conflict;
      if (this.conflict) {
        this.error.replaceChildren(node('p', '', this.conflict));
        const keep = node('button', '', 'Use my draft'); keep.onclick = async () => {
          try { this.base = await AgoraApp.request('read'); this.conflict = ''; this.dirty = true; await this.save(); } catch (error) { this.showError(error); }
        };
        const incoming = node('button', '', 'Use saved text'); incoming.onclick = async () => {
          this.object = await AgoraApp.request('read'); this.base = this.object; this.title.value = titleOf(this.object); this.input.value = textOf(this.object);
          this.dirty = false; this.conflict = ''; await this.persistState(); this.render(); this.emit();
        };
        this.error.append(keep, incoming);
      }
      if (this.preview) {
        if (format === 'markdown' && window.marked && window.DOMPurify) {
          const html = marked.parse(this.input.value, {async: false});
          this.preview.innerHTML = DOMPurify.sanitize(html, {ALLOWED_TAGS: ['p','br','strong','em','del','blockquote','pre','code','ul','ol','li','h1','h2','h3','h4','h5','h6','hr','a','table','thead','tbody','tr','th','td'], ALLOWED_ATTR: ['href','title']});
          for (const link of this.preview.querySelectorAll('a')) { link.removeAttribute('href'); link.title = 'Use the native link workflow to open external resources.'; }
        } else { this.preview.replaceChildren(node('pre', 'plain-preview', this.input.value)); }
      }
    }
    showError(error) { this.error.hidden = false; this.error.replaceChildren(node('p', '', error.message || String(error))); }
  }
  window.ObjectEditor = ObjectEditor;
  window.EditorUtilities = Object.freeze({node, digest});
})();
