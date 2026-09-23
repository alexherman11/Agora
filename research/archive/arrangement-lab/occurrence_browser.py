"""Observation-browser transport only; no fixture setup or runtime selection."""

import json
import subprocess
import threading
from pathlib import Path

from agora3.world import Refusal

NODE = Path(
    "C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
)
WORKER = Path("C:/Projects/Agora/worlds/parallel-desk/browser_worker.cjs")
SPEC_FILE = Path("C:/Projects/Agora/worlds/parallel-desk/browser_specs.py")


class Browser:
    def __init__(self, output):
        source = WORKER.read_text(encoding="utf-8")
        source = source.replace(
            "if(req.op==='evaluate'){const f=await frame();",
            "if(req.op==='evaluate'){const f=await frame(page,req.view);",
        )
        source = source.replace(
            "fontSize:getComputedStyle(n).fontSize}",
            "fontSize:getComputedStyle(n).fontSize,zIndex:getComputedStyle(n).zIndex,position:getComputedStyle(n).position}",
        )
        path = output / "browser_worker.cjs"
        path.write_text(source, encoding="utf-8")
        self.process = subprocess.Popen(
            [str(NODE), str(path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=(output / "browser.stderr.log").open("w"),
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.lock = threading.RLock()

    def call(self, **args):
        with self.lock:
            self.process.stdin.write(json.dumps(args) + "\n")
            self.process.stdin.flush()
            result = json.loads(self.process.stdout.readline())
            if "error" in result:
                raise Refusal(result["error"])
            return result["result"]

    def close(self):
        try:
            self.call(op="close")
        finally:
            self.process.stdin.close()
            self.process.wait(timeout=15)
