(async () => {   // a10486 test: wait (at most 15 s) until the draft says a capture is coming; how long that took
  const t0 = Date.now();
  while (Date.now() - t0 < 15000) {
    const c = document.querySelector('[data-key$="/coming"]');
    if (c && !c.hidden && c.offsetHeight) return `"Attaching capture…" shown ${Date.now() - t0} ms after asking`;
    await new Promise(r => setTimeout(r, 50));
  }
  return "NOT SHOWN in 15 s";
})()
