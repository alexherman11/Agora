const {fs,path,vm,assert,lab,Element,descendants,node,ctx,P,component,api,part,button,tick}=require('./component_test_support.cjs');
let checks=0;function check(label,fn){fn();checks++;console.log('PASS '+label)}
(async()=>{
  const inputComponent=component(path.join(lab,'components/catalogue.js'));
  const a=api('input');let root=inputComponent.mount(a,{commit:'submit',submitLabel:'Post'});
  let input=part(root,'control'),send=part(root,'submit');
  input.value='Need a ladder';await input.event('input');await input.event('change');await input.event('blur');
  await input.event('keydown',{key:'Escape'});await input.event('keydown',{key:'Enter',isComposing:true});
  check('explicit input: blur, change, Escape and IME Enter do not send',()=>assert.equal(a.calls.length,0));
  let resolve; a.fire=async(event,values)=>{a.calls.push({event,values});await new Promise(r=>resolve=r);return {made:['one']}};
  await input.event('keydown',{key:'Enter'});await send.click();
  check('Enter sends once and pending button is disabled',()=>{assert.equal(a.calls.length,1);assert.equal(send.disabled,true)});
  // Simulate the real painter remounting while api.fire awaits its post-admission reading.
  root=inputComponent.mount(a,{commit:'submit'});resolve();await tick();
  check('successful submit clears the current mounted draft',()=>{assert.equal(part(root,'control').value,'');assert.match(part(root,'status').textContent,/Sent/)});
  a.fire=async()=>{throw Error('refused: fixture failure')};input=part(root,'control');input.value='Keep my draft';await input.event('input');await part(root,'submit').click();
  check('refused submission retains text and an inline reason',()=>{assert.equal(input.value,'Keep my draft');assert.match(part(root,'status').textContent,/fixture failure/);assert.equal(part(root,'submit').disabled,false)});
  a.fire=async(event,values)=>{a.calls.push({event,values});return {made:['two']}};await part(root,'submit').click();
  check('explicit button retries successfully',()=>assert.equal(a.draft.value,''));
  const ordinary=api('input'),ordinaryRoot=inputComponent.mount(ordinary,{});await part(ordinaryRoot,'control').event('change');
  check('ordinary change-bound inputs retain their contract',()=>assert.equal(ordinary.calls[0].event,'change'));

  check('component-local pagination covers boundaries without a widget helper',()=>{
    assert.equal(P.pageBounds,undefined);
    for(const file of [path.join(__dirname,'board-components.bundle.js'),path.join(lab,'components/file.js'),path.join(lab,'components/work-overview.js')]){
      const source=fs.readFileSync(file,'utf8');assert.doesNotMatch(source,/P\.pageBounds/);
      const bounds=vm.runInNewContext(source.replace('export default','const component =')+'\npageBounds',{...ctx});
      for(const [total,size,page,expected]of [[0,12,0,[false,false,0]],[1,1,0,[false,false,0]],[25,12,0,[false,true,0]],[25,12,2,[true,false,2]],[4,2,99,[true,false,1]]]){
        const b=bounds(total,size,page);assert.deepEqual([b.previous,b.next,b.page],expected);
      }
    }
  });
  const reader=component(path.join(lab,'components/file.js'));
  const f=api('file',{facts:{id:'entry1',groups:['library-group']},node:{component:'file',path:'reader',gestures:[{event:'reply'},{event:'start'}]}});
  const settings={target:'file1',name:'Minutes',content:{kind:'document',pages:['Exact passage','Second page']},quoteMode:'inline',replyTarget:'post1',replyLabel:'Minutes discussion'};
  let readRoot=reader.mount(f,settings);await tick();
  check('reader first page disables Previous',()=>{assert.equal(button(readRoot,'Previous page').disabled,true);assert.equal(button(readRoot,'Next page').disabled,false)});
  await button(readRoot,'Next page').click();
  check('reader last page disables Next and displays new content',()=>{assert.equal(button(readRoot,'Next page').disabled,true);assert.equal(part(readRoot,'page').textContent,'Second page')});
  await button(readRoot,'Quote selection').click();
  check('quote opens named inline destination without sending',()=>{assert.match(part(readRoot,'quote-reply').textContent,/Minutes discussion/);assert.equal(f.calls.length,0)});
  let replyText=part(readRoot,'reply-text');replyText.value='My response';await replyText.event('input');
  f.fire=async(event,values)=>{f.calls.push({event,values});readRoot=reader.mount(f,settings);return {made:['reply1']}};
  await part(readRoot,'reply-send').click();await tick();
  check('reply sends exact quote, page, source and fresh target revision',()=>{const c=f.calls[0];assert.equal(c.event,'reply');assert.equal(c.values.target,'post1');assert.equal(c.values.fields.quote,'Exact passage');assert.equal(c.values.fields.page,2);assert.equal(c.values.fields.source,'file1');assert.equal(c.values.saw.post1,7)});
  check('posted outcome survives remount',()=>{assert.match(part(readRoot,'quote-reply').textContent,/Posted to Minutes discussion/);assert.equal(part(readRoot,'reply-text').value,'')});
  const g=api('file',{facts:{id:'entry2',groups:['other-group']},node:{component:'file',path:'other-reader',gestures:[{event:'reply'},{event:'start'}]}});
  const otherSettings={...settings,target:'file2',replyTarget:'',replyLabel:'Reading club',content:{kind:'document',pages:['Exact passage']}};
  const other=reader.mount(g,otherSettings);await button(other,'Quote selection').click();
  replyText=part(other,'reply-text');replyText.value='Please discuss';await replyText.event('input');
  g.fire=async()=>{throw Error('permission denied in fixture')};await part(other,'reply-send').click();
  check('failed new discussion keeps quote and response',()=>{assert.equal(part(other,'reply-text').value,'Please discuss');assert.match(part(other,'quote-reply').textContent,/permission denied/);assert.equal(g.draft.quotedReply.quote,'Exact passage')});
  g.fire=async(event,values)=>{g.calls.push({event,values});return {made:['club-thread']}};await part(other,'reply-send').click();
  check('reuse: unrelated reader starts only on explicit send in its group',()=>{assert.equal(g.calls[0].event,'start');assert.equal(g.calls[0].values.group,'other-group');assert.match(g.calls[0].values.fields.text,/> Exact passage/);assert.match(g.calls[0].values.fields.text,/\[\[file2\|Minutes\]\]/);assert.equal(g.draft.quotedReply.thread,'club-thread')});
  const switched=reader.mount(g,{...otherSettings,target:'file3'});await button(switched,'Quote selection').click();
  check('opening another document does not reuse a previous reply target',()=>{assert.equal(g.draft.quotedReply.source,'file3');assert.equal(g.draft.quotedReply.thread,undefined);assert.equal(part(switched,'reply-send').textContent,'Start conversation with quote')});

  const calendar=component(path.join(lab,'components/calendar.js'));
  const cal=calendar.mount(api('calendar'),{date:'2026-11-04'});
  check('calendar owns a named container; breakpoints are not viewport queries',()=>{assert.equal(cal.attrs.class,'cal-container');assert.equal(part(cal,'body').attrs.class,'cal');assert.match(calendar.css,/@container calendar/);assert.doesNotMatch(calendar.css,/@media/)});
  const work=component(path.join(lab,'components/work-overview.js'),{ResizeObserver:class{observe(){}disconnect(){}}});
  const workRoot=work.mount(api('work-overview'),{});
  check('Work empty view disables both page controls',()=>{assert.equal(button(workRoot,'Previous').disabled,true);assert.equal(button(workRoot,'Next').disabled,true)});
  const board=component(path.join(__dirname,'board-components.bundle.js'));
  check('importable board bundle includes the submit footer CSS',()=>assert.match(board.css,/\.nb-compose-actions/));
  const feed=board.mount(api('board-feed',{node:{component:'board-feed',collection:{total:25,limit:12,offset:24}},children:[{}]}),{});
  check('feed last page disables Older',()=>{assert.equal(button(feed,'Older →').disabled,true);assert.equal(button(feed,'← Newer').disabled,false)});
  const composerApi=api('board-composer',{draft:{chosen:true,kind:'event'},tell:e=>{throw e},read:async line=>line==='rows kind'?[{name:'event',compose_scope:'board',fields:'start location',compose_fields_first:'yes',compose_message_rows:'3'}]:line==='board.badges'?[]:[{group:'g',title:'Neighbours'}],file:async()=>({})});
  let form;P.overlay=(kind,body)=>{form=body;return {node:body,close(){}}};board.mount(composerApi,{});await tick();
  check('kind metadata puts details before message and actions outside scrolling step',()=>{const step=form.querySelector('.nb-compose-step'),fields=step.querySelector('.nb-composefields'),body=step.querySelector('textarea');assert.ok(step.children.indexOf(fields)<step.children.indexOf(body));assert.equal(body.rows,3);assert.equal(form.children.at(-1).attrs.class,'nb-compose-actions')});
  const map=component(path.join(lab,'apps/map/map-components.bundle.js'));
  const m=api('map-layers',{read:async()=>[{kind:'map',id:'map1'},{id:'layer1',name:'Neighbour posts',count:0,unplaced:2}]});
  const layers=map.mount(m,{map:'Fixture map',collapsed:true});await tick();
  check('layer toggle is inside its initially collapsed panel',()=>{assert.equal(layers.querySelector('.gm-layer-body').hidden,true);assert.equal(part(layers,'toggle').attrs['aria-expanded'],'false')});
  await part(layers,'toggle').click();
  check('layer toggle opens content and counts use plain words',()=>{assert.equal(layers.querySelector('.gm-layer-body').hidden,false);assert.match(layers.textContent,/Neighbour posts0 on map · 2 without a location/)});
  await part(layers,'toggle').click();
  check('layer toggle closes again',()=>assert.equal(layers.querySelector('.gm-layer-body').hidden,true));
  console.log('ROUND1 COMPONENT CHECKS '+checks);
})().catch(e=>{console.error(e);process.exitCode=1});
