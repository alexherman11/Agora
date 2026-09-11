/* Agora live Markdown widget. Pure view adapter; no world/network calls.
   Build: npm ci --ignore-scripts; node node_modules/esbuild/bin/esbuild ...
   Exact Markdown is the model. Decorations NEVER serialize HTML back to text. */
import {EditorState,EditorSelection,Compartment,Transaction} from "@codemirror/state";
import {EditorView,Decoration,ViewPlugin,keymap,drawSelection,dropCursor,highlightSpecialChars} from "@codemirror/view";
import {defaultKeymap,history,historyKeymap} from "@codemirror/commands";
import {markdown,markdownKeymap} from "@codemirror/lang-markdown";
import {syntaxTree} from "@codemirror/language";

function decorations(view){
 const ranges=[],state=view.state,doc=state.doc,selections=state.selection.ranges;
 const touched=(from,to)=>selections.some(s=>s.empty?s.head>=from&&s.head<=to:s.from<to&&s.to>from);
 const mark=(from,to,cls)=>{if(to>from)ranges.push(Decoration.mark({class:cls}).range(from,to));};
 const hide=(from,to)=>{if(doc.sliceString(from,to).includes("\n")){mark(from,to,"md-syntax");return;}if(to>from&&!touched(from,to))ranges.push(Decoration.replace({inclusive:false}).range(from,to));else mark(from,to,"md-syntax");};
 const lines=new Set();
 const lineStyle=(from,to,cls)=>{
  for(let n=doc.lineAt(from).number,last=doc.lineAt(Math.max(from,to-1)).number;n<=last;n++){
   const l=doc.line(n),key=n+cls;if(lines.has(key))continue;lines.add(key);
   ranges.push(Decoration.line({class:cls}).range(l.from));
  }
 };
 syntaxTree(state).iterate({enter(node){
  const n=node.name;
  if(/^ATXHeading[1-6]$/.test(n)||/^SetextHeading[12]$/.test(n))lineStyle(node.from,node.to,"md-heading md-h"+n.slice(-1));
  if(n==="StrongEmphasis")mark(node.from,node.to,"md-strong");
  if(n==="Emphasis")mark(node.from,node.to,"md-emphasis");
  if(n==="Strikethrough")mark(node.from,node.to,"md-strike");
  if(n==="InlineCode")mark(node.from,node.to,"md-inline-code");
  if(n==="FencedCode"||n==="IndentedCode")lineStyle(node.from,node.to,"md-code-line");
  if(n==="Blockquote")lineStyle(node.from,node.to,"md-quote-line");
  if(n==="Link"){
   const raw=doc.sliceString(node.from,node.to),match=/^\[([\s\S]*)\]\(([\s\S]*)\)$/.exec(raw);
   if(match&&!touched(node.from,node.to)){
    const labelStart=node.from+1,labelEnd=labelStart+match[1].length;
    mark(labelStart,labelEnd,"md-link");hide(node.from,labelStart);hide(labelEnd,node.to);
    return false;
   }
   mark(node.from,node.to,"md-link");
  }
  if(n==="EmphasisMark"||n==="StrikethroughMark")hide(node.from,node.to);
  if(n==="HeaderMark"){
   let end=node.to;while(end<doc.length&&doc.sliceString(end,end+1)===" ")end++;
   hide(node.from,end);
  }
  if(n==="QuoteMark")hide(node.from,node.to+(doc.sliceString(node.to,node.to+1)===" "?1:0));
  if(n==="ListMark")mark(node.from,node.to,"md-list-marker");
  if(n==="CodeMark"){
   if(node.node.parent?.name==="InlineCode")hide(node.from,node.to);else mark(node.from,node.to,"md-syntax");
  }
 }});
 return Decoration.set(ranges,true);
}
const livePreview=ViewPlugin.fromClass(class{
 constructor(view){this.decorations=decorations(view);}
 update(u){if(u.docChanged||u.selectionSet||u.viewportChanged||syntaxTree(u.startState)!==syntaxTree(u.state))this.decorations=decorations(u.view);}
},{decorations:v=>v.decorations});

