"""Real isolated entry/door/widget/painter fixture, launched ONLY by runner.py.

Synthetic identity provisioning is fixture setup, not an account connection.
No StandInEntry, fake Kernel/Principal, mocked renderer, inference or live world.
Unexecuted source candidate: assertions are obligations, never evidence of pass.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from wsgiref.simple_server import make_server, WSGIRequestHandler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from runner import AdmissionLatch, verify


def Q(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    verify()
    work = Path(sys.argv[1]).resolve()
    require(work.is_relative_to(ROOT) and work.name.startswith("search-"), "fixture path")
    sys.path.insert(0, str(ROOT / "research/text-desk-lab/notation"))
    import guard_context
    deadline = time.monotonic() + 80
    # This is an attempt-owned failure receipt, never admission publication.
    # A partial/unreadable marker is UNKNOWN to the outer runner, never clear.
    def persist_loss(failures):
        (work / "admission-lost.json").write_text(json.dumps(failures), encoding="utf-8")

    admission = AdmissionLatch(on_loss=persist_loss)

    def gate(boundary):
        with admission.lock:
            if admission.closed:
                raise RuntimeError("fixture observations closed; no further host work")
            if time.monotonic() >= deadline:
                admission.lose(boundary, "80 second gate deadline exceeded")
                raise RuntimeError("80 second fixture gate deadline")
            admission.read(guard_context.read, boundary)

    checks = []
    result = {"ok": False, "checks": checks, "kind": "unexecuted until authorized"}
    # All imports which can initialize fixture state follow the unchanged gate.
    gate("fixture imports")
    sys.path[:0] = [str(ROOT / "research/kernel-lab"),
                    str(ROOT / "research/window-lab/kernel-desktop"),
                    str(ROOT / "research/community-app/site")]
    from agora_entry.config import Config
    from agora_entry.web import App
    from kernel.kernel import Kernel
    from kernel.door import EntryClient, Server, make_handler
    from kernel import modules as module_transport
    import kdesk
    from widget_browser import CDP
    secret = secrets.token_urlsafe(32)
    app = None
    servers = []
    browser = None
    cdp = None
    host = None
    auth_audit = {}
    auth_lock = threading.Lock()
    # Guard wrappers delegate to the actual transport, not an emulated module.
    # Its autonomous offer/see/do messages need admission as well as HTTP.
    ProductionModuleProcess = module_transport.ModuleProcess

    class GuardedModuleProcess(ProductionModuleProcess):
        def __init__(self, *args, **kwargs):
            gate("production module process creation")
            super().__init__(*args, **kwargs)

        def handle(self, message):
            gate("production module message: " + str(message.get("t")))
            return super().handle(message)

    module_transport.ModuleProcess = GuardedModuleProcess

    class Quiet(WSGIRequestHandler):
        def log_message(self, *args):
            pass

    def request(url, body, token=None, headers=None):
        gate("authenticated HTTP request")
        head = {"Content-Type": "application/json", **(headers or {})}
        if token:
            head["Authorization"] = "Bearer " + token
        req = urllib.request.Request(url, json.dumps(body).encode(), head)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    class Door:
        def __init__(self, url, token):
            self.url, self.token = url, token

        def raw(self, line, see=False, saw=None, extra=None):
            code, out = request(self.url + ("/see" if see else "/do"),
                                {"line": line, "saw": saw, **(extra or {})}, self.token)
            require(code == 200, "door HTTP status")
            return out

        def say(self, line):
            out = self.raw(line)
            require(out.get("ok"), "door refused: " + line.split()[0] + " " + out.get("text", ""))
            return out

        def rows(self, kind, **filters):
            line = "rows " + kind + "".join(" " + k + "=" + Q(v) for k, v in filters.items())
            out = self.raw(line, see=True)
            require(out.get("ok"), "rows refused")
            return out.get("rows", [])

    def check(name, condition):
        require(condition, name)
        checks.append(name)

    def wait(predicate, label, seconds=6):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            gate("bounded wait: " + label)
            value = predicate()
            if value:
                return value
            time.sleep(.05)
        raise AssertionError("timeout: " + label)

    try:
        gate("entry database and synthetic sign-in setup")
        cfg = Config(mode="test", base_url="http://127.0.0.1:1", data_dir=work / "entry",
                     secret_key=secrets.token_bytes(32), kernel_secret=secret,
                     google_mode="off", email_mode="file",
                     leaders=frozenset({"owner@example.invalid", "viewer@example.invalid",
                                        "other@example.invalid"}))
        cfg.check()  # no from_env/.env, SMTP, Google or real address
        app = App(cfg)
        identities = []
        for name in ("owner", "viewer", "other"):
            gate("synthetic one-use code redemption: " + name)
            rid, delivery = app.service.request_email_signin(name + "@example.invalid", None)
            # Service owns token hashing, single use and session verification.
            # Delivery is synthetic in-process test-mode data, never real email.
            token, account = app.service.redeem_code(rid, delivery["code"])
            identities.append((token, account["id"]))
        owner_token, owner_account = identities[0]
        gate("entry listener")
        def entry_wsgi(environ, start_response):
            gate("entry HTTP/session boundary")
            return app(environ, start_response)

        entry = make_server("127.0.0.1", 0, entry_wsgi, handler_class=Quiet)
        servers.append(entry)
        cfg.base_url = f"http://127.0.0.1:{entry.server_port}"
        threading.Thread(target=entry.serve_forever, kwargs={"poll_interval": .1}, daemon=True).start()
        gate("synthetic kernel genesis")
        py = str(Path(sys._base_executable).resolve())
        window_file = ROOT / "research/window-lab/kernel-desktop/kd_window.py"
        k = Kernel(work / "world", {"tag": "sh", "name": "Search acceptance synthetic",
                   "steward": {"account": owner_account, "name": "Fixture owner"},
                   "modules": [{"name": "window", "run": [py, "-B", str(window_file), "--headless"],
                                "publishes": "window.*", "for": "steward",
                                "grants": kdesk.WINDOW_GRANTS, "only": "kind:window"}]})
        client = EntryClient(cfg.base_url, secret, cache_s=0)
        Base = kdesk.make_desk_handler(k, client)

        class Handler(Base):
            # Admission stays checked on the host side, including requests
            # initiated by widget JS after a previously admitted input.
            def do_POST(self):
                gate("host POST effect/reading")
                return super().do_POST()

            def do_GET(self):
                gate("host GET")
                return super().do_GET()

            def _actor(self):
                # Observe the production resolver's actual return, without
                # manufacturing actors or changing its identity/authorization.
                actor, why = super()._actor()
                trace = self.headers.get("X-Search-Fixture-Trace")
                if trace:
                    accounts = [] if actor is None else [
                        account for account, person in k.accounts.items() if person == actor.person]
                    with auth_lock:
                        auth_audit.setdefault(trace, []).append(None if actor is None else {
                            "principal": actor.id, "person": actor.person,
                            "kind": actor.kind, "accounts": sorted(accounts)})
                return actor, why

        class JoinHandler(make_handler(k, client, secret)):
            def do_POST(self):
                gate("production join seam")
                return super().do_POST()

        gate("kernel listener")
        # Desktop handler deliberately has no keep/account shared secret.
        # Bootstrap uses the real kernel door on this same isolated listener,
        # then switches to the real desktop handler before any widget request.
        server = Server(("127.0.0.1", 0), JoinHandler)
        servers.append(server)
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .1}, daemon=True).start()
        for token, account in identities[1:]:
            code, out = request(origin + "/keep/account",
                                {"account": account, "name": "Synthetic viewer", "invite": {"admitted": True}},
                                headers={"X-Kernel-Secret": secret})
            require(code == 200 and out.get("person"), "real join seam")
        gate("complete bootstrap; bind desktop handler")
        server.RequestHandlerClass = Handler
        owner, viewer, other = [Door(origin, token) for token, _ in identities]
        viewer_id, other_id = [k.accounts[account] for _, account in identities[1:]]
        owner_id = k.accounts[owner_account]
        check("unknown bearer rejected", request(origin + "/see", {"line": "rows any"}, "not-a-session")[0] == 401)

        def authenticated(door, route, body):
            trace = secrets.token_hex(16)
            code, out = request(origin + route, body, door.token,
                                {"X-Search-Fixture-Trace": trace})
            with auth_lock:
                resolved = auth_audit.pop(trace, [])
            require(len(resolved) == 1 and resolved[0] is not None,
                    "exactly one production authenticated principal resolution")
            return code, out, resolved[0]

        code, owner_identity, owner_principal = authenticated(owner, "/see", {"line": "who"})
        check("canonical owner baseline", code == 200 and owner_identity.get("ok") is True
              and owner_principal == {"principal": owner_id, "person": owner_id,
                                      "kind": "person", "accounts": [owner_account]})
        code, viewer_identity, viewer_principal = authenticated(viewer, "/see", {"line": "who"})
        check("canonical viewer baseline", code == 200 and viewer_identity.get("ok") is True
              and viewer_principal == {"principal": viewer_id, "person": viewer_id,
                                       "kind": "person", "accounts": [identities[1][1]]}
              and viewer_principal != owner_principal)
        forged_identity = {"as": owner_id, "person": owner_id, "account": owner_account}
        code, forged, forged_principal = authenticated(viewer, "/see",
                                                       {"line": "who", **forged_identity})
        check("body forgery retains canonical viewer identity", code == 200
              and forged.get("ok") is True and forged_principal == viewer_principal
              and forged_principal != owner_principal)
        result["canonical_identity_baselines"] = {
            "owner": owner_principal, "viewer": viewer_principal, "forged": forged_principal}
        gate("only headless window module reconcile")
        host = module_transport.Host(k, ROOT / "research/kernel-lab")
        host.reconcile()
        wait(lambda: k.find_entry("window.open"), "headless window offer")
        spec = importlib.util.spec_from_file_location("search_fixture_install",
                ROOT / "research/kernel-lab/apps/smart-search/install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        ids = installer.install(owner)
        owner.say("look " + ids["component"])
        owner.say("component " + ids["component"])
        owner.say("look " + ids["widget"])
        owner.say("widget " + ids["widget"] + " grants=" + Q(installer.REQUIRED_GRANTS))
        # This activates ONLY a newly seeded fixture. No live object is read.
        check("installed component exact frozen bytes",
              hashlib.sha256(k.state.get(ids["component"], "code").encode()).hexdigest()
              == verify()["product_component_sha256"])
        check("installed generated painter exact frozen bytes",
              hashlib.sha256(k.state.get(ids["widget"], "code").encode()).hexdigest()
              == verify()["generated_widget_sha256"])
        entry_button = installer.entry(owner)
        check("one-click entry is evidence surface", owner.rows("button", name="smart-search-button")[0]["does"]
              == "window.open smart-search")
        marker = owner.say("make kind=note name=PRIVATE_FIELD_SENTINEL title=PRIVATE_TITLE_SENTINEL"
                           " label=PRIVATE_LABEL_SENTINEL text=visibilityneedle"
                           + "".join(" sees." + field + "=" + Q("person:" + other_id)
                                     for field in ("name", "title", "label")))["made"][0]
        private = owner.say("make kind=note name=WHOLE_PRIVATE_SENTINEL text=visibilityneedle sees="
                            + Q("person:" + other_id))["made"][0]
        target = owner.say("make kind=note name=PublicEvidence text=clickneedle")["made"][0]
        ui_revoked = owner.say("make kind=note name=UIRevocationEvidence text=uirevocationneedle")["made"][0]
        headers = {"X-Agora-Widget-Host": Handler.widget_broker.guard_key}

        def widget(door, action, body):
            code, out = request(origin + "/desk/widget/" + action, body, door.token, headers)
            require(code == 200, "widget HTTP status")
            return out

        opened = widget(viewer, "open", {"widget": ids["widget"]})
        require(opened.get("ok"), "authenticated module open")
        instance = opened["instance"]

        def module(line, see=False, saw=None, door=viewer, inst=instance):
            return widget(door, "call", {"instance": inst, "op": "see" if see else "do",
                                        "line": line, "saw": saw})

        hits = module('search "visibilityneedle" limit=50', see=True)
        encoded = json.dumps(hits)
        check("projected label/snippet excludes private fields", marker in encoded
              and all(sentinel not in encoded for sentinel in (
                  "PRIVATE_FIELD_SENTINEL", "PRIVATE_TITLE_SENTINEL", "PRIVATE_LABEL_SENTINEL"))
              and private not in encoded
              and "WHOLE_PRIVATE_SENTINEL" not in encoded)
        owner.say("look " + marker)
        owner.say("set " + marker + " sees=" + Q("person:" + other_id))
        check("visibility revocation affects existing module", marker not in json.dumps(
            module('search "visibilityneedle" limit=50', see=True)))
        check("module cannot change evidence", not module("set " + target + " text=UNAUTHORIZED").get("ok"))
        check("instance cannot be stolen by another viewer", not widget(other, "call",
              {"instance": instance, "op": "see", "line": "rows any"}).get("ok"))

        def windows():
            return owner.rows("window")

        def window_targets():
            return {row["id"]: row.get("target") for row in windows()}

        def created_window(before, after, wanted):
            added = set(after) - set(before)
            return (len(added) == 1 and not (set(before) - set(after))
                    and all(after[wid] == target for wid, target in before.items())
                    and after[next(iter(added))] == wanted)

        def wait_for_window_delta(before, wanted):
            current = window_targets()
            return current if created_window(before, current, wanted) else None

        # Owner-only operation has its own successful exact-effect baseline.
        # Neither who display text nor a generic HTTP 200 is an identity oracle.
        before_identity_action = window_targets()
        command = "window.open thing " + target + " new=yes"
        code, allowed, resolved = authenticated(owner, "/do", {"line": command})
        after_identity_action = window_targets()
        check("canonical owner can perform owner-only action", code == 200
              and allowed.get("ok") is True and resolved == owner_principal
              and created_window(before_identity_action, after_identity_action, target))
        code, refused, resolved = authenticated(viewer, "/do",
                                                {"line": command, **forged_identity})
        check("forged viewer refused owner-only action", code == 200
              and refused.get("ok") is False and resolved == viewer_principal
              and window_targets() == after_identity_action)

        owner_open = widget(owner, "open", {"widget": ids["widget"]})
        require(owner_open.get("ok"), "owner module open")
        owner_instance = owner_open["instance"]
        # The real window provider is owner-only. Prove it can admit a fresh
        # action before interpreting a stale refusal as a revision check.
        fresh = owner.rows("note", name="PublicEvidence")[0]
        before_fresh = window_targets()
        positive = module("window.open thing " + target + " new=yes", saw={target: fresh["rev"]},
                          door=owner, inst=owner_instance)
        after_fresh = window_targets()
        check("fresh owner evidence creates exact window delta",
              positive.get("ok") is True and created_window(before_fresh, after_fresh, target))
        result["fresh_action_window_delta"] = {wid: after_fresh[wid] for wid in set(after_fresh) - set(before_fresh)}
        old = owner.rows("note", name="PublicEvidence")[0]
        owner.say("look " + target)
        owner.say("set " + target + " text=clickneedle-updated")
        stale = module("window.open thing " + target + " new=yes", saw={target: old["rev"]},
                       door=owner, inst=owner_instance)
        check("real window.open stale revision fence", stale.get("ok") is False
              and any(word in str(stale).lower() for word in ("changed", "stale", "revision"))
              and window_targets() == after_fresh)
        for row in windows():
            owner.say("look " + row["id"])
            owner.say("window.close " + row["id"])
        before = window_targets()
        # Own-lens health is a real broker/principal/kernel exercise with
        # explicitly synthetic health inputs, not proof of browser watchdog.
        second = owner.say("make kind=lens name=foreign-fixture painter=components text="
                           + Q("root : smart-search"))["made"][0]
        foreign = module("component-action " + second + " path=root action=off")
        check("module recovery confined to own lens", not foreign.get("ok"))
        reports = Q(json.dumps([{"path": "root", "health": "stopped",
                                "last_error": "SYNTHETIC_HEALTH", "elapsed_ms": 1}]))
        n = len(k.log.records)
        for _ in range(2):
            require(module("component-health " + ids["lens"] + " data=" + reports).get("ok"), "health admission")
        from painter.health import reports_for
        local = reports_for(k, viewer_id, ids["lens"])
        check("quarantine is per viewer and not recorded",
              local["root"]["quarantined"] and len(k.log.records) == n
              and reports_for(k, other_id, ids["lens"]) == {})
        check("viewer cannot clear quarantine", not module(
              "component-action " + ids["lens"] + " path=root action=clear").get("ok"))
        require(module("component-action " + ids["lens"] + " path=root action=off").get("ok"), "own off")
        prefs = viewer.rows("view-preference")
        check("off preference private to viewer", bool(prefs) and not other.rows("view-preference"))
        require(module("component-action " + ids["lens"] + " path=root action=retry").get("ok"), "own retry")
        check("retry does not bypass quarantine", reports_for(k, viewer_id, ids["lens"])["root"]["quarantined"])
        # The pristine owner gets the real browser because the production
        # window provider is owner-only; the nonowner health stays quarantined.
        widget(viewer, "close", {"instance": instance})

        gate("headless browser creation inside inherited live job")
        profile = work / "browser-profile"
        profile.mkdir()
        edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        require(edge.is_file(), "existing Edge required; no alternate executable/install")
        browser = subprocess.Popen([str(edge), "--headless=new", "--inprivate", "--disable-gpu",
                    "--disable-sync", "--disable-extensions", "--disable-background-networking",
                    "--no-first-run", "--no-default-browser-check", "--remote-debugging-port=0",
                    "--user-data-dir=" + str(profile), "about:blank"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
        active = profile / "DevToolsActivePort"
        wait(active.is_file, "debug endpoint", seconds=10)
        port = int(active.read_text().splitlines()[0])  # PermissionError is final
        gate("CDP connection")
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=3) as response:
            pages = json.loads(response.read())
        cdp = CDP(next(p["webSocketDebuggerUrl"] for p in pages if p["type"] == "page"))
        contexts = set()

        def event(ev):
            if ev.get("method") == "Runtime.executionContextCreated":
                contexts.add(ev["params"]["context"]["id"])
            if ev.get("method") == "Runtime.executionContextDestroyed":
                contexts.discard(ev["params"]["executionContextId"])
            if ev.get("method") != "Fetch.requestPaused":
                return
            gate("browser request continuation")
            p = ev["params"]
            url = urlsplit(p["request"]["url"])
            allowed = url.scheme + "://" + url.netloc == origin
            if allowed:
                h = dict(p["request"].get("headers") or {})
                # Cookie enters the trusted HTTP request, never the iframe API.
                h["Cookie"] = "agora_session=" + owner.token
                if url.path.startswith("/desk/widget/"):
                    h.update(headers)
                cdp.send("Fetch.continueRequest", requestId=p["requestId"],
                         headers=[{"name": key, "value": str(value)} for key, value in h.items()])
            elif url.scheme in ("about", "blob", "data") and p.get("resourceType") == "Document":
                cdp.send("Fetch.continueRequest", requestId=p["requestId"])
            else:
                cdp.send("Fetch.failRequest", requestId=p["requestId"], errorReason="BlockedByClient")

        cdp.on_event = event

        def call(method, **params):
            gate("CDP " + method)
            return cdp.call(method, **params)

        call("Network.enable")
        call("Fetch.enable", patterns=[{"urlPattern": "*"}])
        call("Runtime.enable")
        call("Page.enable")
        call("Page.navigate", url=origin + "/desk/widget.html?widget=" + ids["widget"])

        def js(expression, context=None):
            value = call("Runtime.evaluate", expression=expression, awaitPromise=True,
                         returnByValue=True, **({"contextId": context} if context else {}))
            require(not value.get("exceptionDetails"), "real DOM evaluation")
            return value.get("result", {}).get("value")

        def find_context():
            for context in list(contexts):
                if js("!!document.querySelector('.smart-search')", context):
                    return context
            return None

        context = wait(find_context, "real frozen component mount", seconds=12)

        def search(query):
            js("(()=>{const i=document.querySelector('input[type=search]');i.value=" + json.dumps(query)
               + ";i.dispatchEvent(new Event('input',{bubbles:true}));"
               + "i.focus();return true})()", context)
            call("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter",
                 windowsVirtualKeyCode=13, text="\r")
            call("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter",
                 windowsVirtualKeyCode=13)
            wait(lambda: js("document.querySelector('[role=status]').textContent.includes('Word matches only')",
                            context), "real search completion")

        search("clickneedle")
        check("real UI search Enter has no action", window_targets() == before)
        check("real UI renders evidence", js("document.querySelector('.search-hit').textContent.includes('PublicEvidence')", context))
        # Freeze the displayed hit, then mutate its source using a second writer.
        owner.say("look " + target)
        owner.say("set " + target + " text=clickneedle-next")
        js("document.querySelector('.search-hit button').click()", context)
        wait(lambda: js("document.querySelector('[role=status]').textContent.includes('changed')", context),
             "fresh click abstention")
        check("real UI changed evidence abstains", window_targets() == before)
        search("clickneedle")
        js("document.querySelector('.search-hit button').click()", context)
        after_ui = wait(lambda: wait_for_window_delta(before, target),
                        "real evidence click into headless window")
        check("real click opens only requested evidence",
              created_window(before, after_ui, target))
        result["ui_action_window_delta"] = {wid: after_ui[wid] for wid in set(after_ui) - set(before)}
        # Independent UI-only record: it was never revoked by the earlier
        # module-only case. Keep its genuine rendered button/closure for the
        # stale click, without fabricating a gesture or bypassing the UI.
        search("uirevocationneedle")
        exact = module('search "uirevocationneedle" limit=50', see=True,
                       door=owner, inst=owner_instance)
        check("UI revocation source exact visible baseline", exact.get("ok") is True
              and [row["id"] for row in exact.get("rows", [])] == [ui_revoked])
        check("real UI evidence visible before revocation", js(
              "(()=>{const hits=[...document.querySelectorAll('.search-hit')];"
              "if(hits.length!==1||hits[0].querySelector('h2 button')?.textContent!=='UIRevocationEvidence')return false;"
              "globalThis.__searchRevocationButton=hits[0].querySelector('h2 button');"
              "return __searchRevocationButton.isConnected})()", context) is True)
        before_revoke_click = window_targets()
        owner.say("look " + ui_revoked)
        owner.say("set " + ui_revoked + " sees=" + Q("person:" + other_id))
        js("globalThis.__searchRevocationButton.click()", context)
        wait(lambda: js("document.querySelector('[role=status]').textContent.includes('no longer available')",
                        context), "real stale revoked-evidence click refusal")
        check("real UI revoked stale click has zero window delta", window_targets() == before_revoke_click)
        search("uirevocationneedle")
        refreshed = module('search "uirevocationneedle" limit=50', see=True,
                           door=owner, inst=owner_instance)
        check("real UI refreshed results exclude exact revoked evidence",
              refreshed.get("ok") is True and refreshed.get("rows") == []
              and js("document.querySelectorAll('.search-hit').length", context) == 0
              and window_targets() == before_revoke_click)
        # Stage an independent widget-off fixture BEFORE revoking the search
        # widget's grant. Never restore/broaden the revoked grant to test off.
        off_widget = owner.say("make kind=widget name=search-off-case component_lens=smart-search code="
                               + Q(k.state.get(ids["widget"], "code")))["made"][0]
        owner.say("look " + off_widget)
        owner.say("widget " + off_widget + " grants=" + Q(installer.REQUIRED_GRANTS))
        off_open = widget(other, "open", {"widget": off_widget})
        require(off_open.get("ok") is True, "independent off-case open")
        off_grants = owner.rows("grant", to=off_widget)
        require(any(not g.get("revoked") for g in off_grants), "off-case live authorization")
        # Revocation uses a different widget and its own positive baseline.
        final = widget(other, "open", {"widget": ids["widget"]})
        require(final.get("ok"), "final open")
        revocation_baseline = module('search "clickneedle" limit=50', see=True,
                                     door=other, inst=final["instance"])
        check("grant revocation authorized baseline", revocation_baseline.get("ok") is True
              and target in [r["id"] for r in revocation_baseline.get("rows", [])])
        grant = next(g for g in owner.rows("grant", to=ids["widget"]) if not g.get("revoked"))
        owner.say("look " + grant["id"])
        owner.say("set " + grant["id"] + " revoked=yes")
        denied = widget(other, "call", {"instance": final["instance"], "op": "see", "line": 'search "clickneedle"'})
        check("module grant revocation effective", denied.get("ok") is False)
        check("independent off-case grants still authorized",
              owner.rows("grant", to=off_widget) == off_grants)
        owner.say("look " + off_widget)
        off_baseline = module('search "clickneedle" limit=50', see=True,
                              door=other, inst=off_open["instance"])
        check("widget off immediate authorized success baseline", off_baseline.get("ok") is True
              and target in [r["id"] for r in off_baseline.get("rows", [])])
        owner.say("off " + off_widget)
        check("widget off invalidates existing instance", widget(other, "call",
              {"instance": off_open["instance"], "op": "see", "line": 'search "clickneedle" limit=50'}).get("ok") is False)
        # Disable the synthetic entry session using the real service store;
        # cache_s=0 prevents a cache lifetime from hiding session revocation.
        gate("synthetic session revocation")
        with app.store.connect() as conn:
            conn.execute("UPDATE accounts SET disabled_at=? WHERE id=?", (time.time(), identities[2][1]))
        check("entry account revocation rejects existing bearer",
              request(origin + "/see", {"line": "rows any"}, other.token)[0] == 401)
        gate("feature assertions complete")
        with admission.lock:
            require(not admission.failures, "no lost or unknown child admission")
            admission.closed = True  # refuse new host work before publishing the final child outcome
        result.update(ok=True, kind="actual host assertions if executed; not semantic acceptance",
                      entry="production App/Service/Seam", identity="production EntryClient",
                      module="production Widgets/Principal; caller-narrowed",
                      processes={"fixture": os.getpid(), "browser": browser.pid,
                                 "modules": [p.proc.pid for p in host.procs.values()]},
                      component_sha256=verify()["product_component_sha256"])
    except BaseException as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        # Host/thread/browser lifetime ends via the outer live Job only.
        # No subprocess kill, PID adoption, profile deletion or retry here.
        with admission.lock:
            admission.closed = True
            result["guard_observations"] = list(admission.observations)
            result["admission_failures"] = list(admission.failures)
            result["admission_observations_closed"] = True
            if admission.failures:
                result["ok"] = False
        result["cleanup_authority"] = "outer live Job; closure must be independently observed"
        (work / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        # Preserve processes until the outer owner observes the result and
        # performs its one owned cleanup. Never detach/delegate them.
        time.sleep(10)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
