"""Bounded data-only research packets. No network, native calls, or filesystem I/O."""
import json, hashlib, copy, re
from comments import validate_thread, locate, T
from datetime import datetime, timezone
FORMAT='agora.research-packet'; VERSION=2; MAX_BYTES=2097152
C='studio.citation'; H='studio.citation-history'; S='studio.source'; A='studio.packet-attempt'
VF=('source_revision','content_hash','content','title','author','published','requested_url','final_url','retrieved_at')
SF=VF+('identity','external_id','versions')
CF=('document_id','source_id','source_revision','content_hash','quoted_text','citation_markdown','created_at')
def now(): return datetime.now(timezone.utc).isoformat()
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii')).hexdigest()
def text_hash(v): return hashlib.sha256(v.encode('utf-8')).hexdigest()
def fail(e): return {'result':{'ok':False,'error':str(e),'code':'packet_invalid'}}
def objects(ctx):
 v=ctx.get('objects',[]);return {o['id']:o for o in (v.values() if isinstance(v,dict) else v)}
def shape(o,keys,label):
 if not isinstance(o,dict) or set(o)!=set(keys): raise ValueError(label+': incorrect/missing fields')
def txt(v,label,n=2048,empty=False):
 if not isinstance(v,str) or len(v)>n or (not empty and not v.strip()): raise ValueError(label+': invalid text/length')
 try: v.encode('utf-8')
 except UnicodeError: raise ValueError(label+': invalid Unicode')
def seq(v,label,n,minimum=0):
 if not isinstance(v,list) or not minimum<=len(v)<=n: raise ValueError(label+': count outside '+str(minimum)+'..'+str(n))
def provenance(v):
 seq(v,'provenance',16,1)
 for p in v:
  shape(p,('original_id','native_revision','written_by'),'provenance');txt(p['original_id'],'original_id',500);txt(p['written_by'],'written_by',500,True)
  if type(p['native_revision']) is not int or p['native_revision']<1: raise ValueError('Invalid native provenance revision')
def origin(o):
 return copy.deepcopy(o['facets'].get('studio.packet-origin',{}).get('chain',[]))+[{'original_id':o['id'],'native_revision':o['revision'],'written_by':o.get('written_by','')}]
def version(v):
 shape(v,VF,'source version')
 for k in VF: txt(v[k],k,100000 if k=='content' else 2048)
 if text_hash(v['content'])!=v['content_hash']: raise ValueError('Source content SHA-256 mismatch')
def pairs_hook(pairs):
 out={}
 for k,v in pairs:
  if k in out: raise ValueError('Duplicate JSON key: '+k)
  out[k]=v
 return out
