"""Experimental adapter for the existing Agora4 gateway; not a second store writer.

The tested planner model prepares data. Only Gateway.commit changes the native world.
"""

import hashlib
import json
from copy import deepcopy

import agora3.applications as applications_module
from agora3.applications import VIEW
from agora3.gateway import Gateway
from agora3.schemas import validate
from agora3.world import Refusal, encoded
from field_witnesses import witnesses
from model import Lab, key
from model import Refusal as PlanRefusal
from rendered_observation import observe
from surface_planning import contribute, plan_surface

REVISION = "v3"
STATE = "agora.arrangement.desk"
STATE_FACET = "agora.arrangement"
INTENT = "agora.arrangement-intent"

# Prototype the single additive application-data branch without editing Agora4.
# Applications.dispatch has already checked installation, open state and exact lease.
# This branch computes only over caller-supplied data: no world reads or writes.
_stock_application_request = applications_module.request


def application_request(gateway, actor, obj, method, args):
    if method == "arrangement.plan":
        return gateway.dispatch(actor, "arrangement.plan", args)
    return _stock_application_request(gateway, actor, obj, method, args)


applications_module.request = application_request


def spec(name, description, properties, required=()):
    return {
        "name": "arrangement." + name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": list(required),
            "additionalProperties": False,
        },
    }


SPECS = [
    spec(
        "observe",
        "Read actual rendered desktop appearances keyed by occurrence ID: local bounds, stacking, and differences from a stable native snapshot. Read-only. Use after apply/undo or reload to distinguish committed changes from rendered changes. A false match can be transient; inspect differences before acting. This checks geometry, not content legibility.",
        {},
    ),
    spec(
        "plan",
        'Pure shared planner for application-owned freeform surfaces. Also callable inside an application via AgoraApp.request("arrangement.plan", {snapshot,operations}), through the existing authenticated lease; no shell bridge is needed. snapshot: {contract:"freeform/v1",surface:string,items:[{id:occurrence ID,subject:subject ID,bounds:[x,y,w,h],minimum:[w,h]}],order:[all occurrence IDs bottom-to-top],viewport:{width:number,height:number}}. operations use the same tile/place/sink/raise shape as arrangement.prepare. Returns semantic effects and input digest, writes nothing. An application adapter retains its own data schema, membership, revision guards and authenticated commit action. This does not create a board or apply a desktop plan. Ordered lists keep their own order policy.',
        {
            "snapshot": {"type": "object"},
            "operations": {
                "type": "array",
                "minItems": 1,
                "maxItems": 100,
                "items": {"type": "object"},
            },
        },
        ["snapshot", "operations"],
    ),
    spec(
        "inspect",
        "Inspect the desktop arrangement: occurrence IDs, shared subjects, titles, tags, retained bounds, bottom-to-top stack and actual viewport. These IDs address appearances, not subjects.",
        {},
    ),
    spec(
        "prepare",
        'Prepare a zero-write, atomic desktop arrangement. operations: [{operator:"tile",targets:[view IDs],region:[x,y,width,height],columns:2}, {operator:"place",target:view ID,bounds:[x,y,width,height]}, {operator:"sink"|"raise",targets:[view IDs]}]. Operations share one snapshot, unequal writes conflict, stacking constraints join. Coordinates are local to the desk stage. This is a one-time arrangement, not a maintained rule. Returns a pinned plan ID and proposed effects. Must apply separately.',
        {
            "operations": {
                "type": "array",
                "minItems": 1,
                "maxItems": 30,
                "items": {"type": "object"},
            },
            "reason": {"type": "string", "maxLength": 2000},
        },
        ["operations", "reason"],
    ),
    spec(
        "apply",
        "Accept the exact prepared plan as one native intent, atomically updating every appearance and stacking relation. A stale plan refuses all changes. Retrying its ID returns the accepted receipt. Retain the returned intent ID for undo.",
        {"plan": {"type": "string"}},
        ["plan"],
    ),
    spec(
        "undo",
        "Undo one accepted arrangement intent as a new atomic compensation, preserving document content and editor state. Refuses atomically if affected layout or view binding changed afterward, including changes later reverted to the same value.",
        {"intent": {"type": "string"}},
        ["intent"],
    ),
]


def render_source(source):
    source = deepcopy(source)
    source["files"]["arrangement.js"] = """(() => {
      let active=false;
      async function sync(){ if(active)return; active=true;
        try {const state=await window.AgoraDesktop.request('arrangement.inspect',{});
          state.order.forEach((id,i)=>{const el=document.querySelector('[data-view="'+id+'"]');
            if(el)el.style.zIndex=String(i+10);});
        }catch(e){console.error('Arrangement stack: '+e.message)}finally{active=false;}}
      setInterval(sync,1200); sync();
    })();"""
    source["manifest"]["ui"]["scripts"].append("arrangement.js")
    return source


