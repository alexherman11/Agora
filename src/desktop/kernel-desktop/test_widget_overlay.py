"""Exercise the actual offscreen renderer/capture loop with an invisible sink.
Native windows are never created by this check; all facts are scratch facts.
"""
import importlib.util
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from test_kdesk import Desk
import widget_overlay

WIDGETS=Path(__file__).resolve().parents[2]/'agora/widgets'
spec=importlib.util.spec_from_file_location('widget_installer',WIDGETS/'install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)


class OverlayTest(unittest.TestCase):
    def test_real_renderer_produces_alpha_pixels_on_the_desktop_surface(self):
        d=Desk();stop=threading.Event();images=[];errors=[]
        class Invisible:
            def __init__(self,*args,**kwargs):pass
            def start(self):pass
            def hide(self,*args):pass
            def close(self):pass
            def show(self,key,image,x,y):
                if image.getchannel('A').getbbox():
                    images.append((image.copy(),x,y))
                    if len(images)>=3:stop.set()
        try:
            door=installer.taskboard.Door(d.url,d.entry.token('alex'))
            ids=installer.install(door)
            overlay=widget_overlay.Overlay(d.k,d.url,d.entry,ids['desktop-guy'],stop)
            def run():
                try:overlay.run()
                except Exception:
                    import traceback
                    errors.append(traceback.format_exc())
            with patch.object(widget_overlay,'Sprite',Invisible),patch.object(widget_overlay,'reasons',return_value=[]):
                thread=threading.Thread(target=run,daemon=True);thread.start();thread.join(25)
                stop.set();thread.join(4)
            self.assertFalse(errors,str(errors))
            self.assertFalse(thread.is_alive(),'renderer did not stop')
            self.assertTrue(images,'no frame reached the surface')
            image,x,y=images[0]
            self.assertEqual('RGBA',image.mode)
            self.assertTrue(image.getchannel('A').getbbox(),'captured no visible companion')
            self.assertEqual(0,image.getpixel((0,0))[3])
            alpha=image.getchannel('A')
            self.assertLess(sum(alpha.histogram()[1:]),image.width*image.height*.6,'opaque rectangle behind the companion')
            self.assertLess(image.width*image.height,400*400)
            self.assertGreater(y,500)
            print(f'OVERLAY: real Chromium -> {image.width}x{image.height} RGBA -> invisible native sink; visible alpha; desktop y={y}',flush=True)
        finally:
            stop.set();d.close()


if __name__=='__main__':unittest.main()
