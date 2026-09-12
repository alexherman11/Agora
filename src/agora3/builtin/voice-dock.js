/* Reserve footer geometry; the parent retains microphone and call controls. */
(() => {
  'use strict';
  const chat = document.getElementById('conversation');
  if (!chat || document.getElementById('chat-voice-footer')) return;
  const footer = document.createElement('div'); footer.id = 'chat-voice-footer';
  const slot = document.createElement('div'); slot.id = 'chat-voice-slot'; slot.setAttribute('aria-hidden', 'true');
  const progress = document.getElementById('chat-progress');
  footer.append(slot); if (progress) footer.append(progress); chat.append(footer);
  let pending = false, last = '';
  function publish() {
    pending = false;
    const r = slot.getBoundingClientRect(), visible = !!slot.getClientRects().length;
    const bounds = {x:r.x,y:r.y,width:r.width,height:r.height};
    const value = JSON.stringify({bounds,visible});
    if (last !== value) { last = value; parent.postMessage({agora:true,event:'voice-dock',bounds,visible}, '*'); }
  }
  function schedule() { if (!pending) { pending = true; requestAnimationFrame(publish); } }
  const size = new ResizeObserver(schedule); size.observe(slot); size.observe(footer);
  new MutationObserver(schedule).observe(document.body, {attributes:true,attributeFilter:['class']});
  window.addEventListener('resize', schedule);
  window.addEventListener('message', e => {
    if (e.source !== parent || !e.data?.agora) return;
    if (e.data.event === 'voice-dock-request') { last = ''; schedule(); }
    else if (e.data.event === 'voice-dock-height' && Number.isFinite(e.data.height)) {
      slot.style.height = Math.max(40, Math.min(112, e.data.height)) + 'px'; schedule();
    } else if (e.data.event === 'voice-show' && !document.body.classList.contains('chat-open')) {
      document.getElementById('chat-toggle')?.click();
    }
  });
  schedule();
})();
