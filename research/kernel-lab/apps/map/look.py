"""Open the map window in a hidden browser over a scratch world, and take pictures (nothing shows on the screen).

    python look.py [out-folder]    -> map-*.png in research/kernel-lab/apps/map/evidence/ (or the folder given)
The browser is headless Chrome/Edge with a software GPU (SwiftShader), so WebGL draws without a screen.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(HERE), str(LAB)]
from scratch import Scratch  # noqa: E402
import painter.browser as pb  # noqa: E402

GL_FLAGS = ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist']


class MapPage(pb.Page):
    """painter.browser.Page with a software GPU, so the map's WebGL has something to draw with."""
    def __init__(self, url, token, widget, width=1500, height=940):
        real = pb.Browser
        pb.Browser = lambda u, test_flags=(): real(u, test_flags=list(test_flags) + GL_FLAGS)
        try:
            super().__init__(url, token, widget, width, height)
        finally:
            pb.Browser = real


def open_map(s, width=1500, height=940, who='alex'):
    page = MapPage(s.url, s.token(who), s.ids['widget'], width, height)
    page.until('!!document.querySelector(".gm-root")', 40)
    page.until('document.querySelector(".gm-overlay")?.dataset.state==="ready"', 60)
    page.js('new Promise(r=>setTimeout(r,600))')
    return page


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'evidence'
    out.mkdir(parents=True, exist_ok=True)
    s = Scratch()
    try:
        s.say('make kind=spot map=Seabright name="Tide pools" lat=36.9630 lon=-122.0040')
        s.say('map.route name="Flyers: Murray to the beach" stops="Seabright Station > Java Junction > Seabright Beach"')
        t0 = time.time()
        page = open_map(s)
        print('window ready in', round(time.time() - t0, 1), 's')
        print(json.dumps(page.js('({gl:!!document.querySelector(".gm-canvas")?.getContext("webgl2")||!!document.querySelector(".gm-canvas")?.getContext("webgl"),'
                                 'status:document.querySelector(".gm-status")?.innerText,pins:document.querySelectorAll(".gm-pin").length,'
                                 'streets:[...document.querySelectorAll(".gm-street")].filter(e=>e.style.display!=="none").length,'
                                 'places:[...document.querySelectorAll(".gm-place")].filter(e=>e.style.display!=="none").length})')))
        page.shot(str(out / 'map-first.png'))
        errs = [e for e in page.errors if e.get('method') == 'Runtime.exceptionThrown' or e.get('params', {}).get('entry', {}).get('level') == 'error']
        print('errors', json.dumps(errs)[:3000])
        page.close()
    finally:
        s.close()
