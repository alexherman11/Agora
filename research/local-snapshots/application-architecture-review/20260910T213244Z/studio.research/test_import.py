"""Source-only regression tests; real fixture HTTP, isolated in-memory context."""
import unittest, copy, json, io
from unittest.mock import patch
from actions import import_source

class SourcesTests(unittest.TestCase):
    def fetch(self,path,objects=[]):
        return import_source({'url':'http://127.0.0.1:8860/sources/'+path},{'objects':objects})
    def test_fixture_identity_hash_and_reimport(self):
        import hashlib
        a=self.fetch('coast')
        self.assertTrue(a['result']['ok'])
        change=a['changes'][0]
        s=change['facets']['studio.source']
        self.assertEqual(hashlib.sha256(s['content'].encode()).hexdigest(),s['content_hash'])
        obj={'id':change['id'],'revision':1,'facets':change['facets']}
        b=self.fetch('slow',[obj])
        self.assertEqual(a['result']['source_id'],b['result']['source_id'])
        self.assertTrue(b['result']['reused'])
        self.assertEqual(len(b['changes'][0]['facets']['studio.source']['versions']),1)
        self.assertNotEqual(a['result']['source_id'],self.fetch('orchard')['result']['source_id'])
    def test_http_errors_write_nothing(self):
        for path,code in [('broken','http_503'),('missing','http_404')]:
            r=self.fetch(path)
            self.assertFalse(r['result']['ok']);self.assertEqual(r['result']['code'],code)
            self.assertFalse(r.get('changes'))
    def test_invalid_url(self):
        r=import_source({'url':'file:///etc/passwd'},{'objects':[]})
        self.assertFalse(r['result']['ok']);self.assertFalse(r.get('changes'))
    def test_malformed_payloads(self):
        class Response(io.BytesIO):
            def geturl(self): return 'http://127.0.0.1:8860/sources/coast'
        for data in [[],{}, {'id':'x'},'not json']:
            with patch('actions.urlopen',return_value=Response(json.dumps(data).encode())):
                r=self.fetch('coast')
                self.assertFalse(r['result']['ok']);self.assertFalse(r.get('changes'))
    def test_revision_snapshots_preserved(self):
        class Response(io.BytesIO):
            def geturl(self): return 'http://127.0.0.1:8860/sources/coast'
        a=self.fetch('coast');c=a['changes'][0];old=copy.deepcopy(c['facets']['studio.source'])
        data={'id':'coast','title':'Revised fictional source','author':'Mira Chen','published':'2026-09-01','revision':'2','content':'Changed fixture test text.'}
        with patch('actions.urlopen',return_value=Response(json.dumps(data).encode())):
            b=self.fetch('coast',[{'id':c['id'],'revision':1,'facets':c['facets']}])
        s=b['changes'][0]['facets']['studio.source']
        self.assertEqual(len(s['versions']),2)
        self.assertEqual(s['versions'][0],old['versions'][0])
        self.assertEqual(s['source_revision'],'2')
if __name__=='__main__': unittest.main()
