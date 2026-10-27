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

    def task_message(self):
        return dict(use='proof', word='summarize.task', caller=dict(name='Alex'), args=dict(target='tb1'))

    def test_unregistered_model_literal_fallback(self):
        with patch.object(S, 'read', side_effect=[[], [], [dict(id='tb1', rev=4, title='Bring tea; keep warm')]]):
            out = S.call(self.task_message())
        self.assertIn('short="Bring tea"', out['lines'][0])
        self.assertIn('short version, no model', out['lines'][0])

    def test_registered_model_delegates(self):
        prepared = dict(lines=['set tb1 short="Tea" short_source="model"'], saw=dict(tb1=4))
        with patch.object(S, 'read', side_effect=[[], [dict(id='tb2')], [dict(id='tb1',rev=4)], [prepared]]) as read:
            out = S.call(self.task_message())
        self.assertEqual(out['lines'][0], prepared['lines'][0])
        self.assertEqual(read.call_args.args, ('proof', 'model.preview tb1 operation=summarize words=10'))

    def test_model_refusal_is_not_bypassed(self):
        with patch.object(S, 'read', side_effect=[[], [dict(id='tb2')], [dict(id='tb1',rev=4)], ValueError('limit reached')]):
            with self.assertRaisesRegex(ValueError, 'limit reached'):
                S.call(self.task_message())

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