def validate(raw):
 txt(raw,'packet_json',MAX_BYTES)
 if len(raw.encode('utf-8'))>MAX_BYTES: raise ValueError('Packet exceeds 2 MiB UTF-8')
 try: p=json.loads(raw,object_pairs_hook=pairs_hook,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Non-finite JSON number')))
 except (ValueError,RecursionError) as e: raise ValueError('Malformed packet JSON: '+str(e))
 if not isinstance(p,dict):raise ValueError('packet: expected object')
 shape(p,('format','version','exported_at','documents','sources','citations','history','checksum')+ (('threads',) if p.get('version')==2 else ()), 'packet')
 if p['format']!=FORMAT or type(p['version']) is not int or p['version'] not in (1,2): raise ValueError('Unsupported packet format/version; expected agora.research-packet v1 or v2')
 txt(p['exported_at'],'exported_at');txt(p['checksum'],'checksum',64)
 if digest({k:v for k,v in p.items() if k!='checksum'})!=p['checksum']: raise ValueError('Packet checksum mismatch (consistency, not author authenticity)')
 ids=set();groups={}
 for g,bound,minimum in [('documents',8,1),('sources',16,0),('citations',64,0),('history',64,0)]+([('threads',32,0)] if p['version']==2 else []):
  seq(p[g],g,bound,minimum);groups[g]={}
  for v in p[g]:
   if not isinstance(v,dict): raise ValueError(g+': expected object')
   txt(v.get('id'),'packet ID',500)
   if v['id'] in ids: raise ValueError('Duplicate packet ID: '+v['id'])
   ids.add(v['id']);groups[g][v['id']]=v
   provenance(v.get('provenance'))
 for d in p['documents']:
  shape(d,('id','title','markdown','provenance'),'document');txt(d['title'],'title',500,True);txt(d['markdown'],'markdown',100000,True)
 evidence={};version_count=0
 for s in p['sources']:
  shape(s,('id','source','provenance'),'source');v=s['source'];shape(v,SF,'source value');version({k:v[k] for k in VF});txt(v['identity'],'identity');txt(v['external_id'],'external_id');seq(v['versions'],'source versions',16,1)
  seen=set()
  for e in v['versions']:
   version(e);pair=(e['source_revision'],e['content_hash'])
   if pair in seen: raise ValueError('Duplicate source revision/hash evidence')
   seen.add(pair);evidence[(s['id'],)+pair]=e;version_count+=1
  if (v['source_revision'],v['content_hash']) not in seen: raise ValueError('Current source evidence missing')
 if version_count>64: raise ValueError('At most 64 retained source versions per packet')
 used=set()
 def citation(c,doc=None):
  shape(c,CF,'citation')
  for k in CF: txt(c[k],k,100000 if k=='citation_markdown' else 20000 if k=='quoted_text' else 2048)
  if c['document_id'] not in groups['documents'] or c['source_id'] not in groups['sources']: raise ValueError('Broken document/source reference')
  if doc is not None and doc!=c['document_id']: raise ValueError('History belongs to a different document')
  e=evidence.get((c['source_id'],c['source_revision'],c['content_hash']))
  if not e or c['quoted_text'] not in e['content']: raise ValueError('Required citation evidence missing or quotation is not in source')
  used.add(c['source_id'])
 for c in p['citations']:
  shape(c,('id','citation','provenance'),'citation record');citation(c['citation'])
 for h in p['history']:
  shape(h,('id','citation_id','citation','original_proposal_id','replaced_at','provenance'),'history')
  if h['citation_id'] not in groups['citations']: raise ValueError('Broken history citation reference')
  txt(h['original_proposal_id'],'original_proposal_id',500);txt(h['replaced_at'],'replaced_at')
  citation(h['citation'],groups['citations'][h['citation_id']]['citation']['document_id'])
 per_doc={}
 for t in p.get('threads',[]):
  shape(t,('id','thread','location','provenance'),'thread record');validate_thread(t['thread'])
  did=t['thread']['document_id']
  if did not in groups['documents']:raise ValueError('Broken comment document reference')
  per_doc[did]=per_doc.get(did,0)+1
  if per_doc[did]>16:raise ValueError('At most 16 threads per document')
  loc=t['location']
  if not isinstance(loc,dict) or loc.get('state') not in ['attached','orphaned','ambiguous']:raise ValueError('Malformed comment location')
  if loc['state']=='attached' and (set(loc)!={'state','start','end'} or type(loc['start'])!=int or type(loc['end'])!=int):raise ValueError('Malformed comment offsets')
  if t['location']!=locate(t['thread']['anchor'],groups['documents'][did]['markdown']):raise ValueError('Comment location/evidence mismatch')
 if used!=set(groups['sources']): raise ValueError('Unreferenced source is not allowed')
 return p

def export_packet(args,ctx):
 try:
  data=objects(ctx);ids=args['document_ids'];seq(ids,'document_ids',8,1)
  if len(set(ids))!=len(ids): raise ValueError('Select distinct documents')
  p={'format':FORMAT,'version':VERSION,'exported_at':now(),'documents':[],'sources':[],'citations':[],'history':[],'threads':[]}
  for did in ids:
   o=data.get(did)
   if not o or 'studio.document' not in o['facets']: raise ValueError('Native document not found: '+did)
   p['documents'].append({'id':did,'title':o['facets']['core.title']['text'],'markdown':o['facets']['core.text']['text'],'provenance':origin(o)})
  needed={}
  for o in sorted(data.values(),key=lambda o:o['id']):
   c=o['facets'].get(C)
   if not c or c['document_id'] not in ids: continue
   p['citations'].append({'id':o['id'],'citation':copy.deepcopy(c),'provenance':origin(o)})
   values=[c]
   for i,h in enumerate(o['facets'].get(H,{}).get('entries',[])):
    event=data.get(h['proposal_id']); original_event=event['facets'].get('studio.packet-history-event') if event else None
    p['history'].append({'id':o['id']+':history:'+str(i),'citation_id':o['id'],'citation':copy.deepcopy(h['citation']),'original_proposal_id':original_event['original_proposal_id'] if original_event else h['proposal_id'],'replaced_at':h['replaced_at'],'provenance':origin(event) if original_event else origin(o)})
    values.append(h['citation'])
   for c in values: needed.setdefault(c['source_id'],set()).add((c['source_revision'],c['content_hash']))
  for sid,pairs in sorted(needed.items()):
   o=data.get(sid)
   if not o or S not in o['facets']: raise ValueError('Required source missing: '+sid)
   s=o['facets'][S];pairs.add((s['source_revision'],s['content_hash']))
   value={k:copy.deepcopy(s[k]) for k in SF};value['versions']=[{k:v[k] for k in VF} for v in s['versions'] if (v['source_revision'],v['content_hash']) in pairs]
   p['sources'].append({'id':sid,'source':value,'provenance':origin(o)})
  for o in sorted(data.values(),key=lambda o:o['id']):
   t=o['facets'].get(T)
   if t and t['document_id'] in ids:
    p['threads'].append({'id':o['id'],'thread':copy.deepcopy(t),'location':locate(t['anchor'],data[t['document_id']]['facets']['core.text']['text']),'provenance':origin(o)})
  p['checksum']=digest(p);raw=json.dumps(p,ensure_ascii=True,indent=2);validate(raw)
  pid='research-packet-'+p['checksum'];old=data.get(pid)
  return {'result':{'ok':True,'packet_id':pid,'packet_json':raw,'checksum':p['checksum'],'counts':counts(p)},'changes':[] if old else [{'id':pid,'expected_revision':0,'facets':{'studio.research-packet':{'packet_json':raw,'checksum':p['checksum'],'created_at':p['exported_at']}}}]}
 except (ValueError,KeyError,TypeError,RecursionError) as e: return fail(e)
def counts(p): return {g:len(p[g]) for g in ('documents','sources','citations','history')+ (('threads',) if p['version']==2 else ())}|{'source_versions':sum(len(s['source']['versions']) for s in p['sources'])}
def attempt_id(token):
 if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}',token): raise ValueError('attempt_token must be 8..128 ASCII letters/digits/_/-; reuse it for retries')
 return 'packet-attempt-'+hashlib.sha256(token.encode()).hexdigest()
