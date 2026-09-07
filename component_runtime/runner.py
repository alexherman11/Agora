"""Disposable JavaScript evaluator. No host callbacks, filesystem, browser, or network API."""

import json
import sys

import quickjs


def run(request):
    ctx = quickjs.Context()
    ctx.set_memory_limit(32 * 1024 * 1024)
    ctx.set_max_stack_size(512 * 1024)
    ctx.set_time_limit(0.15)
    # Input and source enter as data; generated code receives no Python objects.
    ctx.set("sourceText", request["source"])
    ctx.set("inputText", json.dumps(request["context"], allow_nan=False))
    ctx.set("requestText", json.dumps(request.get("event"), allow_nan=False))
    ctx.set("actionName", request.get("action", ""))
    result = ctx.eval("""
    (() => {
      const stringify = JSON.stringify.bind(JSON);
      const input = JSON.parse(inputText), event = JSON.parse(requestText);
      const component = (0, eval)('(' + sourceText + '\\n)');
      if (!component || typeof component.render !== 'function')
        throw Error('source must evaluate to an object with render(ctx)');
      let result = {};
      if (actionName) {
        const fn = component.actions && component.actions[actionName];
        if (typeof fn !== 'function') throw Error('missing action implementation');
        result = fn(input, event || {}) || {};
      } else if (event) {
        if (typeof component.handle !== 'function') throw Error('missing handle(ctx,event)');
        result = component.handle(input, event) || {};
      }
      if (Object.prototype.hasOwnProperty.call(result, 'state')) input.state = result.state;
      if (Object.prototype.hasOwnProperty.call(result, 'local')) input.local = result.local;
      return stringify({...result, tree:component.render(input), local:input.local || {}});
    })()
    """)
    if len(result) > 500_000:
        raise ValueError("component output exceeds 500 KB")
    return result


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            result = run(json.loads(line))
        except Exception as exc:
            result = json.dumps({"runtime_error": str(exc)[:2000]})
        print(result, flush=True)
