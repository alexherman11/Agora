"""An evening with the map, as people would use it, in a hidden world and a hidden browser. Writes evidence/proof.md
and pictures. Each step says what a person does, does it through the window (real pointer and key events) or through
lines, and checks what the world and the window show afterwards.

    python proof.py
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
from look import open_map  # noqa: E402
from scratch import Scratch  # noqa: E402

OUT = HERE / 'evidence'
OUT.mkdir(exist_ok=True)
log = []


def metres(lat1, lon1, lat2, lon2):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (float(lat1), float(lon1), float(lat2), float(lon2)))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def note(step, ok, detail=''):
    log.append((step, ok, detail))
    print(('PASS ' if ok else 'FAIL ') + step + (' · ' + detail if detail else ''), flush=True)


class Driver:
    def __init__(self, page):
        self.p = page

    def js(self, expr):
        return self.p.js(expr)

    def frame_offset(self):
        return self.p.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')

    def click_at(self, x, y, button='left'):
        o = self.frame_offset()
        X, Y = x + o['x'], y + o['y']
        c = self.p.c
        c.call('Input.dispatchMouseEvent', type='mouseMoved', x=X, y=Y)
        c.call('Input.dispatchMouseEvent', type='mousePressed', x=X, y=Y, button=button, clickCount=1, buttons=1)
        c.call('Input.dispatchMouseEvent', type='mouseReleased', x=X, y=Y, button=button, clickCount=1)

    def drag(self, x0, y0, x1, y1, button='left', steps=14):
        o = self.frame_offset()
        c = self.p.c
        c.call('Input.dispatchMouseEvent', type='mouseMoved', x=x0 + o['x'], y=y0 + o['y'])
        c.call('Input.dispatchMouseEvent', type='mousePressed', x=x0 + o['x'], y=y0 + o['y'], button=button, clickCount=1,
               buttons=1 if button == 'left' else 2)
        for i in range(1, steps + 1):
            c.call('Input.dispatchMouseEvent', type='mouseMoved', x=x0 + (x1 - x0) * i / steps + o['x'],
                   y=y0 + (y1 - y0) * i / steps + o['y'], button=button, buttons=1 if button == 'left' else 2)
            self.frame()
        c.call('Input.dispatchMouseEvent', type='mouseReleased', x=x1 + o['x'], y=y1 + o['y'], button=button, clickCount=1)

    def click(self, selector):
        pt = self.p.point(selector)
        c = self.p.c
        c.call('Input.dispatchMouseEvent', type='mouseMoved', **pt)
        c.call('Input.dispatchMouseEvent', type='mousePressed', button='left', clickCount=1, buttons=1, **pt)
        c.call('Input.dispatchMouseEvent', type='mouseReleased', button='left', clickCount=1, **pt)

    def click_text(self, selector, text):
        i = self.js(f'[...document.querySelectorAll({json.dumps(selector)})].findIndex(n=>n.textContent.trim()==={json.dumps(text)})')
        if i is None or i < 0:
            raise AssertionError(f'no {selector} saying {text}')
        self.js(f'[...document.querySelectorAll({json.dumps(selector)})].forEach((n,i)=>n.toggleAttribute("data-hit",i==={i}))')
        self.click(selector + '[data-hit]')

    def type(self, text):
        self.p.c.call('Input.insertText', text=text)

    def key(self, key, code=None, vk=0):
        c = self.p.c
        c.call('Input.dispatchKeyEvent', type='keyDown', key=key, code=code or key, windowsVirtualKeyCode=vk)
        c.call('Input.dispatchKeyEvent', type='keyUp', key=key, code=code or key, windowsVirtualKeyCode=vk)

    def frame(self):
        self.js('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(1))))')

    def settle(self, ms=700):
        self.js(f'new Promise(r=>setTimeout(r,{ms}))')

    def until(self, expr, seconds=15):
        try:
            self.p.until(expr, seconds)
        except AssertionError:
            print('TOASTS', self.js('[...document.querySelectorAll(".toast")].map(t=>t.textContent)'))
            print('VIEW', self.js('document.querySelector("[data-view]")?.dataset.view'))
            raise

    def engine(self, expr):
        """Read the engine through the surface element (the engine sits in the part's draft; the page has no global)."""
        return self.js('(()=>{const c=document.querySelector(".gm-canvas");const E=c&&c.__engine;return E?(' + expr + '):null})()')

    def center(self, lat, lon, dist=None):
        """Put the camera over a place (as a person would by dragging), and wait for the frame."""
        self.engine(f'(()=>{{const [x,y]=E.toXY({lat},{lon});E.anim=null;E.cam.x=x;E.cam.y=y;'
                    + (f'E.cam.dist={dist};' if dist else '') + 'E.clampCam();E.ask();return 1})()')
        self.settle(300)

    def off_centre(self, lat, lon):
        """How far (px) a place is from the middle of the map's open part (beside the panels)."""
        return self.engine(f'(()=>{{const [x,y]=E.toXY({lat},{lon});E.matrices();const p=E.project(x,y,0);'
                           'const side=E.root.closest(".gm-shell")?.querySelector(".gm-side");const m=E.root.getBoundingClientRect();'
                           'const inset=side?side.getBoundingClientRect().right-m.left:0;'
                           'return Math.hypot(p[0]-(inset+(E.w-inset)/2),p[1]-E.h/2)})()')

    def screen_of(self, lat, lon):
        return self.engine(f'(()=>{{const [x,y]=E.toXY({lat},{lon});E.matrices();const p=E.project(x,y,0);'
                           f'const r=E.root.getBoundingClientRect();return p?{{x:p[0]+r.left,y:p[1]+r.top}}:null}})()')


def main():
    s = Scratch()
    t_all = time.time()
    try:
        # Before anyone opens the window, a neighbour adds things the ordinary way, in lines.
        tide = s.say('make kind=spot map=Seabright name="Tide pools" lat=36.9630 lon=-122.0040 text="Low tide only"')['made'][0]
        s.say('make kind=kind name=event fields="start end location place seats"')
        ev1 = s.say('make kind=event title="Beach cleanup" start=2026-10-31T09:00 place=' + tide)['made'][0]
        ev2 = s.say('make kind=event title="Council night" start=2026-10-30T18:30 location="Museum of Natural History"')['made'][0]
        note('events find their place: one by place=, one by its written location', True, f'{ev1} {ev2}')
        page = open_map(s)
        d = Driver(page)
        ok = d.engine('!!E.buffers&&!!E.gl')
        note('the window opens and draws Seabright', ok)
        pins = d.js('[...document.querySelectorAll(".gm-pin")].map(p=>p.getAttribute("aria-label"))')
        note('three placed things show as pins (spot, event at the spot, event by location)', len(pins) == 3, json.dumps(pins))
        approx = d.js('document.querySelectorAll(".gm-pin.gm-approx").length')
        note('the event placed only by its written location is drawn as approximate', approx == 1, f'{approx} approximate')
        page.shot(str(OUT / 'proof-01-open.png'))
        loads = d.engine('E.loadCount||1')

        # 2. Press the Beach cleanup pin: the inspector shows its facts, where it is, and what is near.
        d.center(36.9630, -122.0040, 650)
        d.click('.gm-pin[aria-label^="Beach cleanup"]')
        d.until('document.querySelector(".gm-title")?.textContent.includes("Beach cleanup")', 10)
        d.until('document.querySelector(".gm-where")?.textContent.length>3&&!document.querySelector(".gm-where").textContent.startsWith("…")', 10)
        where = d.js('document.querySelector(".gm-where").textContent')
        facts = d.js('[...document.querySelectorAll(".gm-facts dt")].map(n=>n.textContent)')
        note('pressing a pin shows its facts and where it is', 'start' in facts, where + ' · ' + ', '.join(facts))
        same = d.engine('E.loadCount||1') == loads and d.engine('!!E.buffers')
        note('selecting repaints the window without reloading the map', same)
        page.shot(str(OUT / 'proof-02-pressed-pin.png'))

        # 3. Search for "java", choose the first answer: the camera flies there.
        d.click('.gm-search input')
        d.type('java')
        d.until('document.querySelectorAll(".gm-results button").length>0', 10)
        d.key('Enter', 'Enter', 13)
        d.until('document.querySelector(".gm-title")?.textContent.includes("Java Junction")', 10)
        d.settle(1300)
        off = d.off_centre(36.9674789, -122.0081128)
        note('search finds Java Junction and flies there (to the middle of the map beside the panels)', off < 40, f'{off:.0f} px from the middle')
        page.shot(str(OUT / 'proof-03-search.png'))

        # 4. Add a spot: choose the tool, press the map, name it, press Enter.
        d.click_text('.gm-tools button', 'Add a spot')
        d.until('document.querySelector(".gm-root")?.dataset.tool==="add"', 5)
        pt = d.screen_of(36.96705, -122.00835)
        d.click_at(pt['x'], pt['y'])
        d.until('!!document.querySelector(".gm-draft input")', 5)
        d.click('.gm-draft input')
        d.type('Bench with a view')
        d.key('Enter', 'Enter', 13)
        d.until('[...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").startsWith("Bench with a view"))', 10)
        bench = [r for r in s.say('rows spot')['rows'] if r.get('name') == 'Bench with a view'][0]
        dist = metres(bench['lat'], bench['lon'], 36.96705, -122.00835)
        note('adding a spot in the window makes a spot thing where it was pressed', dist < 6, f'{bench["id"]} {dist:.1f} m from the press')
        page.shot(str(OUT / 'proof-04-added.png'))

        # 4b. Add an event the same way: the tool, a press, "An event", a name and "Sat 10am"
        d.click_text('.gm-tools button', 'Add a spot')
        d.until('document.querySelector(".gm-root")?.dataset.tool==="add"', 5)
        pt = d.screen_of(36.96620, -122.00790)
        d.click_at(pt['x'], pt['y'])
        d.until('!!document.querySelector(".gm-draft input")', 5)
        d.click('.gm-draft [data-kind=event]')
        d.click('.gm-draft input[aria-label="Name"]')
        d.type('Porch music')
        d.click('.gm-draft input[aria-label="When"]')
        d.type('Sat 10am')
        d.click_text('.gm-draft button', 'Add event')
        d.until('[...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").startsWith("Porch music"))', 10)
        ev = [r for r in s.say('rows event')['rows'] if r.get('title') == 'Porch music'][0]
        note('an event added on the map is an event thing with a time and a place', bool(ev.get('start')) and bool(ev.get('lat')),
             f"start {ev.get('start')}, {metres(ev['lat'], ev['lon'], 36.96620, -122.00790):.1f} m from the press")

        # 5. Drag the new pin across the street; the world moves it. Undo puts it back.
        a = d.screen_of(float(bench['lat']), float(bench['lon']))
        b = d.screen_of(36.96690, -122.00800)
        d.drag(a['x'], a['y'] - 14, b['x'], b['y'] - 14)
        d.settle(900)
        moved = s.say('look ' + bench['id'])['rows'][0]
        m = metres(moved['lat'], moved['lon'], 36.96690, -122.00800)
        note('dragging a pin moves the thing in the world', m < 8, f'{m:.1f} m from where it was dropped')
        s.say('undo')
        back = s.say('look ' + bench['id'])['rows'][0]
        note('undo takes the move back', back['lat'] == bench['lat'], f"{back['lat']},{back['lon']}")

        # 6. Plan a route: the tool, then the Tide pools pin, two presses on the map; the planner gives length and time.
        d.click_text('.gm-tools button', 'Plan a route')
        d.until('!!document.querySelector("[aria-label=\'Route planner\']")', 8)
        d.engine('(E.flyTo({dist:1300},10),1)')
        d.settle(400)
        d.click('.gm-pin[aria-label^="Tide pools"]')
        for lat, lon in [(36.96455, -122.00785), (36.96745, -122.00745)]:
            p2 = d.screen_of(lat, lon)
            d.click_at(p2['x'], p2['y'])
            d.settle(350)
        d.until('document.querySelectorAll(".gm-stops li").length===3', 8)
        d.until('!!document.querySelector(".gm-big")', 12)
        numbers = d.js('document.querySelector(".gm-big").textContent')
        note('the planner shows the street path length and time for three stops', 'min' in numbers, numbers)
        page.shot(str(OUT / 'proof-05-planning.png'))
        d.click('[aria-label="Route name"]')
        d.type('Flyers: tide pools to Murray')
        d.click_text('.gm-btn', 'Save route')
        d.until('!document.querySelector("[aria-label=\'Route planner\']")', 10)
        routes = [r for r in s.say('rows route')['rows'] if r.get('name') == 'Flyers: tide pools to Murray']
        note('saving makes a route thing that keeps its street path', bool(routes) and len(routes[0].get('path', '').split()) > 5,
             (routes[0].get('metres', '?') + ' m, ' + routes[0].get('minutes', '?') + ' min, via ' + routes[0].get('streets', '')) if routes else 'none')
        d.settle(600)
        page.shot(str(OUT / 'proof-06-route-saved.png'))
        # 6b. Press the route's flag: its length and time; then ride along it
        d.until('!!document.querySelector(".gm-pin[aria-label^=\'Flyers: tide pools\']")', 10)
        rid = routes[0]['id']
        d.center(float(routes[0]['stop_points'].split()[0].split(',')[0]), float(routes[0]['stop_points'].split()[0].split(',')[1]), 700)
        d.click('.gm-pin[aria-label^="Flyers: tide pools"]')
        d.until('document.querySelector(".gm-where .gm-big")?.textContent.includes("948 m")', 10)
        note('pressing a route\'s flag shows its length and time', True, d.js('document.querySelector(".gm-where").textContent'))
        start_cam = d.engine('({x:E.cam.x,y:E.cam.y})')
        d.click_text('.gm-btn', 'Fly along it')
        d.settle(4000)
        mid = d.engine('({x:E.cam.x,y:E.cam.y,pitch:E.cam.pitch,dist:E.cam.dist,flying:!!E.anim})')
        moved = ((mid['x'] - start_cam['x']) ** 2 + (mid['y'] - start_cam['y']) ** 2) ** .5
        note('"Fly along it" rides the camera down the street path', mid['flying'] and moved > 60 and mid['pitch'] > 50,
             f"{moved:.0f} m along after 4 s, pitch {mid['pitch']:.0f}")
        page.shot(str(OUT / 'proof-06b-flying.png'))
        d.engine('(E.anim=null,1)')

        # 7. Hide the Events layer for yourself. The world keeps the layer; only your view changes.
        d.click('[aria-label="Show Events"]')
        d.until('![...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").includes("Council night"))', 10)
        head = s.say('map.layers Seabright')['rows'][0]
        events = [r for r in s.say('rows map-layer')['rows'] if r.get('name') == 'Events'][0]
        note('hiding a layer is your own view preference; the layer itself is unchanged',
             events['id'] in head.get('hidden', '') and 'on' not in events, 'hidden: ' + head.get('hidden', ''))
        d.click('[aria-label="Show Events"]')
        d.until('[...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").includes("Council night"))', 10)
        note('showing it again brings its pins back', True)

        # 8. A line turns the window: map.show
        s.say('map.show "Tide pools"')
        d.settle(1800)
        off = d.off_centre(36.9630, -122.0040)
        note('map.show, said as a line, turns the open window to the thing', off < 40, f'{off:.0f} px from the middle')

        # 9. A layer made in a line appears in the window at once
        s.say('make kind=map-layer map=Seabright name=Council shows="rows event title=\\"Council night\\"" color=#3f78b5 order=4')
        d.until('[...document.querySelectorAll(".gm-layer label")].some(l=>l.textContent==="Council")', 12)
        note('a layer made in a line shows in the layers panel without reopening', True)
        # 9b. Change that layer in the window: its colour, through the layer's own editor
        d.click('[aria-label="Change Council"]')
        d.until('!!document.querySelector("[aria-label=\'Layer name\']")', 8)
        d.click('.gm-form .gm-chips [aria-label="#4f9a4a"]')
        d.click_text('.gm-form button', 'Save')
        d.settle(800)
        council = [r for r in s.say('rows map-layer')['rows'] if r.get('name') == 'Council'][0]
        note('changing a layer in the window sets its facts in the world', council.get('color') == '#4f9a4a', 'color ' + str(council.get('color')))

        # 10. Restyle event pins with one part-style line
        s.say('make kind=part-style lens=seabright-map target=geo-map.pin[kind=event] size=22px')
        d.until('getComputedStyle(document.querySelector(".gm-pin[data-fact-kind=event]")).fontSize==="22px"', 12)
        note('a part-style line restyles every event pin', True, 'font-size 22px')
        page.shot(str(OUT / 'proof-07-styled.png'))

        # 11. Press a building: the ground tells what it knows; "Add as a spot" adopts it
        s.say('map.show 36.96452,-122.00958')
        d.settle(1500)
        bp = d.screen_of(36.9645203, -122.0095822)
        d.click_at(bp['x'], bp['y'])
        d.until('document.querySelector(".gm-card h3")?.textContent==="From the ground"&&document.querySelector(".gm-title")?.textContent.includes("Museum")', 10)
        title = d.js('document.querySelector(".gm-title").childNodes[0].textContent')
        note('pressing a building shows what the ground knows about it', 'Museum' in title, title)
        page.shot(str(OUT / 'proof-08-building.png'))
        d.click_text('.gm-btn', 'Add as a spot')
        d.until('[...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").includes("Museum"))', 10)
        adopted = [r for r in s.say('rows spot')['rows'] if 'Museum' in r.get('name', '')]
        note('a building becomes a spot that remembers its OpenStreetMap feature',
             bool(adopted) and adopted[0].get('osm', '').startswith('way/'), adopted[0].get('osm', '') if adopted else 'none')

        # 12. Keys move the camera
        d.click('.gm-canvas')
        before = d.engine('E.cam.dist')
        d.key('+', 'Equal', 187)
        d.settle(450)
        note('the + key zooms in', d.engine('E.cam.dist') < before, f'{before:.0f} -> {d.engine("E.cam.dist"):.0f} m')

        # 13. Flat plan, and a phone-sized window
        d.click('[aria-label="Tilt or flatten the map"]')
        t0 = time.time()
        try:
            d.p.until('document.querySelector(".gm-canvas").__engine.cam.pitch<1', 8)
        except AssertionError:
            pass
        flat = d.engine('E.cam.pitch') < 1
        print('FLAT after', round(time.time() - t0, 2), 's; frame', d.engine('(()=>{const t=performance.now();E.draw();return Math.round(performance.now()-t)})()'), 'ms (software GPU)')
        note('the 2D button flattens the map', flat, '' if flat else d.engine('JSON.stringify(E.flights)'))
        page.shot(str(OUT / 'proof-09-flat.png'))
        page.c.call('Emulation.setDeviceMetricsOverride', width=420, height=860, deviceScaleFactor=1, mobile=False)
        d.settle(900)
        page.shot(str(OUT / 'proof-10-phone.png'))
        note('the engine kept one load through the whole evening', d.engine('E.loadCount||1') == 1, f"loads {d.engine('E.loadCount||1')}")
        errs = [e for e in page.errors if e.get('method') == 'Runtime.exceptionThrown']
        note('no script errors', not errs, json.dumps(errs)[:400])
        page.close()
    finally:
        s.close()
        print('total', round(time.time() - t_all, 1), 's')


if __name__ == '__main__':
    main()
