// Authored slots, world readings and guarded gestures; no network or native door.
const uploadQueues=new Map();
export default {mount(api,s){
  const {P}=api,L=api.label,kind=api.node.component,v=api.view();
  const root=api.part('body','section',{class:'documents '+kind,'aria-label':L('label','Documents')});
  const status=api.part('status','p',{role:'status','aria-live':'polite'});
  const button=(label,fn)=>P.press(label,api.guard(async()=>{try{await fn()}catch(e){status.textContent=String(e.message||e)}}));
  const folder=()=>v.documentsFolder||s.library;
  const choose=id=>api.select({documentsFolder:id,documentsOpen:''});
  if(kind==='document-library'){
    root.append(api.part('heading','h2',{},api.display('title')||L('title','Research & documents')));
    for(const child of api.children)root.append(api.render(child));
  }else if(kind==='document-toolbar'){
    const crumbs=api.part('breadcrumbs','nav',{'aria-label':L('path','Folder path')});
    crumbs.append(button(L('all','All documents'),()=>choose(s.library)));
    root.append(crumbs);
    api.read('rows document-folder').then(api.guard(rows=>{
      const path=[],seen=new Set();let id=folder();
      while(id&&id!==s.library&&!seen.has(id)){seen.add(id);const row=rows.find(r=>r.id===id);if(!row)break;path.unshift(row);id=row.parent}
      for(const row of path)crumbs.append(button(row.name,()=>choose(row.id)));
    })).catch(api.tell);
    const input=api.part('name','input',{'aria-label':L('foldername','Folder name'),required:'',maxlength:200});
    // No <form>: the widget frame is sandboxed without allow-forms, so the browser drops submit events (3 Nov).
    const make=api.guard(async()=>{if(!input.value.trim())return;try{await api.fire('folder',{parent:folder(),value:input.value.trim()});input.value=''}catch(e){status.textContent=String(e.message||e)}});
    input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();make()}});
    const form=P.node('div',{class:'document-folder-form'},P.node('label',{},L('foldername','Folder name'),input),P.press(L('newfolder','Make folder'),make));
    root.append(form,status);
  }else if(kind==='document-upload'){
    const picker=api.part('picker','input',{type:'file',multiple:'','aria-label':L('upload','Upload files')});
    const drop=api.part('drop','div',{tabindex:0,role:'button'},L('drop','Drop files here or choose from your computer'));
    const prepare=api.guard(async files=>{
      // Files dropped while a batch is still uploading join it (3 Nov: they were silently dropped). Each keeps the
      // folder it was dropped into. The queue lives in this page only: File objects never go into a draft.
      const queue=uploadQueues.get(api.node.path)||[];uploadQueues.set(api.node.path,queue);
      for(const file of Array.from(files))queue.push({file,destination:folder()});
      if(api.draft.busy)return;
      api.draft.busy=true;picker.disabled=true;
      try{
        while(queue.length){const {file,destination}=queue.shift();
          status.textContent=L('preparing','Uploading and preparing')+' '+file.name;
          const uploaded=await api.upload(file,api.facts.groups?.[0]);
          if(!uploaded.ok||!uploaded.made?.[0])throw Error(uploaded.text||'Upload failed');
          const target=uploaded.made[0];
          // Index first, then attach to the uploader's own entry. If sharing
          // refuses, retain that entry so the user can retry explicitly.
          const stored=await api.fire('store',{target,parent:destination});
          const entry=stored.made[0];
          // attach is fenced: read the new file and its entry first, so the act knows what it saw (3 Nov).
          try{const [f]=await api.rows('look '+target),[n]=await api.rows('look '+entry);
            await api.fire('attach',{target,entry,saw:{[f.id||target]:f.rev,[n.id||entry]:n.rev}})}
          catch(e){api.draft.pending={target,entry};throw e}
        }
        status.textContent=L('ready','Files are ready in this folder.');
      }catch(e){queue.length=0;api.tell(String(e.message||e))}
      finally{api.draft.busy=false;picker.disabled=false;picker.value='';await api.redraw()}
    });
    picker.addEventListener('change',()=>prepare(picker.files));
    drop.addEventListener('click',()=>picker.click());
    drop.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();picker.click()}});
    drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('over')});
    drop.addEventListener('dragleave',()=>drop.classList.remove('over'));
    drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('over');prepare(e.dataTransfer.files)});
    root.append(P.node('p',{},L('sharing','Uploaded files are shared with this library when ready.')),picker,drop,status);
    if(api.draft.pending)root.append(button(L('retry','Finish sharing uploaded file'),async()=>{
      await api.fire('attach',api.draft.pending);delete api.draft.pending;await api.redraw();
    }));
  }else if(kind==='document-list'){
    if(!api.children.length)root.append(api.part('empty','p',{},L('empty','No documents here yet. Make a folder or upload a file.')));
    for(const child of api.children)root.append(api.render(child));
  }else if(kind==='document-entry'){
    const item=s.item||api.facts,isFolder=item.kind==='document-folder';
    const title=api.part('name','button',{type:'button',on:{click:()=>isFolder?choose(item.id):api.select({documentsOpen:v.documentsOpen===item.id?'':item.id})}},(isFolder?'▸ ':'')+item.name);
    root.append(title);
    if(isFolder&&v.documentsFolder===item.id)title.setAttribute('aria-current','page');
    if(!isFolder)title.setAttribute('aria-expanded',v.documentsOpen===item.id?'true':'false');
    const details=P.node('details',{},P.node('summary',{},L('organise','Organise')));
    const name=P.node('input',{'aria-label':L('name','Name'),value:item.name,maxlength:200});
    if(item.kind!=='document-link')details.append(name,button(L('rename','Rename'),()=>api.fire('rename',{target:item.id,value:name.value,saw:{[item.id]:item.rev}})));
    const destinations=api.part('destination','select',{'aria-label':L('destination','Move into folder')});
    destinations.append(P.node('option',{value:item.library},L('all','All documents')));
    api.read('rows document-folder').then(api.guard(rows=>{
      const descendants=new Set([item.id]);let changed=true;
      while(changed){changed=false;for(const r of rows)if(descendants.has(r.parent)&&!descendants.has(r.id)){descendants.add(r.id);changed=true}}
      const path=row=>{const names=[row.name],seen=new Set([row.id]);let id=row.parent;while(id&&id!==item.library&&!seen.has(id)){seen.add(id);const parent=rows.find(r=>r.id===id);if(!parent)break;names.unshift(parent.name);id=parent.parent}return names.join(' / ')};
      for(const row of rows.filter(r=>r.library===item.library&&!descendants.has(r.id)))destinations.append(P.node('option',{value:row.id},path(row)));
      destinations.value=item.parent||item.library;
    })).catch(api.tell);
    details.append(destinations,button(L('move','Move into folder'),()=>api.fire(item.kind==='document-link'?'store':'move',{target:item.id,parent:destinations.value,saw:{[item.id]:item.rev}})));
    root.append(details,status);
    if(item.source_post){
      const source=P.node('details',{},P.node('summary',{},L('frompost','From post')+': '+(item.source_title||L('post','Neighbour post'))),P.node('p',{},item.source_text||''));
      root.append(api.part('source','div',{},source));
    }
    if(!isFolder&&v.documentsOpen===item.id)root.append(api.child('preview',{target:item.file_id,name:item.name,owner:item.upload_owner}));
  }
  return root;
}};
