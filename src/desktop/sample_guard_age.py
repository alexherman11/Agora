"""Bounded read-only freshness receipt: no launch, admission retry or publication."""
import ctypes
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import guard_context as g


def main():
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetTickCount64.restype = ctypes.c_ulonglong
    rows = []
    for i in range(20):
        result = g.read()
        observation = result.get("observation", {})
        now = time.time()
        wall = now - observation["observed_at"] if "observed_at" in observation else None
        tick = ((int(kernel.GetTickCount64()) - observation["uptime_ms"]) / 1000
                if "uptime_ms" in observation else None)
        rows.append({
            "sample": i + 1, "read_at": now, "wall_age_s": wall, "tick_age_s": tick,
            "issuer_pid": observation.get("issuer_pid"),
            "observed_at": observation.get("observed_at"),
            "admitted": result["admitted"], "reason": result.get("reason"),
            "foreground_exe": observation.get("foreground_exe"),
            "foreground_hud": observation.get("foreground_hud"),
            "game": observation.get("game"),
            "notification_state": observation.get("notification_state"),
            "input_desktop": observation.get("input_desktop"),
        })
        if i < 19:
            time.sleep(1)
    ages = sorted(row["wall_age_s"] for row in rows if row["wall_age_s"] is not None)
    fresh = all(row["wall_age_s"] is not None and row["tick_age_s"] is not None
                and 0 <= row["wall_age_s"] <= g.MAX_AGE
                and 0 <= row["tick_age_s"] <= g.MAX_AGE for row in rows)
    print(json.dumps({
        "source": str(g.location()), "samples": rows, "all_20_fresh": fresh,
        "wall_age_min_s": ages[0] if ages else None,
        "wall_age_median_s": (ages[9] + ages[10]) / 2 if len(ages) == 20 else None,
        "wall_age_max_s": ages[-1] if ages else None,
        "distinct_observations": len({r["observed_at"] for r in rows}),
        "limit": "Freshness measurement only; admitted/reason retained, no run requested."
    }, indent=2))
    return 0 if fresh else 1


if __name__ == "__main__":
    sys.exit(main())
