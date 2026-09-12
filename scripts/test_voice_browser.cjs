const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const evidence = path.join(root, 'local/voice-browser-check'); fs.mkdirSync(evidence, {recursive:true});
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1400,height:900}});
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    const calls = []; let session = null;
    await page.route('http://localhost/**', async route => {
      const url = new URL(route.request().url());
      if (url.pathname === '/api/rpc') {
        const {method,args} = route.request().postDataJSON(); calls.push({method,args});
        let result = {};
        if (method === 'host.surface') result = {enabled:true,revision:1,watermark:1,html:'<textarea id="draft">A saved draft</textarea>'};
        if (method === 'host.voice.status') result = {configured:true,active:!!session&&!session.closed,owner:session?.client===args.client,...(session?.client===args.client?session:{})};
        if (method === 'host.voice.start') { session = {client:args.client,closed:false}; result = {sdp:'answer'}; }
        if (method === 'host.voice.end' && session?.client===args.client) session.closed = true;
        return route.fulfill({json:{result}});
      }
      const file = url.pathname === '/' ? 'frame.html' : url.pathname.slice(1);
      return route.fulfill({body:fs.readFileSync(path.join(root,'src/agora3/host',file)),contentType:file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html'});
    });
    await page.addInitScript(() => {
      window.tracks = []; window.sent = []; window.peers = [];
      const track = () => { const value = {enabled:true,readyState:'live',stop(){this.readyState='ended'}}; tracks.push(value); return value; };
      Object.defineProperty(navigator, 'mediaDevices', {value:{getUserMedia:async () => { const t=track(); return {getTracks:()=>[t],getAudioTracks:()=>[t]}; }}});
      window.RTCPeerConnection = class {
        constructor(){this.iceGatheringState='complete';this.connectionState='new';peers.push(this)}
        addTrack(){} async createOffer(){return {type:'offer',sdp:'v=0\r\n'}} async setLocalDescription(v){this.localDescription=v}
        createDataChannel(){return this.channel={readyState:'open',send:value=>sent.push(JSON.parse(value)),close(){this.readyState='closed'}}}
        async setRemoteDescription(){this.connectionState='connected';setTimeout(()=>this.channel.onmessage({data:JSON.stringify({type:'session.started'})}),0)}
        close(){this.connectionState='closed'}
      };
    });
    await page.goto('http://localhost/#test-operator');
    await page.locator('#voice-start').click();
    await page.waitForFunction(() => document.querySelector('#voice-state').textContent.startsWith('Listening'));
    assert.equal(calls.filter(c=>c.method==='host.voice.start').length,1);
    await page.evaluate(() => peers[0].channel.onmessage({data:JSON.stringify({type:'session.input_transcript.delta',event_id:'a',delta:'<img src=x onerror=alert(1)> Read the note.'})}));
    assert.equal(await page.locator('#voice-captions').count(),0);
    assert.equal(await page.locator('#voice-panel img').count(),0);
    await page.locator('#voice-mute').click();
    assert.equal(await page.evaluate(() => tracks[0].enabled),false);
    assert.equal(await page.evaluate(() => sent.at(-1).type),'session.input_audio.mute');
    await page.locator('#voice-mute').click();
    assert.equal(await page.evaluate(() => tracks[0].enabled),true);
    await page.screenshot({path:path.join(evidence,'desktop.png')});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1));
    await page.screenshot({path:path.join(evidence,'mobile.png')});
    await page.locator('#voice-end').click();
    assert.equal(await page.evaluate(() => tracks[0].readyState),'ended');
    assert(calls.some(c=>c.method==='host.voice.end'));
    await page.evaluate(() => peers[0].channel.onmessage({data:JSON.stringify({type:'session.closed'})}));
    await page.locator('#voice-start').click();
    await page.waitForFunction(() => document.querySelector('#voice-state').textContent.startsWith('Listening'));
    await page.evaluate(() => window.dispatchEvent(new Event('pagehide')));
    await page.waitForFunction(() => tracks[1].readyState === 'ended');
    await new Promise(resolve=>setTimeout(resolve,100));
    assert(calls.filter(c=>c.method==='host.voice.end').length>=2);
    await page.reload();
    assert.deepEqual(errors,[]);
    console.log('PASS microphone lifecycle, mute/unmute, safe captions, mobile layout, reopen, pagehide cleanup, zero script errors');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
