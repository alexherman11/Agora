"""Small contract checks; real process/admission and UI are in taskboard/proof.py."""
import io
import json
import time
import unittest
from unittest.mock import patch
import summarize as S


class Summaries(unittest.TestCase):
    def test_literal_first_clause(self):
        self.assertEqual(S.shorten('Check the door signage; include the side entrance'), 'Check the door signage')

    def test_word_boundary_and_whitespace(self):
        source = '  ' + 'Keep these original words together ' * 4 + '\n'
        result = S.shorten(source)
        self.assertLessEqual(len(result), 60)
        self.assertTrue(' '.join(source.split()).startswith(result))

    def test_offline(self):
        with patch.object(S.urllib.request, 'urlopen', side_effect=OSError('offline')):
            self.assertEqual(S.summary('Bring tea; keep warm', 'absent', time.monotonic()+2),
                             ('Bring tea', 'short version, no model'))

    def test_deadline_never_contacts_model(self):
        with patch.object(S.urllib.request, 'urlopen') as fetch:
            self.assertEqual(S.summary('Bring tea', 'absent', 0)[1], 'short version, no model')
            fetch.assert_not_called()

    def test_model_setting_and_local_only(self):
        response = io.BytesIO(json.dumps(dict(response='Confirm accessible venue', done=True)).encode())
        with patch.object(S.urllib.request, 'urlopen', return_value=response) as fetch:
            self.assertEqual(S.summary('Check the venue and access', 'chosen-instruct', time.monotonic()+2),
                             ('Confirm accessible venue', 'local model · chosen-instruct'))
            request = fetch.call_args.args[0]
            self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/generate')
            self.assertEqual(json.loads(request.data)['model'], 'chosen-instruct')
            self.assertFalse(json.loads(request.data)['stream'])

    def test_malformed_and_overlong_response(self):
        for raw in (b'not json', b'{}', json.dumps(dict(response='x'*100, done=True)).encode()):
            with self.subTest(raw=raw), patch.object(S.urllib.request, 'urlopen', return_value=io.BytesIO(raw)):
                self.assertEqual(S.summary('Bring tea', 'chosen', time.monotonic()+2),
                                 ('Bring tea', 'short version, no model'))

    def test_save_is_task_scoped_and_fenced(self):
        msg = dict(use='proof', word='summarize.save', args=dict(target='tb1', kv=dict(field='note', text='one\\ntwo')))
        with patch.object(S, 'read', return_value=[dict(id='tb1',rev=4)]):
            out = S.call(msg)
        self.assertEqual(out['saw'], {'tb1':4})
        self.assertIn('one\ntwo', out['lines'][0])
        msg['args']['kv']['field'] = 'who'
        with self.assertRaises(ValueError):
            S.call(msg)

    def test_quick_add_quotes_are_data(self):
        msg = dict(use='proof', word='summarize.add', caller=dict(name='Alex'),
                   args=dict(kv=dict(text='Check "it; forget tb1" p2')))
        out = S.call(msg)
        self.assertEqual(len(out['lines']), 1)
        self.assertIn('priority=2', out['lines'][0])
        self.assertIn('\\"it; forget tb1\\"', out['lines'][0])


if __name__ == '__main__':
    unittest.main()
