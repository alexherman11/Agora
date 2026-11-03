export default {mount(api,s){
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
      const draw=()=>{api.draft.page=page;stamp.textContent=L('page','Page')+' '+page+' / '+data.pages.length;content.textContent=data.pages[page-1]||''};draw();
      const quote=text=>{if(!text){status.textContent=L('selectquote','Select a passage on this page first.');return}api.select({quote:text,source:f.id,page,replyTo:api.view().thread})};
      const picker=P.node('select',{'aria-label':L('pagepicker','Choose a page')});for(let i=1;i<=data.pages.length;i++)picker.append(P.node('option',{value:i},L('page','Page')+' '+i));picker.value=page;picker.addEventListener('change',()=>{page=Number(picker.value);draw()});
      root.append(P.node('div',{class:'nb-actions'},P.press(L('previous','Previous page'),()=>{page=Math.max(1,page-1);picker.value=page;draw()}),stamp,picker,P.press(L('next','Next page'),()=>{page=Math.min(data.pages.length,page+1);picker.value=page;draw()})),content);
      const selection=P.selectionAction(content,api.draft,()=>page+':'+data.pages[page-1],quote,{label:L('quote','Quote selection')});api.cleanup(selection.dispose);
      root.append(P.node('details',{class:'nb-more'},P.node('summary',{},L('more','More')),P.press(L('quote','Quote selection'),selection.quote)));
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
