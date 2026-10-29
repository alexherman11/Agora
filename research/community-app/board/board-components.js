// Reviewed presentation only. Arrangements own bindings and world-word gestures.
export default {mount(api,s){
  const {P}=api,L=api.label,kind=api.node.component,f=api.facts,v=api.view();
  const root=api.part('body','section',{class:'nb-'+kind.replace('board-',''),'aria-label':L('label',s.title||kind.replace('board-',''))});
  const kids=()=>api.children.map(api.render),text=(tag,value,cls='')=>P.node(tag,{class:cls},value);
  const press=(key,fallback,fn,cls='nb-text-button')=>P.press(L(key,fallback),fn,cls);
  const status=()=>api.part('status','p',{class:'nb-meta',role:'status','aria-live':'polite'});
  const safe=fn=>async()=>{try{await fn()}catch(e){api.tell(String(e.message||e).replace(/^refused:\s*/,'Please try again in a little while. '))}};
  const open=(id,extra={})=>api.select({thread:id,replyTo:id,focus:'',quote:'',source:'',page:1,documentPage:1,documentFile:'',...extra});
  const chooseSaved=async()=>{const orders=await api.read('rows board-order');return api.select({order:orders.find(o=>o.rule==='bookmarks')?.id||'',offset:0,thread:'',search:'',queue:'no',opens:''})};
  const chooseQueue=()=>api.select({queue:'yes',search:'',thread:'',opens:''});
  // A channel opens its own view when its world thing says so (board-channel opens=calendar); the lens
  // arranges one part per view name. Conversations stay one press away in the toolbar.
  const chooseChannel=async channel=>{if(channel==='__saved')return chooseSaved();if(channel==='__queue')return chooseQueue();const [orders,channels]=await Promise.all([api.read('rows board-order'),api.read('rows board-channel')]);return api.select({channel,offset:0,thread:'',search:'',queue:'no',summary:'',opens:channels.find(c=>c.group===channel)?.opens||'',calendarAdd:'no',calendarEvent:'',order:orders.some(o=>o.id===v.order&&o.rule==='bookmarks')?'':v.order||''})};
  const titleCase=value=>String(value||'').replace(/^./,c=>c.toUpperCase());
  const icons={discussion:'☰',question:'?',event:'▦',poll:'▥',ask:'↗',offer:'♡',document:'▤',announcement:'⌖',decision:'✓'};
  const viewer=api.node.viewer?.id;
  const searchBox=()=>{const input=P.node('input',{'aria-label':L('search','Search the board'),placeholder:L('searchhint','Search conversations and documents'),value:api.draft.search??v.search??''});input.addEventListener('input',()=>{api.draft.search=input.value});input.addEventListener('keydown',e=>{if(e.key==='Enter')api.select({search:input.value,offset:0,queue:'no',thread:''})});return input};
  if(kind==='board-shell'){
    const channel=P.node('select',{'aria-label':L('channel','Channel'),class:'nb-phone-channel',on:{change:e=>chooseChannel(e.target.value)}},P.node('option',{value:''},L('all','All conversations')));
    Promise.all([api.read('rows board-channel'),api.read('board.badges'),api.read('rows board-order')]).then(api.guard(async([channels,people,orders])=>{const group=P.node('optgroup',{label:L('channels','Channels')});for(const c of channels)group.append(P.node('option',{value:c.group},L(c.title,c.title)));const personal=P.node('optgroup',{label:L('yourboard','Your board')},P.node('option',{value:'__saved'},L('saved','Saved')));const me=people.find(p=>p.id===viewer);if(me?.badges.some(b=>['leader','steward'].includes(b))){const queue=await api.read('board.queue');personal.append(P.node('option',{value:'__queue'},L('queue','Leaders’ queue')+' ('+queue.length+')'))}channel.append(group,personal);channel.value=v.queue==='yes'?'__queue':orders.some(o=>o.id===v.order&&o.rule==='bookmarks')?'__saved':v.channel||''})).catch(api.tell);
    const search=searchBox();search.classList.add('nb-top-search');
    const header=P.node('header',{class:'nb-masthead'},text('strong',api.display('title'),'nb-brand'),channel,search,press('searchbutton','⌕',()=>{root.classList.toggle('nb-search-open');search.focus()},'nb-search-icon'),press('compose','Write a post',()=>api.select({compose:'yes'}),'nb-primary'));
    const rendered=api.children.map(child=>({child,element:api.render(child)})),centre=rendered.find(row=>row.child.role==='nb-centre')?.element;
    for(const row of rendered)if(row.child.component==='board-navigation')row.element.classList.add('nb-navigation');
    const extras=rendered.filter(row=>row.element!==centre&&!['board-navigation','board-thread','board-composer'].includes(row.child.component));
    if(centre&&s.extras!=='alongside')centre.prepend(...extras.map(row=>row.element));
    root.append(header,P.node('main',{class:'nb-layout'},...rendered.filter(row=>!centre||s.extras==='alongside'||!extras.includes(row)).map(row=>row.element)),press('compose','＋ Write a post',()=>api.select({compose:'yes'}),'nb-compose-fab nb-primary'));
    root.classList.toggle('nb-thread-open',!!v.thread);
    root.dataset.ready='true';return root;
  }
  if(kind==='board-navigation'){
    root.append(press('all','All conversations',()=>chooseChannel(''),!v.channel?'nb-channel active':'nb-channel'),text('p',L('channels','Channels'),'nb-eyebrow'));
    const links=P.node('div',{class:'nb-channel-list'}),phone=P.node('select',{'aria-label':L('channel','Channel'),on:{change:e=>chooseChannel(e.target.value)}},P.node('option',{value:''},L('all','All conversations')));
    api.read('rows board-channel').then(api.guard(async channels=>{const [posts,seen]=await Promise.all([api.read('rows post'),api.read('rows board-seen')]);const mine=seen.filter(r=>(r.for||r.made_by)===viewer);for(const ch of channels){const since=mine.filter(r=>!r.group||r.group===ch.group).map(r=>r.at).sort().pop()||'1970';const unread=posts.filter(p=>p.groups?.includes(ch.group)&&p.made>since&&(p.for||p.made_by)!==viewer).length;const button=P.press(L(ch.title,ch.title),()=>chooseChannel(ch.group),'nb-channel'+(v.channel===ch.group?' active':''));if(unread)button.append(text('span',String(unread),'nb-unread'));links.append(button);phone.append(P.node('option',{value:ch.group},L(ch.title,ch.title)))}phone.value=v.channel||''})).catch(api.tell);
    const personal=P.node('div',{class:'nb-personal'},press('saved','Saved',chooseSaved,'nb-channel'));
    api.read('board.badges').then(api.guard(async people=>{const me=people.find(p=>p.id===api.node.viewer?.id);if(me?.badges.some(b=>['leader','steward'].includes(b))){const queue=await api.read('board.queue'),button=press('queue','Leaders’ queue',()=>api.select({queue:'yes',search:'',thread:''}),'nb-channel');button.append(text('span',String(queue.length),'nb-unread'));personal.append(button)}})).catch(()=>{});
    root.append(links,phone,personal);return root;
  }
  if(kind==='board-toolbar'){
    const title=text('h1',L('all','All conversations'));
    const order=P.node('select',{'aria-label':L('ordering','Order conversations'),on:{change:e=>api.select({order:e.target.value,offset:0})}});order.hidden=!!v.opens;
    const views=P.node('div',{class:'nb-views',role:'group','aria-label':L('views','Show')});
    api.read('rows board-channel').then(api.guard(ch=>{const here=ch.find(c=>c.group===v.channel);if(v.channel)title.textContent=here?.title||L('channel','Channel');
      if(here?.opens)for(const [value,label] of [[here.opens,here.opens_label||titleCase(here.opens)],['','Conversations']]){const b=press(value||'conversations',label,()=>api.select({opens:value,thread:'',offset:0}),'nb-view');b.setAttribute('aria-pressed',String((v.opens||'')===value));views.append(b)}}));
    api.read('rows board-order').then(api.guard(orders=>{for(const o of orders)order.append(P.node('option',{value:o.id},L(o.name,o.name)));if(v.order)order.value=v.order;else api.read('rows board-settings').then(api.guard(settings=>{order.value=settings[0]?.default_order||orders[0]?.id}))}));
    root.append(P.node('div',{class:'nb-titleline'},title,views,order));return root;
  }
  if(kind==='board-catchup'){
    // Per channel, and only when something is new: no rows, no header. The header jumps to the oldest unseen thing.
    if(!api.children.length){root.hidden=true;root.dataset.empty='yes';return root}
    const groups=new Map();for(const child of api.children){const key=child.facts.thread||child.facts.id;if(!groups.has(key))groups.set(key,{...child,facts:{...child.facts,categories:[]}});const group=groups.get(key);if(!group.facts.categories.includes(child.facts.category))group.facts.categories.push(child.facts.category)}
    const oldest=[...api.children].map(c=>c.facts).sort((a,b)=>String(a.at||a.made).localeCompare(String(b.at||b.made)))[0];
    const jump=()=>open(oldest.thread||oldest.id,{focus:oldest.first||oldest.id});
    const heading=P.node('button',{type:'button',class:'nb-catchup-jump',title:L('jumpoldest','Go to the first thing you haven’t seen'),on:{click:jump}},text('h2',groups.size+' '+L('newthings','new since your last visit')));
    const mine=rows=>rows.filter(r=>(r.for||r.made_by)===viewer&&['',v.channel||''].includes(r.group||'')).map(r=>r.at).sort().pop()||'';
    api.read('rows board-seen').then(api.guard(rows=>{const at=mine(rows);if(at)heading.firstChild.textContent=groups.size+' '+L('newthingssince','new since')+' '+new Date(at).toLocaleDateString(undefined,{weekday:'long'});if(v.summary&&v.summarySeenAt!==at)api.select({summary:''})}));
    const toggle=P.node('div',{class:'nb-catchup-toggle'},heading,P.node('button',{type:'button',class:'nb-catchup-expand','aria-label':L('showall','Show what’s new'),'aria-expanded':String(v.catchupExpanded==='yes'),on:{click:()=>api.select({catchupExpanded:v.catchupExpanded==='yes'?'no':'yes'})}},'⌄'));
    const entries=P.node('div',{class:'nb-catchup-entries'},...[...groups.values()].slice(0,v.catchupExpanded==='yes'?groups.size:s.previewCount).map(api.render));
    const actions=P.node('div',{class:'nb-catchup-actions'},press('seen','Mark all seen',safe(()=>api.fire('seen',{select:{summary:''}}))));
    root.dataset.expanded=v.catchupExpanded||'no';root.append(toggle,entries,actions);
    api.read('model.status').then(api.guard(rows=>{if(v.summaryUnavailable!=='yes'&&rows[0]?.up&&rows[0]?.installed?.includes(rows[0]?.model))actions.append(press('summary','Summarise',async()=>{try{const seen=mine(await api.read('rows board-seen')),caught=await api.rows('board.catch-up'+(v.channel?' in='+api.Q(v.channel):''));const snapshot=await api.fire('snapshot',{value:JSON.stringify(caught)});const summary=await api.fire('summarize',{target:snapshot.made[0]});const unavailable=/not running|unavailable|offline/i.test(summary.text||''),value=String(summary.text||'').replace(/^local model\s*·\s*.*?:\s+/i,'');await api.select({summary:unavailable?'':value,summaryUnavailable:unavailable?'yes':'no',summaryChannel:v.channel||'',summarySeenAt:seen})}catch{await api.select({summary:'',summaryUnavailable:'yes'})}}))})).catch(()=>{});
    if(v.summary&&api.children.length&&v.summaryChannel===(v.channel||''))root.append(P.node('div',{class:'nb-summary'},text('strong',L('modellabel','Local model summary')),text('p',v.summary,'nb-meta')));return root;
  }
  if(kind==='board-entry'){
    const button=P.press('',()=>open(f.about||f.thread||f.id,f.match==='document page'?{documentPage:f.page,documentFile:f.file_source,documentRequest:Number(api.view().documentRequest||0)+1}:{}),'nb-entry-button');
    if(f.match){button.append(text('strong',f.match==='document page'?L('page','Page')+' '+f.page+' '+L('of','of')+' '+f.title:f.title||L('conversation','Conversation')));const query=String(v.search||''),raw=f.text||'',at=raw.toLocaleLowerCase().indexOf(query.toLocaleLowerCase()),start=Math.max(0,at-55),snippet=raw.slice(start,start+220),match=snippet.toLocaleLowerCase().indexOf(query.toLocaleLowerCase()),body=P.node('p',{class:'nb-result-snippet'});if(match>=0&&query)body.append(document.createTextNode((start?'…':'')+snippet.slice(0,match)),P.node('mark',{},snippet.slice(match,match+query.length)),document.createTextNode(snippet.slice(match+query.length)));else body.textContent=snippet;button.append(body);const meta=text('p',L(f.post_kind,titleCase(f.post_kind))+' · '+api.format('stamp',f.made),'nb-meta');button.append(meta);Promise.all([api.read('board.badges'),api.read('rows board-channel')]).then(api.guard(([people,channels])=>{meta.prepend((people.find(p=>p.id===(f.for||f.made_by))?.name||L('neighbour','Neighbour'))+' · '+(channels.find(c=>f.groups?.includes(c.group))?.title||'')+' · ')}))}
    else {const categories=f.categories||[f.category].filter(Boolean);for(const c of categories)button.append(text('span',({new:'✦',decision:'✓',event:'▦',answer:'☑',busy:'☰',following:'↳'})[c]||'·','nb-catchup-icon'));button.append(text('span',f.title||f.text||f.reason||L('conversation','Conversation')))}
    root.append(button);return root;
  }
  if(kind==='board-feed'){
    root.append(...kids());const collection=api.node.collection;
    if(!api.children.length)root.append(text('span','☀','nb-empty-icon'),text('h2',L('empty','Room for a first conversation')),text('p',L('emptyhint','Ask a question, share a plan or say hello. Your neighbours will find it here.')),press('first','Start a conversation',()=>api.select({compose:'yes'}),'nb-primary'));
    if(collection&&collection.total>collection.limit)root.append(P.node('nav',{class:'nb-pagination','aria-label':L('pages','Conversation pages')},press('previous','← Newer',()=>api.select({offset:Math.max(0,collection.offset-collection.limit)})),text('span',(collection.offset+1)+'–'+Math.min(collection.total,collection.offset+collection.limit)+' / '+collection.total,'nb-meta'),press('older','Older →',()=>api.select({offset:Math.min(Math.floor((collection.total-1)/collection.limit)*collection.limit,collection.offset+collection.limit)}))));return root;
  }
  if(kind==='board-post'){
    root.dataset.post=f.id;root.dataset.kind=f.post_kind||'discussion';root.dataset.depth=f.depth||0;
    root.dataset.detail=s.detail?'yes':'no';root.style.setProperty('--excerpt-lines',Math.max(1,Math.min(9,s.excerptLines||3)));
    const identity=api.part('identity','div',{class:'nb-identity'}),author=text('strong',L('neighbour','Neighbour')),avatar=P.content('avatar','',{'aria-label':L('avatar','Neighbour initials')}),badges=api.part('badge','span',{class:'nb-role'}),stamp=text('time',api.format('stamp',f.made),'nb-meta'),channel=text('span','','nb-card-channel');stamp.dateTime=f.made||'';stamp.title=api.format('date',f.made);
    identity.append(avatar,author,badges,channel,stamp);
    api.read('rows board-channel').then(api.guard(channels=>{const groups=f.groups||Object.keys(f).filter(k=>k.startsWith('in:')).map(k=>k.slice(3));channel.textContent=channels.find(c=>groups.includes(c.group))?.title||''}));
    api.read('board.badges').then(api.guard(people=>{const person=people.find(p=>p.id===(f.via_actor||f.made_by)&&p.badges.includes('agent'))||people.find(p=>p.id===(f.for||f.made_by));if(person){author.textContent=person.name;avatar.textContent=api.format('initials',person.name);badges.textContent=person.badges.map(b=>L(b,titleCase(b))).join(' · ');badges.setAttribute('data-fact-role',person.badges[0]||'neighbour')}})).catch(api.tell);
    const chip=api.part('kind','span',{class:'nb-kind-chip'},(icons[f.post_kind]||'✦')+' '+L(f.post_kind,titleCase(f.post_kind||'discussion')));
    api.read('rows kind').then(api.guard(kinds=>{const token=kinds.find(k=>k.name===f.post_kind)?.accent;if(/^[a-z][\w-]*$/.test(token||'')){root.style.setProperty('--kind-accent','var(--'+token+',var(--accent))')}})).catch(api.tell);
    root.append(identity);
    root.append(chip);
    const outcomeText=f.outcome||(f.post_kind==='decision'?f.text:'');
    if(outcomeText){const outcome=api.part('outcome','aside',{class:'nb-outcome'},text('strong',L('decided','Decided')+': '+outcomeText));if(s.detail){const by=text('p',api.format('date',f.decided_at||f.made),'nb-meta');outcome.append(by);api.read('board.badges').then(api.guard(people=>{by.prepend((people.find(p=>p.id===(f.decided_by||f.for||f.made_by))?.name||L('leader','Leader'))+' · ')}));root.prepend(outcome)}else root.append(outcome)}
    if(f.pinned)root.append(text('p','⌖ '+L('pinned','Pinned')+((f.pin_until||f.until)?' · '+L('until','until')+' '+api.format('date',f.pin_until||f.until):''),'nb-state'));
    if(f.post_kind==='question')root.append(text('span',f.answered?L('answered','Answered'):L('needsanswer','Needs an answer'),'nb-state '+(f.answered?'nb-answered':'nb-needs-answer')));
    if(f.title)root.append(api.part('title','h2',{},f.title));
    if(f.quote)root.append(api.part('quote','blockquote',{},f.quote,text('small',L('quoted','Quoted passage')+' · '+L('page','page')+' '+f.quote_page,'nb-meta')));
    root.append(...api.children.filter(child=>!(f.post_kind==='decision'&&!f.outcome&&child.name==='body')).map(api.render));
    if(f.answered)api.read('rows post').then(api.guard(posts=>{const answer=posts.find(p=>p.id===f.answered);if(answer){const preview=api.part('answer','aside',{class:'nb-answer-preview'},text('strong',L('markedanswer','Marked answer')),text('p',answer.text));if(s.detail)root.insertBefore(preview,root.querySelector('.nb-actions'));else root.insertBefore(preview,root.querySelector('.nb-actions'))}}));
    const actions=P.node('div',{class:'nb-actions'});
    const upvote=P.press(L('upvote','↑')+(Number(f.likes)?' '+f.likes:''),safe(()=>{if(!f.you_liked)return api.fire('like')}),'nb-upvote');upvote.setAttribute('aria-label',f.you_liked?L('youupvoted','You upvoted'):L('upvoteLabel','Upvote')+'; '+(f.likes||0)+' '+L('votes','upvotes'));upvote.setAttribute('aria-pressed',!!f.you_liked);if(f.you_liked)upvote.title=L('youupvoted','You upvoted');
    actions.append(upvote,press('reply','Reply',()=>{if(s.detail){api.select({replyTo:Number(f.depth||0)>=2?(f.thread||f.id):f.id});root.closest('.nb-thread')?.querySelector('textarea')?.focus()}else open(f.thread||f.id)}));
    const activity=text('span','','nb-activity nb-meta');if(!f.reply_to)api.read('rows post').then(api.guard(posts=>{const replies=posts.filter(p=>p.thread===f.id),latest=replies.reduce((a,r)=>r.made>a?r.made:a,f.made);activity.textContent=replies.length+' '+L(replies.length===1?'onereply':'replies',replies.length===1?'reply':'replies')+' · '+L('active','Active')+' '+api.format('stamp',latest)}));actions.append(activity);
    let quoteAction;
    {
      const source=root.querySelector('[data-component=markdown]')||root;
      const selection=P.selectionAction(source,api.draft,()=>f.text,quote=>{if(!quote){api.tell(L('selectquote','Select a passage first.'));return}api.select({thread:f.thread||f.id,quote,source:f.id,page:1,replyTo:Number(f.depth||0)>=2?(f.thread||f.id):f.id})},{label:L('quote','Quote selection')});api.cleanup(selection.dispose);quoteAction=selection.quote;
    }
    const details=P.node('details',{class:'nb-more'},P.node('summary',{'aria-label':L('more','More conversation actions')},L('more','More'))),menu=P.node('div',{class:'nb-menu'});
    if(quoteAction)menu.append(press('quote','Quote selection',quoteAction));
    for(const action of ['bookmark','follow','hide','mute']){
      let existing;const button=press(action,({bookmark:'Save for later',follow:'Follow replies',hide:'Hide for me',mute:'Mute thread'})[action],safe(async()=>{if(existing){const history=await api.rows('history '+existing.id),record=String(history[0].record);await api.fire('unpersonal',{value:record.startsWith('r')?record:'r'+record})}else await api.fire('personal',{value:action})}));
      api.read('rows board-mark').then(api.guard(marks=>{existing=marks.find(m=>m.about===f.id&&m.action===action);if(existing)button.textContent=L('undo-'+action,action==='bookmark'?'Remove bookmark':action==='follow'?'Unfollow replies':'Undo '+action)})).catch(api.tell);menu.append(button);
    }
    menu.append(press('why','Why is this here?',safe(async()=>{const r=await api.rows('board.why-here '+f.id);api.tell(r[0]?.why||'')})),press('history','Edit history',safe(async()=>{const rows=await api.rows('history '+f.id),words={post:'Posted',reply:'Replied',set:'Edited',like:'Upvoted',vote:'Voted',pin:'Pinned',forget:'Hidden',undo:'Undone','board.decide':'Decision recorded','board.answer':'Answer marked'};const body=P.node('section',{},text('h2',L('history','Edit history')),...rows.map(r=>P.node('section',{},text('p',api.format('stamp',r.at)+' · '+(r.sealed?L('privateaction','Private action'):r.by||L('neighbour','Neighbour'))+' · '+L(r.word,words[r.word]||'Updated')),...(r.facts||[]).filter(f=>['title','text','outcome','forget_reason'].includes(f.aspect)&&!f.removed).map(f=>text('p',String(f.value))))));P.overlay('dialog',body,{label:L('history','Edit history')})})),press('report','Report to leaders',()=>api.select({report:f.id})));details.append(menu);actions.append(details);root.append(actions);
    const owner=f.for||f.made_by;
    api.read('board.badges').then(api.guard(async people=>{
      const viewer=api.node.gestures[0]?.env.viewer.id,profile=people.find(p=>p.id===viewer),groups=f.groups||Object.keys(f).filter(k=>k.startsWith('in:')).map(k=>k.slice(3));
      const leads=profile?.badges.includes('steward')||(profile?.leads||[]).some(g=>groups.includes(g));
      if(leads&&!f.reply_to){menu.append(press('leaderhide','Hide with a reason',()=>api.select({hide:f.id})),press('decide','Record a decision',()=>api.select({decide:f.id})));if(f.post_kind==='announcement')menu.append(press('pin','Pin until…',()=>api.select({pin:f.id})))}
      if(f.reply_to){const thread=(await api.read('rows post')).find(t=>t.id===f.thread);if(thread?.answered===f.id)root.prepend(text('p',L('markedanswer','Marked answer ✓'),'nb-state'));if(thread?.post_kind==='question'&&((thread.for||thread.made_by)===viewer||leads))actions.append(press('answer','Mark as answer',safe(()=>api.fire('answer',{target:f.thread,reply:f.id}))))}
      if(owner===viewer||leads)menu.append(press('edit','Edit post',()=>api.select({edit:f.id,editText:f.text||''})));
    })).catch(api.tell);
    if(f.post_kind==='event'){
      const toggle=P.node('div',{class:'nb-rsvp',role:'group','aria-label':L('attendance','Your attendance')}),buttons={};for(const state of ['going','maybe']){buttons[state]=press(state,titleCase(state),safe(()=>api.fire('rsvp',{value:state})),'nb-soft');buttons[state].setAttribute('aria-pressed','false');toggle.append(buttons[state])}
      const counts=text('p','','nb-event-count');root.insertBefore(counts,actions);
      api.read('rows board-rsvp').then(api.guard(rows=>{const all=rows.filter(r=>r.about===f.id),own=all.find(r=>(r.for||r.made_by)===viewer);if(own)buttons[own.status]?.setAttribute('aria-pressed','true');counts.textContent=all.filter(r=>r.status==='going').length+' '+L('goingcount','going')+' · '+Number(f.seats_left||0)+' '+L('left','places left')}));
      actions.append(toggle,press('calendar','Add to calendar',safe(async()=>{await api.downloadReading('board.calendar '+f.id)})));
    }
    return root;
  }
  if(kind==='board-thread'){
    if(!v.thread)return root;
    root.append(P.node('div',{class:'nb-titleline'},press('back','← Back',()=>api.select({thread:'',quote:''})),text('h2',L('conversation','Conversation'))),...kids());
    const target=v.focus&&root.querySelector('[data-post="'+CSS.escape(v.focus)+'"]');
    if(target){target.classList.add('nb-focus');if(api.draft.focused!==v.thread+' '+v.focus){api.draft.focused=v.thread+' '+v.focus;requestAnimationFrame(()=>target.scrollIntoView({block:'center'}))}}
    if(!root.querySelector('[data-post]')){if(!root.querySelector('.nb-notice'))root.append(text('p',L('unavailablethread','This conversation is unavailable.')));return root}
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
      const filters=P.node('div',{class:'nb-searchfilters','aria-label':L('filters','Search filters')});
      for(const [key,label,reading]of [['channel','Channel','rows board-channel'],['kind','Post type','rows kind'],['person','Person','board.badges']]){
        const input=P.node('select',{'aria-label':L(key,label),on:{change:e=>api.select({[key]:e.target.value,offset:0,...(key==='channel'?{summary:''}:{})})}},P.node('option',{value:''},L('any-'+key,'Any '+label.toLowerCase())));filters.append(input);
        api.read(reading).then(api.guard(rows=>{for(const row of rows)input.append(P.node('option',{value:key==='person'?row.id:key==='channel'?row.group:row.name},L(row.title||row.name,titleCase(row.title||row.name))));input.value=v[key]||''})).catch(api.tell);
      }
      const dates=P.node('select',{'aria-label':L('when','When'),on:{change:e=>{const value=e.target.value;if(value==='custom'){const from=P.node('input',{type:'date','aria-label':L('from','From')}),to=P.node('input',{type:'date','aria-label':L('through','Through')}),body=P.node('div',{},text('h2',L('choosedates','Choose dates')),P.node('label',{},L('from','From'),from),P.node('label',{},L('through','Through'),to));const overlay=P.overlay('dialog',body,{label:L('choosedates','Choose dates')});body.append(press('usedates','Use these dates',()=>{api.select({since:from.value?new Date(from.value+'T00:00').toISOString():'',before:to.value?new Date(new Date(to.value+'T00:00').getTime()+86400000).toISOString():'',dateRange:'custom'});overlay.close()}))}else api.select({since:value?new Date(Date.now()-Number(value)*86400000).toISOString():'',before:'',dateRange:value})}}},...['','7','30','custom'].map((value,i)=>P.node('option',{value},L(['anytime','week','month','choosedates'][i],['Any time','Past week','Past month','Choose dates…'][i]))));dates.value=v.dateRange||'';filters.append(dates);root.append(filters);
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
      input.addEventListener('input',()=>{api.draft.specialText=input.value});input.value=api.draft.specialText??input.value;
      form.append(P.node('button',{type:'submit',class:'nb-primary'},L('save','Save')),out);P.submit(form,async e=>{e.preventDefault();try{const target=(await api.rows('look '+v[special]))[0];await api.fire(special,{target:v[special],value:input.value,saw:{[target.id]:target.rev},select:{compose:'no',hide:'',report:'',decide:'',edit:'',pin:''}});delete api.draft.specialText;close()}catch(err){out.textContent=String(err.message||err);api.tell(err)}});return root;
    }
    const type=P.node('select',{'aria-label':L('type','Post type'),hidden:''}),channel=P.node('select',{'aria-label':L('channel','Channel')}),title=P.node('input',{'aria-label':L('title','Title (optional)'),placeholder:L('title','Title (optional)'),value:api.draft.title||''}),body=P.node('textarea',{'aria-label':L('body','Your message'),placeholder:L('bodyhint','What would you like your neighbours to know?'),rows:5,required:'',value:api.draft.body||''}),fields=P.node('div',{class:'nb-composefields'});
    const tiles=P.node('div',{class:'nb-kind-tiles'}),step=P.node('div',{class:'nb-compose-step'}),chosen=text('strong','','nb-compose-type');
    const uploads=api.draft.uploads||(api.draft.uploads=[]),attachments=P.node('div',{class:'nb-upload-list'});
    const drawUploads=()=>{attachments.replaceChildren();for(const file of uploads){const preview=P.node('div',{class:'nb-upload-preview'},text('p',file.name,'nb-meta'),press('removeattachment','Remove',()=>{uploads.splice(uploads.indexOf(file),1);drawUploads()}));attachments.append(preview);api.file(file.id,'thumbnail').then(api.guard(({url,blob})=>{if(blob.type.startsWith('image/'))preview.prepend(P.node('img',{src:url,alt:file.name}))})).catch(()=>{})}};drawUploads();
    const save=()=>{api.draft.title=title.value;api.draft.body=body.value;api.draft.kind=type.value;api.draft.channel=channel.value};title.addEventListener('input',save);body.addEventListener('input',save);channel.addEventListener('change',save);
    let definitions=[];
    const draw=()=>{save();fields.replaceChildren();const definition=definitions.find(k=>k.name===type.value),types=JSON.parse(definition?.field_types||'{}'),labels=JSON.parse(definition?.field_labels||'{}'),advanced=P.node('details',{class:'nb-advanced'},P.node('summary',{},L('moreoptions','More options')));chosen.textContent=(definition?.compose_icon||icons[type.value]||'✦')+' '+L(definition?.compose_label||type.value,definition?.compose_label||titleCase(type.value));for(const key of String(definition?.fields||'').split(/\s+/).filter(Boolean)){const label=L(key,labels[key]||key.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase())),format=types[key]||'text',input=P.node('input',{'aria-label':label,name:key,type:format==='number'?'number':'text','data-format':format,value:api.draft[key]||'',...(format==='number'?{min:1,max:10000,step:1}:{}),...(String(definition.required||'').split(' ').includes(key)?{required:''}:{})}),wrap=P.node('label',{},label,input);input.addEventListener('input',()=>{api.draft[key]=input.value});
      if(format==='datetime'){input.placeholder=L('datehint','e.g. Thu 6pm');const confirm=P.node('small',{role:'status',class:'nb-date-confirm'}),picker=P.node('input',{type:'datetime-local','aria-label':label+' · '+L('picker','Choose date and time'),'data-picker':'yes'});picker.addEventListener('change',()=>{input.value=picker.value;input.dispatchEvent(new Event('input'))});const check=()=>{const parsed=P.parseDateEntry(input.value);input.setCustomValidity(input.value&&!parsed.ok?parsed.message:'');confirm.textContent=input.value?(parsed.ok?L('dateconfirmed','That is')+' '+parsed.label:parsed.message):'';if(parsed.ok)picker.value=parsed.local};input.addEventListener('input',check);wrap.append(P.node('details',{class:'nb-date-picker'},P.node('summary',{},L('choosewhen','Choose date and time…')),picker),confirm);check()}
      (String(s.advancedFields||'closes place').split(' ').includes(key)?advanced:fields).append(wrap)
    }if(advanced.children.length>1)fields.append(advanced);tiles.hidden=!!api.draft.chosen;step.hidden=!api.draft.chosen};
    api.read('rows kind').then(api.guard(async kinds=>{const people=await api.read('board.badges'),me=people.find(p=>p.id===viewer),leader=me?.badges.some(b=>['steward','leader'].includes(b));definitions=kinds.filter(k=>k.name!=='reply'&&(!k.leaders_only||leader));const rank=k=>{const n=['discussion','question','event','poll','ask','document'].indexOf(k.name);return n<0?99:n},ordered=[...definitions].sort((a,b)=>rank(a)-rank(b));for(const k of ordered){type.append(P.node('option',{value:k.name},L(k.name,titleCase(k.name))));tiles.append(P.press('',()=>{type.value=k.name;api.draft.chosen=true;draw()},'nb-kind-tile'));const tile=tiles.lastChild;tile.dataset.postType=k.name;tile.append(text('span',k.compose_icon||icons[k.name]||'✦','nb-tile-icon'),text('strong',L(k.compose_label||k.name,k.compose_label||titleCase(k.name))),text('span',L(k.compose_description||k.name+'-description',k.compose_description||'Share this with your neighbours.')))}type.value=api.draft.kind||'discussion';draw()})).catch(api.tell);type.addEventListener('change',()=>{api.draft.chosen=true;draw()});
    api.read('rows board-channel').then(api.guard(channels=>{for(const c of channels)channel.append(P.node('option',{value:c.group},L(c.title,c.title)));channel.value=api.draft.channel||v.channel||channels.find(c=>c.title==='Neighbours')?.group||channels[0]?.group}));
    const upload=api.part('upload','input',{type:'file',multiple:'',hidden:'','aria-label':L('attach','Add photos or files')}),dropzone=P.node('div',{class:'nb-upload',tabindex:0,role:'button','aria-label':L('attach','Add photos or files')},text('strong',L('dropfiles','Drop photos or files here')),text('span',L('browsefiles','or choose files')));
    const prepare=async files=>{submit.disabled=true;for(const file of files){out.textContent=L('uploading','Preparing your attachment…');try{const result=await api.upload(file,channel.value);uploads.push({id:result.made[0],name:file.name});drawUploads();out.textContent=L('privateupload','Ready. Attachments stay private until you post.')}catch(e){out.textContent=String(e.message||e)}}submit.disabled=false};upload.addEventListener('change',()=>prepare(upload.files));dropzone.addEventListener('click',()=>upload.click());dropzone.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();upload.click()}});dropzone.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('over')});dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('over'));dropzone.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('over');prepare(e.dataTransfer.files)});
    const submit=P.node('button',{type:'submit',class:'nb-primary'},L('publish','Post to neighbours'));
    step.append(P.node('div',{class:'nb-titleline'},chosen,press('changetype','← Choose a different post',()=>{save();api.draft.chosen=false;draw()})),P.node('label',{},L('channel','Channel'),channel),title,body,fields,dropzone,upload,attachments,submit,out);form.append(type,tiles,step);
    P.submit(form,async e=>{e.preventDefault();if(!api.draft.chosen)return;save();submit.disabled=true;try{const values={text:body.value,title:title.value,post_kind:type.value,in:channel.value};for(const input of fields.querySelectorAll('input[name]'))if(input.value)values[input.name]=input.dataset.format==='datetime'?P.parseDateEntry(input.value).iso:input.value;
      // Retain a successful post if a later attach refuses; retry attaches to it
      // instead of creating duplicate conversations.
      const finished={offset:0,compose:'no',hide:'',report:'',decide:'',edit:'',pin:''};
      if(!api.draft.post){const receipt=await api.fire('post',{fields:values,...(!uploads.length?{select:finished}:{})});api.draft.post=receipt.made[0]}
      for(const file of [...uploads]){const rows=await Promise.all([api.rows('look '+file.id),api.rows('look '+api.draft.post)]),saw=Object.fromEntries(rows.flat().map(r=>[r.id,r.rev]));await api.fire('attach',{file:file.id,target:api.draft.post,saw,...(uploads.length===1?{select:finished}:{})});uploads.splice(uploads.indexOf(file),1)}
      for(const key of Object.keys(api.draft))delete api.draft[key];close();await api.select({offset:0,compose:'no',hide:'',report:'',decide:'',edit:''});
    }catch(e){out.textContent=L('slow','Please give neighbours time to respond. ')+String(e.message||e).replace(/^refused:\s*/,'');api.tell(out.textContent)}finally{submit.disabled=false}});return root;
  }
  return root;
}};
