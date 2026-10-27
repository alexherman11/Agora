"""Actual wm process + disposable kernel/HTTP door. Headless, never port 8810."""
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
import unittest

HERE=Path(__file__).resolve().parent;LAB=HERE.parents[1]/'kernel-lab'
sys.path[:0]=[str(LAB),str(LAB/'tests')]
from kernel.kernel import Kernel
from kernel.door import serve
from test_skeleton import StandInEntry,post
from install import fragment


class KernelIntegration(unittest.TestCase):
    def test_real_protocol_help_reading_intent_undo_and_owner(self):
        with tempfile.TemporaryDirectory(prefix='wm-kernel-',dir=HERE/'evidence') as directory:
            entry=StandInEntry(secrets.token_hex(16))
            genesis={'tag':'wt','name':'WM proof','steward':{'account':'owner','name':'Owner'},
                'invites_counted_by':'kernel','invites':[{'code':'join','uses':2}],**fragment(headless=True)}
            kernel=Kernel(directory,genesis);srv,host=serve(kernel,entry.url,entry.secret,0,LAB)
            thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
            url=f'http://127.0.0.1:{srv.server_address[1]}';entry.kernel_url=url
            entry.sessions['owner']={'account':'owner','method':'test'}
            try:
                mid=kernel.module_named('wm');self.assertTrue(host.wait_offered(mid),'wm offers missing')
                def say(line,who='owner',ok=True):
                    code,result=post(url+('/see' if line.split()[0] in ('wm.windows','help','rows','status') else '/do'),{'line':line},token=who)
                    self.assertEqual(code,200,result);self.assertEqual(result['ok'],ok,result);return result
                end=time.monotonic()+5
                while time.monotonic()<end:
                    reading=say('wm.windows')
                    if 'shadow' in reading['text']:break
                    time.sleep(.1)
                self.assertEqual(reading['rows'],[])
                self.assertIn('never titles',say('help wm.windows')['text'])
                before=len(kernel.log.records);say('wm.windows');self.assertEqual(len(kernel.log.records),before)
                result=say('wm.mode off');self.assertEqual(len(result['records']),1)
                time.sleep(1.2);self.assertIn('off',say('wm.windows')['text'])
                say('undo '+result['records'][0]);time.sleep(1.2);self.assertIn('shadow',say('wm.windows')['text'])
                result=say('wm.leave-alone Browser');settings=say('rows wm-settings')['rows'][0]
                self.assertIn('Browser',settings['never']);say('undo '+result['records'][0])
                say('wm.mode live',ok=False)
                entry.sign_in('neighbour','Neighbour',invite='join')
                entry.sessions['neighbour']={'account':'neighbour','method':'test'}
                say('wm.windows','neighbour',ok=False)
                print('Module kernel: real process, offers/help, title-free reading, no reading record, fenced mode/exclusion, undo, owner denial passed')
            finally:
                srv.shutdown();srv.server_close();kernel.modules=None;host.stop_all()
                entry.srv.shutdown();entry.srv.server_close()


if __name__=='__main__':unittest.main()
