"""Lowering sketch (Pike, round six): a nested derive becomes named, printed steps (three-address code).

Not the lab compiler. It shows the printing rule: every intermediate gets a name from its place in the definition
(`off.1`, `off.2`), prints `name = op(inputs) = result`, and an `if` prints its test, inputs and the branch taken.
Operators are a table, so a new operator is one entry, not a branch.
    .venv/Scripts/python.exe research/object-facet-frontier/experiments/growth/lower.py
"""
import ast
import datetime as dt
import operator as op

OPS = {ast.Add: ("+", op.add), ast.Sub: ("-", op.sub), ast.Mult: ("×", op.mul), ast.Div: ("÷", op.truediv)}
CMP = {ast.Lt: ("<", op.lt), ast.LtE: ("<=", op.le), ast.Gt: (">", op.gt), ast.GtE: (">=", op.ge), ast.Eq: ("=", op.eq)}
FUNS = {"days": lambda n: dt.timedelta(days=n), "date": dt.date.fromisoformat, "weekday": lambda d: d.strftime("%a")}


def lower(name, src, env):
    steps, n = [], [0]

    def show(v):
        return v.isoformat() if isinstance(v, dt.date) else (f"{v.days}d" if isinstance(v, dt.timedelta) else str(v))

    def go(e, final=False):
        if isinstance(e, ast.Constant):
            return str(e.value), e.value
        if isinstance(e, ast.Name):                      # $week is written week here; the source is printed
            return f"{e.id} {show(env[e.id])}", env[e.id]
        if isinstance(e, ast.Call):
            args = [go(a) for a in e.args]
            v = FUNS[e.func.id](*[a[1] for a in args])
            label = f"{e.func.id}({', '.join(a[0] for a in args)})"
        elif isinstance(e, ast.BinOp):
            (la, lv), (ra, rv) = go(e.left), go(e.right)
            sym, f = OPS[type(e.op)]
            v, label = f(lv, rv), f"{la} {sym} {ra}"
        elif isinstance(e, ast.IfExp):                   # an if must be total, and it prints test, inputs and branch
            (ca, cv) = go(e.test)
            taken = e.body if cv else e.orelse
            ta, tv = go(taken)
            v, label = tv, f"if {ca} → {'then' if cv else 'else'} {ta}"
        elif isinstance(e, ast.Compare):
            (la, lv), (ra, rv) = go(e.left), go(e.comparators[0])
            sym, f = CMP[type(e.ops[0])]
            v, label = f(lv, rv), f"{la} {sym} {ra}"
        else:
            raise SyntaxError(f"not in the lens expression grammar: {type(e).__name__}")
        if final:
            steps.append(f"{name} = {label} = {show(v)}")
            return name, v
        n[0] += 1
        step = f"{name}.{n[0]}"
        steps.append(f"  {step} = {label} = {show(v)}")
        return step, v

    go(ast.parse(src, mode="eval").body, final=True)
    return steps


if __name__ == "__main__":
    env = {"start": dt.date(2027, 3, 29), "week": 6, "breakweek": 4, "pages": 575, "pace": 80,
           "due": dt.date(2026, 10, 2), "today": dt.date(2026, 10, 3), "done": False}
    for name, src in [
        ("dd", "start + days(7 * (week - 1) + 2 + (7 if week >= breakweek else 0))"),   # Juniper's course: off=45 by hand
        ("meetings", "pages / pace"),
        ("status", "'done' if done else ('late' if due < today else 'open')"),
    ]:
        print(f"derive {name} = {src}")
        print("\n".join(lower(name, src, env)), "\n")
