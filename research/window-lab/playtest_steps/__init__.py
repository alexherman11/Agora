"""HUD steps discovered from files, with no shared registration list."""
from dataclasses import dataclass
from importlib import import_module, invalidate_caches
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Step:
    name: str
    description: str
    order: int
    needs: tuple
    script: Callable
    # Existing scripts assert during the press sequence, so their assertion
    # stays inside that callback. This describes the condition being checked.
    assertion: str
    budget: tuple[int, int] = (100, 300)


def discover(directory=None, package=__name__):
    """Load public .py files; numeric order, then name breaks ties predictably."""
    directory = Path(directory) if directory is not None else Path(__file__).parent
    invalidate_caches()
    steps = []
    seen = set()
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module = import_module(f"{package}.{path.stem}")
        step = getattr(module, "STEP", None)
        if not isinstance(step, Step):
            raise ValueError(f"{path.name}: export STEP = Step(...)")
        if not step.name or step.name in seen:
            raise ValueError(f"{path.name}: duplicate or empty step name {step.name!r}")
        if not isinstance(step.order, int) or isinstance(step.order, bool):
            raise ValueError(f"{path.name}: order must be an integer")
        if not callable(step.script) or not step.assertion:
            raise ValueError(f"{path.name}: script and assertion are required")
        if (len(step.budget) != 2 or not all(isinstance(n, (int, float)) for n in step.budget)
                or not 0 <= step.budget[0] <= step.budget[1]):
            raise ValueError(f"{path.name}: budget must be (aim_ms, slow_ms)")
        seen.add(step.name)
        steps.append(step)
    return sorted(steps, key=lambda step: (step.order, step.name))
