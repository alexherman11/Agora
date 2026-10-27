"""The first kits (a13319): two independent communities, real loopback HTTP.

Imagined: people, meetings and choices; no model calls. Ran: numbered checks,
facts replay and optional headless phone pictures. No live Desk is touched.
"""
import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROOF = Path(__file__).resolve().parent
LAB = PROOF.parent
sys.path[:0] = [str(PROOF), str(LAB), str(LAB / "tests")]
import council_night as council
from kernel.kernel import Kernel
from kernel.door import serve
from test_skeleton import StandInEntry, post
from test_painter import quoted

PEOPLE = ["Marisol", "Lucia", "Rosa", "Diego", "Elena", "Pablo", "Sofia", "Mateo",
          "Carmen", "Javier", "Teresa", "Andres", "Isabel", "Miguel", "Dolores"]


class Community(council.Night):
    """Same HTTP actor helpers as Council night; a separate folder, tag and keep."""
    def __init__(self, out):
        self.out = out
        self.dir = tempfile.mkdtemp(prefix="watsonville-kits-")
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        self.k = Kernel(self.dir, {"tag": "wt", "name": "Watsonville Tenants Union",
            "steward": {"account": "google:marisol", "name": "Marisol"},
            "invites_counted_by": "kernel", "invites": [{"code": council.INVITE, "uses": 30}],
            "groups": [{"name": "Tenant organizing", "open": True}]})
        self.clock = council.Clock("2026-11-03T22:00Z")
        self.k.clock = self.clock
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.entry.sessions["marisol"] = {"account": "google:marisol", "method": "google"}
        self.tok = {"Marisol": "marisol"}
        self.pid = {"Marisol": self.k.accounts["google:marisol"]}
        self.checks, self.acts, self.refusals = [], [], []
        self.lock = threading.Lock()


def close(n):
    n.host.stop_all()
    for srv in (n.srv, n.entry.srv):
        srv.shutdown()
        srv.server_close()
    shutil.rmtree(n.dir, ignore_errors=True)


