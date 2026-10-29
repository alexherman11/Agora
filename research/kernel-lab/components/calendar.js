// A shared calendar: month and week over any dated things arranged as its children.
// Each child's facts give start (ISO time), optional end, title, a place, text, and
// optionally going/maybe counts, coming/maybe_coming names and your_rsvp. Where it
// keeps its place (view, day, add form) is ordinary view state: calendarView,
// calendarDate, calendarAdd, calendarEvent. Words are authored gestures:
//   on select do …   (value = YYYY-MM-DD)     on add do … $fields   (title start end <place> text)
//   on rsvp do … $target status=$value        (value = going | maybe)
// Without an add or rsvp gesture those controls are simply not offered.
export default {css:`
.cal{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,300px);gap:var(--nb-space-4,16px);color:var(--ink,#303d37);font-size:var(--nb-small,14px);line-height:1.4}
.cal[data-view=week]{grid-template-columns:minmax(0,1fr)}
.cal button{font:inherit;color:inherit;cursor:pointer}
.cal-head{grid-column:1/-1;display:flex;align-items:center;flex-wrap:wrap;gap:var(--nb-space-2,8px)}
.cal-head h2{margin:0 var(--nb-space-2,8px) 0 0;font-size:var(--nb-h2,21px);font-weight:var(--nb-heading-weight,650);min-width:11ch}
.cal .cal-step,.cal .cal-soft{border:1px solid var(--nb-border,#e3e6de);background:var(--card,#fff);border-radius:var(--nb-radius-small,8px);padding:6px 12px;min-height:36px}
.cal .cal-step{min-width:36px;padding:6px 10px}
.cal-switch{display:inline-flex;border:1px solid var(--nb-border,#e3e6de);border-radius:var(--nb-pill,24px);overflow:hidden;background:var(--card,#fff)}
.cal .cal-switch button{border:0;background:none;padding:6px 14px;min-height:34px}
.cal-switch button[aria-pressed=true]{background:var(--nb-soft,#edf3ed);color:var(--accent,#315f52);font-weight:600}
.cal .cal-add{margin-left:auto;border:0;border-radius:var(--nb-pill,24px);padding:8px 16px;min-height:38px;background:var(--accent,#315f52);color:#fff!important;font-weight:600}
.cal-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));border:1px solid var(--nb-border,#e3e6de);border-radius:var(--nb-radius,14px);overflow:hidden;background:var(--nb-border,#e3e6de);gap:1px}
.cal-dow{background:var(--paper,#faf9f5);color:var(--muted,#59685f);font-size:var(--nb-tiny,12px);text-transform:uppercase;letter-spacing:.06em;padding:6px 8px}
.cal-day{background:var(--card,#fff);min-height:96px;padding:4px 6px 6px;display:flex;flex-direction:column;gap:3px;min-width:0;cursor:pointer}
.cal-day[data-outside=yes]{background:var(--paper,#faf9f5);color:var(--muted,#59685f)}
.cal-day[aria-selected=true]{box-shadow:inset 0 0 0 2px var(--accent,#315f52)}
.cal .cal-num{align-self:flex-start;border:0;background:none;border-radius:50%;width:28px;height:28px;min-height:28px;padding:0;font-weight:600}
.cal-day[data-today=yes] .cal-num{background:var(--accent,#315f52);color:#fff}
.cal .cal-chip{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;width:100%;min-height:0;text-align:left;border:0;border-left:3px solid var(--nb-kind-event,#315d86);background:#eef3f8;border-radius:4px;padding:2px 6px;font-size:var(--nb-tiny,12px);line-height:1.3;overflow:hidden;overflow-wrap:anywhere}
.cal-chip[data-yours=going]{background:#dfeee6;border-left-color:var(--accent,#315f52)}
.cal-chip[aria-current=true]{outline:2px solid var(--nb-kind-event,#315d86);outline-offset:-1px}
.cal .cal-more{min-height:0;border:0;background:none;color:var(--muted,#59685f);font-size:var(--nb-tiny,12px);text-align:left;padding:0 6px}
.cal-week{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:var(--nb-space-2,8px)}
.cal-col{display:flex;flex-direction:column;gap:var(--nb-space-2,8px);min-width:0;border-radius:var(--nb-radius,14px);background:var(--paper,#faf9f5);border:1px solid var(--nb-border,#e3e6de);padding:var(--nb-space-2,8px);min-height:240px}
.cal-col[data-today=yes]{border-color:var(--accent,#315f52)}
.cal-col>header{display:flex;cursor:default;justify-content:space-between;align-items:baseline;border:0;background:none;padding:2px 4px;text-align:left}
.cal-col>header strong{font-size:20px}
.cal-col>header span{color:var(--muted,#59685f);font-size:var(--nb-tiny,12px);text-transform:uppercase;letter-spacing:.06em}
.cal-side{display:flex;flex-direction:column;gap:var(--nb-space-3,12px);min-width:0}
.cal-side>h3{margin:4px 0 0;font-size:17px}
.cal-event{background:var(--card,#fff);border:1px solid var(--nb-border,#e3e6de);border-left:4px solid var(--nb-kind-event,#315d86);border-radius:var(--nb-radius-small,8px);padding:var(--nb-space-3,12px);display:flex;flex-direction:column;gap:4px;min-width:0}
.cal-event[aria-current=true]{box-shadow:0 0 0 2px var(--nb-kind-event,#315d86)}
.cal-week .cal-event{padding:8px}
.cal-event h4{margin:0;font-size:15px;overflow-wrap:anywhere}
.cal-event p{margin:0;overflow-wrap:anywhere}
.cal-when{font-weight:600;color:var(--nb-kind-event,#315d86)}
.cal-meta{color:var(--muted,#59685f);font-size:var(--nb-tiny,12px)}
.cal-notes{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.cal-rsvp{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.cal .cal-rsvp button{border:1px solid var(--nb-soft-border,#cbdcd0);background:var(--card,#fff);border-radius:var(--nb-pill,24px);padding:4px 12px;min-height:32px}
.cal-week .cal-rsvp button{padding:2px 10px;min-height:28px}
.cal-rsvp button[aria-pressed=true]{background:var(--accent,#315f52);border-color:var(--accent,#315f52);color:#fff}
.cal .cal-rsvp .cal-open{border:0;background:none;color:var(--accent,#315f52);text-decoration:underline;padding:4px 2px}
.cal-quiet{color:var(--muted,#59685f);margin:0}
.cal-form{display:flex;flex-direction:column;gap:var(--nb-space-2,8px);background:var(--card,#fff);border:1px solid var(--nb-border,#e3e6de);border-radius:var(--nb-radius,14px);padding:var(--nb-space-4,16px)}
.cal-form h3{margin:0;font-size:17px}
.cal-form label{display:flex;flex-direction:column;gap:3px;color:var(--muted,#59685f);font-size:var(--nb-tiny,12px)}
.cal-form input,.cal-form textarea{font:inherit;font-size:var(--nb-small,14px);color:var(--ink,#303d37);border:1px solid var(--nb-border,#e3e6de);border-radius:var(--nb-radius-small,8px);padding:7px 9px;background:var(--paper,#faf9f5);min-width:0}
.cal-times{display:grid;grid-template-columns:1fr 1fr;gap:var(--nb-space-2,8px)}
.cal-form-actions{display:flex;gap:var(--nb-space-2,8px);align-items:center}
.cal-form-actions .cal-add{margin-left:0}
.cal-status{color:#8a3b2a;font-size:var(--nb-tiny,12px);margin:0}
@media (max-width:820px){.cal{grid-template-columns:minmax(0,1fr)}.cal-day{min-height:64px}.cal-week{grid-template-columns:minmax(0,1fr)}.cal-col{min-height:0}.cal .cal-rsvp button{min-height:40px}}
@media (max-width:560px){.cal .cal-chip{font-size:0;height:6px;padding:0;border-left:0;background:var(--nb-kind-event,#315d86);border-radius:3px}.cal .cal-chip[data-yours=going]{background:var(--accent,#315f52)}.cal-day{padding:4px 3px;align-items:center}}
`,mount(api,s){
  const {P}=api,L=api.label,v=api.view(),node=api.node;
  const has=event=>node.gestures.some(g=>g.event===event);
  const pad=n=>String(n).padStart(2,'0'),ymd=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());
  const parse=text=>{const m=/^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(String(text||''));return m?new Date(+m[1],+m[2]-1,+(m[3]||1)):null};
  const today=ymd(new Date()),day=parse(v.calendarDate)||parse(s.date)||parse(s.month)||parse(today);
  const mode=(v.calendarView||s.view)==='week'?'week':'month',weekStart=Math.max(0,Math.min(6,Number(s.weekStart)||0));
  const place=s.placeField||'location',locale=undefined;
  const add=(d,n)=>new Date(d.getFullYear(),d.getMonth(),d.getDate()+n);
  const startOfWeek=d=>add(d,-((d.getDay()-weekStart+7)%7));
  const time=iso=>{const d=new Date(iso);return Number.isFinite(+d)?d.toLocaleTimeString(locale,{hour:'numeric',minute:'2-digit'}).replace(':00','').replace(/\s?([AP])M$/i,(m,x)=>x.toLowerCase()==='a'?' am':' pm'):''};
  const span=e=>{const a=time(e.start),b=e.end?time(e.end):'';return b?(a.replace(/ (am|pm)$/,(m,x)=>b.endsWith(x)?'':m)+'–'+b):a};
  const longDay=d=>d.toLocaleDateString(locale,{weekday:'long',month:'long',day:'numeric'});
  const events=api.children.map(c=>c.facts||{}).filter(f=>f.start&&Number.isFinite(+new Date(f.start)))
    .sort((a,b)=>new Date(a.start)-new Date(b.start));
  const byDay=new Map();for(const e of events){const key=ymd(new Date(e.start));if(!byDay.has(key))byDay.set(key,[]);byDay.get(key).push(e)}
  const go=values=>api.select(values).catch(api.tell);
  const choose=(d,extra={})=>{go({calendarDate:ymd(d),...extra});if(has('select'))api.fire('select',{value:ymd(d)}).catch(api.tell)};
  const root=api.part('body','section',{class:'cal','data-view':mode,'aria-label':L('label',s.label||'Calendar')});

  // Header: where you are, step back/forward, today, month|week, add.
  const title=mode==='month'?day.toLocaleDateString(locale,{month:'long',year:'numeric'})
    :(()=>{const a=startOfWeek(day),b=add(a,6),md=d=>d.toLocaleDateString(locale,{month:'short',day:'numeric'});
      return md(a)+(a.getFullYear()!==b.getFullYear()?', '+a.getFullYear():'')+' – '+(a.getMonth()===b.getMonth()?b.getDate():md(b))+', '+b.getFullYear()})();
  const step=n=>()=>choose(mode==='month'?new Date(day.getFullYear(),day.getMonth()+n,1):add(day,7*n),{calendarEvent:''});
  const sw=P.node('div',{class:'cal-switch',role:'group','aria-label':L('viewchoice','Calendar view')});
  for(const [key,label] of [['month','Month'],['week','Week']]){const b=P.press(L(key,label),()=>go({calendarView:key}),'');b.setAttribute('aria-pressed',String(mode===key));sw.append(b)}
  const head=api.part('heading','header',{class:'cal-head'},P.node('h2',{'aria-live':'polite'},title),
    P.press('‹',step(-1),'cal-step'),P.press('›',step(1),'cal-step'),P.press(L('today','Today'),()=>choose(new Date(),{calendarEvent:''}),'cal-soft'),sw);
  head.querySelectorAll('.cal-step')[0].setAttribute('aria-label',L(mode==='month'?'previousmonth':'previousweek',mode==='month'?'Previous month':'Previous week'));
  head.querySelectorAll('.cal-step')[1].setAttribute('aria-label',L(mode==='month'?'nextmonth':'nextweek',mode==='month'?'Next month':'Next week'));
  if(has('add'))head.append(P.press(L('add','＋ Add event'),()=>go({calendarAdd:'yes'}),'cal-add'));
  root.append(head);

  // One event, in full: when, where, notes, who is coming, and one-click RSVP.
  const card=e=>{
    const c=api.part('event','article',{class:'cal-event','data-event':e.id||'','aria-current':String(!!e.id&&v.calendarEvent===e.id)});
    c.append(P.node('p',{class:'cal-when'},span(e)),P.node('h4',{},e.title||String(e.text||'').split('\n')[0]||L('untitled','Event')));
    if(e[place])c.append(P.node('p',{class:'cal-meta'},'⌖ '+e[place]));
    if(e.text&&e.text!==e.title)c.append(P.node('p',{class:'cal-notes'},e.text));
    const going=Number(e.going||0),maybe=Number(e.maybe||0);
    if(going||maybe||'going' in e)c.append(P.node('p',{class:'cal-meta'},
      (e.coming?L('goingnames','Going')+': '+e.coming:going+' '+L('goingcount','going'))+(maybe?' · '+L('maybe','Maybe')+': '+(e.maybe_coming||maybe):'')));
    const row=P.node('div',{class:'cal-rsvp'});
    if(has('rsvp')&&e.id)for(const [status,label] of [['going','Going'],['maybe','Maybe']]){
      const b=P.press(L(status,label),async()=>{if(e.your_rsvp===status)return;b.disabled=true;
        try{await api.fire('rsvp',{target:e.id,value:status})}catch(err){api.tell(String(err.message||err).replace(/^refused:\s*/,''))}finally{b.disabled=false}},'');
      b.setAttribute('aria-pressed',String(e.your_rsvp===status));b.dataset.rsvp=status;row.append(b)}
    if(s.openKey&&e.id)row.append(P.press(L('open','Open conversation'),()=>go(Object.fromEntries(String(s.openKey).split(/\s+/).filter(Boolean).map(key=>[key,e.id]))),'cal-open'));
    if(row.children.length)c.append(row);
    return c;
  };

  if(mode==='month'){
    const grid=api.part('grid','div',{class:'cal-grid',role:'grid','aria-label':title});
    const first=new Date(day.getFullYear(),day.getMonth(),1),from=startOfWeek(first);
    const weeks=Math.ceil(((first.getDay()-weekStart+7)%7+new Date(day.getFullYear(),day.getMonth()+1,0).getDate())/7);
    for(let i=0;i<7;i++)grid.append(P.node('div',{class:'cal-dow',role:'columnheader'},add(from,i).toLocaleDateString(locale,{weekday:'short'})));
    for(let i=0;i<weeks*7;i++){
      const d=add(from,i),key=ymd(d),list=byDay.get(key)||[];
      const cell=P.node('div',{class:'cal-day',role:'gridcell','data-date':key,'aria-selected':String(key===ymd(day)),
        'data-outside':d.getMonth()===day.getMonth()?'no':'yes','data-today':key===today?'yes':'no'});
      cell.addEventListener('click',e=>{if(!e.target.closest('button'))choose(d,{calendarEvent:''})});
      cell.addEventListener('dblclick',e=>{if(has('add')&&!e.target.closest('.cal-chip'))go({calendarDate:key,calendarAdd:'yes'})});
      const num=P.press(String(d.getDate()),()=>choose(d,{calendarEvent:''}),'cal-num');num.setAttribute('aria-label',longDay(d)+(list.length?', '+list.length+' '+L(list.length===1?'oneevent':'events',list.length===1?'event':'events'):''));
      cell.append(num);
      for(const e of list.slice(0,3)){const chip=P.press((time(e.start)?time(e.start)+' ':'')+(e.title||e.text||L('untitled','Event')),()=>choose(d,{calendarEvent:e.id||''}),'cal-chip');
        chip.dataset.event=e.id||'';chip.dataset.yours=e.your_rsvp||'';chip.setAttribute('aria-current',String(!!e.id&&v.calendarEvent===e.id));cell.append(chip)}
      if(list.length>3)cell.append(P.press('+'+(list.length-3)+' '+L('more','more'),()=>choose(d,{calendarEvent:''}),'cal-more'));
      grid.append(cell);
    }
    root.append(grid);
  } else {
    const week=api.part('grid','div',{class:'cal-week','aria-label':title}),from=startOfWeek(day);
    for(let i=0;i<7;i++){
      const d=add(from,i),key=ymd(d),list=byDay.get(key)||[];
      const col=P.node('section',{class:'cal-col','data-date':key,'data-today':key===today?'yes':'no','aria-label':longDay(d)});
      const top=P.node('header',{},P.node('span',{},d.toLocaleDateString(locale,{weekday:'short'})),P.node('strong',{},String(d.getDate())));
      if(has('add')){top.title=L('addhere','Add an event this day');top.style.cursor='pointer';top.addEventListener('click',()=>go({calendarDate:key,calendarAdd:'yes'}))}
      col.append(top,...list.map(card));
      if(!list.length)col.append(P.node('p',{class:'cal-quiet'},'—'));
      week.append(col);
    }
    root.append(week);
  }

  // Side: the add form, or the chosen day's agenda.
  const side=api.part('agenda','aside',{class:'cal-side','aria-label':L('agenda','Selected day')});
  if(v.calendarAdd==='yes'&&has('add')){
    const D=api.draft,form=P.node('form',{class:'cal-form','aria-label':L('addform','Add an event')}),out=P.node('p',{class:'cal-status',role:'status','aria-live':'polite'});
    const field=(key,label,{tag='input',...attrs})=>{const input=P.node(tag,{name:key,'aria-label':L(key,label),...attrs,value:D[key]??attrs.value??''});
      input.addEventListener('input',()=>{D[key]=input.value});return [P.node('label',{},L(key,label),input),input]};
    const [whatL,what]=field('title','What',{required:'',placeholder:L('titlehint','Garden workday, council meeting…'),tag:'input'});
    const [dayL,date]=field('day','Day',{type:'date',required:'',value:ymd(day)});
    const [fromL,from]=field('from','Starts',{type:'time',required:'',value:s.defaultTime||'18:00'});
    const [toL,to]=field('to','Ends',{type:'time'});
    const [whereL,where]=field('where','Where',{placeholder:L('wherehint','Community hall, the park…')});
    const [notesL,notes]=field('notes','Notes',{tag:'textarea',rows:3,placeholder:L('noteshint','Anything people should know or bring')});
    const submit=P.node('button',{type:'submit',class:'cal-add'},L('save','Add to calendar'));
    form.append(P.node('h3',{},L('addform','Add an event')),whatL,dayL,P.node('div',{class:'cal-times'},fromL,toL),whereL,notesL,
      P.node('div',{class:'cal-form-actions'},submit,P.press(L('cancel','Cancel'),()=>go({calendarAdd:'no'}),'cal-soft')),out);
    P.submit(form,async e=>{e.preventDefault();
      const at=(d,t)=>{const x=parse(d);if(!x||!/^\d{2}:\d{2}/.test(t||''))return '';const [h,m]=t.split(':').map(Number);x.setHours(h,m,0,0);return x.toISOString().replace(/\.\d{3}Z$/,'Z')};
      const start=at(date.value,from.value),end=to.value?at(date.value,to.value):'';
      if(!what.value.trim()||!start){out.textContent=L('needwhat','Give it a name, a day and a start time.');return}
      if(end&&new Date(end)<=new Date(start)){out.textContent=L('endafter','It should end after it starts.');return}
      const fields={title:what.value.trim(),start,...(end?{end}:{}),...(where.value.trim()?{[place]:where.value.trim()}:{}),...(notes.value.trim()?{text:notes.value.trim()}:{})};
      submit.disabled=true;out.textContent='';
      try{const kept=date.value;await api.fire('add',{fields,select:{calendarAdd:'no',calendarDate:kept,calendarEvent:''}});for(const k of Object.keys(D))delete D[k]}
      catch(err){out.textContent=String(err.message||err).replace(/^refused:\s*/,'')}finally{submit.disabled=false}});
    side.append(form);api.requestAnimationFrame(()=>{if(!form.contains(document.activeElement))what.focus()});
  } else if(mode==='month'){
    const list=byDay.get(ymd(day))||[];
    side.append(P.node('h3',{},longDay(day)),...list.map(card));
    if(!list.length){side.append(P.node('p',{class:'cal-quiet'},L('nothing','Nothing planned yet.')));
      if(has('add'))side.append(P.press(L('addday','＋ Add an event this day'),()=>go({calendarAdd:'yes'}),'cal-soft'))}
  }
  if(side.children.length)root.append(side);
  return root;
}};
