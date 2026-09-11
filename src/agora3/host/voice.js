/* Protected microphone transport. Authored frames receive neither keys nor voice controls. */
(() => {
  const $ = id => document.getElementById(id);
  let client = crypto.randomUUID();
  const panel = $('voice-panel'), start = $('voice-start'), state = $('voice-state');
  let pc = null, stream = null, channel = null, active = false, ending = false;
  let muted = false, generation = 0, checking = false, timer = null, connectedTimer = null;
  const seen = new Set();
  function micOff() { stream?.getTracks().forEach(track => track.stop()); stream = null; }
  function release() {
    micOff(); clearTimeout(timer); clearTimeout(connectedTimer);
    channel?.close(); pc?.close(); channel = pc = null;
    $('voice-audio').srcObject = null;
    active = ending = false; start.disabled = false; start.setAttribute('aria-pressed', 'false');
    $('voice-mute').disabled = true;
  }
  function send(type) { if (channel?.readyState === 'open') channel.send(JSON.stringify({type, event_id: crypto.randomUUID()})); }
  async function end(message = 'Ending voice…') {
    if (!active || ending) return;
    ending = true; generation++; micOff(); clearTimeout(connectedTimer);
    $('voice-mute').disabled = true; state.textContent = message;
    send('session.close');
    timer = setTimeout(() => { release(); state.textContent = 'Voice disconnected. Checking server closure…'; }, 8000);
    try { await rpc('host.voice.end', {client}); }
    catch { state.textContent = 'Microphone off. Server connection lost; automatic call cleanup is pending.'; }
  }
  function event(value) {
    if (value.event_id) { if (seen.has(value.event_id)) return; seen.add(value.event_id); if (seen.size > 2000) seen.delete(seen.values().next().value); }
    if (value.type === 'session.started' && !ending) {
      clearTimeout(connectedTimer); state.textContent = 'Listening · GPT Live 1'; $('voice-mute').disabled = false;
      frame.contentWindow.postMessage({agora:true,event:'voice-active'}, '*');
    } else if (value.type === 'session.closed') {
      release(); state.textContent = 'Voice ended';
    } else if (value.type === 'error') {
      end('Voice error · closing the call');
    } else if (['session.input_transcript.delta', 'session.output_transcript.delta'].includes(value.type) && typeof value.delta === 'string') {
      // Captions come from the trusted sideband in the shared chat, not a second transcript.
    }
  }
  async function begin() {
    if (active) { panel.hidden = !panel.hidden; return; }
    active = true; ending = false; muted = false; client = crypto.randomUUID(); const run = ++generation, callClient = client;
    start.disabled = true; start.setAttribute('aria-pressed', 'true'); panel.hidden = false;
    seen.clear(); $('voice-mute').textContent = 'Mute microphone';
    state.textContent = 'Connecting microphone…';
    try {
      const media = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
      if (run !== generation) { media.getTracks().forEach(track => track.stop()); return; }
      stream = media; pc = new RTCPeerConnection();
      pc.ontrack = e => { $('voice-audio').srcObject = e.streams[0] || new MediaStream([e.track]); $('voice-audio').play().catch(() => { state.textContent = 'Click Talk to JEFF to enable audio playback'; }); };
      pc.onconnectionstatechange = () => { if (pc && ['failed','closed'].includes(pc.connectionState) && !ending) end('Audio connection lost · ending voice'); };
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
      channel = pc.createDataChannel('oai-events'); channel.onmessage = e => { if (callClient !== client) return; try { event(JSON.parse(e.data)); } catch { /* Ignore malformed transport events. */ } };
      channel.onclose = () => { if (active && !ending) end('Voice connection closed'); };
      await pc.setLocalDescription(await pc.createOffer());
      await new Promise((resolve, reject) => {
        if (pc.iceGatheringState === 'complete') return resolve();
        const peer = pc, timeout = setTimeout(() => reject(Error('Audio network setup timed out.')), 10000);
        peer.addEventListener('icegatheringstatechange', () => { if (peer.iceGatheringState === 'complete') { clearTimeout(timeout); resolve(); } });
      });
      if (run !== generation) return;
      state.textContent = 'Connecting GPT Live 1 · Stone…';
      const result = await rpc('host.voice.start', {client:callClient, sdp: pc.localDescription.sdp});
      if (run !== generation) { await rpc('host.voice.end', {client:callClient}); return; }
      await pc.setRemoteDescription({type: 'answer', sdp: result.sdp});
      start.disabled = false;
      connectedTimer = setTimeout(() => end('Voice startup timed out · ending call'), 30000);
    } catch (error) {
      if (run !== generation) return;
      const message = error.name === 'NotAllowedError' ? 'Microphone permission is needed. Allow it in your browser and try again.' : error.message;
      await end(message); state.textContent = message;
    }
  }
  start.onclick = () => { $('voice-audio').play().catch(() => {}); begin(); };
  $('voice-end').onclick = () => end();
  $('voice-mute').onclick = () => {
    muted = !muted; stream?.getAudioTracks().forEach(track => { track.enabled = !muted; });
    send(muted ? 'session.input_audio.mute' : 'session.input_audio.unmute');
    $('voice-mute').textContent = muted ? 'Unmute microphone' : 'Mute microphone';
    state.textContent = muted ? 'Microphone muted' : 'Listening · GPT Live 1';
  };
  async function check() {
    if (checking || !token) return; checking = true;
    try {
      const statusClient = client;
      const status = await rpc('host.voice.status', {client:statusClient});
      if (statusClient !== client) return;
      if (!active) { start.disabled = !status.configured || (status.active && !status.owner); start.title = !status.configured ? 'Voice API credential is not configured' : status.active && !status.owner ? 'Voice is open in another browser' : 'GPT Live 1 · Stone'; }
      if (status.owner && status.closed) { if (active) release(); state.textContent = status.error || (status.confirmed_closed ? 'Voice ended' : 'Voice disconnected; provider closure was not confirmed.'); }
      else if (status.owner && status.closing && active && !ending) end('Ending voice…');
    } catch { if (active && !ending) end('Server connection lost · microphone off'); }
    finally { checking = false; }
  }
  window.addEventListener('pagehide', () => {
    micOff(); if (!active) return; send('session.close');
    fetch('/api/rpc', {method:'POST', keepalive:true, headers:{'Content-Type':'application/json', Authorization:'Bearer '+token}, body:JSON.stringify({method:'host.voice.end', args:{client}})}).catch(() => {});
  });
  check(); setInterval(check, 2000);
})();
