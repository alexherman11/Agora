"""Serve the combined Desk with the retained native and browser development tools."""

from pathlib import Path
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, 'C:\\Projects\\Agora\\worlds\\application-experiment\\repo\\src')
os.environ.setdefault("AGORA_CODEX_BIN", r"C:\Users\Alex\AppData\Local\OpenAI\Codex\bin\fd4c151a749f3ab4\codex.exe")
os.environ.setdefault("AGORA_JEFF_MODEL", "gpt-6-astra")
os.environ.setdefault("AGORA_JEFF_REASONING", "high")
os.environ.setdefault("AGORA_JEFF_MAX_CALLS", "250")
os.environ.setdefault("AGORA_JEFF_TIMEOUT", "1800")

from agora3.gateway import Gateway
from agora3.schemas import validate
from agora3.server import serve
from agora3.world import Refusal
from browser_specs import extra_specs
from fixture_tunnel import attach_yard_fixture, close_fixture, open_fixture


def fixture_ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8860/sources/coast", timeout=2) as response:
            return response.status == 200
    except OSError:
        return False


class Browser:
    def __init__(self):
        self.log = (ROOT / "logs/browser.log").open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            ["node", str(ROOT / "browser_worker.cjs")], cwd=ROOT,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.lock = threading.RLock()

    def call(self, request):
        with self.lock:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise Refusal("Desk browser observation stopped; inspect logs/browser.log.")
            response = json.loads(line)
            if "error" in response:
                raise Refusal(response["error"])
            return response.get("result")


def main():
    settings = json.loads((ROOT / "desk.json").read_text())
    (ROOT / "evidence").mkdir(exist_ok=True)
    fixture_process = None
    if not fixture_ready():
        fixture_log = (ROOT / "logs/fixture.log").open("a", encoding="utf-8")
        fixture_process = subprocess.Popen(
            [sys.executable, str(ROOT / "source_fixture.py")], cwd=ROOT,
            stdin=subprocess.DEVNULL, stdout=fixture_log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for _ in range(30):
            if fixture_ready():
                break
            time.sleep(.25)
        else:
            raise RuntimeError("The retained synthetic research source did not start.")
    gateway = Gateway(ROOT / "world")
    gateway.guest.start()
    connection_error = "No SSH response"
    for _ in range(45):
        connection = gateway.guest.execute("true", timeout=3)
        if connection["exit_code"] == 0:
            break
        connection_error = connection["stderr"]
        time.sleep(1)
    else:
        raise RuntimeError("The dedicated Desk guest did not become ready: " + connection_error)
    server, app = serve(ROOT / "world", settings["port"])
    attach_yard_fixture(app.gateway.yard)
    browser = Browser()
    original_dispatch = app.gateway.dispatch
    original_describe = app.gateway.describe

    def describe():
        return original_describe() + extra_specs

    def dispatch(actor, name, args):
        app.gateway.check_authority(actor)
        spec = next((item for item in extra_specs if item["name"] == name), None)
        if spec is not None:
            validate(spec["input_schema"], args)
        if name == "experiment.observe":
            return browser.call({"op": "observe", **args})
        if name == "experiment.interact":
            return browser.call({"op": "interact", **args})
        if name == "experiment.sequence":
            return browser.call({"op": "sequence", **args})
        if name == "experiment.inspect_candidate":
            html = app.gateway.packages.browser_html(args["build"])
            return browser.call({"op": "candidate", "html": html})
        return original_dispatch(actor, name, args)

    app.gateway.describe = describe
    app.gateway.dispatch = dispatch
    threading.Thread(target=server.serve_forever, daemon=True).start()
    bridge = app.connect_guest()
    if not bridge.get("connected"):
        raise RuntimeError("The dedicated guest native bridge did not connect.")
    fixture = open_fixture(app.gateway.guest)
    browser.call({"op": "open", "url": f"http://127.0.0.1:{settings['port']}/#" + app.gateway.keep["operator"]})
    ready = {
        "pid": os.getpid(), "port": settings["port"], "ready": True,
        "tools": [item["name"] for item in describe()],
        "account": app._agent().status(), "model_turn_started": False,
        "replay": app.gateway.world.verify(), "started": time.time(),
        "launch_id": os.environ.get("AGORA_DESK_LAUNCH_ID"),
    }
    (ROOT / "ready.json").write_text(json.dumps(ready, indent=2))
    print(json.dumps({k: v for k, v in ready.items() if k != "tools"}), flush=True)
    control = ROOT / "control"
    control.mkdir(exist_ok=True)
    while True:
        for path in sorted(control.glob("*.request.json")):
            response = path.with_name(path.name.replace(".request.json", ".response.json"))
            if response.exists():
                continue
            close = False
            try:
                request = json.loads(path.read_text(encoding="utf-8"))
                op = request["op"]
                if op == "status":
                    result = {"running": app.running, "error": app.error,
                              "system": app.system_status()}
                elif op == "rpc":
                    result = dispatch(app.gateway.principal("human"), request["name"], request.get("args", {}))
                elif op == "browser":
                    result = browser.call(request["request"])
                elif op == "close":
                    if app.running:
                        raise Refusal("JEFF is working; finish or stop that turn before closing.")
                    app.bridge.close()
                    close_fixture(fixture)
                    if app.jeff:
                        app.jeff.close()
                    browser.call({"op": "close"})
                    server.shutdown()
                    if fixture_process:
                        fixture_process.terminate()
                    result, close = {"closed": True}, True
                else:
                    raise Refusal("Unknown local Desk control operation.")
                content = {"result": result}
            except Exception as exc:
                content = {"error": str(exc)}
            pending = response.with_suffix(".pending")
            pending.write_text(json.dumps(content, indent=2), encoding="utf-8")
            pending.replace(response)
            if close:
                return
        time.sleep(.1)


if __name__ == "__main__":
    main()
