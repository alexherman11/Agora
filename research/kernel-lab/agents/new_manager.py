"""Provision a fresh Rowan manager at reviewed local startup; never activate models.

Manifest: resident, approval, tasks (exactly three), soul and charter. Each text
has source, author, text and sha256; the soul's source starts with fresh:.
The local entry alone creates credentials. No archive or provider auth is read.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

APPROVAL = "Sentinel_46885ac60b708191a9048a25719ec998"
ACCOUNT = "desktop:rowan"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate(data):
    if not isinstance(data, dict) or set(data) != {"resident", "approval", "tasks", "soul", "charter"}:
        raise ValueError("manifest needs resident, approval, tasks, soul and charter only")
    if data["resident"] != "Rowan" or data["approval"] != APPROVAL:
        raise ValueError("only the approved fresh Rowan manager is supported")
    tasks = data["tasks"]
    if (not isinstance(tasks, list) or len(tasks) != 3
            or any(not isinstance(t, str) or not re.fullmatch(r"[a-z]+[0-9]+", t) for t in tasks)
            or len(set(tasks)) != 3):
        raise ValueError("exactly three distinct task IDs are required")
    for kind in ("soul", "charter"):
        item = data[kind]
        if not isinstance(item, dict) or set(item) != {"source", "author", "text", "sha256"}:
            raise ValueError(f"{kind} needs source, author, text and sha256")
        if any(not isinstance(v, str) or not v.strip() for v in item.values()):
            raise ValueError(f"{kind} contains empty text or attribution")
        if digest(item["text"]) != item["sha256"]:
            raise ValueError(f"{kind} hash mismatch")
    if not data["soul"]["source"].startswith("fresh:"):
        raise ValueError("Rowan is fresh; soul source must start fresh:")


def load_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(data)
    return data


def install(k, entry, data):
    """Startup only, before House starts. Return metadata, never credentials.

    Complete preflight precedes writes. Authority is enabled last; an interrupted
    installation remains asleep and can be resumed from its matching belongings.
    Existing/revoked authority and later runtime settings are never overwritten.
    """
    from kernel.kernel import Tx

    validate(data)
    fingerprint = digest(json.dumps(data, sort_keys=True, ensure_ascii=False))
    authority_path = k.keep_dir / "house-managers.json"
    with k.lock:
        alex = k.accounts.get("desktop:alex")
        if not alex or not k.is_steward(alex):
            raise ValueError("Alex must exist as the local steward")
        person = k.accounts.get(ACCOUNT)
        if person and (k.state.get(person, "kind") != "person" or k.name(person) != "Rowan"
                       or k.is_steward(person)):
            raise ValueError("existing Rowan identity conflicts or has steward powers")
        if any(k.name(p) == "Rowan" and p != person for p in k.things("person")):
            raise ValueError("ambiguous Rowan person")
        existing = [a for a in k.things("house-agent") if k.state.get(a, "name") == "Rowan"]
        if len(existing) > 1:
            raise ValueError("ambiguous Rowan house-agent")
        agent = existing[0] if existing else None
        if agent and (k.state.get(agent, "person") != person
                      or k.state.get(agent, "provision_manifest") != fingerprint):
            raise ValueError("existing Rowan provision differs; preserve it for review")
        if person and not agent and k.state.get(person, "joined_via") != {"channel": "approved fresh manager"}:
            raise ValueError("existing Rowan has no matching provisioning origin")
        settings = list(k.things("house-settings"))
        if len(settings) > 1:
            raise ValueError("ambiguous house-settings")
        if settings:
            maker = k.state.get(settings[0], "made_by")
            if maker != alex and not (k.state.get(maker, "kind") == "agent" and k.state.get(maker, "for") == alex):
                raise ValueError("house-settings is not owned by Alex")
        houses = [m for m in k.things("module") if k.state.get(m, "name") == "house"]
        if len(houses) != 1 or not k.state.get(houses[0], "on") or k.state.get(houses[0], "for") != alex:
            raise ValueError("one active House installed for Alex is required")
        house = houses[0]
        grant_ids = []
        if agent:
            try:
                grant_ids = json.loads(k.state.get(agent, "manager_grants", ""))
            except (ValueError, TypeError):
                raise ValueError("existing manager grant receipt is missing") from None
            if not isinstance(grant_ids, list) or len(grant_ids) != 3 or len(set(grant_ids)) != 3:
                raise ValueError("existing manager grant receipt conflicts")
        for index, task in enumerate(data["tasks"]):
            def matches(g):
                return (k.state.get(g, "kind") == "grant" and k.state.get(g, "to") == house
                        and k.state.get(g, "words") == "set" and k.state.get(g, "only") == "thing:" + task
                        and k.state.get(g, "where") == k.place and k.state.get(g, "by") == alex)
            if agent:
                grant = grant_ids[index]
                if not matches(grant) or k.state.get(grant, "revoked") or k.state.get(grant, "forgotten"):
                    raise ValueError("manager task grant was removed or revoked; preserve that decision")
            else:
                matches_now = [g for g in k.state.things if matches(g)]
                if len(matches_now) > 1 or any(k.state.get(g, "revoked") or k.state.get(g, "forgotten") for g in matches_now):
                    raise ValueError("manager task grant is ambiguous or revoked")
                grant_ids.append(matches_now[0] if matches_now else None)
        entry.check_manager_sessions(ACCOUNT)
        authorities = json.loads(authority_path.read_text(encoding="utf-8")) if authority_path.exists() else {}
        if not isinstance(authorities, dict):
            raise ValueError("manager authority file is not a mapping")
        expected = {"tasks": list(data["tasks"]), "enabled": True, "approval": APPROVAL}
        if person in authorities and authorities[person] != expected:
            raise ValueError("existing manager authority differs or is disabled")
        if person in authorities and not agent:
            raise ValueError("manager authority exists without matching Rowan provision")
        for other, spec in authorities.items():
            if other != person and (not isinstance(spec, dict) or set(spec.get("tasks", [])) & set(data["tasks"])):
                raise ValueError("task authority conflicts with another manager")
        false = ("", "no", "false", "0")
        for task in data["tasks"]:
            if k.state.get(task, "kind") not in ("task", "taskboard-task") or k.state.get(task, "forgotten"):
                raise ValueError("manifest names a missing or non-task item")
            for field in ("who", "lead"):
                if k.state.get(task, field, "") not in ("", "Rowan", person):
                    raise ValueError("task has a foreign owner or lead")
            if not agent:
                if any(k.state.get(task, f) for f in ("builder", "build_run", "build", "build_phase")):
                    raise ValueError("task is already claimed")
                if str(k.state.get(task, "lane", "")).lower() == "done":
                    raise ValueError("task is already finished")
                if str(k.state.get(task, "status", "")).lower() in ("paused", "held", "blocked", "cancelled", "canceled", "done"):
                    raise ValueError("task is held or finished")
                if any(str(k.state.get(task, f, "")).lower() not in false for f in
                       ("paused", "cancelled", "canceled", "permission_required", "approval_required", "blocked", "hold")):
                    raise ValueError("task is held")
        if agent:
            for kind in ("soul", "charter"):
                target = k.state.get(agent, kind)
                if (k.state.get(target, "text") != data[kind]["text"]
                        or k.state.get(target, "source") != data[kind]["source"]
                        or k.state.get(target, "source_author") != data[kind]["author"]):
                    raise ValueError("existing Rowan text differs; preserve it")
            for key, value in (("signer", "rowan"), ("provider", "codex"), ("model", "gpt-6.1-sol"),
                               ("reasoning", "medium"), ("wake_policy", "addressed")):
                if k.state.get(agent, key) != value:
                    raise ValueError("existing Rowan configuration differs; preserve it")
            if k.state.get(agent, "fallback_provider"):
                raise ValueError("Rowan must not acquire a provider fallback")
        # Ordinary grants, one independently narrowed grant per task. Never
        # restore a grant remembered by an existing provision after revocation.
        for index, task in enumerate(data["tasks"]):
            if grant_ids[index] is None:
                out = k.run(k.actor_for(alex), f"grant {house} words=set only=thing:{task}")
                if not out.get("ok") or len(out.get("made", [])) != 1:
                    raise ValueError("House task grant refused; installation stopped before authority enable")
                grant_ids[index] = out["made"][0]
        if person is None:
            person = k.join(ACCOUNT, "Rowan", invite={"channel": "approved fresh manager"})["person"]
        created = not bool(agent)
        if created:
            tx = Tx(k)
            tx.part("install", None, "install")
            order = len(k.log.records) + 1

            def thing(**facts):
                target = tx.mint()
                for key, value in facts.items():
                    tx.set(target, key, value)
                tx.set(target, "made_by", alex)
                tx.set(target, f"in:{k.place}", order)
                return target

            own = thing(kind="group", name="Rowan's things", open=False)
            tx.set(own, f"member:{person}", "leader")
            tx.set(own, f"member:{alex}", "leader")
            carried = {}
            for kind in ("soul", "charter"):
                item = data[kind]
                target = thing(kind=kind, name=f"Rowan's {kind}", text=item["text"],
                               source=item["source"], source_author=item["author"],
                               source_sha256=item["sha256"], approval=APPROVAL)
                tx.set(target, "made_by", person)
                tx.set(target, f"in:{k.place}")
                tx.set(target, f"in:{own}", order)
                tx.set(target, "sees", f"group:{own}")
                carried[kind] = target
            chat = thing(kind="chat", name="Talk with Rowan",
                         **{"with": f"{alex} {person}", "sees": f"person:{alex}|person:{person}"})
            previous = k.state.get(settings[0], "builder_capacity", "") if settings else ""
            setting = settings[0] if settings else thing(kind="house-settings", name="House settings")
            tx.set(setting, "builder_capacity", "3")
            agent = thing(kind="house-agent", name="Rowan", person=person, signer="rowan",
                          provider="codex", model="gpt-6.1-sol", reasoning="medium", speaks="text",
                          want="asleep", wake_policy="addressed", next_steps="on", role="manager",
                          chat=chat, provision_manifest=fingerprint, approval=APPROVAL,
                          previous_builder_capacity=str(previous), manager_grants=json.dumps(grant_ids), **carried)
            for task in data["tasks"]:
                tx.set(task, "who", "Rowan")
                tx.set(task, "lead", person)
            k._commit(tx, by=alex, words="install: approved fresh Rowan; three tasks, asleep")
        # Establish the represented builder actor without using another person's
        # session. LocalEntry persists both dedicated session records together.
        k.actor_for(person, "rowan-builder")
        entry.add_manager_sessions(ACCOUNT)
        if person not in authorities:
            authorities[person] = expected
            tmp = authority_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(authorities, indent=2), encoding="utf-8")
            os.replace(tmp, authority_path)
        return {"person": person, "agent": agent, "chat": k.state.get(agent, "chat"),
                "tasks": list(data["tasks"]), "grants": grant_ids, "created": created,
                "previous_builder_capacity": k.state.get(agent, "previous_builder_capacity", "")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    args = parser.parse_args()
    data = load_manifest(args.manifest)
    print(json.dumps({"resident": "Rowan", "tasks": data["tasks"], "approval": APPROVAL,
                      "want": "asleep", "provider": "codex"}))


if __name__ == "__main__":
    main()
