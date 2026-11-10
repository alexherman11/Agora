"""JEFF regression: disposable kernel and hidden browser; no live messages."""
import unittest
from urllib.parse import quote
import test_shell_components as fixture
import jeff_chat

class JeffLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ShellComponents.setUpClass.__func__(cls)
        cls.d.say('make kind=shell-settings name=Shell-settings')
        jeff_chat.install(cls.d.entry.token('claude'), cls.d.srv.server_address[1])
    @classmethod
    def tearDownClass(cls):
        fixture.ShellComponents.tearDownClass.__func__(cls)
    def test_open_dismiss_reopen_and_preserve_conversation(self):
        d,p=self.d,self.top
        before={kind:d.say('rows '+kind)['rows'] for kind in ('conversation-draft','chat','said')}
        p.js('''(()=>{const act=ShellKit.Data.act.bind(ShellKit.Data);
        globalThis.jeffCalls=[];globalThis.jeffReplies=[];
        ShellKit.Data.act=async line=>{jeffCalls.push(line);const r=await act(line);jeffReplies.push(r);return r;};ShellKit.poke('settings');})()''')
        p.until("(async()=> (await ShellKit.Data.settings()).jeff_open==='window.open jeff-chat')()")
        p.js("document.querySelector('.btn.jeff').click(); document.querySelector('.btn.jeff').click()")
        self.assertEqual(p.js('jeffCalls'),[])
        def launch(n):
            p.js("document.querySelector('.btn.jeff').click()")
            p.until("!!document.querySelector('[data-pop=jeff] .link')")
            p.js("document.querySelector('[data-pop=jeff] .link').click()")
            p.until('jeffReplies.length==='+str(n))
            self.assertTrue(p.js('jeffReplies.at(-1).ok'),p.js('jeffReplies'))
            self.assertEqual(p.js('jeffCalls.at(-1)'),'window.open jeff-chat')
        launch(1)
        row=d.wait(lambda:d.window('jeff-chat'))
        launch(2)
        self.assertEqual(d.window('jeff-chat')['id'],row['id'])
        self.assertIn('tucked away',d.say('window.focus '+row['id'])['text'])
        # Native minimisation transfers foreground; the headless adapter keeps it.
        d.say('window.open help')
        d.wait(lambda:d.window('help'))
        launch(3)
        self.assertIn('brought forward',p.js('jeffReplies.at(-1).text'))
        self.assertTrue(d.say('window.close '+row['id'])['ok'])
        d.wait(lambda:not d.window('jeff-chat'))
        launch(4)
        print('reopen receipts:',p.js('jeffReplies'),flush=True)
        d.wait(lambda:d.window('jeff-chat'))
        for kind,rows in before.items():self.assertEqual(d.say('rows '+kind)['rows'],rows)
        with fixture.Browser(None) as c:
            c.call('Page.navigate',url=d.url+'/dev/signin?token='+d.entry.token('alex')+'&next='+quote('/lens.html?lens=jeff-chat',safe=''))
            c.until("document.body.innerText.includes('JEFF lives on your desktop now.')",20)
            self.assertTrue(c.js("!!document.querySelector('[contenteditable],textarea,input')"))
        print('JEFF: dispatch accepted; dismiss/reopen; window reuse; close/reopen preserves chat, draft and history; lens renders hidden.')
if __name__=='__main__':unittest.main()





