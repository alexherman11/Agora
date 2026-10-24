/* A bar grants space to widget surfaces; widget code never joins this document. */
(() => {
  const edge=new URLSearchParams(location.search).get('edge') || (location.pathname.endsWith('taskbar.html')?'bottom':'top');
  const slots=new Map();
  async function sync(){
    try{
      const r=await fetch('/see',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({line:'rows widget surface='+edge})}).then(r=>r.json());
      const rows=(r.rows||[]).filter(w=>w.code&&w.on);
      for(const [id,f] of slots)if(!rows.some(w=>w.id===id)){f.remove();slots.delete(id)}
      for(const w of rows){const old=slots.get(w.id);if(old&&old.widgetCode!==w.code){old.remove();slots.delete(w.id)}}
      for(const w of rows)if(!slots.has(w.id)){
        const f=document.createElement('iframe');f.title='Widget · '+w.name;
        f.widgetCode=w.code;
        f.src='/desk/widget.html?slot=1&widget='+encodeURIComponent(w.id);
        Object.assign(f.style,{position:'relative',width:'310px',height:'100%',border:'0',flex:'0 0 310px',background:'transparent'});
        document.body.append(f);slots.set(w.id,f);
      }
    }finally{setTimeout(sync,2000)}
  }
  sync();
})();
