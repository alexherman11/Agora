export default {mount(api,s){
  const root=api.part('body','dl',{class:'nb-fields'}),f=api.facts;
  if(!f.post_kind)return root;
  const draw=fields=>{for(const key of String(s.fields||fields||'').split(/\s+/).filter(Boolean))if(f[key]!==undefined&&f[key]!=='')root.append(api.part('label','dt',{},api.label(key,key.replaceAll('_',' '))),api.part('value','dd',{},/^(start|end|until|closes)$/.test(key)?new Date(f[key]).toLocaleString():String(f[key])))};
  api.read('rows kind').then(api.guard(kinds=>{const kind=kinds.find(k=>k.name===f.post_kind);draw(kind?.card_fields??kind?.fields)})).catch(api.tell);return root;
}};
