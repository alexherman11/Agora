"""Real browser + native gateway regression for the failed measurement bridge."""

import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time

from live_trials import Browser, seed, server_module
from native_arrangement import ArrangementGateway, SPECS

root = Path("C:/Projects/Agora/local/arrangement-trials-20260916")
output = root / ("browser-smoke-" + str(time.time_ns()))
output.mkdir()
gateway = ArrangementGateway(output / "world")
seed(gateway, True)
server_module.Gateway = ArrangementGateway
extra = "\n" + "".join("allowed.add(" + json.dumps(s["name"]) + ");" for s in SPECS) + "\n"
server_module.FRAME = server_module.FRAME.replace(
    "for(const method of [", extra + "for(const method of [", 1
)
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
server, app = server_module.serve(output / "world", port)
threading.Thread(target=server.serve_forever, daemon=True).start()
browser = Browser(output)
try:
    browser.call(op="open", url=f"http://127.0.0.1:{port}/#" + app.gateway.keep["operator"])
    app.gateway.arrangements.browser = browser
    actor = app.gateway.principal("jeff")
    snapshot = app.gateway.dispatch(actor, "arrangement.inspect", {})
    assert snapshot["viewport"]["width"] > 500 and snapshot["viewport"]["height"] > 500
    row = snapshot["items"][0]
    plan = app.gateway.dispatch(
        actor,
        "arrangement.prepare",
        {
            "reason": "Browser smoke",
            "operations": [
                {"operator": "place", "target": row["id"], "bounds": [30, 30, 300, 300]}
            ],
        },
    )
    receipt = app.gateway.dispatch(actor, "arrangement.apply", {"plan": plan["plan"]})
    browser.call(op="observe", wait=1700)
    found = browser.call(op="observe", selectors=['[data-view="' + row["id"] + '"]'])
    box = found["selected"]['[data-view="' + row["id"] + '"]'][0]["box"]
    assert abs(box["width"] - 300) < 1 and abs(box["height"] - 300) < 1
    assert not found["errors"], found["errors"]
    observation = app.gateway.dispatch(actor, "arrangement.observe", {})
    assert observation["rendered_matches_snapshot"], observation
    watermark = app.gateway.world.query(limit=1)["watermark"]
    browser.call(
        op="evaluate",
        expression="document.querySelector("
        + json.dumps('[data-view="' + row["id"] + '"]')
        + ').style.left="35px"',
    )
    mismatch = app.gateway.dispatch(actor, "arrangement.observe", {})
    assert not mismatch["rendered_matches_snapshot"] and mismatch["differences"]
    assert app.gateway.world.query(limit=1)["watermark"] == watermark
    application_plan=browser.call(op='evaluate',view=row['id'],expression='''(async () =>
      await AgoraApp.request('arrangement.plan', {snapshot:{contract:'freeform/v1',
        surface:'local',items:[{id:'one',subject:'supplied',bounds:[0,0,100,100]}],
        order:['one'],viewport:{width:600,height:400}},
        operations:[{operator:'place',target:'one',bounds:[44,60,100,100]}]}))()''')
    assert application_plan['native_writes']==0
    assert application_plan['effects'][0]['value']['rect']==[44,60,100,100]
    app.gateway.dispatch(actor, "arrangement.undo", {"intent": receipt["intent"]})
    report = {
        "passed": True,
        "viewport": snapshot["viewport"],
        "rendered_box": box,
        "observation": observation,
        "transient_mismatch_detected": True,
        "application_planning_through_real_browser": True,
        "replay": app.gateway.world.verify(),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"output": str(output), **report}), flush=True)
finally:
    browser.close()
    server.shutdown()
    server.server_close()
    app.bridge.close()
