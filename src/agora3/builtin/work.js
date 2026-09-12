/* Native work queue: render observed tasks and send explicit authenticated commands. */
(() => {
  'use strict';
  if (!window.AgoraDesktop) return;
  const call = AgoraDesktop.request;
  const node = (tag, cls, text) => { const e=document.createElement(tag); if(cls)e.className=cls; if(text!==undefined)e.textContent=text; return e; };
  const button=node('button','','Work'); button.id='work-toggle'; button.setAttribute('aria-expanded','false');
  (document.querySelector('.topbar') || document.body).append(button);
  const panel=node('section','work-panel'); panel.id='work-panel'; panel.hidden=true; panel.setAttribute('aria-label','Work queue');
  const header=node('header'), heading=node('strong','','Work queue'), close=node('button','','×'); close.setAttribute('aria-label','Close work queue');
  header.append(heading,close); const summary=node('p','work-summary'), alert=node('p','work-error'), list=node('div','work-list'); alert.hidden=true;alert.setAttribute('role','alert');
  panel.append(header,summary,alert,list);document.body.append(panel);
  button.onclick=()=>{panel.hidden=!panel.hidden;button.setAttribute('aria-expanded',String(!panel.hidden));};close.onclick=()=>{panel.hidden=true;button.setAttribute('aria-expanded','false');};
  const cards=new Map();let polling=false;
  const labels={queued:'Waiting',starting:'Starting',running:'Working',waiting_resource:'Waiting for a resource',ready:'Candidate ready',adopted:'Adopted',blocked:'Blocked',failed:'Failed',interrupted:'Interrupted',cancelled:'Cancelled'};
  async function action(method,args){try{alert.hidden=true;const result=await call(method,args);await poll();return result;}catch(e){alert.textContent=e.message;alert.hidden=false;throw e;}}
  function card(task){
    const article=node('article','work-card');article.dataset.task=task.id;
    const title=node('h3'),state=node('span','work-state'),detail=node('p','work-detail'),progress=node('p','work-progress');
    const controls=node('div','work-controls'),inspect=node('button','','Details'),cancel=node('button','','Stop task'),retry=node('button','','Retry'),adopt=node('button','','Adopt changes');
    const details=node('div','work-details');details.hidden=true;
    const input=node('textarea');input.rows=2;input.placeholder='Send an update to this worker…';input.setAttribute('aria-label','Update '+task.title);
    const send=node('button','','Send update'),receipt=node('small','work-receipt');
    const message=node('div','work-message');message.append(input,send,receipt);
    const row={article,title,state,detail,progress,cancel,retry,adopt,details,input,message,receipt,task};
    inspect.onclick=async()=>{if(!details.hidden){details.hidden=true;return;}try{const data=await action('work.inspect',{id:task.id});details.replaceChildren(node('p','',data.brief),node('p','',data.result?.text||'No finished result yet.'));const permissions=node('details'),label=node('summary','','Scope and evidence');const pre=node('pre','',JSON.stringify({scope:data.scope,resources:data.resources,attempts:data.attempt_history.map(a=>({state:a.state,started_at:a.started_at,finished_at:a.finished_at})),changed_objects:data.result?.changed_objects,evidence_count:data.result?.evidence_count},null,2));permissions.append(label,pre);details.append(permissions);details.hidden=false;}catch{}};
    cancel.onclick=()=>action('work.cancel',{id:task.id}).catch(()=>{});
    retry.onclick=()=>action('work.retry',{id:task.id}).catch(()=>{});
    adopt.onclick=()=>action('work.adopt',{id:task.id,expected_brief_revision:row.task.brief_revision}).catch(()=>{});
    send.onclick=async()=>{const text=input.value.trim();if(!text)return;send.disabled=true;try{const result=await action('work.message',{id:task.id,text});if(input.value.trim()===text)input.value='';receipt.textContent=result.delivery==='runtime_accepted'?'Accepted by the running worker':'Saved for the worker’s next check';}catch{}finally{send.disabled=false;}};
    controls.append(inspect,cancel,retry,adopt);article.append(title,state,detail,progress,controls,details,message);list.append(article);return row;
  }
  async function poll(){if(polling)return;polling=true;try{
    const data=await call('work.list',{}),active=data.tasks.filter(t=>['queued','starting','running','waiting_resource'].includes(t.state));
    button.textContent='Work'+(active.length?' · '+active.length:'');
    summary.textContent=data.scheduler.error?'Scheduler needs attention: '+data.scheduler.error:(data.scheduler.active+' of '+data.scheduler.slots+' workers active'+(data.tasks.length?'':' · Ask JEFF to delegate a task'));
    const running=t=>['queued','starting','running','waiting_resource'].includes(t.state);
    const ordered=[...data.tasks].sort((a,b)=>Number(running(b))-Number(running(a))||b.updated_at-a.updated_at);
    for(const task of ordered){
      const row=cards.get(task.id)||card(task);cards.set(task.id,row);row.task=task;
      row.title.textContent=task.title;row.state.textContent=labels[task.state]||task.state;row.article.dataset.state=task.state;
      row.detail.textContent=task.detail;row.progress.textContent=task.progress?'Last worker report:\n'+task.progress:'';
      row.cancel.hidden=!['queued','starting','running','waiting_resource'].includes(task.state);
      row.retry.hidden=!['blocked','failed','interrupted','cancelled'].includes(task.state);row.adopt.hidden=task.state!=='ready';
      row.message.hidden=!running(task);
    }
    if(!panel.contains(document.activeElement))for(const task of ordered)list.append(cards.get(task.id).article);
  }catch(e){alert.hidden=false;alert.textContent=e.message;}finally{polling=false;}}
  poll();setInterval(poll,1500);
})();