export function create({parent,text="",onChange=()=>{},onSelection=()=>{},onAsk=()=>{},onError=()=>{}}){
 let suppress=0,currentId="",readonly=false;
 const states=new Map(),scrolls=new Map(),readConfig=new Compartment();
 const clamp=(n,length)=>Math.max(0,Math.min(Number(n)||0,length));
 let view;
 const selection=()=>[view.state.selection.main.from,view.state.selection.main.to];
 const apply=(from,to,insert,anchor=from+insert.length,head=anchor)=>{
  if(readonly)return false;
  view.dispatch({changes:{from,to,insert},selection:EditorSelection.single(anchor,head),scrollIntoView:true,userEvent:"input"});
  view.focus();return true;
 };
 const inline=(marker,fallback)=>{
  const s=view.state.selection.main,doc=view.state.doc,value=doc.sliceString(s.from,s.to);
  if(value.startsWith(marker)&&value.endsWith(marker)&&value.length>=marker.length*2)
   return apply(s.from,s.to,value.slice(marker.length,-marker.length),s.from,s.to-marker.length*2);
  if(s.from>=marker.length&&doc.sliceString(s.from-marker.length,s.from)===marker&&doc.sliceString(s.to,s.to+marker.length)===marker)
   return apply(s.from-marker.length,s.to+marker.length,value,s.from-marker.length,s.to-marker.length);
  const word=value||fallback;
  return apply(s.from,s.to,marker+word+marker,s.from+marker.length,s.from+marker.length+word.length);
 };
 const prefix=(prefix)=>{
  const s=view.state.selection.main,doc=view.state.doc,from=doc.lineAt(s.from).from;
  const last=doc.lineAt(s.to>s.from&&doc.lineAt(s.to).from===s.to?s.to-1:s.to),to=last.to;
  const parts=doc.sliceString(from,to).split("\n"),remove=parts.every(x=>x.startsWith(prefix));
  const inserted=parts.map(x=>remove?x.slice(prefix.length):prefix+x).join("\n");
  return apply(from,to,inserted,from,from+inserted.length);
 };
 const bindings=[
  {key:"Mod-b",run:()=>inline("**","bold text")},
  {key:"Mod-i",run:()=>inline("*","italic text")},
  {key:"Mod-Shift-Enter",run:()=>{onAsk();return true;}}
 ];
 const extensions=[
  markdown(),history(),drawSelection(),dropCursor(),highlightSpecialChars(),
  EditorView.lineWrapping,livePreview,
  readConfig.of([EditorState.readOnly.of(false),EditorView.editable.of(true)]),
  keymap.of([...bindings,...markdownKeymap,...historyKeymap,...defaultKeymap]),
  EditorView.contentAttributes.of({"aria-label":"Live Markdown editor","aria-describedby":"docs-help","spellcheck":"true","data-testid":"live-markdown"}),
  EditorState.transactionFilter.of(tr=>{
   if(tr.docChanged&&tr.newDoc.length>100000){onError("Document limit is 100,000 UTF-16 characters. Your previous text was kept.");return [];}
   return tr;
  }),
  EditorView.updateListener.of(u=>{
   if(suppress)return;
   if(u.docChanged)onChange(u.state.doc.toString());
   if(u.docChanged||u.selectionSet)onSelection(selection());
  }),
  EditorView.theme({
   "&":{fontSize:"16px",color:"#202124",backgroundColor:"#fff"},
   "&.cm-focused":{outline:"none"},
   ".cm-scroller":{fontFamily:'Arial,"Segoe UI",sans-serif',lineHeight:"1.8",overflow:"visible"},
   ".cm-content":{padding:"64px 72px",minHeight:"760px",caretColor:"#1a73e8",whiteSpace:"pre-wrap",overflowWrap:"anywhere"},
   ".cm-line":{padding:"0"},
   ".cm-cursor, .cm-dropCursor":{borderLeftColor:"#1a73e8"},
   "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection":{backgroundColor:"#d2e3fc"},
   ".md-heading":{fontWeight:"500",lineHeight:"1.35",paddingTop:"8px",paddingBottom:"8px"},
   ".md-h1":{fontSize:"30px"},".md-h2":{fontSize:"24px"},".md-h3":{fontSize:"20px"},
   ".md-h4, .md-h5, .md-h6":{fontSize:"17px"},
   ".md-strong":{fontWeight:"700"},".md-emphasis":{fontStyle:"italic"},".md-strike":{textDecoration:"line-through"},
   ".md-inline-code":{fontFamily:"ui-monospace,monospace",fontSize:".9em",backgroundColor:"#eef2f7",borderRadius:"3px"},
   ".md-code-line":{fontFamily:"ui-monospace,monospace",fontSize:"14px",backgroundColor:"#f3f5f8",paddingLeft:"12px"},
   ".md-quote-line":{borderLeft:"3px solid #bbc9dd",paddingLeft:"14px",color:"#526170"},
   ".md-link":{color:"#1967d2",textDecoration:"underline"},
   ".md-syntax":{color:"#8793a4",fontWeight:"400"},".md-list-marker":{color:"#1967d2",fontWeight:"700"}
  })
 ];
 function makeState(value,range=[0,0]){
  return EditorState.create({doc:value,selection:EditorSelection.single(clamp(range[0],value.length),clamp(range[1],value.length)),extensions});
 }
 view=new EditorView({state:makeState(text),parent});
 const setReadonly=value=>{
  readonly=!!value;
  suppress++;try{view.dispatch({effects:readConfig.reconfigure([EditorState.readOnly.of(readonly),EditorView.editable.of(!readonly)])});}finally{suppress--;}
 };
 function load(id,value,range=[0,0],locked=false){
  const changedId=currentId!==id;
  if(changedId&&currentId){states.set(currentId,view.state);scrolls.set(currentId,view.scrollDOM.scrollTop);}
  suppress++;
  try{
   if(changedId||view.state.doc.toString()!==value){
    let retained=states.get(id);
    if(!retained||retained.doc.toString()!==value)retained=makeState(value,range);
    view.setState(retained);currentId=id;
   }
   const [a,b]=range.map(n=>clamp(n,value.length)),s=view.state.selection.main;
   if(s.from!==a||s.to!==b)view.dispatch({selection:EditorSelection.single(a,b)});
  }finally{suppress--;}
  setReadonly(locked);
  if(changedId)view.scrollDOM.scrollTop=scrolls.get(id)||0;
 }
 function sync(value,range=selection()){
  const old=view.state.doc.toString();suppress++;
  try{
   if(old!==value){
    let from=0,end=old.length,newEnd=value.length;
    while(from<end&&from<newEnd&&old[from]===value[from])from++;
    while(end>from&&newEnd>from&&old[end-1]===value[newEnd-1]){end--;newEnd--;}
    view.dispatch({changes:{from,to:end,insert:value.slice(from,newEnd)},selection:EditorSelection.single(...range.map(n=>clamp(n,value.length)))});
   }else{
    const [a,b]=range.map(n=>clamp(n,value.length)),s=view.state.selection.main;
    if(s.from!==a||s.to!==b)view.dispatch({selection:EditorSelection.single(a,b)});
   }
  }finally{suppress--;}
 }
 return {view,load,sync,setReadonly,inline,prefix,selection,
  focus(){view.focus();},
  reveal(start,end){view.dispatch({selection:EditorSelection.single(start,end),effects:EditorView.scrollIntoView(start,{y:"center"})});view.focus();},
  get composing(){return view.composing;},
  get text(){return view.state.doc.toString();},
  destroy(){view.destroy();states.clear();}
 };
}
