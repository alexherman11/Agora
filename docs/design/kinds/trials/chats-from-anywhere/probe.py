"""Follow-ups on the world trial.py left behind (<scratch>/world, a copy): speaker names across sources, a 'chat by
app' kind (the window-kinds table as a kind's needs), case of exe names, a window made after the kind, and latest-N.
Run: python probe.py <scratch dir>"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Projects/Agora4/src/agora")
from kernel.kernel import Kernel, Actor  # noqa: E402
from painter.arrangement import compile_view  # noqa: E402

W = Path(sys.argv[1]) / "world"
k = Kernel(W)
A = Actor("dk2", "dk2", "person")
WINMOD = next(t for t in k.things("module") if k.state.get(t, "name") == "window")


def R(line, show=300, actor=A):
    out = k.run(actor, line)
    print(f"> {line[:150]}\n   {'OK ' if out.get('ok') else 'NO '} {str(out.get('text', '')).replace(chr(10), chr(10) + '      ')[:show]}")
    return out


def q2(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


print("== speaker across sources: what a said row and a twitch row carry for 'who'")
conv = "dk828"
said = [t for t in k.things("said") if k.state.get(t, "chat") == conv][-1]
tw = next(t for t in k.things("twitch-message"))
print("said shown keys:", sorted(x for x in k.shown("dk2", said) if not x.startswith("in:")))
print("twitch shown keys:", sorted(x for x in k.shown("dk2", tw) if not x.startswith("in:")))
lens = ('root : column, of tag:message,prop:chat=dk828 as m, limit 3, each line\n'
        'line : text "[$m.display_name] [$m.made_by] [$m.by] [$m.made_by.name] $m.text"\n')
r = R(f"make kind=lens name=probe-who painter=components text={q2(lens)}")
s = json.dumps(compile_view(k, A, r["made"][0]), ensure_ascii=False)
print("rendered:", re.findall(r'\[[^\]]*\] \[[^\]]*\] \[[^\]]*\] \[[^\]]*\] [^"]{0,40}', s)[:3])

print("\n== latest N: limit takes the first N in order; is there a way to say the last N?")
lens2 = ('root : column, of tag:message,prop:chat=dk828 as m, by made, limit 2, each line\n'
         'line : text "$m.text @ $m.made"\n')
r = R(f"make kind=lens name=probe-last painter=components text={q2(lens2)}")
s = json.dumps(compile_view(k, A, r["made"][0]), ensure_ascii=False)
print("rendered with by made, limit 2:", re.findall(r'"([^"]{0,40} @ [^"]{0,25})"', s)[:2])

print("\n== chat by app: the window-kinds table as a kind's needs (kind|exe=chat|ChatGPT.exe|claude.exe)")
R('make kind=kind name=assistant needs="kind|exe=chat|ChatGPT.exe|claude.exe"')
R("rows assistant", show=500)
r = k.module_own(WINMOD, 'make kind=window shows=native native=yes exe=chatgpt.exe app=ChatGPT name="ChatGPT (new)" handle=99')
print("a new window whose exe arrives lower-case:", r.get("text", "")[:80])
r2 = k.module_own(WINMOD, 'make kind=window shows=native native=yes exe=ChatGPT.exe app=ChatGPT name="ChatGPT (newer)" handle=100')
rows = k.run(A, "rows assistant")["rows"]
print("rows assistant now includes the lower-case one:", r["made"][0] in [x["id"] for x in rows],
      "| the exact-case one:", r2["made"][0] in [x["id"] for x in rows])
R(f"look {r2['made'][0]}")
R(f"mark {r2['made'][0]} assistant")
R(f'make kind=note title="ChatGPT.exe crash notes" kind_hint=x exe=ChatGPT.exe')   # anything that says exe=ChatGPT.exe
print("a note that mentions exe=ChatGPT.exe is an assistant too:",
      any(x.get("kind") == "note" for x in k.run(A, "rows assistant")["rows"]))

print("\n== the model's offline fallback on a twitch message (it reads title/text/name, not message)")
row = k.shown("dk2", tw)
print("title/text/name on a twitch message:", [row.get(f) for f in ("title", "text", "name")], "message:", row.get("message"))

print("\n== how a window that is a chat reads to someone who never set the marker: kinds, actions")
gpt = next(t for t in k.things("window") if k.state.get(t, "exe") == "ChatGPT.exe" and k.state.get(t, "chat") == "yes")
R(f"kinds {gpt}")
R(f"actions {gpt}", show=900)
t0 = time.perf_counter()
for _ in range(20):
    k.kinds.kinds_of(k.shown("dk2", tw))
print("kinds_of per thing, ms:", round((time.perf_counter() - t0) / 20 * 1000, 2), "| open kinds:", k.kinds.open_kinds())
