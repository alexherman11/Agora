"""Run only with user-authorized integration testing in the designated guest.
Uses installed actions, not a substitute implementation. Retains one QA collection.
"""
import agora_native as a, json, uuid, copy
def query(f): 
 r=a.call('world.query',{'facets':[f],'limit':1000})
 assert r['complete'], 'Do not truncate verification'
 return r['items']
def invoke(action,args):
 t=next(t for t in a.call('tools.list',{})['actions'] if t['package']=='studio.packets' and t['action']==action)
 return a.call('action.invoke',{'package':t['package'],'revision':t['revision'],'action':action,'args':args})['result']
def applyargs(p):return {k:p[k] for k in ('attempt_id','preview_revision','checksum')}
before={o['id']:o for f in ('studio.document','studio.source','studio.citation') for o in query(f)}
e=invoke('export_packet',{'document_ids':['doc-review-alpha','doc-review-beta']});assert e['ok'],e
assert e['counts']==dict(documents=2,sources=1,citations=2,history=2,source_versions=2),e
token='qa-'+str(uuid.uuid4())
p=invoke('preview',{'packet_json':e['packet_json'],'collection_name':'Packet QA '+token,'attempt_token':token});assert p['ok'],p
assert {o['id'] for o in query('studio.document')}=={i for i,o in before.items() if 'studio.document' in o['facets']}
r=invoke('apply_import',applyargs(p));assert r['ok'],r
r2=invoke('apply_import',applyargs(p));assert r2['ok'] and r2['already_applied'] and r2['mapping']==r['mapping']
for id,o in before.items():assert a.call('world.get',{'id':id})==o, id+' changed'
for c in json.loads(e['packet_json'])['citations']:
 o=a.call('world.get',{'id':r['mapping'][c['id']]});v=o['facets']['studio.citation']
 assert v['source_id']==r['mapping'][c['citation']['source_id']]
 assert v['document_id']==r['mapping'][c['citation']['document_id']]
 h=o['facets']['studio.citation-history']['entries'][0]
 assert 'studio.packet-history-event' in a.call('world.get',{'id':h['proposal_id']})['facets']
bad=invoke('preview',{'packet_json':'{','collection_name':'Invalid QA','attempt_token':'invalid-'+str(uuid.uuid4())});assert not bad['ok']
c=invoke('preview',{'packet_json':e['packet_json'],'collection_name':'Cancelled QA '+token,'attempt_token':'cancel-'+token});assert c['ok']
assert invoke('cancel',{'attempt_id':c['attempt_id']})['ok']
assert not invoke('apply_import',applyargs(c))['ok']
print(json.dumps({'passed':True,'collection_id':r['collection_id'],'mapping':r['mapping'],'packet_id':e['packet_id']},indent=2))
