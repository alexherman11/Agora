// Local to this component module: existing widget runtimes need no upgrade.
function pageBounds(total,size,page=0){
  total=Math.max(0,Math.floor(Number(total)||0));size=Math.max(1,Math.floor(Number(size)||1));
  const pages=Math.max(1,Math.ceil(total/size));
  page=Math.max(0,Math.min(pages-1,Math.floor(Number(page)||0)));
  return {page,pages,start:page*size,end:Math.min(total,(page+1)*size),previous:page>0,next:page<pages-1};
}
export default {css:`
.file-quote-reply{display:flex;flex-direction:column;gap:var(--small,8px);padding:var(--medium,12px);margin-block:var(--medium,12px);border:1px solid var(--muted,#59685f);border-radius:var(--soft,12px);background:var(--card,#fff)}
.file-quote-reply[hidden]{display:none}.file-quote-reply blockquote{white-space:pre-wrap;margin:0;border-left:3px solid var(--accent,#315f52);padding-left:var(--medium,12px)}
.file-quote-reply textarea{font:inherit;color:inherit;background:var(--paper,#faf9f5);min-height:5em;max-width:100%;box-sizing:border-box}
.nb-file button:disabled{opacity:.5;cursor:default}
`,mount(api,s){
  const {P}=api,L=api.label,f={...api.facts,id:s.target||api.facts.id,name:s.name||api.facts.name},root=api.part('body','section',{class:'nb-file','aria-label':f.name||L('attachment','Attachment')}),status=api.part('status','p',{class:'nb-meta',role:'status'},L('loading','Opening attachment…'));
  const heading=P.node('h3',{},f.name||f.title||L('attachment','Attachment'));root.append(heading,status);
  if(!f.id){status.textContent=L('empty','Choose an uploaded file to read or preview it.');return root}
  const download=async()=>{try{await api.download(f.id)}catch(e){status.textContent=String(e.message||e)}};
  root.append(api.part('download','button',{type:'button',class:'nb-text-button',on:{click:download}},L('download','Download')));
  const draw=api.guard(async results=>{
    const data=results[0];status.textContent='';
    if(data.kind==='photo'){
      heading.remove();root.classList.add('nb-photo-file');root.setAttribute('aria-label',L('photo','Photo'));
      const placeholder=P.node('div',{class:'nb-photo-placeholder',role:'status'},L('loadingphoto','Opening photo…'));
      const img=api.part('preview','img',{alt:f.alt||L('noalt','Photo; description not yet supplied'),class:'nb-photo',width:data.width,height:data.height,hidden:''});root.insertBefore(placeholder,status);root.insertBefore(img,status);
      img.addEventListener('load',()=>{img.hidden=false;placeholder.remove()});
      img.addEventListener('error',()=>{placeholder.textContent=L('unavailablephoto','This photo could not be opened.');status.textContent=L('retryphoto','Try opening this attachment again.')});
      api.file(f.id,s.variant||'content').then(api.guard(({url})=>{img.src=url})).catch(api.guard(e=>{placeholder.textContent=L('unavailablephoto','This photo is unavailable.');status.textContent=e.message}));
      const full=async()=>{try{const {url}=await api.file(f.id,'content');P.overlay('dialog',P.node('img',{src:url,alt:img.alt,class:'nb-photo-full'}),{label:img.alt})}catch(e){status.textContent=e.message}};
      img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label',L('fullphoto','Open full size photo'));img.addEventListener('click',full);img.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();full()}});
      let photo=f;
      const input=api.part('alt','input',{'aria-label':L('alt','Photo description'),value:f.alt||'',placeholder:L('alt','Photo description')});
      api.read('rows photo').then(api.guard(photos=>{photo=photos.find(p=>p.file_source===f.id)||f;input.value=photo.alt||'';img.alt=photo.alt||img.alt}));
      const viewer=api.node.viewer?.id;
      const editor=()=>root.append(P.node('details',{},P.node('summary',{},L('adddescription','Add a description')),P.node('label',{},L('alt','Photo description'),input),P.press(L('savealt','Save description'),async()=>{try{const fresh=(await api.rows('look '+photo.id))[0];await api.fire('alt',{target:photo.id,value:input.value,saw:{[photo.id]:fresh.rev}})}catch(e){status.textContent=e.message}})));
      if(s.owner){if(s.owner===viewer)editor()}
      else api.read('rows file').then(api.guard(files=>{const original=files.find(row=>row.id===f.id);if((original?.upload_owner||original?.for||original?.made_by)===viewer)editor()}));
    }else if(data.kind==='document'){
      heading.textContent='▤ '+(f.name||f.title||L('document','Document'));root.append(P.node('p',{class:'nb-meta'},data.pages.length+' '+L('pages','pages')));
      if(s.variant==='thumbnail'){root.append(P.node('p',{class:'nb-document-preview'},(data.pages[0]||'').slice(0,280)));return}
      const requested=!s.pageTarget||s.pageTarget===f.id?Number(s.page||1):1;
      const requestKey=[f.id,s.pageTarget,s.page,s.pageRequest].join('|');
      let page=Math.max(1,Math.min(data.pages.length,Number(api.draft.file===f.id&&api.draft.pageRequestKey===requestKey?api.draft.page||requested:requested)));api.draft.file=f.id;api.draft.pageRequestKey=requestKey;const content=api.part('page','div',{class:'nb-page',tabindex:0}),stamp=P.node('p',{class:'nb-meta'});
      const previous=P.press(L('previous','Previous page'),()=>{page--;draw()}),next=P.press(L('next','Next page'),()=>{page++;draw()});
      const draw=()=>{const bounds=pageBounds(data.pages.length,1,page-1);page=bounds.page+1;api.draft.page=page;
        previous.disabled=!bounds.previous;next.disabled=!bounds.next;picker.value=page;
        stamp.textContent=L('page','Page')+' '+(data.pages.length?page:0)+' / '+data.pages.length;content.textContent=data.pages[page-1]||''};
      const reply=api.part('quote-reply','section',{class:'file-quote-reply',hidden:'','aria-label':L('quotedreply','Reply with this quote')});
      const replyDraft=api.draft.quotedReply?.source===f.id?api.draft.quotedReply:null;
      const paintReply=()=>{
        const draft=api.draft.quotedReply;if(!draft||draft.source!==f.id){reply.hidden=true;return}
        reply.hidden=false;reply.replaceChildren();
        const target=s.replyTarget||draft.thread||'';
        const destination=target?(s.replyLabel||f.name||L('document','Document')):(s.startLabel||s.replyLabel||f.name||L('document','Document'));
        const has=event=>api.node.gestures.some(g=>g.event===event),event=target?'reply':'start';
        reply.append(P.node('strong',{},(target?L('replyto','Reply to'):L('newconversation','New conversation in'))+' '+destination),
          P.node('p',{},(f.name||L('document','Document'))+' · '+L('page','Page')+' '+draft.page),
          api.part('quote-text','blockquote',{},draft.quote));
        const input=api.part('reply-text','textarea',{'aria-label':L('yourreply','Your reply'),rows:3,value:draft.text||''});
        input.addEventListener('input',()=>{draft.text=input.value;send.disabled=!!draft.busy||!input.value.trim()});
        const outcome=P.node('p',{role:'status','aria-live':'polite'},draft.outcome||'');
        const send=api.part('reply-send','button',{type:'button',disabled:!!draft.busy||!draft.text?.trim()},target?L('sendreply','Post reply'):L('startreply','Start conversation with quote'));
        send.addEventListener('click',async()=>{
          if(draft.busy||!input.value.trim())return;
          const sent=input.value;draft.busy=true;send.disabled=true;outcome.textContent='';
          try{
            let values;
            if(target){const fresh=(await api.rows('look '+target))[0];values={target,fields:{text:sent,quote:draft.quote,source:f.id,page:draft.page},saw:{[target]:fresh.rev}}}
            else values={group:s.replyGroup||api.facts.groups?.[0]||'',fields:{title:f.name||L('document','Document'),text:sent+'\n\n'+draft.quote.split('\n').map(line=>'> '+line).join('\n')+'\n\n'+L('source','Source')+': [['+f.id+'|'+String(f.name||L('document','Document')).replace(/[\[\]|]/g,'')+']] · '+L('page','Page')+' '+draft.page}};
            const result=await api.fire(event,values);
            if(!target)draft.thread=result.made?.[0]||'';
            if(draft.text===sent){draft.text='';input.value=''}
            draft.outcome=L('replysent','Posted to')+' '+destination+'.';outcome.textContent=draft.outcome;
          }catch(e){draft.outcome=String(e.message||e);outcome.textContent=draft.outcome}
          finally{draft.busy=false;api.draft.replyPaint?.()}
        });
        const cancel=P.press(L('cancelquote','Dismiss quote'),()=>{if(!draft.busy){delete api.draft.quotedReply;paintReply()}});
        cancel.disabled=!!draft.busy;
        if(has(event))reply.append(input,send);
        else reply.append(P.node('p',{},L('noreply','This reader has no reply action. Select text and right-click Comment to send a quote to Conversation.')));
        reply.append(cancel,outcome);
      };
      api.draft.replyPaint=paintReply;
      const quote=text=>{
        if(!text){status.textContent=L('selectquote','Select a passage on this page first.');return}
        if(s.quoteMode==='inline'){
          if(api.draft.quotedReply?.busy)return;
          api.draft.quotedReply={...(api.draft.quotedReply?.source===f.id?api.draft.quotedReply:{}),quote:text,source:f.id,page,outcome:''};paintReply();
          reply.scrollIntoView({block:'nearest'});reply.querySelector('textarea')?.focus();return;
        }
        api.select({quote:text,source:f.id,page,replyTo:api.view().thread});
      };
      const picker=P.node('select',{'aria-label':L('pagepicker','Choose a page')});for(let i=1;i<=data.pages.length;i++)picker.append(P.node('option',{value:i},L('page','Page')+' '+i));picker.value=page;picker.addEventListener('change',()=>{page=Number(picker.value);draw()});
      draw();root.append(P.node('div',{class:'nb-actions'},previous,stamp,picker,next),content);
      const selection=P.selectionAction(content,api.draft,()=>page+':'+data.pages[page-1],quote,{label:L('quote','Quote selection')});api.cleanup(selection.dispose);
      root.append(P.node('details',{class:'nb-more'},P.node('summary',{},L('more','More')),P.press(L('quote','Quote selection'),selection.quote)));
      if(s.quoteMode==='inline'){root.append(reply);if(replyDraft)paintReply()}
      if(data.preview_status)status.textContent=L('textpreview','Readable page text · original PDF available to download.');
    }else if(data.kind==='table'){
      const columns=data.columns||[],rows=(data.rows||[]).map(r=>Object.fromEntries(columns.map((c,i)=>[c,r[i]??''])));
      root.append(api.child('table',{columns:columns.join('|'),data:rows,sortable:true,label:f.name||L('table','Table')}));
    }else if(data.kind==='media'){
      const media=api.part('preview',String(data.media_type||'').startsWith('video/')?'video':'audio',{controls:'','aria-label':f.name||L('media','Recording')});root.append(media);try{media.src=(await api.file(f.id)).url}catch(e){status.textContent=e.message}
    }else if(data.kind==='event'){
      let event;const going=P.press(L('going','Going'),()=>api.fire('rsvp',{target:event.id,saw:{[event.id]:event.rev}}).catch(api.tell)),calendar=P.press(L('calendar','Add to calendar'),()=>api.downloadGesture('calendar',{target:event.id}).catch(api.tell));
      going.disabled=calendar.disabled=true;
      root.append(P.node('p',{},api.format('stamp',data.start)+' · '+(data.location||'')),going,calendar);
      api.read('rows event').then(api.guard(events=>{event=events.find(e=>e.id===f.id||e.file_source===f.id);if(event){going.disabled=event.seats_left===0;calendar.disabled=false;if(event.seats_left===0)status.textContent=L('filled','All places filled')}})).catch(api.tell);
    }else status.textContent=data.reason||L('plainfile','File ready to download.');
  });
  if(s.content?.kind)draw([s.content]);
  else api.read('file-read '+f.id).then(draw).catch(api.guard(e=>{status.textContent=L('unavailable','This attachment is unavailable to you.')}));return root;
}};
