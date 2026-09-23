"""Guest-side JSON/Markdown source import; no browser fetch or live bridge required."""
import json, hashlib
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError

def import_source(args, context):
    url=args['url'].strip()
    def validate(u):
        p=urlsplit(u)
        if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
            raise ValueError('Use an HTTP(S) source URL without embedded credentials.')
        return p
    try:
        validate(url)
        with urlopen(Request(url,headers={'Accept':'application/json'}),timeout=12) as response:
            final=response.geturl()
            p=validate(final)
            raw=response.read(1048577)
        if len(raw)>1048576:
            raise ValueError('Source exceeds the 1 MiB import limit.')
        data=json.loads(raw)
        if not isinstance(data,dict):
            raise ValueError('Source JSON must be an object.')
        for key in ('id','title','author','published','revision','content'):
            if not isinstance(data.get(key),str) or not data[key].strip():
                raise ValueError('Source JSON needs non-empty text fields: id, title, author, published, revision, content.')
        if len(data['content'])>100000:
            raise ValueError('Source text exceeds 100,000 characters.')
        identity=p.scheme.lower()+'://'+p.netloc.lower()+'|'+data['id']
        sid='source-'+hashlib.sha256(identity.encode()).hexdigest()[:32]
        objects=context.get('objects',[])
        if isinstance(objects,dict): objects=list(objects.values())
        old=next((o for o in objects if o['id']==sid),None)
        previous=old['facets'].get('studio.source') if old else None
        stamp=datetime.now(timezone.utc).isoformat()
        digest=hashlib.sha256(data['content'].encode()).hexdigest()
        snapshot={'source_revision':data['revision'],'content_hash':digest,'content':data['content'],'title':data['title'],'author':data['author'],'published':data['published'],'requested_url':url,'final_url':final,'retrieved_at':stamp}
        versions=list(previous.get('versions',[])) if previous else []
        if not any(v['source_revision']==data['revision'] and v['content_hash']==digest for v in versions):
            versions.append(snapshot)
        value=dict(snapshot,identity=identity,external_id=data['id'],versions=versions)
        return {'result':{'ok':True,'source_id':sid,'reused':bool(previous),'source_revision':data['revision'],'content_hash':digest},
                'changes':[{'id':sid,'expected_revision':old['revision'] if old else 0,'facets':{'studio.source':value}}]}
    except HTTPError as e:
        return {'result':{'ok':False,'code':'http_'+str(e.code),'error':'Import failed: HTTP '+str(e.code)+'. No source was saved; check the URL or retry.'}}
    except (URLError,TimeoutError,OSError,ValueError,TypeError) as e:
        return {'result':{'ok':False,'code':'invalid_or_unavailable','error':'Import failed: '+str(e)+'. No source was saved.'}}


"""Explicit citation review. All writes are returned for one native transaction."""
import copy, re, uuid

PROPOSAL = 'studio.citation-proposal'
HISTORY = 'studio.citation-history'

def objects(context):
    values=context.get('objects', [])
    return {o['id']:o for o in (values.values() if isinstance(values,dict) else values)}

def fail(message, code='invalid', **details):
    return {'result':dict(ok=False, code=code, error=message, **details)}

def change(o, facets):
    return {'id':o['id'],'expected_revision':o['revision'],'facets':facets}

def now():
    return datetime.now(timezone.utc).isoformat()

def markdown(s, quote):
    def esc(v):
        return re.sub(r'([\\`*_\[\]<>])', r'\\\1', v)
    return '> '+quote.replace('\n','\n> ')+'\n\n— '+esc(s['author'])+', ['+esc(s['title'])+'](<'+s['final_url'].replace('>','%3E')+'>), '+esc(s['published'])+'; revision '+esc(s['source_revision'])+'.'

def refresh_source(args, context):
    data=objects(context)
    old=data.get(args['source_id'])
    if not old or 'studio.source' not in old['facets']:
        return fail('Select a retained source first.')
    # Refresh the explicitly selected native identity, including a portable copy.
    # The temporary canonical alias exists only in memory: no original source write.
    prior=old['facets']['studio.source']
    canonical='source-'+hashlib.sha256(prior['identity'].encode()).hexdigest()[:32]
    alias=copy.deepcopy(old);alias['id']=canonical
    response=import_source({'url':args['url']}, {'objects':[alias]})
    if not response['result']['ok']:
        return response
    updated=response['changes'][0]['facets']['studio.source']
    if updated['identity']!=prior['identity']:
        return fail('This URL identifies a different source. Use Import for a new source; the selected source was not changed.', 'identity_mismatch')
    response['changes']=[change(old,{'studio.source':updated})]
    response['result'].update(source_id=old['id'],reused=True,citations_unchanged=True)
    return response

