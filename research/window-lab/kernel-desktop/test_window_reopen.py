"""Window reopen with native reconciliation deliberately delayed; no real windows."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import kd_window

class WindowReopen(unittest.TestCase):
    def host(self, rows, cached):
        h=kd_window.WindowHost.__new__(kd_window.WindowHost)
        h.owner='alex';h.rows={r['id']:r for r in cached};h.intent={}
        h.m=SimpleNamespace(see=Mock(return_value={'ok':True,'rows':rows}))
        h.screen=SimpleNamespace(wins={r['id']:{} for r in cached},is_front=Mock(return_value=True),focus=Mock(return_value='brought forward'))
        h.box_for=Mock(return_value=(0,0,800,600))
        return h
    def open(self,h,view='lines',kv=None):
        return h._call({'word':'window.open','caller':{'person':'alex'},'use':'caller-session','args':{'words':view,'kv':kv or {}}})
    def test_forgotten_window_is_not_reused_before_native_disposal(self):
        for view,kv in [('lines',{}),('page',{'url':'http://127.0.0.1:8810/desk/help.html'})]:
            with self.subTest(view=view):
                old={'id':'old','shows':view,'name':'Old',**kv}
                h=self.host([], [old]);r=self.open(h,view,kv)
                self.assertIn('lines',r,r)
                h.screen.focus.assert_not_called()
                self.assertEqual(h.rows,{'old':old}) # reconciliation still owns native disposal
    def test_current_window_is_reused_without_duplicate(self):
        row={'id':'current','shows':'lines','name':'Lines'}
        h=self.host([row],[row]);r=self.open(h)
        self.assertIn('open already',r['text']);self.assertNotIn('lines',r)
    def test_current_unpainted_window_is_not_created_twice(self):
        row={'id':'new','shows':'lines','name':'Lines'}
        h=self.host([row],[]);r=self.open(h)
        self.assertNotIn('lines',r,r);h.screen.focus.assert_not_called()
        self.assertIn('opening',r['text'])
    def test_failed_world_read_does_not_open_a_duplicate(self):
        h=self.host([],[]);h.m.see.return_value={'ok':False,'text':'unavailable'}
        self.assertIn('refused',self.open(h))
if __name__=='__main__':unittest.main()