def plan(p,aid):
 prefix='packet-copy-'+aid.removeprefix('packet-attempt-')+'-'
 return {'collection_id':prefix+'collection','mapping':{v['id']:prefix+g+'-'+str(i) for g in ('documents','sources','citations','history')+ (('threads',) if p['version']==2 else ()) for i,v in enumerate(p[g])}}
def target_free(data,name,own=None):
 for o in data.values():
  c=o['facets'].get('core.collection')
  if c and c['name'].strip().casefold()==name.strip().casefold() and o['id']!=own: raise ValueError('Collection name already exists; use a fresh preview with a new name/attempt')
def preview(args,ctx):
 try:
  p=validate(args['packet_json']);name=args['collection_name'].strip();txt(name,'collection_name',120);aid=attempt_id(args['attempt_token']);data=objects(ctx);o=data.get(aid)
  if o:
   v=o['facets'].get(A)
   if not v or v['checksum']!=p['checksum'] or v['collection_name']!=name: raise ValueError('Attempt token already binds different input; use a new token')
   if v['status']=='cancelled': raise ValueError('Attempt was cancelled; use a new token for a new preview')
   return {'result':summary(v,o['revision'])}
  target_free(data,name);pl=plan(p,aid)
  v={'attempt_id':aid,'status':'previewed','packet_json':args['packet_json'],'checksum':p['checksum'],'collection_name':name,'created_at':now(),**pl}
  v['preview_seal']=digest(v)
  return {'result':summary(v,1),'changes':[{'id':aid,'expected_revision':0,'facets':{A:v}}]}
 except (ValueError,KeyError,TypeError,RecursionError) as e:return fail(e)
