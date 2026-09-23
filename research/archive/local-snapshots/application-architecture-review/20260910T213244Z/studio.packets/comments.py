"""Bounded local discussions; pure actions and portable anchor validation."""
import copy, hashlib, uuid
from datetime import datetime, timezone
T='studio.comment-thread'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def ulen(s): return len(s.encode('utf-16-le'))//2
def cut(s,a,b):
 try: return s.encode('utf-16-le')[2*a:2*b].decode('utf-16-le')
 except UnicodeError: raise ValueError('Selection splits a UTF-16 surrogate pair')
def positions(s,q):
 out=[];i=0
 while True:
  i=s.find(q,i)
  if i<0:return out
  out.append(i);i+=1

def evidence(text,rev,start,end,quote):
 if type(start)!=int or type(end)!=int or not 0<=start<end<=ulen(text):raise ValueError('Invalid UTF-16 selection range')
 if not quote.strip() or cut(text,start,end)!=quote:raise ValueError('Selection quote mismatches document')
 i=len(cut(text,0,start));j=i+len(quote)
 return dict(convention='utf16-code-units',document_revision=rev,start=start,end=end,quote=quote,prefix=text[max(0,i-32):i],suffix=text[j:j+32],snapshot=text,sha256=sha(text),occurrences=len(positions(text,quote)))
def validate_anchor(a):
 keys={'convention','document_revision','start','end','quote','prefix','suffix','snapshot','sha256','occurrences'}
 if not isinstance(a,dict) or set(a)!=keys:raise ValueError('Malformed anchor evidence')
 if type(a['document_revision'])!=int or a['document_revision']<1 or not isinstance(a['snapshot'],str) or len(a['snapshot'])>100000:raise ValueError('Invalid anchor revision/snapshot')
 if any(not isinstance(a[k],str) for k in ['convention','quote','prefix','suffix','sha256']) or type(a['occurrences'])!=int:raise ValueError('Malformed anchor text/count')
 if evidence(a['snapshot'],a['document_revision'],a['start'],a['end'],a['quote'])!=a:raise ValueError('Anchor evidence mismatch')
def locate(a,text):
 if text==a['snapshot']:return dict(state='attached',start=a['start'],end=a['end'])
 hits=positions(text,a['quote'])
 if not hits:return dict(state='orphaned',reason='Quotation was deleted or replaced')
 if len(hits)!=1 or a['occurrences']!=1:return dict(state='ambiguous',reason='Duplicate quotation after document changed; explicitly reanchor')
 i=hits[0];j=i+len(a['quote'])
 if (a['prefix'] and not text[:i].endswith(a['prefix'])) or (a['suffix'] and not text[j:].startswith(a['suffix'])):return dict(state='orphaned',reason='Surrounding evidence changed; explicitly reanchor')
 return dict(state='attached',start=ulen(text[:i]),end=ulen(text[:j]))
def validate_thread(t):
 if not isinstance(t,dict) or set(t)!={'document_id','anchor','original_anchor','messages','status','created_at','updated_at'}:raise ValueError('Malformed comment thread')
 if not isinstance(t['document_id'],str) or not t['document_id'] or len(t['document_id'])>500 or t['status'] not in ['open','resolved']:raise ValueError('Invalid comment link/state')
 validate_anchor(t['anchor']);validate_anchor(t['original_anchor'])
 if not isinstance(t['messages'],list) or not 1<=len(t['messages'])<=8:raise ValueError('At most eight messages per thread')
 for m in t['messages']:
  if not isinstance(m,dict) or set(m)!={'text','created_at'}:raise ValueError('Malformed comment message')
  message(m['text'])
  if not isinstance(m['created_at'],str) or not 1<=len(m['created_at'])<=100:raise ValueError('Invalid message timestamp')
 for k in ['created_at','updated_at']:
  if not isinstance(t[k],str) or not 1<=len(t[k])<=100:raise ValueError('Invalid thread timestamp')
def message(v):
 if not isinstance(v,str) or not v.strip() or len(v)>3000:raise ValueError('Message must contain 1–3000 Unicode characters')
 v.encode('utf-8');return {'text':v,'created_at':now()}
def objects(ctx):
 v=ctx.get('objects',[]);return {o['id']:o for o in (v.values() if isinstance(v,dict) else v)}
def selected(args,data):
 d=data.get(args['document_id'])
 if not d or 'studio.document' not in d['facets']:raise ValueError('Document not found')
 if d['revision']!=args['document_revision']:raise ValueError('Stale selection: document revision changed; select again')
 return evidence(d['facets']['core.text']['text'],d['revision'],args['start'],args['end'],args['quote'])
def run(action,args,ctx):
 try:
  data=objects(ctx);changes=[]
  if action=='list':
   d=data.get(args['document_id'])
   if not d:raise ValueError('Document not found')
   return {'result':{'ok':True,'document_revision':d['revision'],'threads':[dict(id=o['id'],revision=o['revision'],thread=o['facets'][T],location=locate(o['facets'][T]['anchor'],d['facets']['core.text']['text'])) for o in data.values() if T in o['facets'] and o['facets'][T]['document_id']==d['id']]}}
  if action=='create':
   a=selected(args,data);m=message(args['message'])
   if sum(1 for o in data.values() if o['facets'].get(T,{}).get('document_id')==args['document_id'])>=16:raise ValueError('At most 16 threads per document (including resolved threads)')
   tid='comment-'+str(uuid.uuid4());rev=0;t=dict(document_id=args['document_id'],anchor=a,original_anchor=copy.deepcopy(a),messages=[m],status='open',created_at=now(),updated_at=now())
  else:
   tid=args['thread_id'];o=data.get(tid)
   if not o or T not in o['facets']:raise ValueError('Comment thread not found')
   rev=o['revision']
   if rev!=args['thread_revision']:raise ValueError('Thread changed; refresh before retrying')
   t=copy.deepcopy(o['facets'][T])
   if action=='reply':
    if len(t['messages'])>=8:raise ValueError('At most eight messages per thread; no message added')
    t['messages'].append(message(args['message']))
   elif action=='set_status':t['status']=args['status']
   elif action=='reanchor':
    if args['document_id']!=t['document_id']:raise ValueError('Reanchor must stay in the same document')
    t['anchor']=selected(args,data)
   t['updated_at']=now()
  validate_thread(t)
  return {'result':{'ok':True,'thread_id':tid,'thread_revision':rev+1,'thread':t},'changes':[{'id':tid,'expected_revision':rev,'facets':{T:t}}]}
 except (ValueError,KeyError,TypeError,UnicodeError) as e:return {'result':{'ok':False,'code':'comment_refused','error':str(e)}}
def create(a,c):return run('create',a,c)
def reply(a,c):return run('reply',a,c)
def set_status(a,c):return run('set_status',a,c)
def reanchor(a,c):return run('reanchor',a,c)
def list_threads(a,c):return run('list',a,c)
