"""Widget principals and HTTP broker against real scratch doors."""
import json
import unittest
import urllib.request

from test_kdesk import Desk, quoted
from kernel.inpage import Principal
from kernel.kernel import Refused


class WidgetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=Desk()

    @classmethod
    def tearDownClass(cls):cls.d.close()

    def widget(self,grants='window.surface describe rows look set',only='kind:widget-test'):
        d=self.d
        m=d.say('make kind=widget name=test-widget code="await agora.ready"')['made'][0]
        d.say('look '+m)
        out=d.say(f'widget {m} grants='+quoted(grants)+' only='+only)
        self.assertTrue(out['ok'],out)
        return m

    def viewer(self):
        return self.d.k.actor_for(self.d.k.accounts['desktop:alex'])

    def test_rights_are_intersection_and_every_write_is_authored(self):
        d=self.d;m=self.widget();p=Principal(d.k,m,self.viewer(),'test')
        t=d.say('make kind=widget-test name=counter value=1')['made'][0]
        self.assertTrue(p.run('look '+t,mode='see')['ok'])
        result=p.run('set '+t+' value=2');self.assertTrue(result['ok'],result)
        self.assertEqual(m,d.k.log.records[-1]['by'])
        self.assertEqual(self.viewer().person,d.k.log.records[-1]['for'])
        self.assertFalse(p.run('pin '+t)['ok'])
        self.assertFalse(p.run('set '+m+' code=escape')['ok'])
        self.assertFalse(p.run('set '+t+' value=3',mode='see')['ok'])

    def test_fence_is_per_instance_and_off_undo_never_revives_old_page(self):
        d=self.d;m=self.widget();a=Principal(d.k,m,self.viewer(),'one');b=Principal(d.k,m,self.viewer(),'two')
        t=d.say('make kind=widget-test value=1')['made'][0]
        a.run('look '+t,mode='see')
        self.assertFalse(b.run('set '+t+' value=2')['ok'])
        lease=a.hold('window.surface');self.assertIn(lease,d.k.leases)
        d.say('off '+m);self.assertNotIn(lease,d.k.leases)
        with self.assertRaises(Refused):a.run('look '+t,mode='see')
        d.say('undo')
        with self.assertRaises(Refused):a.run('look '+t,mode='see')
        self.assertTrue(Principal(d.k,m,self.viewer(),'fresh').run('look '+t,mode='see')['ok'])

    def test_revoked_grantor_and_viewer_limits_apply(self):
        d=self.d;m=self.widget('window.surface describe pin')
        person=d.k.join('widget-neighbour','Neighbour',invite={'admitted':True})['person']
        viewer=d.k.actor_for(person)
        p=Principal(d.k,m,viewer,'neighbour')
        target=d.say('post Only leaders may pin')['made'][0]
        self.assertFalse(p.run('pin '+target)['ok'])
        # Revoke the grant itself: an already open instance cannot keep it.
        grant=next(g for g in d.k.things('grant') if d.k.state.get(g,'to')==m and not d.k.state.get(g,'revoked'))
        from kernel.kernel import Tx
        with d.k.lock:
            tx=Tx(d.k);tx.part('test',None,'test revocation');tx.set(grant,'revoked',True);d.k._commit(tx,by='kernel',words='test revocation')
        self.assertFalse(Principal(d.k,m,self.viewer(),'revoked').run('pin '+target)['ok'])

    def test_broker_is_session_bound_cross_origin_refuses_and_filters_hearing(self):
        d=self.d;m=self.widget('window.surface describe rows hear:post')
        def request(action,body,origin=None):
            headers={'Content-Type':'application/json','Authorization':'Bearer '+d.entry.token('alex')}
            headers['X-Agora-Widget-Host']=d.srv.RequestHandlerClass.widget_broker.guard_key
            if origin is not None:headers['Origin']=origin
            with urllib.request.urlopen(urllib.request.Request(d.url+'/desk/widget/'+action,json.dumps(body).encode(),headers)) as r:return json.load(r)
        opened=request('open',{'widget':m});self.assertTrue(opened['ok'],opened)
        instance=opened['instance']
        self.assertFalse(request('call',{'instance':instance,'op':'hear','word':'set'})['ok'])
        self.assertTrue(request('call',{'instance':instance,'op':'hear','word':'post'})['ok'])
        d.say('post A public happening')
        self.assertTrue(request('poll',{'instance':instance})['events'])
        with self.assertRaises(urllib.error.HTTPError) as e:request('call',{'instance':instance,'op':'see','line':'rows any'},'null')
        self.assertEqual(403,e.exception.code)
        self.assertFalse(request('call',{'instance':'invented','op':'see','line':'rows any'})['ok'])
        with self.assertRaises(urllib.error.HTTPError) as absent:
            urllib.request.urlopen(urllib.request.Request(d.url+'/desk/widget/open',json.dumps({'widget':m}).encode(),
                {'Content-Type':'application/json','Authorization':'Bearer '+d.entry.token('alex')}))
        self.assertEqual(403,absent.exception.code)

    def test_kits_copy_code_without_activation_or_grants(self):
        d=self.d
        source=d.say('make kind=widget name=portable code="await agora.ready"')['made'][0]
        kit=d.say('kit '+d.k.place)['made'][0]
        data=d.k.state.get(kit,'bundle')
        definition=next(x for x in data['definitions'] if x['id']==source)
        self.assertEqual({'kind','name','code'},set(definition['facts']))
        self.assertNotIn('on',definition['facts'])
        self.assertNotIn('grants',definition['facts'])
        self.assertEqual('await agora.ready',definition['facts']['code'])

    def test_off_closes_widget_window_and_undo_reopens_it(self):
        d=self.d
        mid=d.say('make kind=widget name=window-widget code="await agora.ready"')['made'][0]
        d.say('look '+mid);d.say(f'widget {mid} grants="window.surface describe"')
        result=d.say('window.open window-widget')
        self.assertTrue(result['ok'],result)
        d.wait(lambda:d.window('window-widget'))
        d.say('off '+mid)
        d.wait(lambda:not d.window('window-widget'))
        d.say('undo')
        d.wait(lambda:d.window('window-widget'))


if __name__=='__main__':unittest.main()
