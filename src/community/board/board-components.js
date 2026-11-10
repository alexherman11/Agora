// Reviewed presentation only. Arrangements own bindings and world-word gestures.
// Local to this component module: existing widget runtimes need no upgrade.
function pageBounds(total,size,page=0){
  total=Math.max(0,Math.floor(Number(total)||0));size=Math.max(1,Math.floor(Number(size)||1));
  const pages=Math.max(1,Math.ceil(total/size));
  page=Math.max(0,Math.min(pages-1,Math.floor(Number(page)||0)));
  return {page,pages,start:page*size,end:Math.min(total,(page+1)*size),previous:page>0,next:page<pages-1};
}
function boardPostKind(k,scope='board'){
  return k.name!=='reply'&&(k.compose_scope? k.compose_scope===scope :
    Object.hasOwn(k,'fields'));
}
// The board's list: board-channel things in made order, minus hidden ones (kept, not deleted).
function channelKey(c){return c.group||c.id}
function shownChannels(channels){return channels.filter(c=>c.hidden!=='yes')}
// Chat rows (CHAT-CONTRACT.md): who said a line, whether the reader did, what it answers, whom it names.
function chatAuthor(r){return r.by_id||r.by||''}
function chatMine(r,me){return r.mine===true||(!!me?.id&&r.by_id===me.id)}
function chatReply(r,byId){if(r.reply&&r.reply.id)return r.reply;const x=r.reply_to&&byId.get(r.reply_to);return x?{id:x.id,name:x.name||x.by,text:x.text,removed:x.removed}:null}
function chatMentions(r,me){return !!me?.id&&(r.mentions||[]).includes(me.id)}
function chatBadges(r){return [...(r.badge?[r.badge]:[]),...(r.guest?['guest']:[])]}
// A person's words as DOM: text nodes plus code, strong, em, http(s) links and @mentions. Never HTML.
function chatInline(P,text,myName){
  const out=[],src=String(text??''),re=/(`[^`\n]+`)|(\*\*[^*\n]+\*\*)|(\*[^*\s][^*\n]*\*)|(https?:\/\/[^\s<>"']*[^\s<>"'.,;:!?)\]])|((?<![\w@])@[A-Za-z][\w.-]*)/g;
  let last=0,m;
  while((m=re.exec(src))){
    if(m.index>last)out.push(src.slice(last,m.index));
    const t=m[0];
    if(m[1])out.push(P.node('code',{},t.slice(1,-1)));
    else if(m[2])out.push(P.node('strong',{},...chatInline(P,t.slice(2,-2),myName)));
    else if(m[3])out.push(P.node('em',{},...chatInline(P,t.slice(1,-1),myName)));
    else if(m[4])out.push(P.node('a',{href:t,target:'_blank',rel:'noopener noreferrer nofollow'},t));
    else{const name=t.slice(1).replace(/[.-]+$/,''),self=!!myName&&myName.split(/\s+/)[0].toLowerCase()===name.toLowerCase();out.push(P.node('span',{class:'nb-mention'+(self?' nb-mention-me':'')},'@'+name));if(name.length+1<t.length)out.push(t.slice(name.length+1))}
    last=m.index+t.length;
  }
  if(last<src.length)out.push(src.slice(last));
  return out;
}
export default {mount(api,s){
  api=feedbackAPI(api);
  const {P}=api,L=api.label,kind=api.node.component,f=api.facts,v=api.view();
  const root=api.part('body','section',{class:'nb-'+kind.replace('board-',''),'aria-label':L('label',s.title||kind.replace('board-',''))});
  const kids=()=>api.children.map(api.render),text=(tag,value,cls='')=>P.node(tag,{class:cls},value);
  const press=(key,fallback,fn,cls='nb-text-button')=>P.press(L(key,fallback),fn,cls);
  const status=()=>api.part('status','p',{class:'nb-meta',role:'status','aria-live':'polite'});
  const safe=fn=>async()=>{try{await fn()}catch(e){api.tell(String(e.message||e).replace(/^refused:\s*/,'Please try again in a little while. '))}};
  const notice=(result,message,token)=>api.feedback.finish(token,result,message);
  const open=(id,extra={})=>api.select({thread:id,replyTo:id,focus:'',quote:'',source:'',page:1,documentPage:1,documentFile:'',...extra});
  const chooseSaved=async()=>{api.feedback.clear();const orders=await api.read('rows board-order');return api.select({order:orders.find(o=>o.rule==='bookmarks')?.id||'',offset:0,thread:'',search:'',queue:'no',opens:''})};
  const chooseQueue=()=>api.select({queue:'yes',search:'',thread:'',opens:''});
  // A channel opens its own view when its world thing says so (board-channel opens=calendar); the lens
  // arranges one part per view name. Conversations stay one press away in the toolbar.
  // A list entry is a board-channel thing: a group's conversations, or (no group) a view of its own (opens=map), or a
  // chat (opens=chat chat=<chat>). Its key is its group, else its own id.
  const chooseChannel=async channel=>{api.feedback.clear();if(channel==='__saved')return chooseSaved();if(channel==='__queue')return chooseQueue();const [orders,channels]=await Promise.all([api.read('rows board-order'),api.read('rows board-channel')]);const here=channels.find(c=>channelKey(c)===channel);if(here&&!here.group)return api.select({channel:'',chat:here.opens==='chat'?here.chat||'':'',opens:here.opens||'',offset:0,thread:'',search:'',queue:'no',summary:'',navOpen:'no'});return api.select({channel,chat:'',navOpen:'no',offset:0,thread:'',search:'',queue:'no',summary:'',opens:here?.opens||'',calendarAdd:'no',calendarEvent:'',order:orders.some(o=>o.id===v.order&&o.rule==='bookmarks')?'':v.order||''})};
  const titleCase=value=>String(value||'').replace(/[-_]+/g,' ').replace(/^./,c=>c.toUpperCase());
  const icons={discussion:'☰',question:'?',event:'▦',poll:'▥',ask:'↗',offer:'♡',document:'▤',announcement:'⌖',decision:'✓'};
  const viewer=api.node.viewer?.id;
  const searchBox=()=>{if(api.draft.searchQuery!==v.search){api.draft.search=v.search||'';api.draft.searchQuery=v.search}const input=P.node('input',{'aria-label':L('search','Search the board'),placeholder:L('searchhint','Search conversations and documents'),value:api.draft.searchQuery===v.search?(api.draft.search??v.search??''):(v.search||'')});input.addEventListener('input',()=>{api.draft.search=input.value;api.draft.searchQuery=v.search});input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.isComposing)api.select({search:input.value,offset:0,queue:'no',thread:''})});return input};
  if(kind==='board-shell'){
    const channel=P.node('select',{'aria-label':L('channel','Channel'),class:'nb-phone-channel',on:{change:e=>chooseChannel(e.target.value)}},P.node('option',{value:''},L('all','All conversations')));
    Promise.all([api.read('rows board-channel'),api.read('board.badges'),api.read('rows board-order')]).then(api.guard(async([channels,people,orders])=>{const group=P.node('optgroup',{label:L('channels','Channels')});for(const c of shownChannels(channels))group.append(P.node('option',{value:channelKey(c)},L(c.label||c.title,c.label||c.title)));const personal=P.node('optgroup',{label:L('yourboard','Your board')},P.node('option',{value:'__saved'},L('saved','Saved')));const me=people.find(p=>p.id===viewer);if(me?.badges.some(b=>['leader','steward'].includes(b))){const queue=await api.read('board.queue');personal.append(P.node('option',{value:'__queue'},L('queue','Leaders’ queue')+' ('+queue.length+')'))}channel.append(group,personal);const here=channels.find(c=>c.opens==='chat'?v.opens==='chat'&&v.chat===c.chat:!c.group&&!v.channel&&c.opens===v.opens);channel.value=v.queue==='yes'?'__queue':orders.some(o=>o.id===v.order&&o.rule==='bookmarks')?'__saved':here?channelKey(here):v.channel||''})).catch(api.tell);
    const search=searchBox();search.classList.add('nb-top-search');
    const menuButton=P.press('☰',()=>api.select({navOpen:v.navOpen==='yes'?'no':'yes'}),'nb-menu-button');menuButton.setAttribute('aria-label',L('menu','Channels and chats'));menuButton.setAttribute('aria-expanded',String(v.navOpen==='yes'));
    const header=P.node('header',{class:'nb-masthead'},menuButton,text('strong',api.display('title'),'nb-brand'),channel,search,press('searchbutton','Search',()=>{if(search.value.trim())api.select({search:search.value.trim(),offset:0,queue:'no',thread:''});else{root.classList.toggle('nb-search-open');search.focus()}},'nb-search-icon'),press('compose','Write a post',()=>api.select({compose:'yes'}),'nb-primary'));
    const rendered=api.children.map(child=>({child,element:api.render(child)})),centre=rendered.find(row=>row.child.role==='nb-centre')?.element;
    for(const row of rendered)if(row.child.component==='board-navigation')row.element.classList.add('nb-navigation');
    const extras=rendered.filter(row=>row.element!==centre&&!['board-navigation','board-thread','board-composer'].includes(row.child.component));
    if(centre&&s.extras!=='alongside')centre.prepend(...extras.map(row=>row.element));
    root.append(header,P.node('main',{class:'nb-layout'},...rendered.filter(row=>!centre||s.extras==='alongside'||!extras.includes(row)).map(row=>row.element)),press('compose','＋ Write a post',()=>api.select({compose:'yes'}),'nb-compose-fab nb-primary'));
    root.classList.toggle('nb-thread-open',!!v.thread);root.classList.toggle('nb-nav-open',v.navOpen==='yes');root.classList.toggle('nb-chat-open',v.opens==='chat'&&!v.thread);root.dataset.opens=v.opens||'';
    if(v.navOpen==='yes'){const scrim=P.press('',()=>api.select({navOpen:'no'}),'nb-nav-scrim');scrim.setAttribute('aria-label',L('closemenu','Close the list'));root.append(scrim)}
    root.dataset.ready='true';return root;
  }
  if(kind==='board-navigation'){
    root.append(press('all','All conversations',()=>chooseChannel(''),!v.channel&&!v.opens?'nb-channel active':'nb-channel'));
    const links=P.node('div',{class:'nb-channel-list'}),phone=P.node('select',{'aria-label':L('channel','Channel'),on:{change:e=>chooseChannel(e.target.value)}},P.node('option',{value:''},L('all','All conversations')));
    const active=c=>c.opens==='chat'?v.opens==='chat'&&v.chat===c.chat:!c.group?!v.channel&&v.opens===c.opens:v.channel===c.group;
    api.read('rows board-channel').catch(()=>[]).then(api.guard(async channels=>{
      const none=()=>[],hasChats=channels.some(c=>c.opens==='chat');
      const [posts,seen,said,chats]=await Promise.all([api.read('rows post').catch(none),api.read('rows board-seen').catch(none),hasChats?api.read('rows said').catch(none):[],hasChats?api.read('rows chat').catch(none):[]]);
      const open=new Set((chats||[]).map(c=>c.id));
      const mine=seen.filter(r=>(r.for||r.made_by)===viewer);let section='';
      for(const ch of shownChannels(channels)){
        if((ch.section||'')!==section){section=ch.section||'';if(section)links.append(text('p',L(section,section),'nb-eyebrow nb-channel-section'))}
        let unread=0;
        if(ch.opens==='chat'){const marks=mine.filter(r=>r.group===ch.chat).map(r=>r.at).sort();const since=marks.pop();if(since)unread=said.filter(x=>x.chat===ch.chat&&x.made>since&&(x.for||x.made_by)!==viewer&&x.text).length}
        else if(ch.group){const since=mine.filter(r=>!r.group||r.group===ch.group).map(r=>r.at).sort().pop()||'1970';unread=posts.filter(p=>p.groups?.includes(ch.group)&&p.made>since&&(p.for||p.made_by)!==viewer).length}
        const label=L(ch.label||ch.title,ch.label||ch.title),button=P.press((ch.opens==='chat'?'# ':'')+label,()=>chooseChannel(channelKey(ch)),'nb-channel'+(active(ch)?' active':'')+(unread?' nb-has-unread':''));
        button.dataset.opens=ch.opens||'';if(ch.opens==='chat'&&!open.has(ch.chat)){button.dataset.locked='yes';button.append(P.node('span',{class:'nb-lock','aria-label':L('signintoread','Sign in to read the chats'),title:L('signintoread','Sign in to read the chats')},'🔒'))}if(unread){button.append(text('span',String(unread),'nb-unread'));button.setAttribute('aria-label',label+', '+unread+' '+L('unread','unread'))}
        links.append(button);phone.append(P.node('option',{value:channelKey(ch)},label));
      }
      const here=channels.find(active);phone.value=here?channelKey(here):v.channel||'';
    })).catch(api.tell);
    const personal=P.node('div',{class:'nb-personal'},press('saved','Saved',chooseSaved,'nb-channel'));
    api.read('board.badges').then(api.guard(async people=>{const me=people.find(p=>p.id===api.node.viewer?.id);if(me?.badges.some(b=>['leader','steward'].includes(b))){const queue=await api.read('board.queue'),button=press('queue','Leaders’ queue',()=>api.select({queue:'yes',search:'',thread:'',navOpen:'no'}),'nb-channel');button.append(text('span',String(queue.length),'nb-unread'));personal.append(button)}})).catch(()=>{});
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
    const summaryStatus=status();summaryStatus.textContent=api.draft.summaryStatus||'';actions.append(summaryStatus);
    api.draft.updateSummary=()=>{summaryStatus.textContent=api.draft.summaryStatus||''};
    const unavailable=message=>{
      summaryStatus.textContent=L('summaryunavailable','Summary not available.')+(message?' '+message:'');
      const button=press('summary','Summarize',()=>{});button.disabled=true;button.title=summaryStatus.textContent;actions.append(button);
    };
    api.read('model.status').then(api.guard(rows=>{
      const state=rows[0]||{};
      if(!state.up||!state.installed?.includes(state.model)){unavailable(state.reason||state.error||state.message||L('modeloffline','Summary not available. No ready local model was reported.'));return}
      const button=press('summary','Summarize',async()=>{
        if(api.draft.summaryBusy)return;api.draft.summaryBusy=true;button.disabled=true;
        api.draft.summaryStatus=L('summarising','Preparing a summary…');api.draft.updateSummary();
        const channel=v.channel||'';let timer;
        try{
          const seen=mine(await api.read('rows board-seen')),caught=await api.rows('board.catch-up'+(channel?' in='+api.Q(channel):''));
          const snapshot=await api.fire('snapshot',{value:JSON.stringify(caught)});
          timer=setTimeout(()=>{api.draft.summaryStatus=L('summarystillwaiting','Summary not available yet. The local model has not answered. You can keep reading.');api.draft.updateSummary?.()},15000);
          const summary=await api.fire('summarize',{target:snapshot.made[0]});
          const value=String(summary.text||'').replace(/^local model\s*·\s*.*?:\s+/i,'');
          if(!value.trim()||/not running|unavailable|offline/i.test(value))throw Error(L('summaryunavailable','The local model did not return a summary.'));
          if((api.view().channel||'')===channel)await api.select({summary:value,summaryChannel:channel,summarySeenAt:seen});
          api.draft.summaryStatus=L('summaryready','Summary ready.');
        }catch(e){api.draft.summaryStatus=L('summaryfailed','Summary not available. ')+String(e.message||e)}
        finally{clearTimeout(timer);api.draft.summaryBusy=false;button.disabled=false;api.draft.updateSummary?.()}
      });api.draft.updateSummary=()=>{summaryStatus.textContent=api.draft.summaryStatus||'';button.disabled=!!api.draft.summaryBusy};api.draft.updateSummary();actions.append(button);
    })).catch(api.guard(e=>unavailable(String(e.message||e))));
    if(v.summary&&api.children.length&&v.summaryChannel===(v.channel||''))root.append(P.node('div',{class:'nb-summary'},text('strong',L('modellabel','Local model summary')),text('p',v.summary,'nb-meta')));return root;
  }
  if(kind==='board-entry'){
    const button=P.press('',()=>open(f.about||f.thread||f.id,f.match==='document page'?{documentPage:f.page,documentFile:f.file_source,documentRequest:Number(api.view().documentRequest||0)+1}:{}),'nb-entry-button');
    if(f.match){button.append(text('strong',f.match==='document page'?L('page','Page')+' '+f.page+' '+L('of','of')+' '+f.title:f.title||L('conversation','Conversation')));const query=String(v.search||''),raw=f.text||'',at=raw.toLocaleLowerCase().indexOf(query.toLocaleLowerCase()),start=Math.max(0,at-55),snippet=raw.slice(start,start+220),match=snippet.toLocaleLowerCase().indexOf(query.toLocaleLowerCase()),body=P.node('p',{class:'nb-result-snippet'});if(match>=0&&query)body.append(document.createTextNode((start?'…':'')+snippet.slice(0,match)),P.node('mark',{},snippet.slice(match,match+query.length)),document.createTextNode(snippet.slice(match+query.length)));else body.textContent=snippet;button.append(body);const meta=text('p',L(f.post_kind,titleCase(f.post_kind))+' · '+api.format('stamp',f.made),'nb-meta');button.append(meta);Promise.all([api.read('board.badges'),api.read('rows board-channel')]).then(api.guard(([people,channels])=>{meta.prepend((people.find(p=>p.id===(f.for||f.made_by))?.name||L('neighbour','Neighbor'))+' · '+(channels.find(c=>f.groups?.includes(c.group))?.title||'')+' · ')}))}
    else {const categories=f.categories||[f.category].filter(Boolean);for(const c of categories)button.append(text('span',({new:'✦',decision:'✓',event:'▦',answer:'☑',busy:'☰',following:'↳'})[c]||'·','nb-catchup-icon'));button.append(text('span',f.title||f.text||f.reason||L('conversation','Conversation')))}
    root.append(button);return root;
  }
  if(kind==='board-feed'){
    root.append(...kids());const collection=api.node.collection;
    if(!api.children.length)root.append(text('span','☀','nb-empty-icon'),text('h2',L('empty','Room for a first conversation')),text('p',L('emptyhint','Ask a question, share a plan or say hello. Your neighbors will find it here.')),press('first','Start a conversation',()=>api.select({compose:'yes'}),'nb-primary'));
    if(collection&&collection.total>collection.limit){
      const bounds=pageBounds(collection.total,collection.limit,collection.offset/collection.limit);
      const previous=press('previous','← Newer',()=>api.select({offset:(bounds.page-1)*collection.limit}));
      const next=press('older','Older →',()=>api.select({offset:(bounds.page+1)*collection.limit}));
      previous.disabled=!bounds.previous;next.disabled=!bounds.next;
      root.append(P.node('nav',{class:'nb-pagination','aria-label':L('pages','Conversation pages')},previous,text('span',(bounds.start+1)+'–'+bounds.end+' / '+collection.total,'nb-meta'),next));
    }return root;
  }
  if(kind==='board-post'){
    root.dataset.post=f.id;root.dataset.kind=f.post_kind||'discussion';root.dataset.depth=f.depth||0;
    root.dataset.detail=s.detail?'yes':'no';root.style.setProperty('--excerpt-lines',Math.max(1,Math.min(9,s.excerptLines||3)));
    const identity=api.part('identity','div',{class:'nb-identity'}),author=text('strong',L('neighbour','Neighbor')),avatar=P.content('avatar','',{'aria-label':L('avatar','Neighbor initials')}),badges=api.part('badge','span',{class:'nb-role'}),stamp=text('time',api.format('stamp',f.made),'nb-meta'),channel=text('span','','nb-card-channel');stamp.dateTime=f.made||'';stamp.title=api.format('date',f.made);
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
    const upvote=P.press('↑ '+L('upvoteLabel','Upvote')+(Number(f.likes)?' '+f.likes:''),safe(()=>api.fire('like')),'nb-upvote');upvote.setAttribute('aria-label',f.you_liked?L('youupvoted','You upvoted'):L('upvoteLabel','Upvote')+'; '+(f.likes||0)+' '+L('votes','upvotes'));upvote.setAttribute('aria-pressed',!!f.you_liked);upvote.disabled=!!f.you_liked;if(f.you_liked)upvote.title=L('youupvoted','You upvoted');
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
      let existing;const button=press(action,({bookmark:'Save for later',follow:'Follow replies',hide:'Hide for me',mute:'Mute thread'})[action],safe(async()=>{const token=api.feedback.begin(L('pending','Working…'));try{if(existing){const history=await api.rows('history '+existing.id),record=String(history[0].record);await api.fire('unpersonal',{value:record.startsWith('r')?record:'r'+record});await notice(null,L('removed-'+action,'Preference removed.'),token)}else{const result=await api.fire('personal',{value:action});await notice(result,L('done-'+action,({bookmark:'Saved for later.',follow:'Following replies.',hide:'Hidden from your board.',mute:'Thread muted.'})[action]),token)}}catch(e){api.feedback.fail(token,e);throw e}}));
      api.read('rows board-mark').then(api.guard(marks=>{existing=marks.find(m=>m.about===f.id&&m.action===action);if(existing)button.textContent=L('undo-'+action,action==='bookmark'?'Remove bookmark':action==='follow'?'Unfollow replies':'Undo '+action)})).catch(api.tell);menu.append(button);
    }
    menu.append(press('why','Why is this here?',safe(async()=>{const r=await api.rows('board.why-here '+f.id);api.tell(r[0]?.why||'')})),press('history','Edit history',safe(async()=>{const rows=await api.rows('history '+f.id),words={post:'Posted',reply:'Replied',set:'Edited',like:'Upvoted',vote:'Voted',pin:'Pinned',forget:'Hidden',undo:'Undone','board.decide':'Decision recorded','board.answer':'Answer marked'};const body=P.node('section',{},text('h2',L('history','Edit history')),...rows.map(r=>P.node('section',{},text('p',api.format('stamp',r.at)+' · '+(r.sealed?L('privateaction','Private action'):r.by||L('neighbour','Neighbor'))+' · '+L(r.word,words[r.word]||'Updated')),...(r.facts||[]).filter(f=>['title','text','outcome','forget_reason'].includes(f.aspect)&&!f.removed).map(f=>text('p',String(f.value))))));P.overlay('dialog',body,{label:L('history','Edit history')})})),press('report','Report to leaders',()=>api.select({report:f.id})));details.append(menu);actions.append(details);root.append(actions);
    const owner=f.for||f.made_by;
    api.read('board.badges').then(api.guard(async people=>{
      const viewer=api.node.gestures[0]?.env.viewer.id,profile=people.find(p=>p.id===viewer),groups=f.groups||Object.keys(f).filter(k=>k.startsWith('in:')).map(k=>k.slice(3));
      const leads=profile?.badges.includes('steward')||(profile?.leads||[]).some(g=>groups.includes(g));
      if(leads&&!f.reply_to){menu.append(press('leaderhide','Hide with a reason',()=>api.select({hide:f.id})),press('decide','Record a decision',()=>api.select({decide:f.id})));if(f.post_kind==='announcement')menu.append(press('pin','Pin until…',()=>api.select({pin:f.id})))}
      if(f.reply_to){const thread=(await api.read('rows post')).find(t=>t.id===f.thread);if(thread?.answered===f.id)root.prepend(text('p',L('markedanswer','Marked answer ✓'),'nb-state'));if(thread?.post_kind==='question'&&((thread.for||thread.made_by)===viewer||leads))actions.append(press('answer','Mark as answer',safe(()=>api.fire('answer',{target:f.thread,reply:f.id}))))}
      if(owner===viewer||leads)menu.append(press('edit','Edit post',()=>api.select({edit:f.id,editText:f.text||''})));
    })).catch(api.tell);
    if(f.post_kind==='event'){
      const toggle=P.node('div',{class:'nb-rsvp',role:'group','aria-label':L('attendance','Your attendance')}),buttons={};for(const state of ['going','maybe']){buttons[state]=press(state,titleCase(state),safe(async()=>{await api.feedback.run('rsvp',{value:state},L('rsvpsaved','Attendance saved.'));}),'nb-soft');buttons[state].setAttribute('aria-pressed','false');toggle.append(buttons[state])}
      const counts=text('p','','nb-event-count');root.insertBefore(counts,actions);
      api.read('rows board-rsvp').then(api.guard(rows=>{const all=rows.filter(r=>r.about===f.id),own=all.find(r=>(r.for||r.made_by)===viewer);if(own)buttons[own.status]?.setAttribute('aria-pressed','true');counts.textContent=all.filter(r=>r.status==='going').length+' '+L('goingcount','going')+(Number(f.seats)>0?' · '+Number(f.seats_left||0)+' '+L('left','places left'):'')}));
      actions.append(toggle,press('calendar','Add to calendar',safe(async()=>{await api.downloadReading('board.calendar '+f.id)})));
    }
    return root;
  }
  if(kind==='board-thread'){
    const threadKey=s.threadKey||'thread',replyKey=s.replyKey||'replyTo';
    v.thread=v[threadKey];v.replyTo=v[replyKey];
    if(!v.thread){root.hidden=true;return root}
    root.append(P.node('div',{class:'nb-titleline'},press('back','← Back',()=>api.select({[threadKey]:'',[replyKey]:'',quote:''})),text('h2',L('conversation','Conversation'))),...kids());
    const target=v.focus&&root.querySelector('[data-post="'+CSS.escape(v.focus)+'"]');
    if(target){target.classList.add('nb-focus');if(api.draft.focused!==v.thread+' '+v.focus){api.draft.focused=v.thread+' '+v.focus;requestAnimationFrame(()=>target.scrollIntoView({block:'center'}))}}
    const containsTarget=n=>n.facts?.id===v.thread||(n.children||[]).some(containsTarget);
    if(!api.children.some(containsTarget)){if(!root.querySelector('.nb-notice'))root.append(text('p',L('unavailablethread','This conversation is unavailable.')));return root}
    const form=P.node('form',{'aria-label':L('replyform','Write a reply')}),input=api.part('reply','textarea',{'aria-label':L('replytext','Your reply'),placeholder:L('replyhint','Add something to the conversation…'),value:api.draft.text||'',rows:3}),out=status();
    input.addEventListener('input',()=>{api.draft.text=input.value});
    if(v.quote)form.append(P.node('blockquote',{},v.quote),press('removequote','Remove quote',()=>api.select({quote:'',source:''})));
    const submit=P.node('button',{type:'submit',class:'nb-primary'},L('sendreply','Post reply'));
    const update=()=>{input.value=api.draft.replyBusy?'':api.draft.text||'';input.disabled=!!api.draft.replyBusy;submit.disabled=!!api.draft.replyBusy||!input.value.trim();out.textContent=api.draft.replyOutcome||''};
    api.draft.updateReply=update;input.addEventListener('input',update);update();
    P.submit(form,async e=>{
      e.preventDefault();if(api.draft.replyBusy||!input.value.trim())return;
      const sentText=input.value,target=v.replyTo||v.thread;
      api.draft.text=sentText;api.draft.replyBusy=true;api.draft.replyOutcome=L('replypending','Posting reply…');update();
      try{
        const participant=(await api.rows('look '+target))[0];
        await api.fire('reply',{target,fields:{text:sentText,...(v.quote?{quote:v.quote,source:v.source,page:v.page}:{})},saw:{[participant.id]:participant.rev}});
        if(api.draft.text===sentText)api.draft.text='';
        api.draft.replyOutcome=L('replyposted','Reply posted.');
        if(api.view().quote===v.quote&&api.view().source===v.source)await api.select({quote:'',source:''});
      }catch(err){api.draft.replyOutcome=String(err.message||err)}
      finally{api.draft.replyBusy=false;api.draft.updateReply?.()}
    });form.append(input,submit,out);root.append(form);return root;
  }
  if(kind==='board-chat'){
    // One chat thing, read through the authored collection (`of reading:"chat $view.chat …"`). Every write is an
    // authored gesture: send, edit, remove, react, pin, seen. Local state (draft, reply, open menus, scroll) lives in
    // api.draft per chat, because every projection mounts this part again.
    const chatId=v[s.chatKey||'chat'];
    if(!chatId){root.hidden=true;return root}
    const q=api.Q||(x=>JSON.stringify(String(x)));
    const store=api.draft.chats||(api.draft.chats={});
    const st=store[chatId]||(store[chatId]={text:'',older:[],reply:null,editing:'',editText:'',picker:'',confirm:'',active:'',outcome:'',refused:false,busy:false,acting:false,atBottom:true,anchor:null,newAfter:null,seenFired:'',olderDone:false,loadingOlder:false,flash:'',showPins:false});
    const emoji=String(s.emoji||'👍 ❤️ 😂 🎉 😮 😢 🙏 👀').split(/\s+/).filter(Boolean);
    const groupMs=Math.max(0,Number(s.groupMinutes??7))*60000;
    const me=api.node.viewer||{},myName=String(me.name||'');
    // Lines come from an authored collection when one is arranged, else from the chat reading itself: a refused
    // reading (a signed-out visitor, a chat they cannot see) becomes a sign-in panel, never a stopped part.
    const own=!api.children.length;
    let current=own?(st.liveFor===chatId?st.live||[]:[]):api.children.map(c=>c.facts),rows,byId;
    const setRows=list=>{const ids=new Set(list.map(r=>r.id));rows=[...st.older.filter(r=>!ids.has(r.id)),...list];byId=new Map(rows.map(r=>[r.id,r]))};setRows(current);
    let leader=false,title=s.title||'';
    const clean=e=>String(e?.message||e||'').replace(/^refused:\s*/i,'');
    const raf=fn=>(api.requestAnimationFrame||requestAnimationFrame)(fn);
    const saw=r=>r&&r.rev!==undefined?{saw:{[r.id]:r.rev}}:{};
    const timeOf=at=>P.formatValue(at,'time');
    const dayOf=at=>{const d=new Date(at);return Number.isFinite(+d)?d.toDateString():''};
    const dayLabel=at=>{const rel=P.formatValue(at,'relative-date');return rel==='Today'||rel==='Yesterday'?L(rel.toLowerCase(),rel):new Date(at).toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric'})};
    const author=r=>chatAuthor(r),mine=r=>chatMine(r,me);
    const canEdit=r=>!r.removed&&(r.can_edit??mine(r));
    const canRemove=r=>!r.removed&&(r.can_remove??(mine(r)||leader));
    const excerptOf=r=>{const x=chatReply(r,byId);return x?{id:x.id,name:x.name||L('neighbour','Neighbor'),text:x.removed?L('removedmessage','Message removed'):String(x.text||'').replace(/\*\*|`|(^|\s)\*(?=\S)|(?<=\S)\*(?=\s|$)/g,'$1').replace(/\s+/g,' ').slice(0,140)}:null};
    // the one place a person's words become DOM: text nodes and a few safe elements, never HTML
    const words=text=>chatInline(P,text,myName);
    const head=P.node('header',{class:'nb-chat-head'}),pinsBox=P.node('div',{class:'nb-chat-pins'});
    const log=P.node('div',{class:'nb-chat-log',role:'log','aria-live':'polite','aria-label':L('messages','Messages'),tabindex:0});
    const latest=P.press(L('jumplatest','Jump to latest ↓'),()=>{st.atBottom=true;st.anchor=null;log.scrollTop=log.scrollHeight;latest.hidden=true},'nb-chat-latest');latest.hidden=st.atBottom;
    const titleText=text('h1','#'+' '+(title||L('chat','Chat')));
    head.append(titleText);
    const findMsg=id=>[...log.querySelectorAll('.nb-msg')].find(n=>n.dataset.said===id);
    const jump=id=>{const n=findMsg(id);if(!n){api.tell(L('notloaded','That message is further back. Scroll up to load earlier messages.'));return}
      st.atBottom=false;st.flash=id;n.dataset.flash='yes';n.scrollIntoView({block:'center',behavior:'smooth'});(api.setTimeout||setTimeout)(()=>{if(st.flash===id)st.flash='';delete n.dataset.flash},1800)};
    const act=async(event,values,before)=>{
      if(st.acting)return false;st.acting=true;st.outcome='';before?.();st.redraw?.();
      try{await api.fire(event,values);return true}
      catch(e){st.outcome=clean(e);st.refused=true;return false}
      finally{st.acting=false;st.redraw?.()}
    };
    const drawPins=()=>{
      const pinned=rows.filter(r=>r.pinned&&!r.removed);pinsBox.replaceChildren();pinsBox.hidden=!pinned.length;if(!pinned.length)return;
      const toggle=P.press('📌 '+pinned.length+' '+L(pinned.length===1?'pinnedone':'pinnedmany',pinned.length===1?'pinned message':'pinned messages'),()=>{st.showPins=!st.showPins;drawPins()},'nb-chat-pintoggle');toggle.setAttribute('aria-expanded',String(!!st.showPins));pinsBox.append(toggle);
      if(st.showPins)for(const r of pinned){const b=P.press('',()=>jump(r.id),'nb-chat-pin');b.append(text('strong',r.name||L('neighbour','Neighbor')),text('span',String(r.text||'').slice(0,160)));pinsBox.append(b)}
    };
    const message=(r,grouped)=>{
      const own=mine(r),mention=!own&&chatMentions(r,me);
      const box=P.node('article',{class:'nb-msg'+(grouped?' nb-msg-grouped':'')+(own?' nb-msg-mine':'')+(mention?' nb-msg-mention':''),'data-said':r.id,'aria-label':(r.name||author(r))+', '+timeOf(r.at)});
      box.dataset.said=r.id;if(st.flash===r.id)box.dataset.flash='yes';if(st.active===r.id)box.dataset.active='yes';if(mention)box.dataset.mention='yes';if(grouped)box.dataset.grouped='yes';
      // touch: a long press (or a tap) opens this line's actions; the press never becomes the shared right-click menu
      let press=null;const stop=()=>{clearTimeout(press);press=null};
      const open=()=>{st.pressed=true;st.active=r.id;st.picker='';st.confirm='';st.redraw?.()};
      box.addEventListener('pointerdown',e=>{st.pointer=e.pointerType||'mouse';st.pressed=false;if(st.pointer!=='touch'||e.target?.closest?.('button,a,textarea'))return;stop();press=setTimeout(()=>{press=null;open()},Number(s.longPressMs||450))});
      for(const end of ['pointerup','pointercancel','pointerleave'])box.addEventListener(end,stop);
      box.addEventListener('pointermove',e=>{if(press&&(Math.abs(e.movementX||0)+Math.abs(e.movementY||0))>6)stop()});
      box.addEventListener('contextmenu',e=>{if(st.pointer==='touch'){e.preventDefault();if(!st.pressed)open()}});
      box.addEventListener('click',e=>{if(st.pointer!=='touch'||e.target?.closest?.('button,a,textarea'))return;if(st.pressed){st.pressed=false;return}st.active=st.active===r.id?'':r.id;st.picker='';st.redraw?.()});
      const gutter=P.node('div',{class:'nb-msg-gutter'});
      if(grouped){const t=P.node('time',{class:'nb-msg-hovertime',datetime:r.at||'',title:r.at?new Date(r.at).toLocaleString():''},timeOf(r.at));gutter.append(t)}
      else gutter.append(P.node('span',{class:'nb-msg-avatar','aria-hidden':'true'},P.formatValue(r.name||author(r)||'?','initials')||'?'));
      const main=P.node('div',{class:'nb-msg-main'});
      if(!grouped){
        const line=P.node('div',{class:'nb-msg-head'},text('strong',r.name||author(r)||L('neighbour','Neighbor'),'nb-msg-name'));
        for(const b of chatBadges(r))line.append(P.node('span',{class:'nb-msg-badge','data-badge':b},L(b,b)));
        const t=P.node('time',{class:'nb-meta',datetime:r.at||'',title:r.at?new Date(r.at).toLocaleString():''},timeOf(r.at));line.append(t);main.append(line);
      }
      const ex=excerptOf(r);
      if(ex)main.append(P.press('',()=>jump(ex.id),'nb-msg-replyto'));
      if(ex){const b=main.lastChild;b.setAttribute('aria-label',L('jumpreply','Go to the message this replies to'));b.append(text('span','↩','nb-msg-replyicon'),text('strong',ex.name),text('span',ex.text,'nb-msg-replytext'))}
      if(r.removed)main.append(text('p',L('removedmessage','Message removed'),'nb-msg-text nb-msg-removed'));
      else if(st.editing===r.id){
        const editor=api.part('edit','textarea',{class:'nb-chat-input nb-msg-editor','aria-label':L('editmessage','Edit your message'),rows:2});editor.value=st.editText;
        const save=()=>{const value=editor.value.trim();if(!value||value===String(r.text||'').trim()){st.editing='';st.redraw?.();return}
          act('edit',{target:r.id,value,...saw(r)},()=>{st.editText=editor.value}).then(ok=>{if(ok){st.editing='';st.editText='';st.redraw?.()}})};
        editor.addEventListener('input',()=>{st.editText=editor.value;grow(editor)});
        editor.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();save()}else if(e.key==='Escape'){e.preventDefault();e.stopPropagation?.();st.editing='';st.editText='';st.redraw?.()}});
        main.append(editor,P.node('p',{class:'nb-meta nb-msg-edithint'},L('edithint','Enter to save · Esc to cancel · '),P.press(L('save','Save'),save,'nb-text-button'),P.press(L('cancel','Cancel'),()=>{st.editing='';st.redraw?.()},'nb-text-button')));
        raf(()=>{if(editor.isConnected!==false&&st.editing===r.id&&document.activeElement!==editor){editor.focus();const n=editor.value.length;editor.setSelectionRange?.(n,n);grow(editor)}});
      }else{
        const body=P.node('p',{class:'nb-msg-text'},...words(r.text));
        if(r.edited)body.append(P.node('span',{class:'nb-msg-edited',title:Number(r.edited)?new Date(Number(r.edited)*1000).toLocaleString():''},' ('+L('edited','edited')+')'));
        main.append(body);
        for(const f of (r.files||[]))main.append(P.node('p',{class:'nb-meta nb-msg-file'},'📎 '+(f.name||f.id||L('file','File'))));
      }
      if(r.pinned&&!r.removed)main.append(text('span','📌 '+L('pinned','Pinned'),'nb-msg-pinned'));
      const reactions=(r.reactions||[]).filter(x=>Number(x.count)>0);
      if(reactions.length&&!r.removed){
        const strip=P.node('div',{class:'nb-msg-reactions',role:'group','aria-label':L('reactions','Reactions')});
        for(const x of reactions){const b=P.press(x.emoji+' '+x.count,()=>act('react',{target:r.id,value:x.emoji,...saw(r)}),'nb-react'+(x.mine?' nb-react-mine':''));b.setAttribute('aria-pressed',String(!!x.mine));b.title=(x.names||[]).join(', ')||'';b.setAttribute('aria-label',x.emoji+' '+x.count+(x.names?.length?' · '+x.names.join(', '):''));b.dataset.emoji=x.emoji;strip.append(b)}
        strip.append(P.press('＋',()=>{st.picker=st.picker===r.id?'':r.id;st.redraw?.()},'nb-react nb-react-add'));strip.lastChild.setAttribute('aria-label',L('addreaction','Add a reaction'));
        main.append(strip);
      }
      if(st.picker===r.id&&!r.removed){
        const picker=P.node('div',{class:'nb-emoji-picker',role:'menu','aria-label':L('chooseemoji','Choose a reaction')});
        for(const e of emoji){const b=P.press(e,()=>act('react',{target:r.id,value:e,...saw(r)},()=>{st.picker=''}),'nb-emoji');b.setAttribute('aria-label',L('reactwith','React with')+' '+e);b.dataset.emoji=e;picker.append(b)}
        main.append(picker);
      }
      if(st.confirm===r.id){
        main.append(P.node('div',{class:'nb-msg-confirm',role:'alertdialog','aria-label':L('confirmdelete','Delete this message?')},text('span',L('confirmdelete','Delete this message?')),
          P.press(L('delete','Delete'),()=>act('remove',{target:r.id,...saw(r)}).then(ok=>{if(ok){st.confirm='';st.redraw?.()}}),'nb-danger'),
          P.press(L('cancel','Cancel'),()=>{st.confirm='';st.redraw?.()},'nb-text-button')));
      }
      box.append(gutter,main);
      if(!r.removed&&st.editing!==r.id){
        const tools=P.node('div',{class:'nb-msg-tools',role:'toolbar','aria-label':L('messageactions','Message actions')});
        const tool=(key,icon,label,fn,cls='')=>{const b=P.press(icon,fn,'nb-msg-tool'+cls);b.setAttribute('aria-label',L(key,label));b.title=L(key,label);b.dataset.tool=key;tools.append(b)};
        tool('react','☺',L('addreaction','Add a reaction'),()=>{st.picker=st.picker===r.id?'':r.id;st.confirm='';st.redraw?.()});
        tool('reply','↩',L('reply','Reply'),()=>{st.reply={id:r.id};st.active='';st.redraw?.();raf(()=>composer.focus())});
        if(canEdit(r))tool('edit','✎',L('edit','Edit'),()=>{st.editing=r.id;st.editText=String(r.text||'');st.picker='';st.confirm='';st.redraw?.()});
        if(r.can_pin??leader)tool(r.pinned?'unpin':'pin','📌',r.pinned?L('unpin','Unpin'):L('pin','Pin'),()=>act(r.pinned?'unpin':'pin',{target:r.id,...saw(r)}));
        if(canRemove(r))tool('delete','🗑',L('delete','Delete'),()=>{st.confirm=r.id;st.picker='';st.redraw?.()},' nb-msg-tool-danger');
        box.append(tools);
      }
      return box;
    };
    const drawLog=()=>{
      log.replaceChildren();
      if(!st.olderDone&&rows.length>=Number(s.pageSize||api.node.collection?.limit||50)){
        const more=P.press(st.loadingOlder?L('loading','Loading…'):L('loadolder','Load earlier messages'),()=>loadOlder(),'nb-text-button nb-chat-older');more.disabled=!!st.loadingOlder;log.append(more);
      }
      if(!rows.length)log.append(P.node('div',{class:'nb-chat-empty'},text('span','☀','nb-empty-icon'),text('h2',L('chatempty','No messages yet')),text('p',L('chatemptyhint','Say hello. Everyone in this chat will see it.'),'nb-meta')));
      let prev=null,newShown=false;
      for(const r of rows){
        const day=dayOf(r.at);
        if(day&&(!prev||dayOf(prev.at)!==day))log.append(P.node('div',{class:'nb-chat-day',role:'separator'},text('span',dayLabel(r.at))));
        const isNew=!newShown&&st.newAfter&&String(r.at||'')>st.newAfter&&!mine(r);
        if(isNew){newShown=true;log.append(P.node('div',{class:'nb-chat-new',role:'separator','aria-label':L('newmessages','New messages')},text('span',L('new','New'))))}
        const grouped=!!prev&&!isNew&&author(prev)===author(r)&&dayOf(prev.at)===day&&!chatReply(r,byId)&&!prev.removed&&(new Date(r.at)-new Date(prev.at))<groupMs;
        log.append(message(r,grouped));prev=r;
      }
    };
    // composer: Enter sends, Shift+Enter is a new line; the box clears at once and the words come back on refusal
    const form=P.node('form',{class:'nb-chat-composer','aria-label':L('chatcompose','Send a message')});
    const replyBar=P.node('div',{class:'nb-chat-replybar'});
    const composer=api.part('composer','textarea',{class:'nb-chat-input','aria-label':L('chatmessage','Message'),placeholder:L('chathint','Message')+(title?' #'+title:''),rows:1,enterkeyhint:'send'});
    const sendButton=P.node('button',{type:'submit',class:'nb-primary nb-chat-send','aria-label':L('send','Send')},L('send','Send'));
    const out=P.node('div',{class:'nb-chat-status',role:'status','aria-live':'polite'});
    function grow(box){if(!box.style)return;box.style.height='auto';if(box.scrollHeight)box.style.height=Math.min(Number(s.maxComposerHeight||200),box.scrollHeight)+'px'}
    const drawComposer=()=>{
      replyBar.replaceChildren();const ex=st.reply&&excerptOf({reply_to:st.reply.id});replyBar.hidden=!ex;
      if(ex)replyBar.append(text('span',L('replyingto','Replying to')+' ','nb-meta'),text('strong',ex.name),text('span',ex.text,'nb-msg-replytext'),P.press('✕',()=>{st.reply=null;st.redraw?.();composer.focus()},'nb-text-button nb-chat-cancelreply'));
      if(ex)replyBar.lastChild.setAttribute('aria-label',L('cancelreply','Cancel reply'));
      if(composer.value!==st.text)composer.value=st.text;
      sendButton.disabled=!!st.busy||!composer.value.trim();
      out.replaceChildren();
      if(st.outcome){out.append(text('span',st.outcome,'nb-chat-refusal'));if(/sign(ed)? ?in|log ?in/i.test(st.outcome)){const a=P.node('a',{class:'nb-primary nb-chat-signin',href:s.signinUrl||'/signin',target:'_top'},L('signin','Sign in'));out.append(a)}}
      out.hidden=!st.outcome;
    };
    const send=async()=>{
      if(st.busy)return;const said=composer.value;if(!said.trim())return;
      const reply=st.reply;st.busy=true;st.outcome='';st.text='';st.reply=null;st.atBottom=true;st.anchor=null;composer.value='';grow(composer);drawComposer();
      try{await api.fire('send',{fields:{text:said.trim(),...(reply?{reply_to:reply.id}:{})}});st.refused=false}
      catch(e){st.outcome=clean(e);st.refused=true;st.text=st.text.trim()?said+'\n'+st.text:said;if(!st.reply)st.reply=reply}
      finally{st.busy=false;st.redraw?.();if(st.refused)st.focusComposer?.()}
    };
    composer.addEventListener('input',()=>{st.text=composer.value;if(st.outcome&&!st.refused)st.outcome='';grow(composer);sendButton.disabled=!!st.busy||!composer.value.trim()});
    composer.addEventListener('keydown',e=>{
      if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&!e.ctrlKey){e.preventDefault();send()}
      else if(e.key==='Escape'&&st.reply){e.preventDefault();st.reply=null;st.redraw?.()}
      else if(e.key==='ArrowUp'&&!composer.value){const last=[...rows].reverse().find(r=>canEdit(r));if(last){e.preventDefault();st.editing=last.id;st.editText=String(last.text||'');st.redraw?.()}}
    });
    P.submit(form,e=>{e?.preventDefault?.();return send()});
    form.append(replyBar,P.node('div',{class:'nb-chat-row'},composer,sendButton),out);
    // older lines: the reading's before= page, kept locally above the live collection
    const loadOlder=async()=>{
      if(st.loadingOlder||st.olderDone||!rows.length)return;st.loadingOlder=true;st.redraw?.();
      const first=rows[0],size=Number(s.pageSize||50);
      try{const got=await api.rows('chat '+q(chatId)+' limit='+size+' before='+q(first.id));const known=new Set(rows.map(r=>r.id));const fresh=got.filter(r=>!known.has(r.id));st.older=[...fresh,...st.older];if(got.length<size||!fresh.length)st.olderDone=true;st.anchor={id:first.id,offset:0};st.atBottom=false}
      catch(e){api.tell(clean(e));st.olderDone=true}
      finally{st.loadingOlder=false;api.redraw?.()}
    };
    log.addEventListener('scroll',()=>{
      const gap=(log.scrollHeight||0)-(log.scrollTop||0)-(log.clientHeight||0);st.atBottom=gap<48;latest.hidden=st.atBottom;
      if(!st.atBottom){const first=[...log.querySelectorAll('.nb-msg')].find(n=>n.offsetTop+n.offsetHeight>log.scrollTop);if(first)st.anchor={id:first.dataset.said,offset:first.offsetTop-log.scrollTop}}
      if((log.scrollTop||0)<60&&!st.olderDone&&!st.loadingOlder&&rows.length>=Number(s.pageSize||api.node.collection?.limit||50))loadOlder();
      if(st.atBottom)markSeen();
    });
    const restore=()=>raf(()=>{if(st.atBottom||!st.anchor){log.scrollTop=log.scrollHeight||0;return}const n=findMsg(st.anchor.id);if(n)log.scrollTop=n.offsetTop-st.anchor.offset});
    const markSeen=()=>{
      const last=[...rows].reverse().find(r=>!mine(r));
      if(!last||!me.id||st.seenFired===last.id||(st.newAfter&&String(last.at||'')<=st.newAfter&&st.seenFired))return;
      // the reader's own marker for this chat (a board-seen thing, sees=me): made once, then moved to the last line read
      st.seenFired=last.id;const at=String(last.at||'');if(!at)return;
      const go=marker=>marker?api.fire('reseen',{target:marker.id,value:at,...(marker.rev!==undefined?{saw:{[marker.id]:marker.rev}}:{})}):api.fire('seen',{value:at});
      Promise.resolve(st.marker!==undefined?st.marker:api.rows('rows board-seen').then(rows=>rows.find(x=>(x.for||x.made_by)===me.id&&x.group===chatId)||null))
        .then(marker=>go(marker)).then(()=>{st.marker=undefined}).catch(()=>{st.marker=undefined});
    };
    st.redraw=()=>{if(st.locked)return drawLocked();setRows(current);drawPins();drawLog();drawComposer();restore()};
    const drawLocked=()=>{
      const link=P.node('a',{class:'nb-primary nb-chat-signin',href:s.signinUrl||'/signin',target:'_top'},L('signin','Sign in'));
      root.replaceChildren(head,P.node('div',{class:'nb-chat-locked'},text('span','🔒','nb-empty-icon'),text('h2',L('signintoread','Sign in to read the chats')),
        text('p',L('signintoreadhint','Chats are for neighbors. Scan the meeting code to join with just your name, or sign in.'),'nb-meta'),link));
      root.dataset.locked='yes';
    };
    st.focusComposer=()=>raf(()=>composer.focus());
    root.dataset.chat=chatId;
    root.append(head,pinsBox,P.node('div',{class:'nb-chat-body'},log,latest),form);
    if(st.locked)drawLocked();else{drawPins();drawLog();drawComposer();restore()}
    if(own){
      const sig=list=>list.map(r=>r.id+':'+(r.rev??'')).join(',');
      api.rows('chat '+q(chatId)+' limit='+Number(s.pageSize||50)).then(api.guard(list=>{
        list=Array.isArray(list)?list:[];const was=st.locked;st.live=list;st.liveFor=chatId;st.locked='';
        if(was||sig(list)!==sig(current)){current=list;root.replaceChildren(head,pinsBox,P.node('div',{class:'nb-chat-body'},log,latest),form);delete root.dataset.locked;st.redraw()}
      })).catch(api.guard(e=>{st.locked=clean(e)||'refused';st.liveFor=chatId;st.live=[];drawLocked()}));
    }
    // phone keyboard: keep the composer above it by fitting the chat to the visual viewport
    const vv=globalThis.visualViewport;
    if(vv&&root.getBoundingClientRect){const fit=()=>{if(innerWidth>650){root.style.height='';return}const top=Math.max(0,root.getBoundingClientRect().top);root.style.height=Math.max(260,Math.round(vv.height+vv.offsetTop-top))+'px';if(st.atBottom)log.scrollTop=log.scrollHeight};
      vv.addEventListener('resize',fit);vv.addEventListener('scroll',fit);api.cleanup(()=>{vv.removeEventListener('resize',fit);vv.removeEventListener('scroll',fit)});raf(fit)}
    // who leads, the chat's title and where this reader left off: watched readings, painted when they arrive
    Promise.all([api.read('board.badges').catch(()=>[]),api.read('rows board-channel').catch(()=>[]),st.newAfter===null?api.read('rows board-seen').catch(()=>[]):null]).then(api.guard(([people,channels,seen])=>{
      const profile=(people||[]).find(p=>p.id===me.id);leader=!!profile?.badges?.some(b=>['leader','steward'].includes(b));
      const here=(channels||[]).find(c=>c.chat===chatId);if(here&&!s.title){title=here.label||here.title;titleText.textContent='# '+L(title,title);composer.placeholder=L('chathint','Message')+' #'+L(title,title);if(here.topic)head.append(text('p',here.topic,'nb-meta nb-chat-topic'))}
      if(seen){const marks=seen.filter(x=>(x.for||x.made_by)===me.id&&x.group===chatId).sort((x,y)=>String(x.at).localeCompare(String(y.at)));st.marker=marks.at(-1)||null;st.newAfter=marks.at(-1)?.at||''}
      root.dataset.leader=leader?'yes':'no';if(st.locked)return;drawPins();drawLog();restore();if(st.atBottom)markSeen();
    })).catch(api.tell);
    return root;
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
        api.read(reading).then(api.guard(rows=>{for(const row of (key==='kind'?rows.filter(k=>boardPostKind(k)):key==='channel'?shownChannels(rows).filter(c=>c.group):rows))input.append(P.node('option',{value:key==='person'?row.id:key==='channel'?row.group:row.name},L(row.title||row.name,titleCase(row.title||row.name))));input.value=v[key]||''})).catch(api.tell);
      }
      const dates=P.node('select',{'aria-label':L('when','When'),on:{change:e=>{const value=e.target.value;if(value==='custom'){const from=P.node('input',{type:'date','aria-label':L('from','From')}),to=P.node('input',{type:'date','aria-label':L('through','Through')}),body=P.node('div',{},text('h2',L('choosedates','Choose dates')),P.node('label',{},L('from','From'),from),P.node('label',{},L('through','Through'),to));const overlay=P.overlay('dialog',body,{label:L('choosedates','Choose dates')});body.append(press('usedates','Use these dates',()=>{api.select({since:from.value?new Date(from.value+'T00:00').toISOString():'',before:to.value?new Date(new Date(to.value+'T00:00').getTime()+86400000).toISOString():'',dateRange:'custom'});overlay.close()}))}else api.select({since:value?new Date(Date.now()-Number(value)*86400000).toISOString():'',before:'',dateRange:value})}}},...['','7','30','custom'].map((value,i)=>P.node('option',{value},L(['anytime','week','month','choosedates'][i],['Any time','Past week','Past month','Choose dates…'][i]))));dates.value=v.dateRange||'';filters.append(dates);root.append(filters);
    }
    root.append(...kids());if(!api.children.length)root.append(text('p',L('noresults',v.queue==='yes'?'No reports need your attention.':'No matches yet. Try a shorter phrase or fewer filters.')));return root;
  }
  if(kind==='board-composer'){
    // One local draft per part survives projections; saved content goes through
    // the authored word and ordinary receipts, never a parallel client store.
    const special=['hide','report','decide','edit','pin'].find(key=>v[key]);
    const dialogTitle=L(special||'compose',({hide:'Hide with a reason',report:'Report to leaders',decide:'Record a decision',edit:'Edit post',pin:'Pin until…'})[special]||'Write a post');
    const form=P.node('form',{'aria-label':dialogTitle}),out=status();let close;
    const dialog=P.overlay('dialog',form,{label:dialogTitle,close:()=>api.select({compose:'no',hide:'',report:'',decide:'',edit:'',pin:''})});close=dialog.close;
    api.cleanup(()=>close(true));dialog.node.classList.add('nb-dialog');
    form.append(P.node('div',{class:'nb-titleline'},text('h2',dialogTitle),press('cancel','Cancel',close)));
    if(special){
      const label=({hide:'Reason for hiding',report:'Reason for reporting',decide:'Decision outcome',edit:'Edit post',pin:'Pin until (UTC date or time)'})[special],input=P.node('textarea',{'aria-label':label,required:'',value:special==='edit'?v.editText||'':'',rows:5});form.append(text('label',label),input);
      input.addEventListener('input',()=>{api.draft.specialText=input.value});input.value=api.draft.specialText??input.value;
      form.append(P.node('button',{type:'submit',class:'nb-primary'},L('save','Save')),out);P.submit(form,async e=>{e.preventDefault();try{const target=(await api.rows('look '+v[special]))[0];await api.fire(special,{target:v[special],value:input.value,saw:{[target.id]:target.rev},select:{compose:'no',hide:'',report:'',decide:'',edit:'',pin:''}});delete api.draft.specialText;close()}catch(err){out.textContent=String(err.message||err);api.tell(err)}});return root;
    }
    const type=P.node('select',{'aria-label':L('type','Post type'),hidden:''}),channel=P.node('select',{'aria-label':L('channel','Channel')}),title=P.node('input',{'aria-label':L('title','Title (optional)'),placeholder:L('title','Title (optional)'),value:api.draft.title||''}),body=P.node('textarea',{'aria-label':L('body','Your message'),placeholder:L('bodyhint','What would you like your neighbors to know?'),rows:5,required:'',value:api.draft.body||''}),fields=P.node('div',{class:'nb-composefields'});
    const tiles=P.node('div',{class:'nb-kind-tiles'}),step=P.node('div',{class:'nb-compose-step'}),chosen=text('strong','','nb-compose-type');
    const uploads=api.draft.uploads||(api.draft.uploads=[]),attachments=P.node('div',{class:'nb-upload-list'});
    const drawUploads=()=>{attachments.replaceChildren();for(const file of uploads){const preview=P.node('div',{class:'nb-upload-preview'},text('p',file.name,'nb-meta'),press('removeattachment','Remove',()=>{uploads.splice(uploads.indexOf(file),1);drawUploads()}));attachments.append(preview);api.file(file.id,'thumbnail').then(api.guard(({url,blob})=>{if(blob.type.startsWith('image/'))preview.prepend(P.node('img',{src:url,alt:file.name}))})).catch(()=>{})}};drawUploads();
    const save=()=>{api.draft.title=title.value;api.draft.body=body.value;api.draft.kind=type.value;api.draft.channel=channel.value};title.addEventListener('input',save);body.addEventListener('input',save);channel.addEventListener('change',save);
    let definitions=[];
    const draw=()=>{save();fields.replaceChildren();const definition=definitions.find(k=>k.name===type.value),types=JSON.parse(definition?.field_types||'{}'),defaults=JSON.parse(definition?.defaults||'{}'),labels=JSON.parse(definition?.field_labels||'{}'),advanced=P.node('details',{class:'nb-advanced'},P.node('summary',{},L('moreoptions','More options')));chosen.textContent=(definition?.compose_icon||icons[type.value]||'✦')+' '+L(definition?.compose_label||type.value,definition?.compose_label||titleCase(type.value));for(const key of String(definition?.fields||'').split(/\s+/).filter(Boolean)){const label=L(key,labels[key]||key.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase())),format=types[key]||'text',input=P.node('input',{'aria-label':label,name:key,type:format==='number'?'number':'text','data-format':format,value:api.draft[key]??defaults[key]??'',...(format==='number'?{min:1,max:10000,step:1}:{}),...(String(definition.required||'').split(' ').includes(key)?{required:''}:{})}),wrap=P.node('label',{},label,input);input.addEventListener('input',()=>{api.draft[key]=input.value});
      if(format==='datetime'){input.placeholder=L('datehint','e.g. Thu 6pm');const confirm=P.node('small',{role:'status',class:'nb-date-confirm'}),picker=P.node('input',{type:'datetime-local','aria-label':label+' · '+L('picker','Choose date and time'),'data-picker':'yes'});picker.addEventListener('change',()=>{input.value=picker.value;input.dispatchEvent(new Event('input'))});const check=()=>{const parsed=P.parseDateEntry(input.value);input.setCustomValidity(input.value&&!parsed.ok?parsed.message:'');confirm.textContent=input.value?(parsed.ok?L('dateconfirmed','That is')+' '+parsed.label:parsed.message):'';if(parsed.ok)picker.value=parsed.local};input.addEventListener('input',check);wrap.append(P.node('details',{class:'nb-date-picker'},P.node('summary',{},L('choosewhen','Choose date and time…')),picker),confirm);check()}
      (String(s.advancedFields||'closes place').split(' ').includes(key)?advanced:fields).append(wrap)
    }if(advanced.children.length>1)fields.append(advanced);
      if(definition?.compose_fields_first==='yes')step.insertBefore(fields,body);else step.insertBefore(body,fields);
      body.rows=Math.max(1,Math.min(12,Number(definition?.compose_message_rows)||5));
      tiles.hidden=!!api.draft.chosen;step.hidden=actions.hidden=!api.draft.chosen};
    api.read('rows kind').then(api.guard(async kinds=>{const people=await api.read('board.badges'),me=people.find(p=>p.id===viewer),leader=me?.badges.some(b=>['steward','leader'].includes(b));definitions=kinds.filter(k=>boardPostKind(k,s.kindScope||'board')&&(!k.leaders_only||leader));const rank=k=>{const n=['discussion','question','event','poll','ask','document'].indexOf(k.name);return n<0?99:n},ordered=[...definitions].sort((a,b)=>rank(a)-rank(b));for(const k of ordered){type.append(P.node('option',{value:k.name},L(k.name,titleCase(k.name))));tiles.append(P.press('',()=>{type.value=k.name;api.draft.chosen=true;draw()},'nb-kind-tile'));const tile=tiles.lastChild;tile.dataset.postType=k.name;tile.append(text('span',k.compose_icon||icons[k.name]||'✦','nb-tile-icon'),text('strong',L(k.compose_label||k.name,k.compose_label||titleCase(k.name))),text('span',L(k.compose_description||k.name+'-description',k.compose_description||'Share this with your neighbors.')))}type.value=api.draft.kind||'discussion';draw()})).catch(api.tell);type.addEventListener('change',()=>{api.draft.chosen=true;draw()});
    api.read('rows board-channel').then(api.guard(all=>{const channels=shownChannels(all).filter(c=>c.group);for(const c of channels)channel.append(P.node('option',{value:c.group},L(c.title,c.title)));channel.value=api.draft.channel||(channels.some(c=>c.group===v.channel)?v.channel:'')||channels.find(c=>c.compose_default==='yes')?.group||channels.find(c=>['Neighbors','Neighbours'].includes(c.title))?.group||channels[0]?.group}));
    const upload=api.part('upload','input',{type:'file',multiple:'',hidden:'','aria-label':L('attach','Add photos or files')}),dropzone=P.node('div',{class:'nb-upload',tabindex:0,role:'button','aria-label':L('attach','Add photos or files')},text('strong',L('dropfiles','Drop photos or files here')),text('span',L('browsefiles','or choose files')));
    const prepare=async files=>{submit.disabled=true;for(const file of files){out.textContent=L('uploading','Preparing your attachment…');try{const result=await api.upload(file,channel.value);uploads.push({id:result.made[0],name:file.name});drawUploads();out.textContent=L('privateupload','Ready. Attachments stay private until you post.')}catch(e){out.textContent=String(e.message||e)}}submit.disabled=false};upload.addEventListener('change',()=>prepare(upload.files));dropzone.addEventListener('click',()=>upload.click());dropzone.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();upload.click()}});dropzone.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('over')});dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('over'));dropzone.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('over');prepare(e.dataTransfer.files)});
    const submit=P.node('button',{type:'submit',class:'nb-primary'},L('publish','Post to neighbors'));
    const actions=P.node('footer',{class:'nb-compose-actions'},submit,out);
    step.append(P.node('div',{class:'nb-titleline'},chosen,press('changetype','← Choose a different post',()=>{save();api.draft.chosen=false;draw()})),P.node('label',{},L('channel','Channel'),channel),title,body,fields,dropzone,upload,attachments);form.append(type,tiles,step,actions);
    P.submit(form,async e=>{e.preventDefault();if(!api.draft.chosen||api.draft.postBusy)return;save();api.draft.postBusy=true;submit.disabled=true;out.textContent=L('posting','Posting…');try{const values={text:body.value,title:title.value,post_kind:type.value,in:channel.value};for(const input of fields.querySelectorAll('input[name]'))if(input.value)values[input.name]=input.dataset.format==='datetime'?P.parseDateEntry(input.value).iso:input.value;
      // Retain a successful post if a later attach refuses; retry attaches to it
      // instead of creating duplicate conversations.
      const finished={offset:0,compose:'no',hide:'',report:'',decide:'',edit:'',pin:''};
      if(!api.draft.post){const receipt=await api.fire('post',{fields:values,...(!uploads.length?{select:finished}:{})});api.draft.post=receipt.made[0]}
      for(const file of [...uploads]){const rows=await Promise.all([api.rows('look '+file.id),api.rows('look '+api.draft.post)]),saw=Object.fromEntries(rows.flat().map(r=>[r.id,r.rev]));await api.fire('attach',{file:file.id,target:api.draft.post,saw,...(uploads.length===1?{select:finished}:{})});uploads.splice(uploads.indexOf(file),1)}
      for(const key of Object.keys(api.draft))delete api.draft[key];close();await api.select({offset:0,compose:'no',hide:'',report:'',decide:'',edit:''});
    }catch(e){out.textContent=L('failedpost','Could not finish posting. Your draft is kept. ')+String(e.message||e).replace(/^refused:\s*/,'');api.tell(out.textContent)}finally{api.draft.postBusy=false;submit.disabled=false}});return root;
  }
  return root;
}};
