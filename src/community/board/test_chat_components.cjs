// board-chat and the chat list: actual component handlers in the in-memory DOM adapter.
// Not browser, layout, focus, scroll or touch evidence (chat_proof.py is the hidden browser check).
const {path,assert,descendants,component,api,part,button,tick}=require('./component_test_support.cjs');
let checks=0;function check(label,fn){fn();checks++;console.log('PASS '+label)}
const cls=(n,c)=>(n.attrs.class||'').split(' ').includes(c);
const all=(root,c)=>descendants(root).filter(n=>cls(n,c));
const tool=(msg,key)=>descendants(msg).find(n=>n.tagName==='button'&&n.dataset.tool===key);
const same=(x,y)=>assert.equal(JSON.stringify(x),JSON.stringify(y));
const keydown=(n,key,extra={})=>n.event('keydown',{key,...extra});
const row=(id,o={})=>({id,kind:'said',chat:'c1',by:'Sam',by_id:'p2',name:'Sam',guest:false,badge:'',mine:false,text:'hi',at:'2026-11-05T18:00:00Z',reply_to:null,reply:null,edited:null,removed:false,pinned:false,reactions:[],mentions:[],files:[],rev:1,...o});
const maya={by:'Maya',by_id:'p1',name:'Maya',mine:true};
function chat(rows,extra={}){
  const a=api('board-chat',{node:{component:'board-chat',path:'root/centre/chat',gestures:[],viewer:{id:'p1',name:'Maya'}},children:rows.map(facts=>({facts,children:[]})),...extra});
  a.select({chat:'c1',opens:'chat'});return a;
}
(async()=>{
  const board=component(path.join(__dirname,'board-components.bundle.js'));
  // grouping and day dividers
  let a=chat([row('s1',{...maya,at:'2026-11-04T18:00:00Z'}),row('s2',{...maya,at:'2026-11-04T18:03:00Z',text:'second'}),row('s3',{at:'2026-11-04T18:04:00Z'}),row('s4',{at:'2026-11-05T18:00:00Z'})]);
  let root=board.mount(a,{});await tick();
  const msgs=()=>all(root,'nb-msg');
  check('consecutive lines by one person group under one name',()=>{same(msgs().map(m=>m.dataset.grouped==='yes'),[false,true,false,false]);assert.equal(all(root,'nb-msg-name').length,3)});
  check('a grouped line keeps its time for hover',()=>assert.equal(all(msgs()[1],'nb-msg-hovertime').length,1));
  check('each day gets a divider',()=>assert.equal(all(root,'nb-chat-day').length,2));
  check('guest and leader badges show beside the name',()=>{
    a=chat([row('g1',{guest:true}),row('l1',{by_id:'p3',name:'Ana',badge:'leader'})]);root=board.mount(a,{});
    same(all(root,'nb-msg-badge').map(b=>b.dataset.badge??b.attrs['data-badge']),['guest','leader']);
  });

  // words are text, never HTML
  a=chat([row('x1',{text:'<img src=x onerror=alert(1)> **bold** *soft* `a<b>` see https://example.org/a?b=1. not javascript:alert(1) @Maya @Sam'})]);
  root=board.mount(a,{});const body=all(root,'nb-msg-text')[0];
  check('HTML in a message stays text',()=>{assert.equal(descendants(body).filter(n=>['img','script'].includes(n.tagName)).length,0);assert.match(body.textContent,/<img src=x onerror=alert\(1\)>/)});
  check('bold, italic and code format',()=>{assert.equal(descendants(body).find(n=>n.tagName==='strong').textContent,'bold');assert.equal(descendants(body).find(n=>n.tagName==='em').textContent,'soft');assert.equal(descendants(body).find(n=>n.tagName==='code').textContent,'a<b>')});
  check('only http(s) links link, without trailing punctuation',()=>{const links=descendants(body).filter(n=>n.tagName==='a');assert.equal(links.length,1);assert.equal(links[0].attrs.href,'https://example.org/a?b=1');assert.match(links[0].attrs.rel,/noopener/)});
  check('@mentions are marked, mine more strongly',()=>{const m=all(body,'nb-mention');assert.equal(m.length,2);assert.ok(cls(m[0],'nb-mention-me'));assert.ok(!cls(m[1],'nb-mention-me'))});
  a=chat([row('m1',{mentions:['p1'],text:'@Maya can you?'}),row('m2')]);root=board.mount(a,{});
  check('a line that names the reader is highlighted',()=>same(msgs().map(m=>cls(m,'nb-msg-mention')),[true,false]));

  // send: clears at once, sends once, keeps the draft on refusal
  a=chat([row('s1')]);root=board.mount(a,{});let release;
  a.fire=async(event,values)=>{a.calls.push({event,values});await new Promise(r=>release=r);return {made:['s9']}};
  let input=part(root,'composer');input.value='  hello **all**  ';await input.event('input');
  const pending=keydown(input,'Enter');await tick();
  const sends=()=>a.calls.filter(c=>c.event==='send');
  check('Enter sends the words and the box clears at once',()=>{assert.equal(sends().length,1);same(sends()[0].values.fields,{text:'hello **all**'});assert.equal(part(root,'composer').value,'')});
  input.value='again';await input.event('input');await keydown(input,'Enter');
  check('a second Enter while sending does not send twice',()=>assert.equal(sends().length,1));
  release();await pending;
  check('typing during the send survives its success',()=>assert.equal(part(root,'composer').value,'again'));
  check('Shift+Enter is a new line, not a send',()=>{const before=sends().length;keydown(part(root,'composer'),'Enter',{shiftKey:true});assert.equal(sends().length,before)});
  a=chat([row('s1')]);root=board.mount(a,{});a.fire=async()=>{throw Error('refused: sign in to send')};
  input=part(root,'composer');input.value='my words';await input.event('input');await keydown(input,'Enter');
  check('refusal puts the exact words back and says why',()=>{assert.equal(part(root,'composer').value,'my words');assert.match(all(root,'nb-chat-status')[0].textContent,/sign in to send/)});
  check('a sign-in refusal offers Sign in',()=>{const link=descendants(root).find(n=>n.tagName==='a'&&cls(n,'nb-chat-signin'));assert.equal(link.attrs.href,'/signin');assert.equal(link.textContent,'Sign in')});

  // reply
  a=chat([row('s1',{text:'the original line'}),row('s2',{reply_to:'s1',reply:{id:'s1',name:'Sam',text:'the original line',removed:false}})]);root=board.mount(a,{});await tick();await tick();
  check('a reply shows what it answers above it',()=>{const ex=all(msgs()[1],'nb-msg-replyto')[0];assert.match(ex.textContent,/Sam.*the original line/)});
    await all(msgs()[1],'nb-msg-replyto')[0].click();
  check('the original is scrolled to and flashed',()=>{assert.equal(msgs()[0].scrolled,true);assert.equal(msgs()[0].dataset.flash,'yes')});
  await tool(msgs()[0],'reply').click();
  check('Reply puts a quote bar above the composer',()=>assert.match(all(root,'nb-chat-replybar')[0].textContent,/Replying to.*Sam.*the original line/));
  input=part(root,'composer');input.value='answer';await input.event('input');await keydown(input,'Enter');
  check('the send carries reply_to and the quote bar clears',()=>{same(a.calls.filter(c=>c.event==='send').at(-1).values.fields,{text:'answer',reply_to:'s1'});assert.equal(all(root,'nb-chat-replybar')[0].hidden,true)});

  // edit own
  a=chat([row('e1',{...maya,text:'tpyo',rev:4}),row('e2')]);root=board.mount(a,{});await tick();await tick();
  check('Edit is offered on your own lines only',()=>{assert.ok(tool(msgs()[0],'edit'));assert.equal(tool(msgs()[1],'edit'),undefined)});
  await tool(msgs()[0],'edit').click();let editor=part(root,'edit');
  check('Edit opens the words inline',()=>assert.equal(editor.value,'tpyo'));
  editor.value='typo';await editor.event('input');await keydown(editor,'Enter');await tick();
  check('Enter saves the edit through the edit gesture with what was read',()=>{const c=a.calls.filter(c=>c.event!=='seen').at(-1);assert.equal(c.event,'edit');assert.equal(c.values.target,'e1');assert.equal(c.values.value,'typo');same(c.values.saw,{e1:4});assert.equal(part(root,'edit'),undefined)});
  await tool(msgs()[0],'edit').click();editor=part(root,'edit');editor.value='never mind';await editor.event('input');const count=a.calls.filter(c=>c.event==='edit').length;await keydown(editor,'Escape');
  check('Esc cancels without saving',()=>{assert.equal(a.calls.filter(c=>c.event==='edit').length,count);assert.equal(part(root,'edit'),undefined)});
  a=chat([row('e1',{...maya,edited:1762309000})]);root=board.mount(a,{});
  check('an edited line says (edited)',()=>assert.match(all(root,'nb-msg-edited')[0].textContent,/\(edited\)/));

  // reactions
  a=chat([row('r1',{reactions:[{emoji:'👍',count:2,mine:true,names:['Maya','Sam']},{emoji:'🎉',count:1,mine:false,names:['Sam']}]})]);root=board.mount(a,{});
  const reacts=all(root,'nb-react').filter(b=>b.dataset.emoji);
  check('reactions show counts, yours pressed, names on hover',()=>{same(reacts.map(b=>b.textContent),['👍 2','🎉 1']);same(reacts.map(b=>b.attrs['aria-pressed']),['true','false']);assert.equal(reacts[0].title,'Maya, Sam')});
  await reacts[0].click();
  check('clicking a reaction toggles it through react',()=>{const c=a.calls.filter(c=>c.event!=='seen').at(-1);assert.equal(c.event,'react');assert.equal(c.values.target,'r1');assert.equal(c.values.value,'👍')});
  await tool(msgs()[0],'react').click();const picker=all(root,'nb-emoji');
  check('the picker offers eight emoji',()=>assert.equal(picker.length,8));
  await picker[3].click();
  check('picking one reacts and closes the picker',()=>{assert.equal(a.calls.at(-1).values.value,picker[3].dataset.emoji);assert.equal(all(root,'nb-emoji').length,0)});
  a=chat([row('r1')]);root=board.mount(a,{});a.fire=async()=>{throw Error('refused: sign in to send')};await tool(msgs()[0],'react').click();await all(root,'nb-emoji')[0].click();
  check('a refused reaction says why where you are typing',()=>assert.match(all(root,'nb-chat-status')[0].textContent,/sign in to send/));

  // delete: own, inline confirm; leaders any; pin for leaders
  a=chat([row('d1',maya),row('d2')]);root=board.mount(a,{});
  check('Delete is offered on your own lines; others need a leader',()=>{assert.ok(tool(msgs()[0],'delete'));assert.equal(tool(msgs()[1],'delete'),undefined);assert.equal(tool(msgs()[1],'pin'),undefined)});
  await tool(msgs()[0],'delete').click();
  check('Delete asks inline first, without a browser dialog',()=>{assert.equal(a.calls.filter(c=>c.event==='remove').length,0);assert.match(all(root,'nb-msg-confirm')[0].textContent,/Delete this message\?/)});
  await button(all(root,'nb-msg-confirm')[0],'Delete').click();await tick();
  check('confirming removes through the remove gesture',()=>{assert.equal(a.calls.filter(c=>c.event==='remove').at(-1).values.target,'d1')});
  a=chat([row('d2')],{read:async line=>line==='board.badges'?[{id:'p1',name:'Maya',badges:['leader']}]:[]});root=board.mount(a,{});await tick();await tick();
  check('a leader may delete and pin anyone’s line',()=>{assert.ok(tool(msgs()[0],'delete'));assert.ok(tool(msgs()[0],'pin'))});
  await tool(msgs()[0],'pin').click();
  check('Pin goes through the pin gesture',()=>assert.equal(a.calls.filter(c=>c.event==='pin').length,1));
  a=chat([row('p1',{pinned:true,text:'Meeting is at 7'}),row('p2')]);root=board.mount(a,{});
  check('pinned lines gather at the top',()=>assert.match(all(root,'nb-chat-pintoggle')[0].textContent,/1 pinned message/));
  a=chat([row('x1',{removed:true,text:'',name:'',by:'',by_id:''}),row('x2',{reply_to:'x1',reply:{id:'x1',name:'',text:'',removed:true}})]);root=board.mount(a,{});
  check('a removed line is a quiet stub and offers no actions',()=>{assert.match(msgs()[0].textContent,/Message removed/);assert.equal(all(msgs()[0],'nb-msg-tools').length,0)});

  // touch: a long press opens the line's actions and keeps the shared right-click menu away
  a=chat([row('t1')]);root=board.mount(a,{longPressMs:5});
  await msgs()[0].event('pointerdown',{pointerType:'touch'});await new Promise(r=>setTimeout(r,30));
  check('a long press on touch opens that line’s actions',()=>assert.equal(msgs()[0].dataset.active,'yes'));
  let prevented=false;await msgs()[0].event('contextmenu',{preventDefault(){prevented=true}});
  check('the long press is not the right-click menu',()=>assert.equal(prevented,true));
  // unread: a New divider where you left off, and a seen marker
  a=chat([row('n1',{at:'2026-11-05T17:00:00Z'}),row('n2',{...maya,at:'2026-11-05T17:30:00Z'}),row('n3',{at:'2026-11-05T18:00:00Z'})],
    {read:async line=>line==='rows board-seen'?[{made_by:'p1',group:'c1',at:'2026-11-05T17:10:00Z'},{made_by:'p2',group:'c1',at:'2026-11-05T19:00:00Z'}]:[]});
  root=board.mount(a,{});await tick();await tick();
  check('New sits before the first line from someone else since you left',()=>{const kids=all(root,'nb-chat-log')[0].children.filter(n=>n.attrs);const at=kids.findIndex(n=>cls(n,'nb-chat-new'));assert.ok(at>0);assert.equal(kids[at+1].dataset.said,'n3')});
  check('reading to the bottom marks the chat seen once',()=>{assert.equal(a.calls.filter(c=>c.event==='reseen').length,1);assert.equal(a.calls.find(c=>c.event==='reseen').values.value,'2026-11-05T18:00:00Z')});

  // the list: chats listed from world things, hidden entries kept out
  const channels=[{id:'b1',group:'g1',title:'Announcements'},{id:'b2',title:'Map',opens:'map'},{id:'b3',group:'g3',title:'Neighbours',hidden:'yes'},{id:'b4',title:'Legal',opens:'chat',chat:'c1',section:'Chats'},{id:'b5',title:'Bugs',opens:'chat',chat:'c2',section:'Chats'}];
  const said=[{chat:'c1',made:'2026-11-05T18:00:00Z',made_by:'p2',text:'x'},{chat:'c1',made:'2026-11-05T18:01:00Z',made_by:'p2',text:'y'},{chat:'c1',made:'2026-11-05T16:00:00Z',made_by:'p2',text:'old'}];
  const n=api('board-navigation',{node:{component:'board-navigation',path:'root/channels',gestures:[],viewer:{id:'p1'}},read:async line=>({'rows board-channel':channels,'rows said':said,'rows board-seen':[{made_by:'p1',group:'c1',at:'2026-11-05T17:00:00Z'}],'rows board-order':[],'rows chat':[{id:'c1'},{id:'c2'}]})[line]||[]});
  n.feedback=undefined;root=board.mount(n,{});await tick();await tick();
  const list=all(root,'nb-channel-list')[0];
  check('the list shows entries in order, chats under their section, hidden ones out',()=>{same(list.children.map(c=>c.textContent.replace(/\d+$/,'')),['Announcements','Map','Chats','# Legal','# Bugs'])});
  check('a chat with new lines since you left is bold with a count',()=>{const legal=list.children[3];assert.ok(cls(legal,'nb-has-unread'));assert.equal(all(legal,'nb-unread')[0].textContent,'2')});
  await list.children[3].click();await tick();
  check('choosing a chat opens it in the centre',()=>{const v=n.view();assert.equal(v.opens,'chat');assert.equal(v.chat,'c1');assert.equal(v.channel,'');assert.equal(v.navOpen,'no')});
  await list.children[1].click();await tick();
  check('choosing Map opens the map view',()=>{const v=n.view();assert.equal(v.opens,'map');assert.equal(v.chat,'')});
  // a signed-out visitor: the chat reading refuses; the part stays calm and offers sign-in
  const visitorNav=api('board-navigation',{node:{component:'board-navigation',path:'root/channels',gestures:[],viewer:{id:'v1'}},read:async line=>{if(line==='rows said')throw Error('refused: no');return ({'rows board-channel':channels,'rows chat':[]})[line]||[]}});
  root=board.mount(visitorNav,{});await tick();await tick();
  check('a visitor still sees the chats, each with a lock, and the list survives a refused reading',()=>{const l=all(root,'nb-channel-list')[0];assert.equal(l.children[3].dataset.locked,'yes');assert.equal(all(l,'nb-lock').length,2);assert.equal(l.children[0].textContent,'Announcements')});
  a=chat([],{rows:async()=>{throw Error('refused: no thing called sb154 here')}});
  root=board.mount(a,{});await tick();await tick();
  check('a refused chat reading shows Sign in to read the chats, not an error',()=>{assert.equal(root.dataset.locked,'yes');assert.match(root.textContent,/Sign in to read the chats/);assert.match(root.textContent,/meeting code/);assert.doesNotMatch(root.textContent,/sb154/);assert.equal(descendants(root).find(n=>n.tagName==='a').attrs.href,'/signin');assert.equal(part(root,'composer'),undefined)});
  a=chat([],{rows:async line=>{a.lines=(a.lines||[]).concat(line);return [row('o1',{text:'read by the part itself'})]}});
  root=board.mount(a,{});await tick();await tick();
  check('without a collection the part reads chat <c> limit=50 itself and paints it',()=>{assert.equal(a.lines[0],'chat "c1" limit=50');assert.match(all(root,'nb-chat-log')[0].textContent,/read by the part itself/)});
  root=board.mount(a,{});
  check('a remount paints the last lines at once while it reads again',()=>assert.match(all(root,'nb-chat-log')[0].textContent,/read by the part itself/));
  console.log('CHAT COMPONENT CHECKS '+checks);
})().catch(e=>{console.error(e);process.exit(1)});
