"""Read-only semantic version projection of the existing native journal.

No new log or writer. Linear scan is deliberate for this small experiment; a production
version belongs beside World replay, with an incrementally derived, rebuildable index.
"""

import json

from agora3.applications import VIEW
from agora3.world import Refusal, encoded


def witnesses(world, identities):
    selected = set(identities)
    result, previous = {}, {}
    with world.connection() as db:
        for row in db.execute("SELECT seq, version, body FROM events ORDER BY seq"):
            if row["version"] != 1:
                raise Refusal("Unknown journal version; cannot verify arrangement dependencies.")
            for obj in json.loads(row["body"])["objects"]:
                oid = obj["id"]
                if oid not in selected:
                    continue
                if VIEW in obj["facets"]:
                    value = obj["facets"][VIEW]
                    value = {
                        k: value.get(k)
                        for k in ("bounds", "subject", "open", "package", "build", "lease", "grant")
                    }
                else:
                    value = obj["facets"].get("agora.arrangement")
                payload = encoded(value)
                if previous.get(oid) != payload:
                    result[oid] = row["seq"]
                    previous[oid] = payload
    if set(result) != selected:
        raise Refusal("Missing arrangement dependency in journal.")
    return result
