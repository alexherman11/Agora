from playtest_steps import Step
from playtest_steps._support import DOCK, json, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_esc():
        icon = DOCK.format(json.dumps("Board"))
        r1 = await play.timed("!!document.getElementById('menu-pop')", press(play, icon, "Board on the dock", right=True))
        if not r1["ok"]:
            r1["want"] = "a right-click on a dock icon opened no menu"
            return r1
        r = await play.timed("!document.getElementById('menu-pop')", lambda: w.key("Escape"))
        if not r["ok"]:
            r["want"] = "Esc did not close the open menu"
            return r
        r["note"] = (f"the dock's menu opened in {r1['ms']} ms and Esc closed it in {r['ms']} ms; Esc hiding the whole home "
                     "base is hud.py's own key (a global hotkey), not a page's, so not played here")
        return r
    return s_esc


STEP = Step(name='esc', description='press Esc: what is open closes', order=2600,
            needs=(), script=bind, assertion='press Esc: what is open closes', budget=(100, 300))
