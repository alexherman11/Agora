"""Read-only local preview using Agora's actual compiler, styles and lens painter.

No sessions are loaded/saved, no models run, no live processes restarted. Only
the small published house/usage state files and a read-only card-name query are
read. All notes/commands below belong to a new ephemeral in-memory desk.
"""
import argparse
import hashlib
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LAB = ROOT / "research/text-desk-lab/notation"
sys.path.insert(0, str(LAB))
import explore
import scene
import style
import witnessed
from data_graphics import number

PALETTE = ["chart.teal", "chart.blue", "chart.violet", "chart.amber", "chart.coral"]


def q(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def iso(value):
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).strftime("%d %b %H:%M UTC")
    except (ValueError, TypeError, OSError, OverflowError):
        return "unknown"


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def age(value, now):
    value = number(value)
    if value is None or value > now + 5:
        return "?"
    seconds = max(0, int(now - value))
    return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m" if seconds < 3600 else f"{seconds // 3600}h{seconds % 3600 // 60:02}m"


def context_value(row):
    tokens, capacity = number(row.get("tokens")), number(row.get("window"))
    return round(tokens / capacity * 100, 1) if tokens is not None and tokens >= 0 and capacity and capacity > 0 else None


def level(value):
    return "full" if value is not None and value >= 100 else "warn" if value is not None and value >= 80 else "ok"


def short_model(model):
    return {"gpt-6-astra":"astra", "gpt-6.1-sol":"sol6.1", "gpt-6-sol":"sol6", "claude-opus-5-5":"opus5.5"}.get(model, model or "?")


class Runtime:
    def __init__(self, world="frontier"):
        self.world = world
        self.names = {}
        self.names_at = 0
        self.queued = "Unknown"

    def read(self):
        now = time.time()
        base = LAB / "house-state" / self.world
        raw_house = load(base / "house.json")
        fields = ("actor", "provider", "model", "reasoning", "status", "doing", "alive", "builder", "turns", "retry_at", "recovery_needed")
        house = {k: raw_house[k] for k in ("beat", "pid") if k in raw_house}
        for group in ("residents", "workers"):
            if isinstance(raw_house.get(group), dict):
                house[group] = {key:{k:v[k] for k in fields if k in v} for key,v in raw_house[group].items() if isinstance(v, dict)}
        raw_plans = load(base / "plan-usage.json")
        fields = ("provider", "label", "percent", "resets", "asof", "source")
        plans = dict(windows={key:{k:v[k] for k in fields if k in v}
                             for key,v in (raw_plans.get("windows") or {}).items() if isinstance(v, dict)})
        raw_usage = witnessed.read(self.world, "usage") or {}
        fields = ("kind", "actor", "corner", "provider", "model", "doing", "tokens", "window", "window_from", "since", "quiet")
        doc = dict(rows=[{k:v[k] for k in fields if k in v} for v in raw_usage.get("rows", []) if isinstance(v, dict)])
        # Name only worker cards, never transcripts or the whole world snapshot.
        if now - self.names_at > 60:
            self.names_at = now
            body = json.dumps(dict(session=self.world, **{"as": "dashboard-builder"}, line="find prop:commission -prop:commission=landed -prop:commission=reported -prop:commission=done -prop:commission=cancelled")).encode()
            try:
                req = urllib.request.Request("http://127.0.0.1:8794/api/do", body, {"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as reply:
                    text = json.load(reply).get("text", "")
                if not re.search(r"find '?prop:commission[^\n]*:", text):
                    raise ValueError("card query unavailable")
                self.names.update(dict(re.findall(r'(a\d+) task "([^"]+)"', text)))
                self.queued = str(len(re.findall(r'commission=asked(?:\s|$)', text)))
                for nid in list((house.get("workers") or {}))[:10]:
                    if nid in self.names or not re.fullmatch(r"a\d+", nid):
                        continue
                    payload = json.dumps(dict(session=self.world, **{"as":"dashboard-builder"}, line=f"read {nid} :1")).encode()
                    req = urllib.request.Request("http://127.0.0.1:8794/api/do", payload, {"Content-Type":"application/json"})
                    with urllib.request.urlopen(req, timeout=3) as reply:
                        title = re.search(r'task "([^"]+)"', json.load(reply).get("text", ""))
                    if title:
                        self.names[nid] = title[1]
            except (OSError, ValueError):
                self.queued = "Unknown"
        beat = number(house.get("beat"))
        stale = beat is None or now - beat > 60 or beat > now + 5
        return dict(house=house, plans=plans, usage=doc, stale=stale, names=self.names, observed_at=now,
                    queued=self.queued, stamp=iso(now), beat=iso(beat))


def build(snapshot):
    d = explore.fresh()
    d._session = "dashboard-inmemory"
    d.world.me = "dashboard-builder"

    def run(line):
        result = d.dispatch("desk", dict(line=line, whole=True))
        text = result.get("text", "")
        if result.get("error") or text.startswith("ERR"):
            raise RuntimeError(result.get("error") or text)
        found = re.search(r"created ([af]\d+)", text)
        return found[1] if found else None

    def note(title, text="", **props):
        run("look " + d.world.root)
        item = run(f'do create {d.world.root} kind=note title={q(title)} text={q(text)}')
        if props:
            run("look " + item)
            run("do prop " + item + " " + " ".join(k + "=" + q(v) for k, v in props.items()))
        return item

    style_id = note("dashboard-style", (HERE / "dashboard.style").read_text(encoding="utf-8"))
    run(f"do tag {style_id} add=style")
    terminal_id = note("terminal-style", (HERE / "terminal.style").read_text(encoding="utf-8"))
    run(f"do tag {terminal_id} add=style")
    house, plans = snapshot["house"], snapshot["plans"]
    usage = snapshot["usage"].get("rows", [])
    agents = [r for r in usage if r.get("kind") == "agent"]
    names = snapshot["names"]
    residents = house.get("residents") or {}
    workers = house.get("workers") or {}
    active_workers = sum(r.get("doing") == "working" for r in workers.values())
    now = snapshot.get("observed_at", time.time())
    status = note("Observation and limits", stamp=f'Read-only local observations · refreshed {snapshot["stamp"]} · house {snapshot["beat"]}'
                  + (" · STALE" if snapshot["stale"] else ""), residents=len(residents) if "residents" in house else "Unknown", workers=f'{active_workers}/{len(workers)}' if "workers" in house else "Unknown",
                  queued=snapshot["queued"], quota_note="Quota is account-wide, not per agent. Expired windows are unknown until another provider report. Reset times are UTC.",
                  method="Context: existing witnessed:usage, last provider-reported total and capacity; the payload does not expose the token observation time or internal composition. Publication age is not measurement age. Quota: plan-usage.json with each provider's as-of/reset. Status: house.json heartbeat and reported activity. Queue: commission=asked cards from the local desk. Billing and cumulative token use are unavailable. No hidden thinking is read or displayed.")
    run("look " + status)
    status_props = dict(clock=datetime.fromtimestamp(now, timezone.utc).strftime("%H:%M UTC"),
                        resident_summary=f"residents {len(residents)}" if "residents" in house else "residents ?",
                        worker_summary=f"workers {active_workers}/{len(workers)} active" if "workers" in house else "workers ?",
                        freshness=("STALE / " if snapshot["stale"] else "") + f'reported / house {age(house.get("beat"), now)} ago / context age ? / ~ last model' + (" / " + snapshot["label"] if snapshot.get("label") else ""),
                        stale="yes" if snapshot["stale"] else "no", inactive_count=len(workers)-active_workers,
                        inactive_summary=f"{len(workers)-active_workers} inactive workers",
                        worker_empty="Worker telemetry unavailable" if "workers" not in house else "No active workers reported" if not active_workers else "")
    run("do prop " + status + " " + " ".join(k + "=" + q(v) for k,v in status_props.items()))

    def chart(key, config):
        return note(key, json.dumps(config, ensure_ascii=False))

    context_rows = []
    for i, r in enumerate(agents):
        label = names.get(r.get("corner"), r.get("actor", "Unnamed"))
        if label.startswith("worker-"):
            label = "Worker (name unavailable)"
        value = context_value(r)
        context_rows.append(dict(label=label.title() if not r.get("actor", "").startswith("worker-") else label,
                                 value=value, role=PALETTE[i % len(PALETTE)]))
    context = chart("Context footprint", dict(title="Context footprint", mode="bars", unit="% of capacity", basis="reported totals", maximum=100,
                    records=context_rows, **(dict(state="unknown", note="No context observation available") if not agents else dict(state="stale", note="House heartbeat is stale; last observations retained") if snapshot["stale"] else {})))
    quota_rows, quota_details, quota_ages = [], [], []
    for i, r in enumerate((plans.get("windows") or {}).values()):
        reset, asof = number(r.get("resets")), number(r.get("asof"))
        value = number(r.get("percent")) if reset is not None and reset > now and asof is not None and asof <= now + 5 else None
        label = f'{r.get("provider", "Unknown").title()} · {r.get("label", "window")}'
        compact_label = f'{r.get("provider", "Unknown").title()} ' + r.get("label", "window").replace(" hours", "h").replace(" days", "d")
        quota_rows.append(dict(label=compact_label, value=value, role="chart." + level(value)))
        quota_details.append(f'{label}: observed {iso(asof)}; resets {iso(reset)}; source {r.get("source", "unknown")}')
        quota_ages.append(f'{compact_label} {age(asof, now)}')
    quota = chart("Account windows", dict(title="Account windows", mode="bars", unit="%", basis="provider quota reports", maximum=100, corner_radius=0, mark_height=10, records=quota_rows,
                  **(dict(state="unknown", note="No quota observations available") if not quota_rows else {})))
    # Detailed provider evidence remains ordinary world text, never hidden UI data.
    run("look " + status)
    run("do prop " + status + " quota_note=" + q("Quota is account-wide, not per agent. " + " | ".join(quota_details)))
    run("do prop " + status + " quota_age=" + q("report age: " + " | ".join(quota_ages) if quota_ages else "Quota observations unavailable"))
    composition = chart("No composition report", dict(title="No composition report", mode="stack", unit="tokens", basis="unknown", records=[dict(label="Prompt / tools / conversation", value=None)]))
    by_corner = {r.get("corner"): r for r in agents}
    shown_workers = [(key,r) for key,r in workers.items() if r.get("doing") == "working"]
    resident_order = sorted(residents, key=lambda k: (residents[k].get("actor", "").lower() != "jeff", k))
    crew_order = snapshot.get("crew_order", resident_order + sorted(workers))
    visible = set(residents) | {key for key, _ in shown_workers}
    for key in crew_order:
        r = residents.get(key, workers.get(key, {}))
        u = by_corner.get(key, {})
        title = names.get(key, r.get("actor", "Unnamed").title())
        if title.lower().startswith("worker-"):
            title = "Worker (name unavailable)"
        detail = f'{title}. Reported activity: {r.get("doing", "unknown")}. Reported status: {r.get("status", "unknown")}; alive flag: {r.get("alive", "unknown")}. House observation: {snapshot["beat"]}. Turns: {r.get("turns", "unknown")}. '
        detail += f'Context: {u.get("tokens", "unknown")} / {u.get("window", "unknown")} tokens; capacity source: {u.get("window_from", "unknown")}. '
        detail += f'Last activity marker: {u.get("since", "unknown")}; quiet: {u.get("quiet") or "not reported"}. Elapsed duration is not supplied. Token observation time is unknown. '
        detail += f'Current configured model: {r.get("model", "unknown")}; effort: {r.get("reasoning", "unknown")}. Last context model: {u.get("model", "unknown")}. Retry at: {iso(r.get("retry_at"))}; recovery needed: {r.get("recovery_needed", "unknown")}. Worker view shows {len(shown_workers)} of {len(workers)} reported entries.'
        model = r["model"] if r.get("model") else "last " + u["model"] if u.get("model") else "model unknown"
        compact_model = short_model(r.get("model")) if r.get("model") else "~" + short_model(u.get("model")) if u.get("model") else "?"
        if r.get("reasoning"):
            compact_model += "/" + str(r["reasoning"])
        value = context_value(u)
        ctx = chart(title + " context", dict(title=title, mode="bars", unit="% of capacity", maximum=100,
                    corner_radius=0, mark_height=28, basis="reported totals; measurement age unknown",
                    records=[dict(label=title, value=value, role="chart." + level(value))],
                    **(dict(state="stale", note="House heartbeat stale; last context retained") if snapshot["stale"] else {})))
        worker_name = re.sub(r"-?builder-?", " ", r.get("builder") or "Worker").strip().title()
        if worker_name.isdigit():
            worker_name = "Worker " + worker_name
        item = note(title, detail, doing=r.get("doing", "unknown"), provider=r.get("provider") or u.get("provider", "unknown"), model=model,
                    model_short=compact_model, status_word=r.get("status") or "unknown",
                    state_word="paused" if r.get("status") == "paused" else r.get("doing", "unknown"), worker_name=worker_name,
                    ctx=ctx, ctx_label="?" if value is None else "error" if value > 100 else f"{value:g}%", ctx_level=level(value))
        if key in visible:
            run(f"do tag {item} add=crew")
        if key in residents or key in workers:
            tag = "watch-resident" if key in residents else "watch-worker" if r.get("doing") == "working" else "watch-inactive"
            run(f"do tag {item} add={tag}")
    configs = {
        "MATERIALS": dict(title="Where the materials go", mode="stack", unit="sheets", basis="illustrative inventory", maximum=120,
                          records=[dict(label="Posters", value=42, role="chart.teal"), dict(label="Programs", value=28, role="chart.blue"), dict(label="Labels", value=18, role="chart.violet"), dict(label="Proofs", value=12, role="chart.amber")]),
        "HISTORY": dict(title="Guest confirmations", mode="line", unit="guests", basis="illustrative samples", x_unit="days in October", role="chart.teal",
                        records=[dict(label="13 Oct", x=13, value=14), dict(label="14 Oct", x=14, value=21), dict(label="17 Oct", x=17, value=49), dict(label="18 Oct · missing", x=18, value=None), dict(label="20 Oct", x=20, value=65), dict(label="22 Oct", x=22, value=84)]),
        "ROOMS": dict(title="Room readiness", mode="bars", unit="% ready", basis="illustrative checklist", maximum=100,
                      records=[dict(label="Print room", value=100, role="chart.teal"), dict(label="Listening corner", value=65, role="chart.blue"), dict(label="Workshop table", value=0, role="chart.violet"), dict(label="Garden annex", value=None, role="chart.amber")]),
        "EMPTY": dict(title="Visitor feedback", mode="line", unit="responses", basis="not yet collected", records=[]),
    }
    refs = dict(STATUS=status, CONTEXT=context, QUOTA=quota, COMPOSITION=composition)
    refs.update({key: chart(config["title"], config) for key, config in configs.items()})
    for name in ("observatory", "studio"):
        src = (HERE / (name + ".lens")).read_text(encoding="utf-8")
        for key, value in refs.items():
            src = src.replace("@" + key + "@", value)
        lid = note(name, src, style="terminal-style" if name == "observatory" else "dashboard-style")
        run(f"do tag {lid} add=lens")
    return d


class Preview:
    def __init__(self, fixture=None):
        self.runtime = Runtime()
        self.fixture = fixture
        self.lock = threading.Lock()
        self.at = 0
        self.desk = None
        self.crew_order = []

    def scene(self, name):
        if name not in ("observatory", "studio"):
            return dict(refused="Choose Observatory or Studio")
        with self.lock:
            if self.desk is None or time.monotonic() - self.at > 15:
                self.snapshot = load(self.fixture) if self.fixture else self.runtime.read()
                residents = self.snapshot["house"].get("residents") or {}
                workers = self.snapshot["house"].get("workers") or {}
                keys = sorted(residents, key=lambda k: (residents[k].get("actor", "").lower() != "jeff", k)) + sorted(workers)
                self.crew_order.extend(k for k in keys if k not in self.crew_order)
                self.snapshot["crew_order"] = self.crew_order
                self.desk = build(self.snapshot)
                self.at = time.monotonic()
            node, text = scene.scene_for(self.desk, name)
            painted = dict(scene.painter_view(node), **{"def": node.get("def")})
            gen = hashlib.sha256(json.dumps(painted, sort_keys=True).encode()).hexdigest()[:16]
            return dict(scene=painted, text=text, gen=gen, events_total=len(self.desk.world.events))


def serve(port, fixture=None):
    preview = Preview(fixture)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(LAB / "desk-shell"), **kwargs)

        def log_message(self, *args):
            pass

        def reply(self, value, code=200):
            data = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            query = urllib.parse.parse_qs(url.query)
            if url.path == "/api/scene":
                try:
                    answer = preview.scene(query.get("lens", ["observatory"])[0])
                    if query.get("have") == [answer.get("gen")]:
                        answer = dict(same=True, gen=answer["gen"])
                    return self.reply(answer)
                except Exception as exc:
                    return self.reply(dict(refused=f"Preview: {type(exc).__name__}: {exc}"))
            if url.path == "/api/style":
                filename = "terminal.style" if query.get("name") == ["terminal-style"] else "dashboard.style"
                return self.reply(dict(looks=style.looks((HERE / filename).read_text(encoding="utf-8"))))
            if url.path == "/api/version":
                return self.reply(dict(code="read-only-preview", painter="current", shape=1))
            if url.path.startswith(("/api/", "/door/")):
                return self.reply({}, 404)
            if url.path in ("/", "/lens.html"):
                content = (LAB / "desk-shell/lens.html").read_text(encoding="utf-8")
                content = re.sub(r'<link[^>]*https://fonts[^>]*>', '', content)
                data = content.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            # Serve only existing painter JavaScript and styles, never source/state.
            target = Path(self.translate_path(url.path)).resolve()
            if not target.is_relative_to((LAB / "desk-shell").resolve()) or target.suffix not in (".js", ".css"):
                return self.reply({}, 404)
            return super().do_GET()

        def do_POST(self):
            size = int(self.headers.get("Content-Length", 0))
            self.rfile.read(min(size, 200_000))
            return self.reply({} if self.path == "/api/observe" else dict(error="Read-only preview; no world mutation"))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f'Observatory: http://127.0.0.1:{server.server_port}/lens.html?lens=observatory&inspect=0', flush=True)
    print(f'Studio: http://127.0.0.1:{server.server_port}/lens.html?lens=studio&inspect=0', flush=True)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8896)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        p = Preview(args.fixture)
        for name in ("observatory", "studio"):
            answer = p.scene(name)
            print(name, len(json.dumps(answer)), "bytes", answer.get("refused", "compiled"))
    else:
        serve(args.port, args.fixture)
