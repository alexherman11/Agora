"""Original-art invariance, scoped authority, real module live uptake and undo."""
import sys
import time
import threading
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from test_kdesk import Desk
from kernel.inpage import Principal
from kd_guy import art, Guy
import guy_looks as looks

WIDGETS=Path(__file__).resolve().parents[2]/'agora/widgets'
sys.path.insert(0,str(WIDGETS))
import pixel_guy_install as studio


class ArtTest(unittest.TestCase):
    def test_default_pixels_are_original_for_every_pose_direction_and_blink(self):
        for pose in art.BODY:
            for facing in (-1,1):
                for blink in (False,True):
                    original=Image.new('RGBA',(300,230));d=ImageDraw.Draw(original)
                    for y,row in enumerate(art.HEAD+art.BODY[pose]):
                        for x,c in enumerate(row):
                            if c=='.':continue
                            col=art.PAL['o'] if blink and y==4 and c=='k' and 4<x<12 else art.PAL[c]
                            xx=15-x if facing<0 else x
                            d.rectangle((110+xx*5,150+y*5,114+xx*5,154+y*5),fill=col+(255,))
                    self.assertEqual(original.tobytes(),art.picture(pose,facing,'',blink).tobytes(),(pose,facing,blink))

    def test_layers_bounded_and_every_pose_renders(self):
        for name,layer in {**looks.HATS,**looks.ACCESSORIES}.items():
            self.assertEqual(8,len(layer),name)
            self.assertTrue(all(len(row)==16 and set(row)<=set('.kobrs') for row in layer),name)
        for hat in looks.HATS:
            for pose in art.BODY:
                for accessory in looks.ACCESSORIES:
                    im=art.picture(pose,1,'',False,dict(hat=hat,accessory=accessory))
                    self.assertIsNotNone(im.getbbox())

    def test_malformed_facts_fall_back_and_custom_rows_are_palette_only(self):
        f=looks.clean(dict(speed='oops',skin='url(x)',hat='missing',eyes='missing'))
        self.assertEqual('95',f['speed']);self.assertEqual('#f2c894',f['skin']);self.assertEqual('none',f['hat'])
        self.assertEqual(art.picture('stand',1,'',False,dict(hat='custom',custom_hat='x')).tobytes(),art.picture('stand',1,'',False).tobytes())


class WorldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=Desk();cls.door=studio.taskboard.Door(cls.d.url,cls.d.entry.token('alex'))
        cls.ids=studio.install(cls.door)

    @classmethod
    def tearDownClass(cls):cls.d.close()

    def test_scope_blocks_other_things_fields_mixed_writes_and_foreign_undo(self):
        d=self.d;ids=self.ids;p=Principal(d.k,ids['widget'],d.k.actor_for(d.k.accounts['desktop:alex']),'scope-proof')
        other=self.door.say('make kind=pixel-guy name=Neighbour hat=none')['made'][0]
        for target in (ids['guy'],other,ids['provider'],ids['widget']):p.run('look '+target,mode='see')
        for line in ('set '+other+' hat=wizard','set '+ids['guy']+' provider=escape',
                     'set '+ids['guy']+' hat=wizard provider=escape','set '+ids['provider']+' run=escape',
                     'set '+ids['widget']+' code=escape','make kind=pixel-guy name=Fake','guy.hop',
                     'off guy','grant '+ids['widget']+' words=set'):
            self.assertFalse(p.run(line)['ok'],line)
        out=p.run('set '+ids['guy']+' hat=wizard');self.assertTrue(out['ok'],out)
        self.assertTrue(p.run('undo '+out['records'][0])['ok'])
        foreign=self.door.say('set '+other+' hat=cap')
        self.assertFalse(p.run('undo '+foreign['records'][0])['ok'])

    def test_real_module_picks_up_set_and_undo_under_one_second_without_restart(self):
        d=self.d;g=self.ids['guy'];provider=self.ids['provider']
        d.wait(lambda:"'hat': 'none'" in d.say('status guy')['text'])
        d.say('look '+g)
        started=time.monotonic();out=d.say('set '+g+' hat=cap')
        d.wait(lambda:"'hat': 'cap'" in d.say('status guy')['text'],1)
        elapsed=time.monotonic()-started
        self.assertLess(elapsed,1)
        d.say('undo '+out['records'][0])
        d.wait(lambda:"'hat': 'none'" in d.say('status guy')['text'],1)
        self.assertEqual(provider,self.ids['provider'])
        print(f'LIVE FACT UPTAKE: {elapsed:.3f}s; cap then undo; same module instance',flush=True)

    def test_install_is_idempotent_and_does_not_activate_rejected_widgets(self):
        before=len(self.d.k.log.records)
        self.assertEqual(self.ids,studio.install(self.door))
        self.assertEqual(before,len(self.d.k.log.records))
        self.assertFalse(self.door.rows('widget',name='desktop-guy'))
        self.assertFalse(self.door.rows('widget',name='guy-editor'))

    def test_real_sprite_drive_receives_changed_pixels_and_undo_in_invisible_sink(self):
        d=self.d;g=Guy();frames=[]
        class Invisible:
            def __init__(self):self.cache={}
            def hide(self,hidden):pass
            def show(self,key,image,x,y):
                # The native Sprite caches its bitmap by key. A new PIL image
                # under an old key would leave the live guy unchanged.
                frames.append(self.cache.setdefault(key,image.tobytes()))
        g.sprite=Invisible();g.m.hello={'id':self.ids['provider']}
        g.m.see=lambda line:self.door.say(line)
        g.fullscreen_app=lambda:False
        g.look_around=lambda:None
        g.pose=lambda:('stand',1,'',False)
        g.refresh_looks()
        drive=threading.Thread(target=g.drive,daemon=True)
        watcher=threading.Thread(target=g.watch_looks,daemon=True)
        drive.start();watcher.start()
        try:
            original=art.picture('stand',1,'',False).tobytes()
            cap=art.picture('stand',1,'',False,{'hat':'cap'}).tobytes()
            d.wait(lambda:original in frames)
            self.door.say('look '+self.ids['guy'])
            out=self.door.say('set '+self.ids['guy']+' hat=cap');started=time.monotonic()
            d.wait(lambda:cap in frames,1)
            self.assertLess(time.monotonic()-started,1)
            frames.clear();self.door.say('undo '+out['records'][0])
            d.wait(lambda:original in frames,1)
            print('SPRITE SINK: original -> cap -> original; production drive, real world, never-shown sink',flush=True)
        finally:
            g.m.closed.set();drive.join(2);watcher.join(2)


if __name__=='__main__':unittest.main()