def prepare(args, context):
    data=objects(context)
    co=data.get(args['citation_id'])
    if not co or 'studio.citation' not in co['facets']:
        return fail('Citation not found.')
    c=co['facets']['studio.citation']
    doc=data.get(c['document_id']); so=data.get(c['source_id'])
    if not doc or 'studio.document' not in doc['facets'] or not so:
        return fail('Citation document or retained source is missing.')
    s=so['facets']['studio.source']
    quote=args['excerpt']
    if not quote.strip() or quote not in s['content']:
        return fail('Choose a non-blank exact excerpt from the current retained source.', 'invalid_excerpt')
    if c['source_revision']==s['source_revision'] and c['content_hash']==s['content_hash']:
        return fail('Citation already uses the current retained source.', 'already_current')
    if not any(v['source_revision']==c['source_revision'] and v['content_hash']==c['content_hash'] and c['quoted_text'] in v['content'] for v in s['versions']):
        return fail('Original quotation evidence is missing; resolve provenance before updating.', 'missing_evidence')
    if not c['citation_markdown'] or doc['facets']['core.text']['text'].count(c['citation_markdown'])!=1:
        return fail('Original citation must occur exactly once in the document; review edited or ambiguous text manually.', 'citation_location')
    proposed=dict(c, source_revision=s['source_revision'], content_hash=s['content_hash'], quoted_text=quote, citation_markdown=markdown(s,quote), created_at=now())
    p={'citation_id':co['id'],'document_id':doc['id'],'source_id':so['id'],
       'document_revision':doc['revision'],'citation_revision':co['revision'],
       'old_citation':copy.deepcopy(c),'proposed_citation':proposed,
       'status':'prepared','created_at':now(),'resolved_at':''}
    pid='proposal-'+str(uuid.uuid4())
    return {'result':{'ok':True,'proposal_id':pid,'proposal':p},
            'changes':[{'id':pid,'expected_revision':0,'facets':{PROPOSAL:p}}]}

def dismiss(args, context):
    data=objects(context); changes=[]
    for pid in dict.fromkeys(args['proposal_ids']):
        o=data.get(pid);p=o['facets'].get(PROPOSAL) if o else None
        if not p: return fail('Proposal not found: '+pid)
        if p['status']=='applied': return fail('Applied proposals cannot be dismissed. Prepare a new review instead.')
        if p['status']=='dismissed': continue
        changes.append(change(o,{PROPOSAL:dict(p,status='dismissed',resolved_at=now())}))
    return {'result':{'ok':True,'dismissed':[c['id'] for c in changes]},'changes':changes}

def apply(args, context):
    data=objects(context); pending=[]; skipped=[]; conflicts=[]; seen=set()
    for pid in dict.fromkeys(args['proposal_ids']):
        o=data.get(pid);p=o['facets'].get(PROPOSAL) if o else None
        if not p: return fail('Proposal not found: '+pid)
        if p['status']=='applied': skipped.append(pid);continue
        if p['status']!='prepared': return fail('A dismissed proposal cannot be applied: '+pid)
        if p['citation_id'] in seen: return fail('Select at most one proposal per citation.', 'duplicate_citation')
        seen.add(p['citation_id'])
        doc=data.get(p['document_id']); co=data.get(p['citation_id']); so=data.get(p['source_id'])
        if (not doc or not co or not so or
            doc['revision']!=p['document_revision'] or co['revision']!=p['citation_revision'] or
            co['facets'].get('studio.citation')!=p['old_citation']):
            conflicts.append(pid);continue
        s=so['facets'].get('studio.source',{}); n=p['proposed_citation']
        if (p['old_citation']['document_id']!=p['document_id'] or
            p['old_citation']['source_id']!=p['source_id'] or
            n['document_id']!=p['document_id'] or n['source_id']!=p['source_id']):
            conflicts.append(pid);continue
        if (s.get('source_revision')!=n['source_revision'] or s.get('content_hash')!=n['content_hash'] or
            not n['quoted_text'].strip() or n['quoted_text'] not in s.get('content','') or
            markdown(s,n['quoted_text'])!=n['citation_markdown']):
            conflicts.append(pid);continue
        old=p['old_citation']['citation_markdown']
        if not old or doc['facets']['core.text']['text'].count(old)!=1:
            conflicts.append(pid);continue
        pending.append((o,p,doc,co))
    if conflicts:
        return fail('Nothing applied: a document, citation, or source changed after preparation. Dismiss affected proposals and prepare again after reviewing current text.', 'conflict', proposal_ids=conflicts)
    replacements={}
    for o,p,doc,co in pending:
        text=doc['facets']['core.text']['text']; old=p['old_citation']['citation_markdown']; start=text.index(old)
        replacements.setdefault(doc['id'],[]).append((start,start+len(old),p['proposed_citation']['citation_markdown']))
    changes=[]
    for did, spans in replacements.items():
        spans.sort()
        if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):
            return fail('Selected citation locations overlap; nothing applied.', 'overlap')
        doc=data[did]; value=doc['facets']['core.text']['text']
        for start,end,new in reversed(spans): value=value[:start]+new+value[end:]
        if len(value)>100000: return fail('Updated document exceeds 100,000 characters; nothing applied.')
        changes.append(change(doc,{'core.text':dict(doc['facets']['core.text'],text=value)}))
    stamp=now()
    for o,p,doc,co in pending:
        history=copy.deepcopy(co['facets'].get(HISTORY,{'entries':[]}))
        history['entries'].append({'citation':p['old_citation'],'proposal_id':o['id'],'replaced_at':stamp})
        changes.append(change(co,{'studio.citation':p['proposed_citation'],HISTORY:history}))
        changes.append(change(o,{PROPOSAL:dict(p,status='applied',resolved_at=stamp)}))
    return {'result':{'ok':True,'applied':[o['id'] for o,p,d,c in pending],'already_applied':skipped,'documents':list(replacements)},'changes':changes}

