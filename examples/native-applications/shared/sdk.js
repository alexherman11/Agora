/* Agora application protocol: one bound subject, per-view state, explicit flush. */
(() => {
  'use strict';
  const pending = new Map(), changes = new Set(), flushers = new Set();
  let context, resolveReady;
  const ready = new Promise(resolve => { resolveReady = resolve; });
  function send(value) { parent.postMessage({agoraApp: true, ...value}, '*'); }
  async function request(method, args = {}) {
    await ready;
    return new Promise((resolve, reject) => {
      const id = crypto.randomUUID();
      const timer = setTimeout(() => { pending.delete(id); reject(new Error('Application request timed out. Your draft remains here.')); }, 15000);
      pending.set(id, {resolve, reject, timer});
      send({type: 'request', id, lease: context.lease, method, args});
    });
  }
  window.addEventListener('message', async event => {
    if (event.source !== parent || event.data?.agoraApp !== true) return;
    const value = event.data;
    if (value.type === 'init' && !context) { context = Object.freeze(value.context); resolveReady(context); }
    if (value.type === 'response') {
      const task = pending.get(value.id);
      if (!task) return;
      clearTimeout(task.timer); pending.delete(value.id);
      if (value.error) task.reject(new Error(value.error)); else task.resolve(value.result);
    }
    if (value.type === 'changed') for (const handler of changes) handler();
    if (value.type === 'flush') {
      try { await ready; for (const handler of flushers) await handler(); send({type: 'flushed', id: value.id, lease: context.lease, ready: true}); }
      catch (error) { send({type: 'flushed', id: value.id, lease: context?.lease, ready: false, error: error.message}); }
    }
  });
  window.AgoraApp = Object.freeze({ready, request,
    onChange(handler) { changes.add(handler); return () => changes.delete(handler); },
    onFlush(handler) { flushers.add(handler); return () => flushers.delete(handler); }
  });
  send({type: 'ready'});
})();
