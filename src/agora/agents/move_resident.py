"""Reviewed, opt-in resident provisioning; no archive or model access.

Supports Sable, then Pike with a reviewed Sable reply. `plan <manifest>` validates without touching a
world. The owner supplies that same manifest to kdesk --resident-manifest at a
safe startup after review. Installation leaves the resident asleep. No existing text,
session, provider, or resident configuration is overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(data)
    return data


def validate(data):
    fields = {"resident", "reviewed_by", "soul", "charter"}
    if data.get("resident") == "Pike":
        fields.add("sable_reply")
    if set(data) != fields:
        raise ValueError("manifest needs resident, reviewed_by, soul, charter; Pike also needs sable_reply")
    if data["resident"] not in ("Sable", "Pike"):
        raise ValueError("only Sable and Pike are approved for this mover")
    if data["resident"] == "Pike" and (
            not isinstance(data["sable_reply"], str) or not data["sable_reply"].strip()):
        raise ValueError("Pike needs the reviewed Sable reply reference")
    if not isinstance(data["reviewed_by"], str) or not data["reviewed_by"].strip():
        raise ValueError("owner review attribution is required")
    for kind, approval in (("soul", "T3"), ("charter", "T2")):
        item = data[kind]
        if not isinstance(item, dict) or set(item) != {"source", "author", "text", "sha256", "approval"}:
            raise ValueError(f"{kind} needs source, author, text, sha256, approval only")
        if any(not isinstance(v, str) or not v.strip() for v in item.values()):
            raise ValueError(f"{kind} contains empty provenance or text")
        if item["approval"] != approval or digest(item["text"]) != item["sha256"]:
            raise ValueError(f"{kind} approval or content hash does not match")
    # These are review attestations, not a substitute for the owner's reading.
    # The old JEFF charter cannot be silently reused as the approved T2 text.
    if "MOVING-IN T2" not in data["charter"]["source"]:
        raise ValueError("charter source must identify reviewed MOVING-IN T2 rules")
    if data["charter"]["author"] != "Alex":
        raise ValueError("the approved rules must credit Alex as author")


def install(k, entry, data):
    """Called by the local entry at startup, before House or any model runs."""
    from kernel.kernel import Tx

    validate(data)
    with k.lock:
        jeff = k.accounts.get("desktop:jeff")
        alex = k.accounts.get("desktop:alex")
        if not alex or not jeff:
            raise ValueError("Alex and JEFF must have moved in first")
        jeff_agents = [a for a in k.things("house-agent") if k.state.get(a, "person") == jeff]
        if len(jeff_agents) != 1 or k.state.get(jeff_agents[0], "next_steps") != "on":
            raise ValueError("JEFF continuity must be enabled first")
        name = data["resident"]
        signer = name.lower()
        account = f"desktop:{signer}"
        if name == "Pike":
            sable = k.accounts.get("desktop:sable")
            agents = [a for a in k.things("house-agent") if k.state.get(a, "person") == sable]
            reply = data["sable_reply"]
            if not sable or len(agents) != 1 or \
                    k.state.get(agents[0], "wake_policy") != "addressed" or \
                    k.state.get(agents[0], "next_steps") != "on" or \
                    k.state.get(reply, "kind") != "said" or \
                    (k.state.get(reply, "for") or k.state.get(reply, "made_by")) != sable or \
                    not str(k.state.get(reply, "text") or "").strip() or \
                    k.shown(alex, reply) is None:
                raise ValueError("Pike follows Sable's reviewed, visible reply and continuity")
        person = k.accounts.get(account)
        existing = [t for t in k.things("house-agent") if k.state.get(t, "name") == name]
        # Preflight before any new person, session or thing. Do not adopt namesakes.
        if any(k.name(p) == name and p != person for p in k.things("person")):
            raise ValueError(f"ambiguous {name} person; owner must resolve")
        if len(existing) > 1:
            raise ValueError(f"ambiguous {name} house-agent")
        entry.check_person_session(signer, account)
        if existing:
            agent = existing[0]
            if k.state.get(agent, "person") != person:
                raise ValueError(f"{name} house-agent belongs to another person")
            for kind in ("soul", "charter"):
                target = k.state.get(agent, kind)
                if not target or k.state.get(target, "import_sha256") != data[kind]["sha256"] or \
                        k.state.get(target, "source") != data[kind]["source"] or \
                        k.state.get(target, "source_author") != data[kind]["author"] or \
                        k.state.get(target, "approved_text") != data[kind]["approval"]:
                    raise ValueError("existing import differs; preserve it for owner review")
            # Correct the original mover's rules attribution without touching
            # the resident's current text or the original import provenance.
            charter = k.state.get(agent, "charter")
            author = k.state.get(charter, "made_by")
            if author not in (alex, person):
                raise ValueError("existing charter authorship differs; preserve it for owner review")
            if author == person:
                tx = Tx(k)
                tx.part("install", None, "install")
                tx.set(charter, "made_by", alex)
                k._commit(tx, by=alex, words=f"install: credit Alex for {name}'s approved rules")
            entry.add_person_session(signer, account)
            return agent
        if person is None:
            person = k.join(account, name, invite={"channel": "moving in"})["person"]
        # One record for the resident's belongings; source text stays byte-for-byte.
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

        own = thing(kind="group", name=f"{name}'s things", open=False)
        tx.set(own, f"member:{person}", "leader")
        tx.set(own, f"member:{jeff}", "leader")
        carried = {}
        for kind in ("soul", "charter"):
            item = data[kind]
            target = thing(kind=kind, name=f"{name}'s {kind}", text=item["text"],
                           source=item["source"], source_author=item["author"],
                           import_sha256=item["sha256"], approved_text=item["approval"],
                           import_reviewed_by=data["reviewed_by"])
            tx.set(target, "made_by", person if kind == "soul" else alex)
            tx.set(target, f"in:{k.place}")
            tx.set(target, f"in:{own}", order)
            tx.set(target, "sees", f"group:{own}")
            carried[kind] = target
        chat = thing(kind="chat", name=f"Talk with {name}",
                     **{"with": f"{alex} {person}", "sees": f"person:{alex}|person:{person}"})
        agent = thing(kind="house-agent", name=name, person=person, signer=signer,
                      provider="claude", model="claude-opus-5-5", reasoning="medium",
                      speaks="text", want="asleep", wake_policy="addressed",
                      next_steps="on", chat=chat, **carried)
        if name == "Pike":
            tx.set(agent, "move_after_reply", data["sable_reply"])
        k._commit(tx, by=alex, words=f"install: reviewed {name} move; asleep until owner activates")
        entry.add_person_session(signer, account)
        return agent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["plan"])
    parser.add_argument("manifest")
    args = parser.parse_args()
    data = load_manifest(args.manifest)
    print(json.dumps({"resident": data["resident"], "reviewed_by": data["reviewed_by"],
                      **({"sable_reply": data["sable_reply"]} if data["resident"] == "Pike" else {}),
                      "imports": {kind: {key: data[kind][key] for key in
                                  ("source", "author", "sha256", "approval")}
                                  for kind in ("soul", "charter")},
                      "want": "asleep", "wake_policy": "addressed",
                      "next_steps": "on", "old_cards": 0}, indent=2))


if __name__ == "__main__":
    main()
