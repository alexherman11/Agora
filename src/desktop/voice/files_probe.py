"""files_probe.py (a8901): Windows' local voice and recognizer, from FILES only. No microphone is opened, no sound is
played: the voice is rendered into a WAV file, then the recognizer reads that file.

    python src/desktop/voice/files_probe.py [out-dir]

Prints one JSON line: the engines' names, the WAV's length, and timings (seconds): say_first (the say asked until the
voice started), say_done, listen_first_hyp, listen_final, and the words recognized. A refusal is printed as it came.
"""
import json
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voice  # noqa: E402

PHRASES = ["Please show me the board and what is waiting on me", "Play some music"]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="voice-probe-"))
    out.mkdir(parents=True, exist_ok=True)
    events, seen = [], threading.Condition()
    eng = voice.SapiEngine()

    def on(ev):
        with seen:
            events.append((time.perf_counter(), ev))
            seen.notify_all()
    eng.event = on

    def wait(pred, timeout):
        end = time.perf_counter() + timeout
        with seen:
            while True:
                hit = next((x for x in events if pred(x[1])), None)
                if hit or time.perf_counter() > end:
                    return hit
                seen.wait(0.1)

    report = {"out": str(out)}
    if not eng.ready.wait(60):
        report["refused"] = "the speech child did not say ready in 60 s"
        print(json.dumps(report))
        return 1
    report["engines"] = {k: eng.info.get(k) for k in ("recognizer", "voices")}
    report["errors"] = [ev for _, ev in events if ev.get("ev") == "error"]
    for k, phrase in enumerate(PHRASES):
        wav = out / f"phrase-{k}.wav"
        t0 = time.perf_counter()
        eng.say(f"probe-{k}", phrase, target=wav)                 # into the file, never the device
        start = wait(lambda e: e.get("ev") == "speaking" and e.get("id") == f"probe-{k}", 30)
        done = wait(lambda e: e.get("ev") == "spoke" and e.get("id") == f"probe-{k}", 60)
        err = wait(lambda e: e.get("ev") == "error" and e.get("where") == "say", 0.2)
        r = {"phrase": phrase, "say_first": round(start[0] - t0, 3) if start else None,
             "say_done": round(done[0] - t0, 3) if done else None, "say_error": err[1] if err else None}
        if done and wav.exists():
            time.sleep(0.3)
            with wave.open(str(wav)) as w:
                r["wav_seconds"] = round(w.getnframes() / w.getframerate(), 3)
            n0 = len(events)
            t1 = time.perf_counter()
            eng.listen(wav)                                         # from the file, never the microphone
            fin = wait(lambda e: e.get("ev") == "stopped" and events.index(next(x for x in events if x[1] is e)) >= n0, 60)
            got = events[n0:]
            hyps = [(t, e) for t, e in got if e.get("ev") == "hyp"]
            finals = [(t, e) for t, e in got if e.get("ev") == "final"]
            r.update(listen_first_hyp=round(hyps[0][0] - t1, 3) if hyps else None,
                     listen_final=round(finals[0][0] - t1, 3) if finals else None,
                     recognized=[e.get("text") for _, e in finals], conf=[e.get("conf") for _, e in finals],
                     stopped=(fin[1].get("why") if fin else None),
                     listen_errors=[e for _, e in got if e.get("ev") == "error"])
        report.setdefault("phrases", []).append(r)
    eng.close()
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
