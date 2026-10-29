"""Small, bounded boolean readings for world-authored see words (SHAPE 15).

This is deliberately not Python eval. Only literals, boolean operators, equality,
field(name), used(word, target) and digest(text) are understood. A result is always
a boolean; no function can read another person's sealed use.
"""
import ast
import hashlib

from .kernel import Refused


def _num(x):
    """A number from a fact (facts from lines are text: "6"), or None."""
    if isinstance(x, bool) or x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def evaluate(k, person, target, expression, value="", policy=False, row=None):
    """`row`, when given, is the thing's facts to judge (a kind's promise judges what an act would leave)."""
    if len(expression) > 2048:
        raise Refused("test's expression is too long")
    try:
        root = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise Refused("test needs a boolean expression; help test says how") from exc
    if sum(1 for _ in ast.walk(root)) > 128:
        raise Refused("test's expression is too large")

    def field(name):
        # Only a policy evaluating its own target sees its raw, non-sealed facts.
        # A normal reading sees exactly the same facts as look.
        if not isinstance(name, str) or name.startswith(("like:", "vote:", "claim:", "contact:", "sees")):
            return None
        facts = row if row is not None else (k.state.things.get(target, {}) if policy else (k.shown(person, target) or {}))
        return facts.get(name)

    def used(word, thing):
        if not isinstance(word, str) or not isinstance(thing, str):
            return False
        eid = k.find_entry(word, (k.groups_of(thing) or [k.place])[0])
        return bool(eid and k.used(person, eid, thing))

    functions = {"field": field, "used": used, "num": _num,
                 "has": lambda name: field(name) not in (None, ""),
                 "digest": lambda s: hashlib.sha256(str(s).strip().casefold().encode()).hexdigest()}

    def visit(n):
        if isinstance(n, ast.Constant) and type(n.value) in (str, bool, int, type(None)):
            return n.value
        if isinstance(n, ast.Name) and n.id in ("value", "target"):
            return value if n.id == "value" else target
        if isinstance(n, ast.BoolOp) and isinstance(n.op, (ast.And, ast.Or)):
            return all(bool(visit(x)) for x in n.values) if isinstance(n.op, ast.And) else any(
                bool(visit(x)) for x in n.values)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not visit(n.operand)
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.Eq, ast.NotEq)):
            same = visit(n.left) == visit(n.comparators[0])
            return same if isinstance(n.ops[0], ast.Eq) else not same
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.Lt, ast.Gt, ast.LtE, ast.GtE)):
            a, b = _num(visit(n.left)), _num(visit(n.comparators[0]))
            if a is None or b is None:
                return False                     # only numbers compare; num(field('panels')) <= 6
            op = n.ops[0]
            return a < b if isinstance(op, ast.Lt) else a > b if isinstance(op, ast.Gt) else \
                a <= b if isinstance(op, ast.LtE) else a >= b
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in functions and not n.keywords:
            try:
                return functions[n.func.id](*(visit(x) for x in n.args))
            except (TypeError, ValueError) as exc:
                raise Refused("test's function arguments do not match; help test says how") from exc
        raise Refused("test understands literals, and/or/not, ==/!=, < > <= >= on numbers, field, has, num, used and "
                      "digest only")

    result = visit(root.body)
    if type(result) is not bool:
        raise Refused("a test must answer yes or no")
    return result
