"""Repeatable guest tests: real HTTP fixture + disposable object contexts; no live writes."""
import unittest, copy
from actions import import_source, refresh_source, prepare, apply, dismiss, markdown, PROPOSAL, HISTORY
SID='source-4cb145483e82fc393af71968cd3d1c3a'
OLD='The team counted twelve tide pools along the eastern path.'
NEW='The team counted fourteen tide pools along the eastern path.'
URL='http://127.0.0.1:8860/sources/'
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  a=import_source({'url':URL+'coast'},{'objects':[]})['changes'][0]
  source={'id':a['id'],'revision':1,'facets':a['facets']}
  s=source['facets']['studio.source']; data=[source]
  for tag in ('a','b'):
   c=dict(document_id='doc-'+tag,source_id=SID,source_revision='1',content_hash=s['content_hash'],quoted_text=OLD,citation_markdown=markdown(s,OLD),created_at='original')
   data += [{'id':'doc-'+tag,'revision':1,'facets':{'studio.document':{'format':'markdown'},'core.text':{'text':'Intro\\n\\n'+c['citation_markdown']+'\\n\\nKeep conclusion.'}}},
            {'id':'cit-'+tag,'revision':1,'facets':{'studio.citation':c}}]
  r=refresh_source({'source_id':SID,'url':URL+'coast?version=3'},{'objects':data})
  cls.base=cls.commit(data,r)
 @staticmethod
 def commit(data,r):
  assert r['result']['ok'],r
  d={o['id']:copy.deepcopy(o) for o in data}
  for ch in r.get('changes',[]):
   o=d.setdefault(ch['id'],dict(id=ch['id'],revision=0,facets={}))
   assert o['revision']==ch['expected_revision']
   o['facets'].update(copy.deepcopy(ch['facets']));o['revision']+=1
  return list(d.values())
 def setUp(self): self.data=copy.deepcopy(self.base)
 def obj(self,id): return next(o for o in self.data if o['id']==id)
 def proposals(self):
  ids=[]
  for tag in ('a','b'):
   r=prepare({'citation_id':'cit-'+tag,'excerpt':NEW},{'objects':self.data})
   self.data=self.commit(self.data,r);ids.append(r['result']['proposal_id'])
  return ids
 def test_invalid_blank_and_non_source(self):
  for excerpt in ('','   ','not in retained source'):
   r=prepare({'citation_id':'cit-a','excerpt':excerpt},{'objects':self.data})
   self.assertEqual(r['result']['code'],'invalid_excerpt');self.assertFalse(r.get('changes'))
 def test_atomic_success_evidence_and_idempotence(self):
  ids=self.proposals();before=copy.deepcopy(self.data)
  r=apply({'proposal_ids':ids},{'objects':self.data})
  self.assertTrue(r['result']['ok']);self.assertEqual(len(r['changes']),6)
  self.data=self.commit(self.data,r)
  for tag in ('a','b'):
   doc=self.obj('doc-'+tag);cit=self.obj('cit-'+tag)
   self.assertIn('Keep conclusion.',doc['facets']['core.text']['text'])
   self.assertEqual(doc['facets']['core.text']['text'].count(NEW),1)
   self.assertEqual(cit['facets'][HISTORY]['entries'][0]['citation']['quoted_text'],OLD)
   self.assertEqual(cit['facets']['studio.citation']['source_revision'],'3')
  r=apply({'proposal_ids':ids},{'objects':self.data})
  self.assertFalse(r['changes']);self.assertEqual(r['result']['already_applied'],ids)
  self.assertEqual(self.obj(SID)['facets']['studio.source']['versions'][0]['source_revision'],'1')
 def test_document_and_citation_conflicts_abort_batch(self):
  for target in ('doc-a','cit-a'):
   self.data=copy.deepcopy(self.base);ids=self.proposals()
   self.obj(target)['revision']+=1
   if target=='doc-a':self.obj(target)['facets']['core.text']['text']+='Author edit.'
   before=copy.deepcopy(self.data)
   r=apply({'proposal_ids':ids},{'objects':self.data})
   self.assertEqual(r['result']['code'],'conflict');self.assertFalse(r.get('changes'));self.assertEqual(self.data,before)
 def test_source_conflict(self):
  ids=self.proposals();self.obj(SID)['facets']['studio.source']['source_revision']='changed'
  r=apply({'proposal_ids':ids},{'objects':self.data})
  self.assertEqual(r['result']['code'],'conflict');self.assertFalse(r.get('changes'))
 def test_cancel_does_not_change_docs(self):
  ids=self.proposals();before=copy.deepcopy(self.obj('doc-a'))
  r=dismiss({'proposal_ids':ids},{'objects':self.data});self.data=self.commit(self.data,r)
  self.assertEqual(self.obj('doc-a'),before)
  self.assertFalse(dismiss({'proposal_ids':ids},{'objects':self.data})['changes'])
  self.assertFalse(apply({'proposal_ids':ids},{'objects':self.data})['result']['ok'])
 def test_duplicate_and_ambiguous_locations(self):
  ids=self.proposals();r=prepare({'citation_id':'cit-a','excerpt':NEW},{'objects':self.data})
  self.data=self.commit(self.data,r)
  result=apply({'proposal_ids':ids+[r['result']['proposal_id']]},{'objects':self.data})
  self.assertEqual(result['result']['code'],'duplicate_citation');self.assertFalse(result.get('changes'))
  doc=self.obj('doc-a');doc['facets']['core.text']['text']+=self.obj('cit-a')['facets']['studio.citation']['citation_markdown']
  r=prepare({'citation_id':'cit-a','excerpt':NEW},{'objects':self.data})
  self.assertEqual(r['result']['code'],'citation_location')
 def test_failed_refresh_and_wrong_identity_write_nothing(self):
  for path in ('broken','orchard'):
   before=copy.deepcopy(self.data)
   r=refresh_source({'source_id':SID,'url':URL+path},{'objects':self.data})
   self.assertFalse(r['result']['ok']);self.assertFalse(r.get('changes'));self.assertEqual(self.data,before)
if __name__=='__main__': unittest.main()

