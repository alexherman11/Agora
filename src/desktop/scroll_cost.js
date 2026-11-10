// scroll_cost.js (a5736): frame times while the chat feed scrolls 40 px a frame for 6 s, and the long tasks meanwhile.
// Used as a screen.py `js` step (paste the file's text); returns {frames, p50, p95, max, over33, longtasks}.
new Promise(r => {
  const el = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/feed'));
  if (!el) return r('no feed');
  el.scrollTop = 0;
  const lt = [];
  new PerformanceObserver(l => l.getEntries().forEach(e => lt.push(Math.round(e.duration)))).observe({type: 'longtask'});
  const fr = []; const t0 = performance.now(); let last = t0;
  const f = () => {
    const now = performance.now(); fr.push(now - last); last = now;
    el.scrollTop += 40; if (el.scrollTop + el.clientHeight >= el.scrollHeight - 2) el.scrollTop = 0;
    if (now - t0 < 6000) return requestAnimationFrame(f);
    fr.sort((a, b) => a - b);
    r({frames: fr.length, p50: +fr[fr.length >> 1].toFixed(1), p95: +fr[Math.floor(fr.length * .95)].toFixed(1),
       max: Math.round(fr[fr.length - 1]), over33: fr.filter(x => x > 33).length, longtasks: lt});
  };
  requestAnimationFrame(f);
})
