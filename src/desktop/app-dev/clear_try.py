"""clear_try: take the App studio surfaces (and all they hold) off the COPY, frontier-try, so apply.py try starts clean.
Only the copy: it refuses any other world. worker-a6431, 20 Oct.
    python src/desktop/app-dev/clear_try.py f6444 [f6491 ...]
"""
import re
import sys

import apply


def clear(w, sid):
    out = w.do(f"look {sid}")
    for kid in re.findall(r"^\s+([af]\d+) (?:note|surface)", out, re.M):
        if kid.startswith("f"):
            clear(w, kid)
        else:
            w.do(f"look {kid}")
            print(kid, w.do(f"do remove {kid}").split("\n")[0][:80])
    w.do(f"look {sid}")
    print(sid, w.do(f"do remove {sid}").split("\n")[0][:80])


if __name__ == "__main__":
    w = apply.Try()
    for s in sys.argv[1:]:
        clear(w, s)
    w.save()