def summary(v,rev):
 p=validate(v['packet_json'])
 return {'ok':True,'attempt_id':v['attempt_id'],'preview_revision':rev,'status':v['status'],'checksum':p['checksum'],'format':FORMAT,'version':p['version'],'collection_name':v['collection_name'],'collection_id':v['collection_id'],'mapping':v['mapping'],'counts':counts(p),'titles':[d['title'] for d in p['documents']],'provenance':[{'title':d['title'],'chain':d['provenance']} for d in p['documents']],'new_native_objects':sum(len(p[g]) for g in ('documents','sources','citations','history')+ (('threads',) if p['version']==2 else ()))+1,'notice':'SHA-256 checks consistency, not author authenticity. No fetch or pending proposals. Apply is explicit; retry this attempt to reuse its mapping.'}
def apply_import(args,ctx):
 try:
  data=objects(ctx);o=data.get(args['attempt_id']);v=copy.deepcopy(o['facets'].get(A)) if o else None
  if not v: raise ValueError('Preview not found')
  if v['checksum']!=args['checksum']: raise ValueError('Preview checksum changed; preview again')
  if v['status']=='applied': return {'result':dict(summary(v,o['revision']),already_applied=True),'changes':[]}
  if v['status']!='previewed': raise ValueError('Attempt is cancelled; no import permitted')
  if o['revision']!=args['preview_revision']: raise ValueError('Preview revision is stale; preview again')
  seal=v.pop('preview_seal')
  if digest(v)!=seal: raise ValueError('Preview data changed; start a fresh preview')
  p=validate(v['packet_json']);pl=plan(p,v['attempt_id'])
  if p['checksum']!=v['checksum'] or any(pl[k]!=v[k] for k in pl): raise ValueError('Preview mapping/data changed')
  target_free(data,v['collection_name']);mapping=pl['mapping'];dest=list(mapping.values())+[pl['collection_id']]
  if len(set(dest))!=len(dest) or any(i in data for i in dest): raise ValueError('Destination identity collision; nothing imported')
  changes=[]
  def add(pid,facets,prov): changes.append({'id':mapping[pid],'expected_revision':0,'facets':dict(facets,**{'studio.packet-origin':{'chain':prov,'attempt_id':v['attempt_id'],'packet_id':pid}})})
  def remap(c): return dict(c,document_id=mapping[c['document_id']],source_id=mapping[c['source_id']])
  for d in p['documents']:add(d['id'],{'core.title':{'text':d['title']},'core.text':{'text':d['markdown']},'studio.document':{'format':'markdown'}},d['provenance'])
  for s in p['sources']:add(s['id'],{S:s['source']},s['provenance'])
  for c in p['citations']:
   history=[{'citation':remap(h['citation']),'proposal_id':mapping[h['id']],'replaced_at':h['replaced_at']} for h in p['history'] if h['citation_id']==c['id']]
   add(c['id'],{C:remap(c['citation']),H:{'entries':history}},c['provenance'])
  for h in p['history']:add(h['id'],{'studio.packet-history-event':{'citation_id':mapping[h['citation_id']],'citation':remap(h['citation']),'original_proposal_id':h['original_proposal_id'],'replaced_at':h['replaced_at']}},h['provenance'])
  for t in p.get('threads',[]):
   value=copy.deepcopy(t['thread']);value['document_id']=mapping[value['document_id']]
   add(t['id'],{T:value},t['provenance'])
  changes.append({'id':pl['collection_id'],'expected_revision':0,'facets':{'core.collection':{'name':v['collection_name'],'entries':[mapping[d['id']] for d in p['documents']]},'studio.packet-collection':{'attempt_id':v['attempt_id'],'checksum':v['checksum']}}})
  v.update(status='applied',preview_seal=seal,applied_at=now());changes.append({'id':o['id'],'expected_revision':o['revision'],'facets':{A:v}})
  return {'result':dict(summary(v,o['revision']+1),already_applied=False),'changes':changes}
 except (ValueError,KeyError,TypeError,RecursionError) as e:return fail(e)
def cancel(args,ctx):
 try:
  o=objects(ctx).get(args['attempt_id']);v=copy.deepcopy(o['facets'].get(A)) if o else None
  if not v: raise ValueError('Attempt not found')
  if v['status']=='applied': raise ValueError('Already applied; cancellation is not deletion')
  if v['status']=='cancelled':return {'result':{'ok':True,'status':'cancelled'},'changes':[]}
  v['status']='cancelled';v['cancelled_at']=now()
  return {'result':{'ok':True,'status':'cancelled'},'changes':[{'id':o['id'],'expected_revision':o['revision'],'facets':{A:v}}]}
 except (ValueError,KeyError,TypeError) as e:return fail(e)
