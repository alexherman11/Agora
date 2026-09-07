"""Run bounded JavaScript in a disposable interpreter process; validate all output.
Never: never gives generated code host callbacks, credentials, or direct world access."""

import json

from component_runtime.host import evaluate
from kernel import component_schema, component_tree


def execute(definition, context, event=None, action=""):
    request = {"source": definition["source"], "context": context, "event": event, "action": action}
    data = json.dumps(request, allow_nan=False)
    if len(data) > 1_500_000:
        raise ValueError("component input exceeds 1.5 MB")
    try:
        output = json.loads(evaluate(data))
    except (ValueError, TypeError) as exc:
        raise ValueError("component interpreter failed without valid output") from exc
    if "runtime_error" in output:
        raise ValueError(
            "component error: " + str(output.get("runtime_error", "interpreter failed"))
        )
    if not isinstance(output, dict) or set(output) - {
        "tree",
        "local",
        "state",
        "effects",
        "value",
        "selected",
    }:
        raise ValueError("component result allows tree, local, state, effects, value, selected")
    component_schema.bounded(output["local"], 32_000)
    if not isinstance(output["local"], dict):
        raise ValueError("local interaction state must be an object")
    if "state" in output:
        component_schema.shape(definition["state_schema"], output["state"])
    effects = output.get("effects", [])
    if not isinstance(effects, list) or len(effects) > 64:
        raise ValueError("at most 64 effects per interaction")
    if event is None and not action and (effects or "state" in output):
        raise ValueError("render must not request effects or persistent state changes")
    component_tree.validate(output["tree"])
    return output
