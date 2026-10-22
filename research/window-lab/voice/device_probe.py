"""device_probe.py (a9138): does the speech child name the microphone a listen would use? Read only.

    python research/window-lab/voice/device_probe.py

Starts voice_host.ps1, sends {"do":"device"} (Windows' Core Audio property store of the endpoint: its name, nothing
opened, no setting changed), prints what came back and how long it took, and quits. It never sends listen or say.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voice  # noqa: E402

eng = voice.SapiEngine()
seen = []
eng.event = seen.append
try:
    if not eng.ready.wait(30):
        sys.exit("the speech child did not start")
    t = time.perf_counter()
    name = eng.device()
    took = time.perf_counter() - t
    ev = next((e for e in seen if e.get("ev") == "device"), {})
    if name is None:
        print(f"no name in time ({took:.3f} s): {ev.get('why', 'no answer')}")
    elif name == "":
        print(f"no input device ({took:.3f} s)")
    else:
        print(f"named in {took:.3f} s, by {ev.get('how')}: {name}")
    print("commands sent: device, quit (never listen or say)")
finally:
    eng.close()
