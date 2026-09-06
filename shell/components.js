"use strict";
// Generated source never executes in this page. This renderer accepts validated data only.
window.AgoraComponents = function (host, command, notice, select, onChange) {
  let frame = null, nodes = new Map(), elements = new Map(), queue = [], running = false;
  let gesture = null, stopped = false, epoch = 0;
  const viewport = () => ({width: Math.max(1, host.clientWidth || host.parentElement.clientWidth), height: Math.max(1, host.clientHeight || host.parentElement.clientHeight - 120)});
  function draw(tree) {
    const nextNodes = new Map(), nextElements = new Map();
    function build(node) {
      let element = elements.get(node.id);
      if (!element || element.tagName.toLowerCase() !== node.tag) element = document.createElement(node.tag);
      element.dataset.componentNode = node.id;
      nextNodes.set(node.id, node); nextElements.set(node.id, element);
      element.style.cssText = "";
      for (const [key, value] of Object.entries(node.style || {})) element.style[key] = value;
      if (node.label) element.setAttribute("aria-label", node.label);
      else element.removeAttribute("aria-label");
      if (node.value !== undefined && element.value !== node.value) element.value = node.value;
      const children = [];
      if (node.text) children.push(document.createTextNode(node.text));
      for (const child of node.children || []) children.push(build(child));
      element.replaceChildren(...children);
      return element;
    }
    const focused = document.activeElement?.dataset.componentNode;
    const selectionStart = document.activeElement?.selectionStart;
    const root = build(tree);
    if (host.firstElementChild !== root) host.replaceChildren(root);
    nodes = nextNodes; elements = nextElements;
    if (focused && elements.has(focused)) {
      const input = elements.get(focused); input.focus({preventScroll:true});
      if (typeof selectionStart === "number" && input.setSelectionRange) input.setSelectionRange(selectionStart, selectionStart);
    }
  }
  function show(next) {
    const changed = !frame || frame.entity !== next.entity || frame.revision !== next.revision || frame.candidate !== next.candidate;
    if (changed) { epoch++; queue = []; gesture = null; stopped = false; elements = new Map(); }
    frame = next;
    if (!stopped) draw(frame.tree);
  }
  async function drain() {
    if (running || stopped) return;
    running = true;
    let failed = false, committed = false;
    try {
      while (queue.length && !stopped) {
        const event = queue.shift(), serial = epoch;
        const args = {event, fingerprint:frame.fingerprint, local:frame.local, viewport:viewport()};
        let name;
        if (frame.candidate) { name = "candidate_event"; args.candidate = frame.candidate; }
        else { name = "component_event"; args.entity = frame.entity; args.revision = frame.revision; }
        const next = (await command(name, args)).result;
        if (serial !== epoch) break;
        frame = {...frame, ...next};
        if (!frame.candidate && (next.effects?.length || next.state !== undefined)) committed = true;
        if (frame.selected) select(frame.selected);
        if (!stopped) draw(frame.tree);
      }
    } catch (error) {
      queue = []; gesture = null; frame.local = {}; notice(error.message); failed = true;
    } finally { running = false; }
    if (failed || committed) onChange();
  }
  function input(event) {
    if (!frame || stopped) return;
    let id = event.target.closest?.("[data-component-node]")?.dataset.componentNode;
    let target = event.target.closest?.("[data-component-node]");
    while (target && target !== host && !nodes.get(id)?.on?.[event.type]) {
      target = target.parentElement?.closest("[data-component-node]");
      id = target?.dataset.componentNode;
    }
    if (gesture && ["pointermove", "pointerup", "pointercancel"].includes(event.type)) id = gesture.node;
    const node = nodes.get(id);
    if (!node?.on?.[event.type]) return;
    if (event.type.startsWith("pointer")) event.preventDefault();
    if (event.type === "pointerdown") {
      gesture = {node:id, pointer:event.pointerId}; host.setPointerCapture(event.pointerId);
      if (node.entity) select(node.entity, node.text);
    }
    if (["pointerup", "pointercancel"].includes(event.type)) {
      if (host.hasPointerCapture(event.pointerId)) host.releasePointerCapture(event.pointerId);
      gesture = null;
    }
    const rect = host.getBoundingClientRect();
    const message = {node:id, type:event.type};
    if (typeof event.clientX === "number") { message.x = event.clientX - rect.left; message.y = event.clientY - rect.top; message.button = event.button; }
    if (event.key) message.key = event.key;
    if (event.target.value !== undefined) message.value = event.target.value;
    if (event.type === "pointermove" && queue.at(-1)?.type === "pointermove") queue[queue.length - 1] = message;
    else if (queue.length < 64) queue.push(message);
    drain();
  }
  for (const type of ["click","pointerdown","pointermove","pointerup","pointercancel","keydown","input","change"]) host.addEventListener(type, input);
  return {show, viewport, snapshot:() => frame, busy:() => running || !!gesture,
    local:() => frame?.local || {}, candidate:() => frame?.candidate,
    stop:() => { stopped = true; epoch++; queue = []; gesture = null; },
    reset:() => { frame = null; stopped = false; epoch++; queue = []; gesture = null; },
  };
};
