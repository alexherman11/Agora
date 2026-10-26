// Reviewed presentation only. Arrangements own bindings and world-word gestures.
export default {mount(api,s){
  const {P}=api,L=api.label,kind=api.node.component,f=api.facts,v=api.view();
  const root=api.part('body','section',{class:'nb-'+kind.replace('board-',''),'aria-label':L('label',s.title||kind.replace('board-',''))});
  const kids=()=>api.children.map(api.render),text=(tag,value,cls='')=>P.node(tag,{class:cls},value);
  const press=(key,fallback,fn,cls='nb-text-button')=>P.press(L(key,fallback),fn,cls);
  const status=()=>api.part('status','p',{class:'nb-meta',role:'status','aria-live':'polite'});
  const safe=fn=>async()=>{try{await fn()}catch(e){api.tell(String(e.message||e).replace(/^refused:\s*/,'Please try again in a little while. '))}};
  const open=id=>api.select({thread:id,replyTo:id,quote:'',source:'',page:1});
  if(kind==='board-shell'){
    const header=P.node('header',{class:'nb-masthead'},P.node('div',{class:'nb-brand'},text('span','S','nb-logo'),P.node('div',{},text('strong',api.display('title')),text('p',api.display('subtitle'),'nb-meta'))),text('span',L('local','A little closer to home'),'nb-mastnote'));
    root.append(header,P.node('main',{class:'nb-layout'},...kids()),press('compose','＋ Write a post',()=>api.select({compose:'yes'}),'nb-compose-fab nb-primary'));
    root.dataset.ready='true';return root;
  }
  if(kind==='board-navigation'){
    root.append(text('p',L('yourboard','YOUR NEIGHBOURHOOD'),'nb-eyebrow'),press('all','All conversations',()=>api.select({channel:'',offset:0,search:'',queue:'no'}),!v.channel?'nb-channel active':'nb-channel'),text('p',L('channels','CHANNELS'),'nb-eyebrow'));
    const links=P.node('div',{class:'nb-channel-list'}),phone=P.node('select',{'aria-label':L('channel','Channel'),on:{change:e=>api.select({channel:e.target.value,offset:0,search:'',queue:'no'})}},P.node('option',{value:''},L('all','All conversations')));
    api.read('rows board-channel').then(api.guard(channels=>{for(const ch of channels){links.append(P.press(L(ch.title,ch.title),()=>api.select({channel:ch.group,offset:0,search:'',queue:'no'}),'nb-channel'+(v.channel===ch.group?' active':'')));phone.append(P.node('option',{value:ch.group},L(ch.title,ch.title)))}phone.value=v.channel||''})).catch(api.tell);
    root.append(links,phone,press('saved','Saved for later',async()=>{const orders=await api.read('rows board-order');await api.select({order:orders.find(o=>o.rule==='bookmarks')?.id||'',offset:0})},'nb-channel'),press('queue','Leaders’ queue',()=>api.select({queue:'yes',search:''}),'nb-channel'),text('p',L('welcome','A shared place for questions, plans and looking out for each other.'),'nb-navnote'));return root;
  }
  if(kind==='board-toolbar'){
    const title=text('h1',L('all','All conversations'));
    api.read('rows board-channel').then(api.guard(ch=>{if(v.channel)title.textContent=ch.find(c=>c.group===v.channel)?.title||L('channel','Channel')}));
    const order=P.node('select',{'aria-label':L('ordering','Order conversations'),on:{change:e=>api.select({order:e.target.value,offset:0})}});
    api.read('rows board-order').then(api.guard(orders=>{for(const o of orders)order.append(P.node('option',{value:o.id},L(o.name,o.name)));if(v.order)order.value=v.order;else api.read('rows board-settings').then(api.guard(settings=>{order.value=settings[0]?.default_order||orders[0]?.id}))}));
    const input=api.part('search','input',{'aria-label':L('search','Search the board'),placeholder:L('searchhint','Find a conversation or document…'),value:api.draft.search??v.search??''});
    input.addEventListener('input',()=>{api.draft.search=input.value});input.addEventListener('keydown',e=>{if(e.key==='Enter')api.select({search:input.value,offset:0,queue:'no'})});
    root.append(P.node('div',{class:'nb-titleline'},title,press('compose','Write a post',()=>api.select({compose:'yes'}),'nb-primary')),text('p',L('intro','News, questions and small ways to help.'),'nb-subtitle'),P.node('div',{class:'nb-tools'},input,order));return root;
  }
  if(kind==='board-catchup'){
    root.append(P.node('div',{class:'nb-titleline'},text('h2',L('catchup','Since you were last here')),press('seen','Mark seen',safe(()=>api.fire('seen')))),...kids());
    if(!api.children.length)root.append(text('p',L('caught','You’re all caught up. Come back whenever you like.'),'nb-meta'));
    else root.append(press('summary','Optional local summary',safe(async()=>{const caught=await api.rows('board.catch-up'+(v.channel?' in='+api.Q(v.channel):''));const snapshot=await api.fire('snapshot',{value:JSON.stringify(caught)});const summary=await api.fire('summarize',{target:snapshot.made[0]});await api.select({summary:summary.text})})));
    if(v.summary)root.append(text('strong',L('modellabel','Local model summary')),text('p',v.summary,'nb-meta'));return root;
  }
  if(kind==='board-entry'){
    root.append(P.press((f.category?L(f.category,f.category)+' · ':'')+(f.title||f.text||f.reason||L('conversation','Conversation')),()=>open(f.about||f.thread||f.id),'nb-entry-button'));return root;
  }
  if(kind==='board-feed'){
    root.append(...kids());const collection=api.node.collection;
    if(!api.children.length)root.append(text('span','☀','nb-empty-icon'),text('h2',L('empty','Room for a first conversation')),text('p',L('emptyhint','Ask a question, share a plan or say hello. Your neighbours will find it here.')),press('first','Start a conversation',()=>api.select({compose:'yes'}),'nb-primary'));
    if(collection&&collection.total>collection.limit)root.append(P.node('nav',{class:'nb-pagination','aria-label':L('pages','Conversation pages')},press('previous','← Newer',()=>api.select({offset:Math.max(0,collection.offset-collection.limit)})),text('span',(collection.offset+1)+'–'+Math.min(collection.total,collection.offset+collection.limit)+' / '+collection.total,'nb-meta'),press('older','Older →',()=>api.select({offset:Math.min(Math.floor((collection.total-1)/collection.limit)*collection.limit,collection.offset+collection.limit)}))));return root;
  }
  if(kind==='board-post'){
    root.dataset.post=f.id;root.dataset.kind=f.post_kind||'discussion';root.dataset.depth=f.depth||0;
    const identity=api.part('identity','div',{class:'nb-identity'}),author=text('strong',L('neighbour','Neighbour')),avatar=P.content('avatar','',{'aria-label':L('avatar','Neighbour initials')}),badges=api.part('badge','span',{class:'nb-role'}),stamp=text('span',new Date(f.made||Date.now()).toLocaleDateString(undefined,{month:'short',day:'numeric'}),'nb-meta');
    identity.append(avatar,P.node('div',{},author,text('p',f.post_kind==='reply'?L('reply','Reply'):L(f.post_kind,f.post_kind||'discussion'),'nb-meta')),badges,stamp);
    api.read('board.badges').then(api.guard(people=>{const person=people.find(p=>p.id===(f.via_actor||f.made_by)&&p.badges.includes('agent'))||people.find(p=>p.id===(f.for||f.made_by));if(person){author.textContent=person.name;avatar.textContent=person.name.split(/\s+/).map(x=>x[0]).slice(0,2).join('').toUpperCase();badges.textContent=person.badges.map(b=>L(b,b)).join(' · ');badges.setAttribute('data-fact-role',person.badges[0]||'neighbour')}})).catch(api.tell);
    api.read('rows kind').then(api.guard(kinds=>{const token=kinds.find(k=>k.name===f.post_kind)?.accent;if(/^[a-z][\w-]*$/.test(token||''))root.style.borderLeftColor='var(--'+token+',var(--accent))'})).catch(api.tell);
    root.append(identity);
    if(f.outcome)root.append(api.part('outcome','aside',{class:'nb-outcome'},text('strong',L('decision','Decision')),text('p',f.outcome)));
    if(f.pinned)root.append(text('p',L('pinned','Pinned by a leader')+((f.pin_until||f.until)?' · '+L('until','until')+' '+new Date(f.pin_until||f.until).toLocaleDateString():''),'nb-state'));
    if(f.post_kind==='question')root.append(text('p',f.answered?L('answered','Answer found ✓'):L('needsanswer','Needs an answer'),'nb-state'));
    if(f.title)root.append(api.part('title','h2',{},f.title));
    if(f.quote)root.append(api.part('quote','blockquote',{},f.quote,text('small',L('quoted','Quoted passage')+' · '+L('page','page')+' '+f.quote_page,'nb-meta')));
    root.append(...kids());
    if(f.start){const days=Math.ceil((new Date(f.start)-new Date())/86400000);root.append(text('p',new Date(f.start).toLocaleString()+' · '+(f.location||f.place||''),'nb-event-date'));if(days>=0&&days<=14)root.append(text('p',days===0?L('today','Happening today'):L('in','In')+' '+days+' '+L('days','days'),'nb-state'))}
    const actions=P.node('div',{class:'nb-actions'});
    const upvote=P.press(L('upvote','↑')+' '+(f.likes||0),safe(()=>api.fire('like')),'nb-upvote');upvote.setAttribute('aria-label',L('upvoteLabel','Upvote')+'; '+(f.likes||0)+' '+L('votes','upvotes'));
    actions.append(upvote,press('reply','Reply',()=>open(f.thread||f.id)));
    if(s.detail){
      const source=root.querySelector('[data-component=markdown]')||root,selected=P.selected(source,api.draft,()=>f.text);
      const quoteButton=press('quote','Quote selection',()=>{const quote=selected();if(!quote){api.tell(L('selectquote','Select a passage first.'));return}api.select({quote,source:f.id,page:1,replyTo:Number(f.depth||0)>=2?(f.thread||f.id):f.id})});quoteButton.addEventListener('pointerdown',()=>{selected()});
      if(source===root)root.append(quoteButton);else source.after(quoteButton);
      actions.append(press('replyhere',Number(f.depth||0)>=2?'Reply to thread':'Reply here',()=>api.select({replyTo:Number(f.depth||0)>=2?(f.thread||f.id):f.id})));
    }
    const details=P.node('details',{class:'nb-more'},P.node('summary',{'aria-label':L('more','More conversation actions')},L('more','More'))),menu=P.node('div',{class:'nb-menu'});
    for(const action of ['bookmark','follow','hide','mute']){
      let existing;const button=press(action,({bookmark:'Save for later',follow:'Follow replies',hide:'Hide for me',mute:'Mute thread'})[action],safe(async()=>{if(existing){const history=await api.rows('history '+existing.id),record=String(history[0].record);await api.fire('unpersonal',{value:record.startsWith('r')?record:'r'+record})}else await api.fire('personal',{value:action})}));
      api.read('rows board-mark').then(api.guard(marks=>{existing=marks.find(m=>m.about===f.id&&m.action===action);if(existing)button.textContent=L('undo-'+action,action==='bookmark'?'Remove bookmark':action==='follow'?'Unfollow replies':'Undo '+action)})).catch(api.tell);menu.append(button);
    }
    menu.append(press('why','Why is this here?',safe(async()=>{const r=await api.rows('board.why-here '+f.id);api.tell(r[0]?.why||'')})),press('history','Edit history',safe(async()=>{const rows=await api.rows('history '+f.id);const body=P.node('section',{},text('h2',L('history','Edit history')),...rows.map(r=>P.node('p',{},String(r.at||r.when||r.time||'')+' · '+String(r.by||'')+' · '+String(r.words||r.word||'')+' '+String(r.changes||''))));P.overlay('dialog',body,{label:L('history','Edit history')})})),press('report','Report to leaders',()=>api.select({report:f.id})));details.append(menu);actions.append(details);root.append(actions);
    const owner=f.for||f.made_by;
    api.read('board.badges').then(api.guard(async people=>{
      const viewer=api.node.gestures[0]?.env.viewer.id,profile=people.find(p=>p.id===viewer),groups=f.groups||Object.keys(f).filter(k=>k.startsWith('in:')).map(k=>k.slice(3));
      const leads=profile?.badges.includes('steward')||(profile?.leads||[]).some(g=>groups.includes(g));
      if(leads&&!f.reply_to){menu.append(press('leaderhide','Hide with a reason',()=>api.select({hide:f.id})),press('decide','Record a decision',()=>api.select({decide:f.id})));if(f.post_kind==='announcement')menu.append(press('pin','Pin until…',()=>api.select({pin:f.id})))}
      if(f.reply_to){const thread=(await api.read('rows post')).find(t=>t.id===f.thread);if(thread?.answered===f.id)root.prepend(text('p',L('markedanswer','Marked answer ✓'),'nb-state'));if(thread?.post_kind==='question'&&((thread.for||thread.made_by)===viewer||leads))actions.append(press('answer','Mark as answer',safe(()=>api.fire('answer',{target:f.thread,reply:f.id}))))}
      if(owner===viewer||leads)menu.append(press('edit','Edit post',()=>api.select({edit:f.id,editText:f.text||''})));
    })).catch(api.tell);
    if(f.post_kind==='event')actions.append(press('going','Going',safe(()=>api.fire('rsvp',{value:'going'})),'nb-soft'),press('maybe','Maybe',safe(()=>api.fire('rsvp',{value:'maybe'}))),press('calendar','Add to calendar',safe(async()=>{await api.downloadReading('board.calendar '+f.id)})));
    return root;
  }
  if(kind==='board-thread'){
    root.append(P.node('div',{class:'nb-titleline'},text('h2',L('conversation','Conversation')),press('close','Close',()=>api.select({thread:'',quote:''}))),...kids());
    if(!v.thread){root.append(text('span','↗','nb-empty-icon'),text('h2',L('open','A little more of the conversation')),text('p',L('openhint','Open a post to read replies, ask a follow-up or share a passage.'),'nb-meta'));return root}
    const form=P.node('form',{'aria-label':L('replyform','Write a reply')}),input=api.part('reply','textarea',{'aria-label':L('replytext','Your reply'),placeholder:L('replyhint','Add something to the conversation…'),value:api.draft.text||'',rows:3}),out=status();
    input.addEventListener('input',()=>{api.draft.text=input.value});
    if(v.quote)form.append(P.node('blockquote',{},v.quote),press('removequote','Remove quote',()=>api.select({quote:'',source:''})));
    const submit=P.node('button',{type:'submit',class:'nb-primary'},L('sendreply','Post reply'));
    P.submit(form,async e=>{e.preventDefault();const sentText=input.value;submit.disabled=true;try{const participant=(await api.rows('look '+(v.replyTo||v.thread)))[0];await api.fire('reply',{target:v.replyTo||v.thread,fields:{text:input.value,...(v.quote?{quote:v.quote,source:v.source,page:v.page}:{})},saw:{[participant.id]:participant.rev}});if(api.draft.text===sentText){api.draft.text='';input.value=''}if(api.view().quote===v.quote&&api.view().source===v.source)await api.select({quote:'',source:''})}catch(err){out.textContent=String(err.message||err)}finally{submit.disabled=false}});form.append(input,submit,out);root.append(form);return root;
  }
  if(kind==='board-notice'){
    root.append(text('strong',L('hidden','Hidden by')+' '+f.by),text('p',f.reason),press('undo','Undo hide',safe(()=>api.fire('undo',{value:f.record}))));return root;
  }
  if(kind==='board-search'){
    root.append(P.node('div',{class:'nb-titleline'},text('h2',v.queue==='yes'?L('queue','Leaders’ queue'):L('results','Search results')),press('clear','Back to conversations',()=>api.select({search:'',queue:'no'}))));
    if(v.queue!=='yes'){
      const filters=P.node('form',{class:'nb-searchfilters','aria-label':L('filters','Search filters')}),inputs={};
      for(const [key,label]of [['kind','Kind'],['person','Person'],['since','From date'],['before','Before date']]){
        const chooser=key==='kind'||key==='person',input=P.node(chooser?'select':'input',{'aria-label':L(key,label),placeholder:L(key,label),value:v[key]||'',...(!chooser?{type:'date'}:{})});inputs[key]=input;filters.append(input);
        if(chooser){input.append(P.node('option',{value:''},L('any-'+key,'Any '+label.toLowerCase())));api.read(key==='person'?'board.badges':'rows kind').then(api.guard(rows=>{for(const row of rows)input.append(P.node('option',{value:key==='person'?row.id:row.name},row.name));input.value=v[key]||''})).catch(api.tell)}
      }
      filters.append(P.node('button',{type:'submit',class:'nb-soft'},L('filter','Apply filters')));P.submit(filters,e=>{e.preventDefault();api.select(Object.fromEntries(Object.entries(inputs).map(([key,input])=>[key,input.value])))});root.append(filters);
    }
    root.append(...kids());if(!api.children.length)root.append(text('p',L('noresults',v.queue==='yes'?'No reports need your attention.':'No matches yet. Try a shorter phrase or fewer filters.')));return root;
  }
  if(kind==='board-composer'){
    // One local draft per part survives projections; saved content goes through
    // the authored word and ordinary receipts, never a parallel client store.
    const form=P.node('form',{'aria-label':L('compose','Write a post')}),out=status();let close;
    const dialog=P.overlay('dialog',form,{label:L('compose','Write a post'),close:()=>api.select({compose:'no',hide:'',report:'',decide:'',edit:'',pin:''})});close=dialog.close;
    api.cleanup(()=>close(true));dialog.node.classList.add('nb-dialog');
    form.append(P.node('div',{class:'nb-titleline'},text('h2',L('compose','Write a post')),press('cancel','Cancel',close)));
    const special=['hide','report','decide','edit','pin'].find(key=>v[key]);
    if(special){
      const label=({hide:'Reason for hiding',report:'Reason for reporting',decide:'Decision outcome',edit:'Edit post',pin:'Pin until (UTC date or time)'})[special],input=P.node('textarea',{'aria-label':label,required:'',value:special==='edit'?v.editText||'':'',rows:5});form.append(text('label',label),input);
      form.append(P.node('button',{type:'submit',class:'nb-primary'},L('save','Save')),out);P.submit(form,async e=>{e.preventDefault();try{const target=(await api.rows('look '+v[special]))[0];await api.fire(special,{target:v[special],value:input.value,saw:{[target.id]:target.rev}});close();await api.select({compose:'no',hide:'',report:'',decide:'',edit:'',pin:''})}catch(err){out.textContent=String(err.message||err);api.tell(err)}});return root;
    }
    const type=P.node('select',{'aria-label':L('kind','Post kind')}),channel=P.node('select',{'aria-label':L('channel','Channel')}),title=P.node('input',{'aria-label':L('title','Title (optional)'),placeholder:L('title','Title (optional)'),value:api.draft.title||''}),body=P.node('textarea',{'aria-label':L('body','Your message'),placeholder:L('bodyhint','What would you like your neighbours to know?'),rows:5,required:'',value:api.draft.body||''}),fields=P.node('div',{class:'nb-composefields'});
    const uploads=api.draft.uploads||(api.draft.uploads=[]),attachments=P.node('div',{class:'nb-upload-list'});for(const f of uploads)attachments.append(text('p','✓ '+f.name,'nb-meta'));
    const save=()=>{api.draft.title=title.value;api.draft.body=body.value;api.draft.kind=type.value;api.draft.channel=channel.value};title.addEventListener('input',save);body.addEventListener('input',save);channel.addEventListener('change',save);
    let definitions=[];
    const draw=()=>{save();fields.replaceChildren();const definition=definitions.find(k=>k.name===type.value),types=JSON.parse(definition?.field_types||'{}'),labels=JSON.parse(definition?.field_labels||'{}');for(const key of String(definition?.fields||'').split(/\s+/).filter(Boolean)){const label=L(key,labels[key]||key.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase())),format=types[key]||'text',input=P.node('input',{'aria-label':label,name:key,type:format==='datetime'?'datetime-local':format==='number'?'number':'text','data-format':format,value:api.draft[key]||'',...(format==='number'?{min:1,max:10000,step:1}:{}),...(String(definition.required||'').split(' ').includes(key)?{required:''}:{})});input.addEventListener('input',()=>{api.draft[key]=input.value});fields.append(P.node('label',{},label,input))}};
    api.read('rows kind').then(api.guard(kinds=>{definitions=kinds;for(const k of kinds)type.append(P.node('option',{value:k.name},L(k.name,k.name)));type.value=api.draft.kind||'discussion';draw()})).catch(api.tell);type.addEventListener('change',draw);
    api.read('rows board-channel').then(api.guard(channels=>{for(const c of channels)channel.append(P.node('option',{value:c.group},L(c.title,c.title)));channel.value=api.draft.channel||v.channel||channels.find(c=>c.title==='Neighbours')?.group||channels[0]?.group}));
    const upload=api.part('upload','input',{type:'file',multiple:'','aria-label':L('attach','Add photos or files')});upload.addEventListener('change',async()=>{for(const file of upload.files){out.textContent=L('uploading','Preparing your attachment…');try{const result=await api.upload(file,channel.value);uploads.push({id:result.made[0],name:file.name});attachments.append(text('p','✓ '+file.name,'nb-meta'));out.textContent=L('privateupload','Ready. Attachments stay private until you post.')}catch(e){out.textContent=String(e.message||e)}}});
    const submit=P.node('button',{type:'submit',class:'nb-primary'},L('publish','Post to neighbours'));
    form.append(P.node('div',{class:'nb-composechoices'},P.node('label',{},L('kind','Post kind'),type),P.node('label',{},L('channel','Channel'),channel)),title,body,fields,P.node('label',{class:'nb-upload'},L('attach','Add photos or files'),upload),attachments,submit,out);
    P.submit(form,async e=>{e.preventDefault();save();submit.disabled=true;try{const values={text:body.value,title:title.value,post_kind:type.value,in:channel.value};for(const input of fields.querySelectorAll('input'))if(input.value)values[input.name]=input.dataset.format==='datetime'?new Date(input.value).toISOString():input.value;
      // Retain a successful post if a later attach refuses; retry attaches to it
      // instead of creating duplicate conversations.
      if(!api.draft.post){const receipt=await api.fire('post',{fields:values});api.draft.post=receipt.made[0]}
      for(const file of [...uploads]){const rows=await Promise.all([api.rows('look '+file.id),api.rows('look '+api.draft.post)]),saw=Object.fromEntries(rows.flat().map(r=>[r.id,r.rev]));await api.fire('attach',{file:file.id,target:api.draft.post,saw});uploads.splice(uploads.indexOf(file),1)}
      for(const key of Object.keys(api.draft))delete api.draft[key];close();await api.select({offset:0,compose:'no',hide:'',report:'',decide:'',edit:''});
    }catch(e){out.textContent=L('slow','Please give neighbours time to respond. ')+String(e.message||e).replace(/^refused:\s*/,'');api.tell(out.textContent)}finally{submit.disabled=false}});return root;
  }
  return root;
}};
