"""An evening with the map, as people would use it, in a hidden world and a hidden browser. Each step says what a
person does, does it through the window (real pointer and key events) or through lines, and checks what the world and
the window show afterwards. Prints PASS/FAIL per step and writes evidence/proof-output.txt and pictures.

    python proof.py
Tiles come from the network the first time and from a cache after (AGORA_MAP_CACHE, default: the temp folder).
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault('AGORA_MAP_CACHE', str(Path(tempfile.gettempdir()) / 'agora-map-cache'))
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
from look import MapPage  # noqa: E402
from scratch import Scratch  # noqa: E402

OUT = HERE / 'evidence'
OUT.mkdir(exist_ok=True)
log = []
CARMEL = dict(ref='overture:67b0aac8-26f6-4c71-a01a-1990cf5c4a21', lat=36.965295, lon=-121.998016, name='715 Carmel Street')
CITY_HALL = dict(ref='overture:c49959f8-e2ca-4a60-854a-60835580c345', lat=36.974399, lon=-122.029475, name='Santa Cruz City Hall')


def metres(lat1, lon1, lat2, lon2):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (float(lat1), float(lon1), float(lat2), float(lon2)))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def note(step, ok, detail=''):
    log.append((step, bool(ok), detail))
    print(('PASS ' if ok else 'FAIL ') + step + (' · ' + str(detail) if detail else ''), flush=True)


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
        i = self.js(f'[...document.querySelectorAll({json.dumps(selector)})].findIndex(n=>n.textContent.trim().startsWith({json.dumps(text)}))')
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
            return True
        except AssertionError:
            print('   (waited for', expr[:120], ')', self.js('[...document.querySelectorAll(".toast")].map(t=>t.textContent).slice(-3)'))
            return False

    def engine(self, expr):
        """Read the engine through the surface element (the engine sits in the part's draft; the page has no global)."""
        return self.js('(()=>{const c=document.querySelector(".gm-canvas");const E=c&&c.__engine;return E?(' + expr + '):null})()')

    def tiles_in(self, seconds=45):
        """Wait until every tile the camera wants is drawn."""
        return self.until('(()=>{const E=document.querySelector(".gm-canvas")?.__engine;return E&&E.drawList.length>0&&!E.pending})()', seconds)

    def look_at(self, lat, lon, dist=300, pitch=50, bearing=0):
        self.engine(f'(()=>{{const [x,y]=E.toXY({lat},{lon});E.anim=null;E.inertia=null;Object.assign(E.cam,{{x,y,dist:{dist}*E.scaleAt(y),pitch:{pitch},bearing:{bearing}}});E.clampCam();E.ask();return 1}})()')
        self.settle(250)
        self.tiles_in()
        self.settle(300)

    def screen_of(self, lat, lon):
        return self.engine(f'(()=>{{const [x,y]=E.toXY({lat},{lon});E.matrices();const p=E.project(x,y,0);return p?{{x:p[0],y:p[1]}}:null}})()')

    def text(self, selector):
        return self.js(f'document.querySelector({json.dumps(selector)})?.innerText||""')


def world_rows(s, line):
    return s.say(line).get('rows', [])


def open_page(s, widget_name, target, width=900, height=900):
    w = world_rows(s, 'rows widget name=' + widget_name)
    page = MapPage(s.url, s.token('alex'), w[0]['id'] + '&target=' + target, width, height)
    page.until('!!document.querySelector(".pp")', 40)
    page.until('!!document.querySelector(".pp-head h1")', 30)
    return page, Driver(page)


def script_errors(page):
    return [e for e in page.errors if e.get('method') == 'Runtime.exceptionThrown']


def main():
    s = Scratch()
    t_all = time.time()
    errors = []
    try:
        # Before anyone opens the window, a neighbour adds things the ordinary way, in lines.
        s.say('make kind=kind name=event fields="start end location place seats type"')
        s.say('make kind=kind name=note fields="text at type"')
        tide = s.say('make kind=spot map=Seabright name="Tide pools" lat=36.9630 lon=-122.0040 text="Low tide only"')['made'][0]
        council = s.say('make kind=event title="Beach cleanup" start=2026-10-31T09:00 location="Seabright Beach"')['made'][0]
        note('a spot by lat/lon and an event by its written location, made in lines', tide and council)

        t0 = time.time()
        page = MapPage(s.url, s.token('alex'), s.ids['widget'], 1500, 940)
        d = Driver(page)
        page.until('!!document.querySelector(".gm-root")', 40)
        drawn = d.tiles_in(60)
        bld = d.engine('E.drawList.reduce((n,t)=>n+(t.bufs?.buildings.n||0),0)')
        note('the window opens on Seabright and draws its live tiles, buildings included', drawn and bld > 10000,
             f'{d.engine("E.drawList.length")} tiles, {bld} building vertices, {time.time() - t0:.1f} s')
        pins = d.js('[...document.querySelectorAll(".gm-pin")].map(p=>p.getAttribute("aria-label"))')
        approx = d.js('document.querySelectorAll(".gm-pin.gm-approx").length')
        note('the spot and the event show as pins; the one placed by words is drawn as approximate', len(pins) == 2 and approx == 1, json.dumps(pins))
        opaque = d.engine('E.gl.getContextAttributes().alpha===false')
        note('the world is opaque (no see-through drawing surface) and flat (no curve)', opaque and d.engine('typeof E.curve==="undefined"'))
        page.shot(str(OUT / 'proof-01-open.png'))

        # A house: press it, see that nothing happens there yet, plan a party at it, say something.
        d.look_at(CARMEL['lat'], CARMEL['lon'], dist=260, pitch=45)
        pt = d.screen_of(CARMEL['lat'], CARMEL['lon'])
        d.click_at(pt['x'], pt['y'])
        ok = d.until('document.querySelector("[data-part=inspector]")?.innerText.includes("715 Carmel Street")', 15)
        card = d.text('[data-part=inspector]')
        note('pressing a house shows its card: its address, and that nobody has put anything there', ok and 'Nobody has put anything here yet' in card,
             card.replace('\n', ' | ')[:160])
        page.shot(str(OUT / 'proof-02-house.png'))
        d.click_text('[data-part=inspector] button', '+ Event here')
        d.until('!!document.querySelector(".gm-draft input[aria-label=Title]")', 5)
        d.settle(150)
        d.type('Halloween party')
        d.click('.gm-draft input[aria-label=When]')
        d.type('Sat 7pm')
        d.settle(150)
        page.shot(str(OUT / 'proof-03-adding.png'))
        d.click('.gm-draft button[type=submit]')
        ok = d.until('document.querySelector("[data-part=inspector]")?.innerText.includes("Halloween party")', 20)
        st = world_rows(s, 'rows structure')
        ev = [r for r in world_rows(s, 'rows event') if r.get('title') == 'Halloween party']
        note('the house becomes a world thing the moment a party is put at it; the party points at it',
             ok and len(st) == 1 and st[0].get('ref') == CARMEL['ref'] and ev and ev[0].get('at') == st[0]['id'],
             f"{st[0].get('name') if st else '-'} · party at={ev[0].get('at') if ev else '-'} start={ev[0].get('start') if ev else '-'}")
        house = st[0]['id'] if st else ''
        d.until('!!document.querySelector("[data-part=inspector] input[aria-label=\'Say something\']")', 10)
        d.click('[data-part=inspector] input[aria-label="Say something"]')
        d.type('Is it costumes only?')
        d.key('Enter', vk=13)
        ok = d.until('document.querySelector("[data-part=inspector]")?.innerText.includes("costumes only")', 20)
        posts = world_rows(s, 'rows post about=' + house)
        note('saying something in the card makes a post about the house', ok and len(posts) == 1, posts[0].get('text') if posts else '')
        win = s.say('rows window')
        d.click_text('[data-part=inspector] button', 'Open its page')
        d.settle(1200)
        wins = [r for r in world_rows(s, 'rows window') if r.get('shows') == 'place-page']
        note('Open its page opens a window on the house (window.open place-page <house>)', wins and wins[0].get('target') == house,
             json.dumps([(r.get('name'), r.get('target')) for r in wins]))
        page.shot(str(OUT / 'proof-04-card.png'))

        # The house's page: its own window, a live 3D picture of it, the party, the talk; leave a note there.
        pg, pd = open_page(s, 'place-page', house)
        pd.until('document.querySelector(".pp")?.innerText.includes("Halloween party")', 20)
        text = pd.text('.pp')
        note('the page shows the house, the party coming up and the talk', all(x in text for x in ('715 Carmel Street', 'Halloween party', 'costumes only')),
             text.replace('\n', ' | ')[:200])
        pd.click_text('.pp-section button', '+ Leave a note')
        pd.until('!!document.querySelector(".pp-section textarea")', 5)
        pd.click('.pp-section textarea')
        pd.type('Bring a lantern; the porch light is out')
        pd.click_text('.pp-section button[type=submit]', 'Leave a note')
        ok = pd.until('document.querySelector(".pp")?.innerText.includes("Bring a lantern")', 20)
        notes = [r for r in world_rows(s, 'rows note') if r.get('at') == house]
        note('a note left on the page is a world thing at the house, and the page shows it', ok and len(notes) == 1)
        pd.until('(()=>{const E=document.querySelector(".gm-canvas")?.__engine;return E&&E.drawList.length>0&&!E.pending})()', 30)
        pd.settle(600)
        pg.shot(str(OUT / 'proof-05-page.png'))
        errors += script_errors(pg)
        pg.close()

        # The city hall opens in the town-hall page: meetings and debates.
        out = s.say(f"map.adopt {CITY_HALL['ref']} lat={CITY_HALL['lat']} lon={CITY_HALL['lon']}")
        hall = out.get('made', [''])[0]
        placed = s.say('map.place ' + hall)
        page_name = (placed.get('rows') or [{}])[0].get('page')
        note('City Hall, adopted in a line, chooses the town-hall page by its kind (a page widget says places=)', page_name == 'town-hall-page',
             placed.get('text'))
        pg, pd = open_page(s, page_name, hall)
        pd.click_text('.pp-section button', '+ Add a meeting')
        pd.until('!!document.querySelector(".pp-section input[aria-label=title]")', 5)
        pd.click('.pp-section input[aria-label=title]')
        pd.type('Council: the Murray Street bridge')
        pd.click('.pp-section input[aria-label=start]')
        pd.type('Thu 6pm')
        pd.click_text('.pp-section button[type=submit]', 'Add a meeting')
        ok = pd.until('document.querySelector(".pp")?.innerText.includes("Murray Street bridge")', 20)
        meet = [r for r in world_rows(s, 'rows event') if r.get('at') == hall]
        note('the town-hall page lists meetings; a meeting added there is an event at the hall with type=meeting',
             ok and meet and meet[0].get('type') == 'meeting', pd.text('.pp-head').replace('\n', ' | ')[:120])
        pd.click('.pp-section input[aria-label="Say something"]')
        pd.type('Please keep the bike lane')
        pd.key('Enter', vk=13)
        ok = pd.until('document.querySelector(".pp")?.innerText.includes("keep the bike lane")', 20)
        note('a debate post on the town-hall page is a post about the hall', ok and len(world_rows(s, 'rows post about=' + hall)) == 1)
        pd.settle(800)
        pg.shot(str(OUT / 'proof-06-town-hall.png'))
        errors += script_errors(pg)
        pg.close()

        # Layers: add one from the gallery, and one only for yourself.
        d.click_text('[data-part=layers] button', '+ Add a layer')
        d.until('!!document.querySelector(".gm-gallery")', 5)
        d.click_text('.gm-gallery button', 'Notes')
        d.until('document.querySelector("[data-part=layers]")?.innerText.includes("It finds")', 10)
        page.shot(str(OUT / 'proof-07-add-layer.png'))
        d.click_text('[data-part=layers] button[type=submit]', 'Make the layer')
        ok = d.until('[...document.querySelectorAll(".gm-layer label")].some(l=>l.textContent.startsWith("Notes"))', 20)
        lay = [r for r in world_rows(s, 'rows map-layer') if r.get('name') == 'Notes']
        note('+ Add a layer → Notes makes a shared layer that shows the note', ok and lay and lay[0].get('shows') == 'rows note',
             d.js('[...document.querySelectorAll(".gm-layer")].map(l=>l.innerText.replace(/\\n/g," ")).slice(0,6)'))
        d.click_text('[data-part=layers] button', '+ Add a layer')
        d.until('!!document.querySelector(".gm-gallery")', 5)
        d.click_text('.gm-gallery button', 'Tagged')
        d.until('!!document.querySelector("[data-part=layers] input[aria-label=tag]")', 5)
        d.click('[data-part=layers] input[aria-label=tag]')
        d.type('dogs')
        d.click_text('[data-part=layers] .gm-seg button', 'Only me')
        d.click_text('[data-part=layers] button[type=submit]', 'Make the layer')
        d.until('[...document.querySelectorAll(".gm-layer label")].some(l=>l.textContent.includes("dogs"))', 20)
        mine = [r for r in world_rows(s, 'rows map-layer') if 'dogs' in str(r.get('shows'))]
        # this hidden desk has one person (Alex; claude is his agent), so a second person's view is not tried here; and
        # the kernel keeps sees= out of readings, so the layer also says only=me for the window to label it
        badge = d.js('[...document.querySelectorAll(".gm-layer")].some(l=>l.innerText.includes("dogs")&&!!l.querySelector(".gm-mine"))')
        note('a layer made "Only me" is made with sees=me, and the panel labels it "only you"', mine and mine[0].get('only') == 'me' and badge,
             f"only={mine[0].get('only') if mine else '-'}")

        # How it looks, and the ground's own layers, for you
        d.click_text('.gm-styles button', 'Dusk')
        ok = d.until('document.querySelector(".gm-canvas")?.__engine?.style==="dusk"', 25)
        prefs = [r for r in world_rows(s, 'rows view-preference') if r.get('map.style')]
        note('choosing Dusk changes your map and is kept as your own view preference', ok and prefs and prefs[-1]['map.style'] == 'dusk')
        d.look_at(36.9665, -122.0015, dist=700, pitch=55, bearing=-20)
        page.shot(str(OUT / 'proof-08-dusk.png'))
        d.click('#gm-g-buildings')
        ok = d.until('document.querySelector(".gm-canvas")?.__engine?.hidden.has("ground:buildings")', 25)
        note('unticking Buildings hides them for you only', ok)
        d.click('#gm-g-buildings')
        d.until('!document.querySelector(".gm-canvas")?.__engine?.hidden.has("ground:buildings")', 25)

        # Search beyond the neighbourhood
        d.click('.gm-search input')
        d.type('Capitola Village')
        d.until('!!document.querySelector(".gm-results button")', 15)
        d.key('Enter', vk=13)
        d.settle(3000)
        here = d.engine('E.toLL(E.cam.x,E.cam.y)')
        dist = metres(here[0], here[1], 36.97268, -121.95214)
        note('searching Capitola Village flies there', dist < 2500, f'{dist:.0f} m from it')

        # A walk: the route tool, two presses, the planner, save
        d.look_at(36.96526, -122.00443, dist=1300, pitch=0)      # both stops in the open middle, clear of the panels
        d.click_text('.gm-tools button', 'Route')
        d.settle(400)
        for lat, lon in ((36.96702, -122.00785), (36.96350, -122.00100)):
            p = d.screen_of(lat, lon)
            d.click_at(p['x'], p['y'])
            d.settle(500)
        ok = d.until('/\\d+(\\.\\d+)? (m|km) · \\d+ min/.test(document.querySelector("[data-part=route]")?.innerText||"")', 25)
        note('two presses with the route tool give a street path with its length and minutes', ok, d.text('[data-part=route] .gm-big'))
        d.click_text('[data-part=route] button', 'Save route')
        ok = d.until('!document.querySelector("[data-part=route]")', 20)
        routes = world_rows(s, 'rows route')
        note('Save makes a route thing that keeps its path', ok and routes and routes[0].get('path'), f"{routes[0].get('metres')} m" if routes else '')

        # California, then home
        d.click('.gm-nav button[aria-label="See all of California"]')
        d.settle(3000)
        d.tiles_in(90)
        z = d.engine('Math.max(...E.drawList.map(t=>t.z))')
        span = d.engine('E.cam.dist')
        note('the globe button shows all of California, drawn from low-zoom tiles', span > 1e6 and z <= 8, f'camera {span / 1000:.0f} km up, tiles z≤{z}')
        page.shot(str(OUT / 'proof-09-california.png'))
        d.click('.gm-nav button[aria-label="Back to Seabright"]')
        d.settle(2600)
        here = d.engine('E.toLL(E.cam.x,E.cam.y)')
        note('the home button comes back to Seabright', metres(here[0], here[1], 36.9672, -122.0088) < 500)
        d.tiles_in(60)

        # A line, said elsewhere, shows up in the open window; a pin dragged moves its thing
        s.say('map.add "Seabright & Murray" kind=spot name="Corner bench"')
        ok = d.until('[...document.querySelectorAll(".gm-pin")].some(p=>p.getAttribute("aria-label").startsWith("Corner bench"))', 25)
        note('a spot added in a line (map.add "Seabright & Murray" …) appears in the open window', ok)
        d.look_at(36.9630, -122.0040, dist=300, pitch=0)
        p = d.screen_of(36.9630, -122.0040)
        d.drag(p['x'], p['y'] - 20, p['x'] + 90, p['y'] - 20 + 60)
        d.settle(1200)
        t = world_rows(s, 'look ' + tide)[0]
        moved = metres(t['lat'], t['lon'], 36.9630, -122.0040)
        note('dragging the Tide pools pin moves the spot in the world', moved > 10, f'{moved:.0f} m')

        # How fast a frame is here (software GPU; a real one is faster)
        d.look_at(36.9665, -122.0015, dist=600, pitch=55, bearing=-20)
        ms = d.js('(async()=>{const E=document.querySelector(".gm-canvas").__engine;const t=[];for(let i=0;i<20;i++){E.cam.bearing+=1;E.draw();t.push(E.frameMs)}t.sort((a,b)=>a-b);return t[10]})()')
        note('a frame over Seabright in 3D takes this long on a software GPU (median of 20)', ms is not None, f'{ms:.1f} ms')
        errors += script_errors(page)
        stopped = d.js('document.querySelectorAll("[data-health=stopped],.part-stopped").length')
        note('no script errors and no stopped parts in any window', not errors and not stopped,
             json.dumps([e.get('params', {}).get('exceptionDetails', {}).get('text') for e in errors])[:400])
        page.shot(str(OUT / 'proof-10-end.png'))
        page.close()
    finally:
        s.close()
    passed = sum(1 for _, ok, _ in log if ok)
    lines = [f"{'PASS' if ok else 'FAIL'} {step}" + (f' · {detail}' if detail else '') for step, ok, detail in log]
    summary = f'{passed} of {len(log)} steps pass · {time.time() - t_all:.0f} s'
    (OUT / 'proof-output.txt').write_text('\n'.join(lines + ['', summary]) + '\n', encoding='utf-8')
    print(summary)
    return passed == len(log)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
