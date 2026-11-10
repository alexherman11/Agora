// Generic cross-lens receivers. Policy remains in each receiver's world gesture.
// A drag snapshots receivers at pickup: repainting cannot grant a new destination
// or silently substitute a newer fence. Also used by specialised carry adapters.
(function (root) {
  "use strict";
  function accepts(receiver, part) {
    return (receiver?._drops || []).some(a => a.part === part || a.part === "any");
  }
  function snapshot(paint, part) {
    return new Map([...paint.querySelectorAll("[data-drop]")]
      .filter(r => accepts(r, part))
      .map(r => [r.dataset.key, { fence: r._n.fence,
        acts: (r._drops || []).filter(a => a.part === part || a.part === "any")
          .map(a => ({ ...a })) }]));
  }
  function plan(receiver, source, seen, pointer) {
    const saved = seen.get(receiver?.dataset?.key);
    if (!saved || !accepts(receiver, source.part)) return null;
    const own = receiver.contains(source.el);
    const acts = saved.acts.filter(a => !own || a.side === "left" || a.side === "right");
    if (!acts.length) return null;
    const b = receiver.getBoundingClientRect();
    if (!(b.width > 0 && b.height > 0)) return null;
    const fx = pointer ? (pointer.clientX - b.left) / b.width : .5;
    const fy = pointer ? (pointer.clientY - b.top) / b.height : .5;
    const distance = { left: fx, right: 1 - fx, top: fy, bottom: 1 - fy };
    const sides = acts.filter(a => a.side).sort((a, b) => distance[a.side] - distance[b.side]);
    // A named receiver wins over the general receiver at the same location.
    const choices = acts.some(a => a.part === source.part) ?
      acts.filter(a => a.part === source.part) : acts;
    const edges = sides.filter(a => choices.includes(a));
    const act = edges.find(a => distance[a.side] < 1 / 3) ||
      choices.find(a => !a.side) || edges[0];
    if (!act) return null;
    const h = { left: [0, 0, .5, 1], right: [.5, 0, .5, 1],
      top: [0, 0, 1, .5], bottom: [0, .5, 1, .5] }[act.side] || [0, 0, 1, 1];
    return { key: receiver.dataset.key, fence: saved.fence, act,
      box: [b.left + h[0] * b.width, b.top + h[1] * b.height, h[2] * b.width, h[3] * b.height] };
  }
  function at(elements, source, seen, pointer) {
    // elementsFromPoint is front-to-back. A child receiver wins over its parent.
    for (const receiver of elements) {
      if (!receiver.dataset?.drop) continue;
      const p = plan(receiver, source, seen, pointer);
      if (p) return { receiver, ...p };
    }
    return null;
  }
  function submit(send, target, sourceFence) {
    if (!target || !sourceFence) return Promise.resolve(null);
    return send({ key: target.key, fence: target.fence }, target.act.line,
      undefined, { carried: sourceFence, receiver: target.fence });
  }
  function session(paint, source, send, exclude, doc = document) {
    const seen = snapshot(paint, source.n.part);
    let target = null, box = null;
    const cancel = () => { box?.remove(); box = null; target = null; };
    return {
      move(pointer) {
        const elements = doc.elementsFromPoint(pointer.clientX, pointer.clientY)
          .filter(el => !exclude?.contains(el));
        target = at(elements, { el: source.el, part: source.n.part }, seen, pointer);
        if (!target) { box?.remove(); box = null; return null; }
        if (!box) {
          box = doc.createElement("div"); box.className = "landing-box";
          Object.assign(box.style, { position: "fixed", pointerEvents: "none", zIndex: "45", transition: "none" });
          doc.body.appendChild(box);
        }
        ["left", "top", "width", "height"].forEach((k, i) => { box.style[k] = target.box[i] + "px"; });
        return target;
      },
      get target() { return target; },
      async release() {
        const chosen = target;
        try { return await submit(send, chosen, source.n.fence); }
        finally { cancel(); }
      },
      cancel
    };
  }
  // The native WM and cards ask the same engine. Only geometry crosses this
  // read-only seam; submit() remains the sole, fenced world mutation.
  function drift(source, selector = '[data-carry]', request = body =>
    fetch('/api/tiling', {method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)}).then(r => {if(!r.ok)throw Error('tiling preview unavailable');return r.json()})) {
    const rect = el => {const r=el.getBoundingClientRect();return [r.x,r.y,r.width,r.height]};
    const start=rect(source), original=new Map(), animations=new Map(), aims=new Map();
    let closed=false, version=0, queued=null, running=null, answer=null, duration=0;
    function shift(el, dy) {
      if(aims.get(el)===dy)return;
      aims.set(el,dy);
      if(!original.has(el))original.set(el,{box:rect(el),transform:el.style.transform});
      const saved=original.get(el), old=el.getBoundingClientRect();
      const previous=animations.get(el);previous?.cancel();
      el.style.transform=dy?`translateY(${dy}px)`:saved.transform;
      const next=el.getBoundingClientRect(), delta=old.y-next.y;
      if(Math.abs(delta)>.1){
        const a=el.animate([{transform:`translateY(${dy+delta}px)`},
          {transform:el.style.transform||'none'}],
          {duration,easing:'cubic-bezier(.2,0,0,1)'});
        animations.set(el,a);
      }
    }
    async function drain() {
      while(queued&&!closed){
        const job=queued;queued=null;
        try{
          const out=await request(job.body);
          if(closed||job.version!==version)continue;
          answer=out;
          duration=out.motion_ms;
          for(const el of original.keys())if(!job.cards.includes(el)||!out.allowed)shift(el,0);
          if(out.allowed)job.cards.forEach((el,i)=>shift(el,out.placements[i][1]-job.body.neighbours[i][1]));
          job.paint?.(out);
        }catch{if(job.version===version){answer=null;for(const el of original.keys())shift(el,0);job.paint?.({allowed:false})}}
      }
      running=null;
    }
    return {
      move(receiver, pointer, paint) {
        version++;answer=null;
        if(!receiver||!pointer){queued=null;for(const el of original.keys())shift(el,0);return;}
        const cards=[...receiver.querySelectorAll(selector)].filter(el=>el!==source&&!source.contains(el)&&el.getBoundingClientRect().height>0);
        for(const el of cards)if(!original.has(el))original.set(el,{box:rect(el),transform:el.style.transform});
        const order=el=>el._tilingOrder||el._n?.tiling_order;
        const sorted=order(source)&&cards.every(el=>order(el));
        const under=cards.findIndex(el=>pointer.clientY<original.get(el).box[1]+original.get(el).box[3]);
        const displaced=sorted?cards:under<0?[]:cards.slice(under);
        const container=cards[0]?.parentElement||receiver.querySelector?.('[data-tiling-list]')||receiver;
        const r=cards.length?original.get(cards[0]).box:rect(container);
        const gap=cards.length>1?Math.max(0,original.get(cards[1]).box[1]-r[1]-r[3]):
          parseFloat(getComputedStyle(container).rowGap)||0;
        const y=displaced.length?original.get(displaced[0]).box[1]:
          cards.length?original.get(cards.at(-1)).box[1]+original.get(cards.at(-1)).box[3]+gap:r[1];
        const body={start,moving:[start[0]+pointer.clientX-pointer.startX,start[1]+pointer.clientY-pointer.startY,start[2],start[3]],
          landing:[r[0],y,r[2],start[3]],neighbours:displaced.map(el=>original.get(el).box),gap};
        if(sorted)body.orders=[order(source),...cards.map(order)];
        queued={version,body,cards:displaced,paint};
        if(!running)running=drain();
      },
      async flush(){while(running)await running;return answer},
      get duration(){return duration},
      close(immediate=false){
        closed=true;version++;queued=null;
        for(const [el,saved] of original){
          if(immediate){animations.get(el)?.cancel();el.style.transform=saved.transform;}
          else shift(el,0);
        }
      }
    };
  }
  const api = { accepts, snapshot, plan, at, submit, session, drift };
  if (typeof module !== "undefined") module.exports = api;
  else root.CarryTargets = api;
})(typeof window === "undefined" ? globalThis : window);
