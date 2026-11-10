"""Lines dock regression: real components, headless Edge and a disposable kernel.

Models the observed live state: JEFF chat exists while Lines is closed, and WM
keys differ from Agora ids. No live desktop or foreground windows are touched.
"""
import json
import unittest
import test_shell_components as fixture


class DockLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ShellComponents.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.ShellComponents.tearDownClass.__func__(cls)

    def test_custom_map_pin_and_chat_use_their_own_windows(self):
        d, p = self.d, self.dock
        for name in ('seabright-map', 'jeff-chat'):
            d.say('make kind=lens name=' + name + ' text=' + fixture.Q('root : text "scratch"'))
        d.say('window.open jeff-chat')
        chat_id = d.wait(lambda: d.window('jeff-chat'))['id']
        pin = d.say('make kind=button bar=taskbar label="Seabright map" does="window.open seabright-map"')['made'][0]
        p.js('''(() => {
          const D=ShellKit.Data;
          globalThis.mapOriginal = {see:D.see, act:D.act};
          globalThis.mapCalls=[]; globalThis.mapReplies=[]; globalThis.mapOpen=false;
          globalThis.mapId=null; const chatId=CHAT_ID;
          D.see = async line => {
            if (line==='wm.windows') return {ok:true,rows:[
              {key:'106164:134376107497969028:12327888',agora:chatId,state:'minimised'},
              ...(mapOpen ? [{key:'106164:134376107497969028:60167110',agora:mapId,state:'minimised'}] : [])]};
            if (line==='window.list') return {ok:true,rows:[
              {id:chatId,kind:'window',name:'Jeff-chat',shows:'jeff-chat'},
              {id:mapId,kind:'window',name:'Seabright map',shows:'seabright-map'}]};
            return mapOriginal.see.call(D,line);
          };
          D.act=async line => {
            mapCalls.push(line);
            const r=await mapOriginal.act.call(D,line); mapReplies.push(r); return r;
          };
          ShellKit.poke('pins'); ShellKit.poke('windows');
        })()'''.replace('CHAT_ID', json.dumps(chat_id)))
        selector = '[data-id="pin:' + pin + '"]'
        try:
            p.until('document.querySelector(' + json.dumps(selector) + ')?.getAttribute("aria-label") === "Seabright map, not running"', 15)
            p.js('document.querySelector(' + json.dumps(selector) + ').click()')
            p.until('mapReplies.length===1', 10)
            self.assertEqual(p.js('mapCalls[0]'), 'window.open seabright-map')
            map_id = d.wait(lambda: d.window('seabright-map'))['id']
            p.js('mapId=' + json.dumps(map_id) + '; mapOpen=true; ShellKit.poke("windows")')
            p.until('document.querySelector(' + json.dumps(selector) + ')?.getAttribute("aria-label").includes("1 window")', 15)
            p.js('document.querySelector(' + json.dumps(selector) + ').click()')
            p.until('mapReplies.length===2', 10)
            self.assertEqual(p.js('mapCalls[1]'), 'window.focus ' + map_id)
            p.js('document.querySelector(\'[data-id="agora:106164:134376107497969028:12327888"]\').click()')
            p.until('mapReplies.length===3', 10)
            self.assertEqual(p.js('mapCalls[2]'), 'window.focus ' + chat_id)
            p.js('''(async()=>{
              const D=ShellKit.Data, w=(await D.windows()).find(w=>w.shows==='seabright-map');
              await D.close(w); mapOpen=false; ShellKit.poke('windows');
            })()''')
            p.until('document.querySelector(' + json.dumps(selector) + ')?.getAttribute("aria-label") === "Seabright map, not running"', 15)
            d.wait(lambda: not d.window('seabright-map'))
            p.until('mapReplies.length===4', 10)
            self.assertEqual(p.js('mapCalls'), ['window.open seabright-map', 'window.focus '+map_id,
                                               'window.focus '+chat_id, 'window.close '+map_id])
            self.assertTrue(p.js('mapReplies.every(r=>r.ok)'), p.js('mapReplies'))
            print('Map/chat: custom map pin opens map; separate real dock items focus correct Agora ids; map closes correctly.')
        finally:
            p.js('ShellKit.Data.see=mapOriginal.see; ShellKit.Data.act=mapOriginal.act; ShellKit.poke("windows")')

    def test_lines_does_not_alias_chat_and_actions_use_agora_ids(self):
        d, p = self.d, self.dock
        d.say('window.open lines')
        row = d.wait(lambda: d.window('lines'))
        wid = row['id']
        p.js('''(() => {
          const D = ShellKit.Data;
          globalThis.dockCalls = []; globalThis.dockReplies = [];
          globalThis.includeLines = false;
          const see = D.see.bind(D), act = D.act.bind(D);
          const wid = WID;
          D.see = async line => {
            if (line === 'wm.windows') return {ok:true, rows:[
              {key:'106164:134376107497969028:12327888', agora:'chat-test', state:'minimised'},
              ...(includeLines ? [{key:'106164:134376107497969028:7654321', agora:wid, state:'minimised'}] : [])]};
            if (line === 'window.list') return {ok:true, rows:[
              {id:'chat-test', kind:'window', name:'Jeff-chat', shows:'jeff-chat'},
              {id:wid, kind:'window', name:'Lines', shows:'lines'}]};
            return see(line);
          };
          D.act = async line => {
            dockCalls.push(line);
            const r = line.startsWith('window.open ') || line.startsWith('window.focus ') || line.startsWith('window.close ')
              ? await act(line) : {ok:true};
            dockReplies.push(r); return r;
          };
          ShellKit.poke('windows');
        })()'''.replace('WID', json.dumps(wid)))
        p.until(r'document.querySelector("[data-id=\"app:lines\"]")?.getAttribute("aria-label") === "Lines, not running"', 15)
        p.js(r'document.querySelector("[data-id=\"app:lines\"]").click()')
        p.until('dockReplies.length > 0', 10)
        self.assertEqual(p.js('dockCalls[0]'), 'window.open lines')
        self.assertTrue(p.js('dockReplies[0].ok'), p.js('dockReplies[0]'))
        p.js('includeLines = true; ShellKit.poke("windows")')
        p.until(r'document.querySelector("[data-id=\"app:lines\"]")?.getAttribute("aria-label").includes("1 window")', 15)
        p.js(r'document.querySelector("[data-id=\"app:lines\"]").click()')
        p.until('dockReplies.length > 1', 10)
        self.assertEqual(p.js('dockCalls[1]'), 'window.focus ' + wid)
        self.assertTrue(p.js('dockReplies[1].ok'), p.js('dockReplies[1]'))
        p.js('''(async () => {
          const D=ShellKit.Data, w=(await D.windows()).find(w=>w.shows==='lines');
          await D.minimise(w); await D.close(w);
          await D.focus({key:'55:66:77',state:'minimised'});
          await D.close({key:'55:66:77'});
        })()''')
        p.until('dockCalls.length >= 6', 10)
        self.assertEqual(p.js('dockCalls.slice(2)'), ['window.focus '+wid, 'window.close '+wid, 'wm.restore 55:66:77', 'wm.close 55:66:77'])
        self.assertTrue(p.js('dockReplies.slice(0,4).every(r=>r.ok)'), p.js('dockReplies'))
        print('Dock: chat stays separate; Lines opens; native WM keys preserved; Agora focus/minimise/close accepted; external WM routing preserved.')


if __name__ == '__main__':
    unittest.main()