def run(out, shots=False):
    source = council.Night(out)
    target = None
    checks = []

    def check(name, ok, detail):
        checks.append({"number": len(checks) + 1, "check": name, "ok": bool(ok), "detail": detail})
        print(f"{len(checks):02d} {'ok' if ok else 'FAIL'} {name} · {detail}", flush=True)
        assert ok, (name, detail)

    def act(n, who, line):
        r = n.do(who, line)
        assert r["ok"], r
        return r

    try:
        source_evidence = Path(source.dir) / "evidence"
        check("Seabright runs the original Council night", council.main(["--out", str(source_evidence)], night=source,
              retain=True) == 0, "original 21 checks, unchanged assertions")
        s = source.k
        sg = next(g for g in s.things("group") if s.name(g) == "Council watch")
        # World-authored definitions supplement the existing council and floor lenses.
        definitions = [
            'verb prepare steps="agenda.load $*" help="Bring in our own posted agenda" may=leaders',
            'verb speak steps="claim $1" takes="<id>" help="Take a public comment slot"',
            'verb pulse steps="vote $1 $2" takes="<id> <option>" sealed=yes once="per person per target" help="Our sealed pulse poll"',
            'make kind=kind name=meeting help="A meeting with ordered items"',
            'make kind=kind name=item help="An item of a meeting"',
            'make kind=style name=community text="token paper = #FBFAF7"',
            'make kind=rule name=acknowledge on=pin do="look $target"',
        ]
        for line in definitions:
            act(source, "Dana", f"{line} in={sg}")
        kit = act(source, "Dana", f'kit {sg} name="Council watch"')["made"][0]
        bundle = act(source, "Dana", f"look {kit}")["rows"][0]["bundle"]
        kinds = {d["facts"]["kind"] for d in bundle["definitions"]}
        check("one kit gathers every definition class", kinds == {"word", "lens", "style", "rule", "kind"},
              f"{len(bundle['definitions'])} definitions: {sorted(kinds)}")
        shared = act(source, "Dana", f'post Council watch tools for another community about={kit}')["made"][0]
        feed = act(source, "Sam", "look")["rows"]
        check("sharing a kit is ordinary posting", any(r["id"] == shared for r in feed)
              and s.state.get(shared, "about") == kit, "ordinary post points to the kit")
        source_snapshot = s.state.snapshot()
        target = Community(out)
        w = target.k
        tg = w.things("group")[0]
        for i, name in enumerate(PEOPLE[1:]):
            target.sign_in(name, f"Watsonville block {i + 1}")
        act(target, "Marisol", f"role {target.pid['Lucia']} leader in={tg}")
        before = len(w.log.records)
        taken = act(target, "Lucia", f"take bundle={quoted(json.dumps(bundle, ensure_ascii=False))} in={tg}")
        copies = taken["made"]
        check("taking places new definitions in one act", len(w.log.records) == before + 1
              and len(copies) == len(bundle["definitions"]), f"{len(copies)} fresh wt things, one record")
        source_data = {t for t, a in s.state.things.items() if t != "world"
                       and a.get("kind") not in {"word", "lens", "style", "rule", "kind"}}
        copied_json = json.dumps([w.state.things[t] for t in copies])
        check("no source people, posts, phones or votes crossed", not source_data.intersection(w.state.things)
              and len(w.things("person")) == 15 and not w.things("post") and not w.things("poll")
              and "831-555" not in copied_json and "vote:" not in copied_json and "claim:" not in copied_json
              and not any(s.name(p) in copied_json for p in s.things("person")),
              "15 Watsonville people, zero imported posts/polls/claims/contacts")
        check("every definition remembers its origin", all(w.state.get(t, "origin") ==
              {"world": bundle["source"], "thing": d["id"]} for t, d in zip(copies, bundle["definitions"])),
              "source genesis digest and source definition id on every fresh copy")
        for name in ("agenda.load", "agenda.next"):
            help_ = act(target, "Lucia", f"help {name} in={tg}")
            refused = target.do("Lucia", f"{name} in={tg}" if name.endswith("load") else
                                f"help {name} in={tg}")
            check(f"{name} arrives unbound", "unbound" in help_["text"] and not w.things("module")
                  and (not refused["ok"] if name.endswith("load") else True), help_["text"].splitlines()[-1])
        prepare = w.find_entry("prepare", tg)
        act(target, "Lucia", f"look {prepare}")
        act(target, "Lucia", f'rename {prepare} word=organize aliases="preparar organizar" in={tg}')
        check("local rename and Spanish aliases leave Seabright alone", w.find_entry("preparar", tg) == prepare
              and w.find_entry("organizar", tg) == prepare and w.find_entry("organize", tg) == prepare
              and s.state.snapshot() == source_snapshot, "three local names; source snapshot unchanged")
        argv = quoted(json.dumps([council.NODE, str(LAB / "modules/agenda/agenda.js")]))
        no = target.do("Lucia", f'module agenda run={argv} grants="find look make set"')
        check("a group leader cannot run a module", not no["ok"] and "stewards" in no["text"], no["text"])
        act(target, "Marisol", f'module agenda run={argv} grants="find look make set"')
        assert target.host.wait_offered(w.module_named("agenda"))
        check("this community grants and runs its own module", target.host.running(w.module_named("agenda"))
              and "unbound" not in act(target, "Lucia", f"help agenda.load in={tg}")["text"],
              "local steward supplied executable and grants; none came from the kit")
        act(target, "Lucia", f"preparar agenda-watsonville.json in={tg}")
        meeting = w.things("meeting")[0]
        hearing = next(t for t in w.things("item") if w.state.get(t, "seats"))
        check("Spanish alias loads Watsonville's own evening", "Watsonville" in w.state.get(meeting, "title")
              and len(w.things("item")) == 3, "new meeting and three items from Watsonville fixture")
        with ThreadPoolExecutor(15) as ex:
            signed = list(ex.map(lambda nm: target.do(nm, f"speak {hearing} in={tg}"), PEOPLE))
        check("fifteen neighbours sign up for twelve comment slots", sum(r["ok"] for r in signed) == 12
              and w.shown(target.pid["Rosa"], hearing)["claims"] == 12, "12 admitted, 3 full refusals")
        poll = act(target, "Lucia", f'make kind=poll title="Ask for tenant protections?" options="yes no" in={tg}')["made"][0]
        with ThreadPoolExecutor(15) as ex:
            votes = list(ex.map(lambda pair: target.do(pair[1], f"pulse {poll} {'no' if pair[0] % 4 == 0 else 'yes'} in={tg}"),
                                enumerate(PEOPLE)))
        shown = w.shown(target.pid["Rosa"], poll)
        vote_records = [r for r in w.log.records if r.get("by") == "sealed"]
        check("fifteen sealed votes through the copied word", all(r["ok"] for r in votes) and shown["votes"] == 15
              and shown["votes_yes"] == 11 and shown["votes_no"] == 4 and len(vote_records) == 15
              and all(not any(re.search(rf"\b{p}\b", json.dumps(r)) for p in target.pid.values()) for r in vote_records),
              f"counts {shown}, admitted {sum(r['ok'] for r in votes)}, sealed records {len(vote_records)}")
        no = target.do("Rosa", f"pulse {poll} no in={tg}")
        check("copied words retain once-each", not no["ok"] and "already" in no["text"], no["text"])
        for _ in range(3):
            act(target, "Lucia", f"agenda.next {meeting} in={tg}")
        outcome = act(target, "Lucia", f'post We asked for tenant protections. Next organizing meeting Friday. in={tg} as=o; pin $o')
        pinned = outcome["made"][0]
        check("Watsonville pins its own outcome", w.state.get(pinned, "pinned") == target.pid["Lucia"],
              "local post pinned by Lucia")
        deadline = time.monotonic() + 3
        while not w.rules_fired and time.monotonic() < deadline:
            time.sleep(.02)
        copied_rule = next(t for t in copies if w.state.get(t, "kind") == "rule")
        check("the copied rule answers as its local maker", any(r[0] == copied_rule and "refused:" not in r[2]
              for r in w.rules_fired)
              and w.state.get(copied_rule, "made_by") == target.pid["Lucia"],
              "local acknowledgement rule read the local pinned outcome")
        page = target.scene("Rosa", "council")
        floor = target.scene("Lucia", "floor")
        check("copied phone views paint local activity", "Watsonville tenants" in page["text"]
              and "tenant protections" in page["text"] and "Next item" in floor["text"],
              "existing council and floor lenses, unchanged text")
        check("source remains independent after the evening", s.state.snapshot() == source_snapshot,
              "all source facts equal the snapshot before taking")
        for label, n in (("Seabright", source), ("Watsonville", target)):
            check(f"{label} replay is identical", Kernel(n.dir).state.snapshot() == n.k.state.snapshot(),
                  f"{len(n.k.log.records)} records replayed, exact snapshot equality")
        pictures = {}
        if shots:
            target.k.dev_sessions = lambda: target.entry.sessions
            for who, lens, filename in (("Rosa", "council", "kits-phone.png"), ("Lucia", "floor", "kits-floor-phone.png")):
                url = f"{target.url}/dev/signin?token={target.tok[who]}&next=/lens.html%3Flens%3D{lens}%26inspect%3D0"
                r = subprocess.run([sys.executable, str(LAB / "shoot.py"), url, str(out / filename),
                                    "--size", "390x1400", "--wait", "3"], capture_output=True, text=True, timeout=60)
                pictures[filename] = {"ok": r.returncode == 0, "size": "390x1400", "who": who,
                                      "said": (r.stdout or r.stderr)[-1500:]}
                check(f"headless phone screenshot: {lens}", r.returncode == 0, filename)
        evidence = {"story": "The first kits (a13319)", "labels": {"ran": "checks and counts below",
                    "read": "kernel contracts in SHAPE section 17", "imagined": "people, choices and agendas; no model called"},
                    "checks": checks, "passed": sum(c["ok"] for c in checks), "of": len(checks),
                    "worlds": {"Seabright": {"tag": s.tag, "records": len(s.log.records)},
                               "Watsonville Tenants Union": {"tag": w.tag, "records": len(w.log.records), "people": 15}},
                    "bundle": bundle, "copies": [{"id": t, "origin": w.state.get(t, "origin")} for t in copies],
                    "source_acts": source.acts, "target_acts": target.acts, "shots": pictures, "complete": True,
                    "council_night": json.loads((source_evidence / "council-night.json").read_text(encoding="utf-8"))}
        (out / "kits.json").write_text(json.dumps(evidence, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{evidence['passed']} of {evidence['of']} checks passed", flush=True)
        return evidence
    finally:
        if target:
            close(target)
        close(source)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--out", type=Path, default=PROOF / "evidence")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    run(a.out, a.shots)
    return 0


if __name__ == "__main__":
    sys.exit(main())