class Arrangements:
    def __init__(self, gateway):
        self.g = gateway
        self.plans = {}
        self.browser = None

    def seed(self, actor):
        try:
            self.g.world.get(STATE)
        except Refusal:
            ids = [v["id"] for v in self.g.applications.rows() if v["facets"][VIEW]["open"]]
            self.g.commit(
                actor,
                [
                    {
                        "id": STATE,
                        "expected_revision": 0,
                        "facets": {STATE_FACET: {"order": ids, "contract": REVISION}},
                    }
                ],
                internal=True,
            )

    def frame(self):
        if self.browser is None:
            return None
        return self.browser.call(
            op="evaluate",
            expression="""(() => {
            const n=document.getElementById('board'); if(!n)return null;
            const r=n.getBoundingClientRect(); return {width:n.clientWidth,height:Math.max(0,innerHeight-r.top),x:r.x,y:r.y};})()""",
        )

    def inspect(self):
        rows = [v for v in self.g.applications.rows() if v["facets"][VIEW]["open"]]
        state = self.g.world.get(STATE)
        ids = [v["id"] for v in rows]
        order = [x for x in state["facets"][STATE_FACET]["order"] if x in ids]
        order += [x for x in ids if x not in order]
        items = []
        for row in rows:
            view = row["facets"][VIEW]
            subject = self.g.world.get(view["subject"])
            items.append(
                {
                    "id": row["id"],
                    "revision": row["revision"],
                    "subject": view["subject"],
                    "title": subject["facets"].get("core.title", {}).get("text"),
                    "metadata": {
                        k: v
                        for k, v in subject["facets"].items()
                        if k not in ("core.text", "core.title")
                    },
                    "bounds": view["bounds"],
                    "package": view["package"],
                }
            )
        return {
            "surface": "desk",
            "contract": REVISION,
            "items": items,
            "order": order,
            "viewport": self.frame(),
            "capabilities": ["tile", "place", "sink", "raise", "prepare", "apply", "undo"],
            "limits": [
                "One native desktop adapter; application surfaces use pure arrangement.plan",
                "No maintained layout",
            ],
        }

    def prepare(self, actor, args):
        with self.g.lock:
            self.g.check_authority(actor)
            snapshot = self.inspect()
            frame = snapshot["viewport"]
            if not frame:
                raise Refusal("Open the actual desk before planning measured layout.")
            rows = {item["id"]: self.g.world.get(item["id"]) for item in snapshot["items"]}
            state = self.g.world.get(STATE)
            data = {
                key("surface", "desk", "members"): list(rows),
                key("surface", "desk", "contract"): REVISION,
                key("surface", "desk", "parent"): None,
                key("surface", "desk", "stack:normal"): snapshot["order"],
            }
            for oid, row in rows.items():
                value = row["facets"][VIEW]
                data[key("occurrence", oid, "binding")] = {
                    "surface": "desk",
                    "subject": value["subject"],
                    "incarnation": value["build"],
                }
                data[key("occurrence", oid, "placement")] = {
                    "mode": "free",
                    "rect": [value["bounds"][k] for k in ("x", "y", "width", "height")],
                }
                data[key("occurrence", oid, "minimum")] = [220, 180]
                data[key("occurrence", oid, "stratum")] = "normal"
            lab = Lab(data)
            lab.observe(
                "browser",
                {
                    "surface": "desk",
                    "width": frame["width"],
                    "height": frame["height"],
                    "active": True,
                    "transform": [1, 0, 0, 1, 0, 0],
                },
            )
            b = lab.builder(actor.name)
            try:
                contribute(b, "desk", args["operations"], "browser")
                plan = b.finish(register=False)
            except (PlanRefusal, KeyError, TypeError, ValueError) as exc:
                raise Refusal(str(exc)) from None
            effects = []
            for address, payload in plan.effects:
                value = json.loads(payload)
                if address[0] == "occurrence":
                    oid = address[1]
                    bounds = dict(zip(("x", "y", "width", "height"), value["rect"], strict=True))
                    self.g.applications.bounds(bounds)
                    effects.append(
                        {
                            "id": oid,
                            "facet": VIEW,
                            "field": "bounds",
                            "before": rows[oid]["facets"][VIEW]["bounds"],
                            "after": bounds,
                        }
                    )
                else:
                    effects.append(
                        {
                            "id": STATE,
                            "facet": STATE_FACET,
                            "field": "order",
                            "before": state["facets"][STATE_FACET]["order"],
                            "after": value,
                        }
                    )
            record = {
                "actor": actor.name,
                "generation": actor.generation,
                "contract": REVISION,
                "reason": args["reason"],
                "operations": args["operations"],
                "effects": effects,
                "members": list(rows),
                "frame": frame,
                "guards": witnesses(self.g.world, list(rows) + [STATE]),
            }
            token = hashlib.sha256(encoded(record).encode()).hexdigest()
            self.plans[token] = record
            return {
                "plan": token,
                "reason": record["reason"],
                "effects": effects,
                "native_writes": 0,
                "contract": REVISION,
            }

    def apply(self, actor, token):
        with self.g.lock:
            self.g.check_authority(actor)
            intent_id = "agora.arrangement.intent." + token
            try:
                accepted = self.g.world.get(intent_id)
                if accepted["facets"][INTENT]["actor"] != actor.name:
                    raise Refusal("Intent belongs to another actor.")
                return {"intent": intent_id, "event": accepted["event"], "already_applied": True}
            except Refusal:
                pass
            if token not in self.plans:
                raise Refusal("Plan expired or unknown; prepare a new one.")
            plan = self.plans[token]
            if (actor.name, actor.generation) != (plan["actor"], plan["generation"]):
                raise Refusal("Plan belongs to another authority context.")
            current = self.inspect()
            if [i["id"] for i in current["items"]] != plan["members"] or current[
                "viewport"
            ] != plan["frame"]:
                raise Refusal("The membership or measured viewport changed; prepare again.")
            if witnesses(self.g.world, plan["guards"]) != plan["guards"]:
                raise Refusal("Stale layout or binding snapshot; prepare again.")
            changes = []
            receipts = []
            next_event = self.g.world.query(limit=1)["watermark"] + 1
            for effect in plan["effects"]:
                obj = self.g.world.get(effect["id"])
                value = deepcopy(obj["facets"][effect["facet"]])
                value[effect["field"]] = effect["after"]
                changes.append(
                    {
                        "id": obj["id"],
                        "expected_revision": obj["revision"],
                        "facets": {effect["facet"]: value},
                    }
                )
                receipts.append(
                    {
                        **effect,
                        "post_witness": next_event
                        if effect["before"] != effect["after"]
                        else plan["guards"][obj["id"]],
                    }
                )
            changes.append(
                {
                    "id": intent_id,
                    "expected_revision": 0,
                    "facets": {
                        INTENT: {
                            "reason": plan["reason"],
                            "operations": plan["operations"],
                            "effects": receipts,
                            "actor": actor.name,
                            "undone": False,
                        }
                    },
                }
            )
            result = self.g.commit(
                actor,
                changes,
                internal=True,
                guards={oid: self.g.world.get(oid)["revision"] for oid in plan["guards"]},
            )
            return {
                "intent": intent_id,
                "event": result["watermark"],
                "changed": len(receipts),
                "reason": plan["reason"],
            }

    def undo(self, actor, intent_id):
        with self.g.lock:
            self.g.check_authority(actor)
            obj = self.g.world.get(intent_id)
            intent = obj["facets"].get(INTENT)
            if not intent:
                raise Refusal("Not an arrangement intent")
            if intent["undone"]:
                return {"intent": intent_id, "already_undone": True}
            changes = []
            current_witnesses = witnesses(self.g.world, [e["id"] for e in intent["effects"]])
            for effect in intent["effects"]:
                current = self.g.world.get(effect["id"])
                if current_witnesses[current["id"]] != effect["post_witness"]:
                    raise Refusal(
                        "Undo conflicts with a later layout or binding edit: " + current["id"]
                    )
                value = deepcopy(current["facets"][effect["facet"]])
                value[effect["field"]] = effect["before"]
                changes.append(
                    {
                        "id": current["id"],
                        "expected_revision": current["revision"],
                        "facets": {effect["facet"]: value},
                    }
                )
            changes.append(
                {
                    "id": intent_id,
                    "expected_revision": obj["revision"],
                    "facets": {INTENT: {**intent, "undone": True}},
                }
            )
            result = self.g.commit(actor, changes, internal=True)
            return {
                "undone": intent_id,
                "event": result["watermark"],
                "restored": len(intent["effects"]),
            }


class ArrangementGateway(Gateway):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrangements = Arrangements(self)

    def describe(self):
        return super().describe() + SPECS

    def dispatch(self, actor, name, args):
        if name.startswith("arrangement."):
            self.check_authority(actor)
            definition = next((s for s in SPECS if s["name"] == name), None)
            if definition is None:
                raise Refusal("Unknown arrangement operation")
            validate(definition["input_schema"], args)
            if name == "arrangement.plan":
                try:
                    return plan_surface(args["snapshot"], args["operations"])
                except (PlanRefusal, KeyError, TypeError, ValueError) as exc:
                    raise Refusal("Invalid freeform snapshot or operations: " + str(exc)) from None
            if name == "arrangement.inspect":
                return self.arrangements.inspect()
            if name == "arrangement.observe":
                return observe(self.arrangements)
            if name == "arrangement.prepare":
                return self.arrangements.prepare(actor, args)
            if name == "arrangement.apply":
                return self.arrangements.apply(actor, args["plan"])
            if name == "arrangement.undo":
                return self.arrangements.undo(actor, args["intent"])
            raise Refusal("Unknown arrangement operation")
        return super().dispatch(actor, name, args)
