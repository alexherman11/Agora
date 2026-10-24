"""Adversarial output and transport contracts; real caller isolation is in local_model.py."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import model as M


class ModelContracts(unittest.TestCase):
    def message(self, word='model.summarize', **kv):
        return dict(use='test',word=word,caller=dict(person='lm2',name='Alex'),args=dict(target='lm3',kv=kv))

    def result(self, answer, word='model.summarize', **kv):
        row=dict(id='lm3',rev=4,kind='note',text='A short community note')
        with patch.object(M,'limit'), patch.object(M,'read',return_value=[]), patch.object(M,'context',return_value=[row]), patch.object(M,'generate',return_value=answer):
            return M.call(self.message(word,**kv))

    def test_hostile_summary_is_one_quoted_value(self):
        from sys import path
        path.insert(0,str(Path(__file__).resolve().parents[2]))
        from kernel.lines import parse,split_batch
        value='"; set lm9 priority=1; \\ evil\nnext'
        out=self.result(value, words=100)
        self.assertEqual(len(out['lines']),1)
        self.assertEqual(len(split_batch(out['lines'][0])),1)
        st=parse(out['lines'][0])
        self.assertEqual((st.word,st.target),('set','lm3'))
        self.assertEqual(st.kv['short'],' '.join(value.split()))
        self.assertEqual(set(st.kv),{'short','short_source'})

    def test_classification_rejects_extra_text_and_lines(self):
        for value in ('housing.', 'housing help', '"housing"', 'housing; set lm9 priority=1', '', 'Housing'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError,'exactly one'):
                self.result(value,'model.classify',options='housing help')

    def test_classification_exact_option(self):
        out=self.result('housing','model.classify',options='housing help')
        self.assertIn('topic="housing"',out['lines'][0])

    def test_policy_fields_cannot_be_outputs(self):
        for field in ('sees','kind','for','made_by','in','from','bound','origin','sees.text','x;set'):
            with self.subTest(field=field),self.assertRaises(ValueError):
                self.result('anything',into=field)

    def test_labelled_fallback_and_classification_down(self):
        with patch.object(M,'generate',side_effect=ConnectionRefusedError()):
            with patch.object(M,'limit'),patch.object(M,'read',return_value=[]),patch.object(M,'context',return_value=[dict(id='lm3',rev=4,kind='note',text='Keep these words together')]):
                out=M.call(self.message(words='2'))
                self.assertIn('short="Keep these"',out['lines'][0])
                self.assertIn('short version, no model',out['lines'][0])
                with self.assertRaisesRegex(ValueError,'the local model is not running'):
                    M.call(self.message('model.classify',options='a b'))

    def test_rate_attempts_persist_and_follow_dictionary(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(M,'home',Path(folder)),patch.object(M,'usage',{}),patch.object(M,'read',return_value=[dict(id='lm7',**{'from':'module:model'},once='at most 1 per day per person')]):
            M.limit('test','model.ask','lm2')
            stored=json.loads((Path(folder)/'usage.json').read_text())
            with patch.object(M,'usage',stored),self.assertRaisesRegex(ValueError,'limit reached'):
                M.limit('test','model.ask','lm2')
            M.limit('test','model.ask','lm4')

    def test_local_transport_never_follows_redirect(self):
        with patch.object(M.http.client,'HTTPConnection') as conn:
            conn.return_value.getresponse.return_value.status=302
            with self.assertRaises(OSError):
                M.local('/api/tags')
            self.assertEqual(conn.call_args.args,('127.0.0.1',11434))
            conn.return_value.close.assert_called_once()


if __name__=='__main__':
    unittest.main()
