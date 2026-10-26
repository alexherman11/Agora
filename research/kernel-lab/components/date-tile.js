export default {css:`
.date-tile{display:flex;align-items:center;flex-wrap:wrap;gap:var(--date-tile-gap,12px);font-size:var(--date-tile-text-size,14px)}
.date-tile-calendar{display:flex;align-items:center;flex-direction:column;overflow:hidden;flex:none;width:var(--date-tile-width,62px);border:1px solid var(--nb-border,#d8dfd8);border-radius:var(--date-tile-radius,8px);background:var(--paper,#faf9f5);color:var(--ink,#303d37);font-size:var(--date-tile-small-size,12px)}
.date-tile-calendar>span:first-child{width:100%;text-align:center;background:var(--nb-soft,#edf3ed);color:var(--accent,#315f52)}
.date-tile-calendar strong{font-size:var(--date-tile-day-size,30px);line-height:1.25}.date-tile p{margin:4px 0}.date-tile>small{flex-basis:100%}
`,mount(api,s){
  const {P}=api,root=api.part('body','div',{class:'date-tile'});
  if(!s.start)return root;
  const d=new Date(s.start);if(!Number.isFinite(+d))return root;
  const tile=api.part('tile','time',{class:'date-tile-calendar',datetime:s.start,'aria-label':api.format('date',s.start,'calendar-date')},
    api.part('month','span',{},api.format('month',s.start,'month')),api.part('day','strong',{},api.format('day',s.start,'day')),api.part('weekday','span',{},api.format('weekday',s.start,'weekday')));
  const range=api.format('time',s.start,'time')+(s.end?'–'+api.format('time',s.end,'time'):'');
  root.append(tile,P.node('div',{},api.part('time','strong',{},range.replace(/ (am|pm)–(?=.*\1)/,'–')),api.part('place','p',{},s.place||'')));
  const minutes=Math.ceil((d-new Date())/60000),days=Math.round((new Date(d.getFullYear(),d.getMonth(),d.getDate())-new Date(new Date().setHours(0,0,0,0)))/86400000);
  if(minutes>0&&minutes<=s.soonDays*1440)root.append(api.part('countdown','small',{class:'nb-meta'},minutes<60?api.label('starts','Starts in')+' '+minutes+' '+api.label('minutes','min'):days===0?api.label('today','Today'):api.label('in','In')+' '+days+' '+api.label('days','days')));
  return root;
}};
