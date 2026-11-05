// Handler and state tests. This adapter is not screenshot, browser, focus or drag evidence.
const {fs,path,vm,assert,lab,node,descendants,ctx,P,component,api,part,button,tick}=require('./component_test_support.cjs');
let checks=0;function check(label,fn){fn();checks++;console.log('PASS '+label)}
(async()=>{
  const board=component(path.join(__dirname,'board-components.bundle.js'));
  const generic=component(path.join(lab,'components/catalogue.js'));
  const notice=component(path.join(lab,'components/action-notice.js'));
  const a=api('board-thread',{children:[{facts:{id:'post1'},children:[]}],draft:{text:'First reply'}});
  await a.select({thread:'post1',replyTo:'post1'});
  let root=board.mount(a,{}),input=part(root,'reply'),form=root.querySelector('form'),release;
  a.fire=async(event,values)=>{a.calls.push({event,values});root=board.mount(a,{});await new Promise(resolve=>release=resolve);return {records:['r52'],made:['reply1']}};
  const first=form.event('submit');await tick();
  await root.querySelector('form').event('submit');
  check('a remount during admission cannot duplicate a pending reply',()=>assert.equal(a.calls.length,1));
  release();await first;
  check('success clears the CURRENT remounted reply and reports the outcome',()=>{
    assert.equal(part(root,'reply').value,'');assert.match(root.textContent,/Reply posted/);
    assert.equal(button(root,'Post reply').disabled,true);
  });
  input=part(root,'reply');input.value='Keep after refusal';await input.event('input');
  a.fire=async()=>{throw Error('permission refused')};await root.querySelector('form').event('submit');
  check('refusal keeps the exact draft and enables retry',()=>{
    assert.equal(part(root,'reply').value,'Keep after refusal');assert.match(root.textContent,/permission refused/);
    assert.equal(button(root,'Post reply').disabled,false);
  });
  a.fire=async()=>{root=board.mount(a,{});const newer=part(root,'reply');newer.value='Next thought';await newer.event('input');return {made:['reply2']}};
  await root.querySelector('form').event('submit');
  check('a successful send never erases newer typing',()=>assert.equal(part(root,'reply').value,'Next thought'));

  const b=api('button');b.display=()=> 'Mark done';
  let done=generic.mount(b,{completionText:'Marked done.'}),finish;
  b.fire=async()=>{b.calls.push('press');await new Promise(r=>finish=r);return {records:['r61']}};
  const pending=done.click();await done.click();
  check('authored completion button sends once',()=>assert.equal(b.calls.length,1));
  finish();await pending;
  check('completion notice records the admitted receipt',()=>assert.equal(notice.feedback(b).get().record,'r61'));
  const n=api('action-notice',{node:{component:'action-notice',gestures:[{event:'undo'}]},view:b.view,select:b.select});
  root=notice.mount(n,{});await button(root,'Undo').click();
  check('Undo targets that receipt, never unqualified latest undo',()=>assert.equal(n.calls[0].values.value,'r61'));
  check('receipt Undo reports completion',()=>assert.equal(notice.feedback(b).get().text,'Undone.'));
  let moveToken=notice.feedback(b).begin('Moving');notice.feedback(b).finish(moveToken,{records:['r70']},'Moved the pin.');
  n.fire=async()=>{throw Error('a later edit prevents undo')};root=notice.mount(n,{});await button(root,'Undo').click();
  check('refused Undo leaves its recovery available and says why',()=>{assert.equal(notice.feedback(b).get().record,'r70');assert.match(root.textContent,/later edit/);assert.equal(button(root,'Undo').disabled,false)});
  n.fire=async()=>{moveToken=notice.feedback(b).begin('Working');notice.feedback(b).finish(moveToken,{records:['r71']},'A newer action')};
  await button(root,'Undo').click();
  check('older Undo completion does not overwrite a newer notice',()=>assert.equal(notice.feedback(b).get().record,'r71'));

  const w=api('work-line',{node:{component:'work-line',gestures:[{event:'done'}]}});
  const work=component(path.join(lab,'components/work-line.js'));
  w.fire=async()=>({records:['r92']});
  root=work.mount(w,{title:'Fixture task',state:'Active'});await button(root,'Mark done').click();
  check('reuse: Work Mark done emits the exact admitted receipt',()=>assert.equal(work.feedback(w).get('workNotice').record,'r92'));
  const wn=api('action-notice',{node:{component:'action-notice',gestures:[{event:'undo'}]},view:w.view,select:w.select});
  await button(notice.mount(wn,{stateKey:'workNotice'}),'Undo').click();
  check('reuse: Work Undo reverses that action',()=>assert.equal(wn.calls[0].values.value,'r92'));

  let overlayOptions,dialogForm;P.overlay=(kind,body,options)=>{overlayOptions=options;dialogForm=body;return {node:body,close(){}}};
  for(const [mode,title]of Object.entries({report:'Report to leaders',hide:'Hide with a reason',decide:'Record a decision',edit:'Edit post'})){
    const c=api('board-composer');await c.select({[mode]:'post1'});board.mount(c,{});
    check(mode+' dialog names its actual action',()=>{assert.equal(overlayOptions.label,title);assert.equal(dialogForm.attrs['aria-label'],title);assert.match(dialogForm.textContent,new RegExp(title))});
  }
  const kinds=[{name:'event',compose_scope:'board',fields:'seats',defaults:'{"seats":"500"}'},{name:'map-layer',compose_scope:'map',compose_label:'Make a map layer'},{name:'club-news',compose_scope:'board',fields:''}];
  const c=api('board-composer',{draft:{chosen:true,kind:'event'},read:async line=>line==='rows kind'?kinds:line==='board.badges'?[]:[]});
  board.mount(c,{});await tick();
  check('world scope excludes map kinds but admits a new scoped kind',()=>{const types=descendants(dialogForm).filter(n=>n.dataset.postType).map(n=>n.dataset.postType);assert.deepEqual(types,['event','club-news'])});
  check('kind defaults populate optional capacity',()=>assert.equal(dialogForm.querySelectorAll('input[name]')[0].value,'500'));
  const reply=api('button');reply.display=()=> 'Reply';
  await generic.mount(reply,{selectKey:'asksThread asksReplyTo',value:'post2'}).click();
  check('Asks reply selects both keys without creating a post',()=>{assert.equal(reply.view().asksThread,'post2');assert.equal(reply.view().asksReplyTo,'post2');assert.equal(reply.calls.length,0)});
  const thread=api('board-thread',{view:reply.view,select:reply.select,children:[{facts:{id:'post2'}}]});
  check('the reusable thread accepts text-block content and namespaced keys',()=>assert.ok(part(board.mount(thread,{threadKey:'asksThread',replyKey:'asksReplyTo'}),'reply')));

  const slots=component(path.join(lab,'components/slots.js'));
  const own=slots.mount(api('slots',{node:{component:'slots',viewer:{id:'p1'}},facts:{id:'offer',seats:3,seats_left:2,'claim:p1':'yes'}}),{});
  check('an already reserved place has a meaningful explicit state',()=>{assert.match(own.textContent,/Your place is reserved/);assert.equal(button(own,'Take a place'),undefined)});
  const poster=api('slots',{node:{component:'slots',viewer:{id:'p1'}},facts:{id:'offer',post_kind:'offer',for:'p1',made_by:'agent',seats:3,seats_left:3}});
  const ownOffer=slots.mount(poster,{});await button(ownOffer,'Take a place').click();
  check('an own offer is disabled with a reason and cannot claim',()=>{assert.equal(button(ownOffer,'Take a place').disabled,true);assert.match(ownOffer.textContent,/This is your offer/);assert.equal(poster.calls.length,0)});
  const offerInput=api('input');let offerRoot=generic.mount(offerInput,{commit:'submit',submitLabel:'Post offer'});
  part(offerRoot,'control').value='Spare seedlings';await part(offerRoot,'control').event('input');
  offerInput.fire=async()=>{offerRoot=generic.mount(offerInput,{commit:'submit',submitLabel:'Post offer'});return {records:['r81']}};
  await part(offerRoot,'submit').click();
  check('Offer uses the shared submit lifecycle and clears the remounted input',()=>assert.equal(part(offerRoot,'control').value,''));
  const docs=component(path.join(__dirname,'document-components.bundle.js'));
  const da=api('document-toolbar',{display:()=>''});root=docs.mount(da,{library:'lib'});
  await button(root,'Make folder').click();
  check('empty folder action explains what is required without a write',()=>{assert.match(root.textContent,/Enter a folder name/);assert.equal(da.calls.length,0)});
  const upload=docs.mount(api('document-upload'),{library:'lib'});
  let picked=0;part(upload,'picker').addEventListener('click',()=>picked++);await button(upload,'Choose files').click();
  check('one native Choose button opens the hidden picker once inside the drop group',()=>{assert.equal(part(upload,'picker').hidden,true);assert.equal(part(upload,'drop').attrs.role,'group');assert.equal(picked,1);assert.equal(upload.querySelectorAll('button').length,1)});
  const file=component(path.join(lab,'components/file.js'));
  const reader=file.mount(api('file'),{target:'f1',content:{kind:'document',pages:['Only page']}});await tick();
  check('one-page document uses singular wording',()=>{assert.match(reader.textContent,/1 page/);assert.doesNotMatch(reader.textContent,/1 pages/)});
  check('one-page reader omits unnecessary pagination controls',()=>{assert.equal(button(reader,'Previous page'),undefined);assert.equal(button(reader,'Next page'),undefined);assert.equal(reader.querySelectorAll('select').length,0)});
  const map=component(path.join(lab,'apps/map/map-components.bundle.js'));
  const ma=api('map-inspector',{read:async()=>[]});
  const emptyMap=map.mount(ma,{map:'Fixture'});await tick();
  check('read-only map help never offers unavailable Add or raw Lines',()=>{assert.doesNotMatch(emptyMap.textContent,/Press Add|press Add|map\.add/);assert.match(emptyMap.textContent,/Explore the map/)});
  await ma.select({selected:JSON.stringify({kind:'ground',lat:36.9,lon:-122,type:'street'})});
  check('map inspector offers no route without an authored planner contract',()=>assert.equal(button(map.mount(ma,{map:'Fixture'}),'Route from here'),undefined));
  const routable=map.mount(ma,{map:'Fixture',routes:true});
  await button(routable,'Route from here').click();
  check('declared planner routing selects actual first-stop coordinates',()=>{assert.equal(ma.view().tool,'route');assert.equal(JSON.parse(ma.view().stops)[0].lat,36.9)});
  const mapSource=fs.readFileSync(path.join(lab,'apps/map/map-components.bundle.js'),'utf8').replace('export default','const mapModule =');
  const mapFire=vm.runInNewContext(mapSource+'\nmapFire',ctx);
  const moveApi=api('geo-map',{fire:async()=>({records:['r601']})});
  await mapFire(moveApi,'move',{thing:'pin',lat:'36.91',lon:'-122.01'},'Moved meeting point');
  check('map action handler publishes the exact movement receipt',()=>assert.equal(map.feedback(moveApi).get().record,'r601'));

  const summaryApi=api('board-catchup',{children:[{facts:{id:'post',made:'2026-11-04'}}],
    read:async line=>line==='model.status'?[{up:true,model:'fixture-stub',installed:['fixture-stub']}]:[],
    rows:async()=>[],Q:JSON.stringify});
  await summaryApi.select({channel:'fixture'});
  let finishSummary;
  summaryApi.fire=async(event)=>{summaryApi.calls.push(event);if(event==='snapshot')return {made:['private-fixture']};await new Promise(r=>finishSummary=r);return {text:'Stub summary: meet at the park.'}};
  root=board.mount(summaryApi,{previewCount:3});await tick();
  const summarise=button(root,'Summarise'),summarising=summarise.click();await tick();await summarise.click();
  check('summary shows pending state and issues one stubbed model request',()=>{assert.match(root.textContent,/Preparing a summary/);assert.equal(summaryApi.calls.filter(e=>e==='summarize').length,1)});
  finishSummary();await summarising;
  check('summary displays the explicit result in the current channel',()=>{assert.match(summaryApi.view().summary,/Stub summary/);assert.match(root.textContent,/Summary ready/)});
  summaryApi.fire=async event=>event==='snapshot'?{made:['private-fixture']}:Promise.reject(Error('fixture model offline'));
  await summarise.click();
  check('summary refusal is visible and retry stays available',()=>{assert.match(root.textContent,/Summary not available.*fixture model offline/);assert.equal(summarise.disabled,false)});
  for(const offlineRead of [async()=>[{up:false}],async()=>{throw Error('status refused')}]){
    const offline=api('board-catchup',{children:[{facts:{id:'post'}}],read:async line=>line==='model.status'?offlineRead():[]});
    const offlineRoot=board.mount(offline,{});await tick();await button(offlineRoot,'Summarise').click();
    check('offline or refused model status keeps a disabled labelled action and reason',()=>{assert.equal(button(offlineRoot,'Summarise').disabled,true);assert.match(offlineRoot.textContent,/Summary not available/);assert.equal(offline.calls.length,0)});
  }
  summaryApi.fire=async event=>event==='snapshot'?{made:['private-fixture']}:{text:''};
  await summarise.click();
  check('empty model answer never reports success',()=>assert.match(root.textContent,/Summary not available/));
  const eventApi=api('board-post',{facts:{id:'event',post_kind:'event'},node:{component:'board-post',gestures:[],viewer:{id:'p1'}}});
  let eventRoot=board.mount(eventApi,{});await tick();
  check('event without an explicit capacity omits places-left text',()=>{assert.match(eventRoot.textContent,/0 going/);assert.doesNotMatch(eventRoot.textContent,/places left/)});
  eventApi.facts={...eventApi.facts,seats:8,seats_left:5};eventRoot=board.mount(eventApi,{});await tick();
  check('event with a capacity retains the actual places-left count',()=>assert.match(eventRoot.textContent,/5 places left/));
  check('upvote has a visible word and invokes its authored action',()=>assert.ok(button(eventRoot,'↑ Upvote')));
  await button(eventRoot,'↑ Upvote').click();
  check('labelled upvote still calls like',()=>assert.equal(eventApi.calls.at(-1).event,'like'));
  const menuSource=fs.readFileSync(path.join(lab,'../window-lab/kernel-desktop/pages/menu.js'),'utf8');
  const names=menuSource.match(/const readable = ([^\n]+);/)[1];
  const readable=vm.runInNewContext('const ID=/^[a-z]{1,8}\\d+$/;('+names+')');
  check('untitled menu naming skips id labels and uses readable first words',()=>{assert.equal(readable('', 'dk82','Bring a spare chair','dk82'),'Bring a spare chair');assert.equal(readable('dk82'),'Selected item')});
  const sa=api('board-shell',{draft:{search:'old query',searchQuery:'old query'}});
  await sa.select({search:''});
  const shell=board.mount(sa,{});await tick();
  check('leaving results clears a stale search draft and leaves an explicit Search button',()=>{assert.equal(shell.querySelector('input').value,'');assert.ok(button(shell,'Search'))});
  console.log('ROUND2 COMPONENT CHECKS '+checks);
})().catch(e=>{console.error(e);process.exitCode=1});
