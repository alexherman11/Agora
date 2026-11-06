"""Read-only process accounting for the kernel-owned system module.

OS seam: CIM reads counters, plus only matching helper-browser profile paths.
No window enumeration, command-line output, persistence, or termination.
All aggregation is pure and can be tested without probing the host.
"""
import json
import ntpath
import os
from pathlib import Path
import subprocess
import tempfile
import time

GROUPS = ("agora", "agora-helper-chrome", "other")
HELP = ("system.processes: read-only top 30 processes by working set, plus totals for ALL processes "
        "in agora (kernel and live descendant tree), agora-helper-chrome (Chrome/Edge with a verified "
        "Agora test/snap profile and their verified descendant trees), and other. Rows: name, pid, parent_pid, working_set, private_bytes "
        "(bytes), cpu_pct (percent of total machine CPU). Only helper profile folders are exposed; "
        "no titles or other command-line data. Samples refresh in the background every 30 seconds; "
        "Each refresh takes two CPU samples about 0.5 seconds apart, off the kernel lock. "
        "CPU stays unknown for new/reused PIDs and missing counters. "
        "Working sets can share pages; their sum is not unique physical RAM. An untraceable orphan "
        "stays other unless its helper profile proves ownership. This reading never ends processes.")


def profile_prefixes(here, home):
    repo = here.parents[2]
    main = repo.parent.parent if repo.parent.name == ".worktrees" else repo
    roots = {here / "state", main / "research/window-lab/kernel-desktop/state",
             main / ".worktrees", main / ".tmp", repo / ".tmp"}
    if home:
        roots.add(Path(home).parent.parent)  # this module's world, not arbitrary user data
    prefixes = [ntpath.normpath(str(p)) + "\\" for p in sorted(roots)]
    # These prefixes are the throwaway directories created by shoot.py and snap.py.
    prefixes += [ntpath.join(tempfile.gettempdir(), p) for p in ("kernel-shoot-", "agora-snap-")]
    return prefixes


def helper_profile(folder, prefixes):
    if not folder or not ntpath.isabs(folder) or not ntpath.splitdrive(folder)[0]:
        return None
    folder = ntpath.normpath(folder)
    return folder if any(folder.casefold().startswith(p.casefold()) for p in prefixes) else None


def collect(prefixes, timeout=8):
    """System-module sampling or explicit helper inventory; never at import."""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
         str(Path(__file__).with_suffix(".ps1"))],
        input=json.dumps({"prefixes": prefixes}), capture_output=True,
        encoding="utf-8", timeout=timeout, creationflags=0x08000000)
    if result.returncode:
        raise OSError("Process inventory unavailable")
    return json.loads(result.stdout)


def _number(value):
    return int(value) if value is not None else None


def helper_processes(raw, prefixes):
    """All verified helper-tree identities, including children lacking a profile flag.

    Birth times bind both the command-line reading and each parent link. Neither
    a browser's name alone nor a dead/reused parent is evidence of ownership.
    The returned birth times are internal, used again at the termination handle.
    """
    processes = {int(p["pid"]): p for p in raw["processes"]}
    browsers = {"chrome.exe", "msedge.exe"}
    direct = {int(p["pid"]): helper_profile(p.get("profile"), prefixes)
              for p in raw.get("profiles", [])
              if p.get("born") and processes.get(int(p["pid"]), {}).get("born") == p["born"]
              and processes[int(p["pid"])]["name"].lower() in browsers}
    found = {}
    for pid, row in processes.items():
        current, seen = pid, set()
        while current in processes and current not in seen:
            seen.add(current)
            child = processes[current]
            if not child.get("born"):
                break
            if current in direct:
                if direct[current]:
                    found[pid] = dict(row, profile=direct[current])
                break
            parent_id = int(child["parent_pid"])
            parent = processes.get(parent_id)
            if not parent or not parent.get("born") or int(parent["born"]) > int(child["born"]):
                break
            current = parent_id
    return found


def snapshot(raw, kernel_pid, prefixes, previous=None, elapsed=0, cpus=1):
    """Sanitize, classify and aggregate every row BEFORE selecting the top 30."""
    processes = {int(p["pid"]): p for p in raw["processes"]}
    helpers = helper_processes(raw, prefixes)

    def ours(pid):
        seen = set()
        while pid in processes and pid not in seen:
            if pid == kernel_pid:
                return True
            seen.add(pid)
            child = processes[pid]
            parent = processes.get(int(child["parent_pid"]))
            # A newer process reusing a dead parent's PID is not an ancestor.
            if not parent or not child.get("born") or not parent.get("born"):
                return False
            if int(parent["born"]) > int(child["born"]):
                return False
            pid = int(child["parent_pid"])
        return False

    rows = []
    for pid, p in processes.items():
        ticks = _number(p.get("cpu_ticks"))
        old = (previous or {}).get(pid)
        cpu = None
        if (old and p.get("born") and old.get("born") == p["born"] and
                ticks is not None and old.get("cpu_ticks") is not None and elapsed > 0):
            delta = ticks - int(old["cpu_ticks"])
            if delta >= 0:
                cpu = round(min(100, delta / 10_000_000 / elapsed / max(1, cpus) * 100), 2)
        # Win32_Process includes the idle pseudo-process: it isn't CPU consumed.
        if pid == 0:
            cpu = 0.0
        profile = helpers.get(pid, {}).get("profile")
        row = {"kind": "process", "name": p["name"], "pid": pid, "parent_pid": int(p["parent_pid"]),
               "working_set": _number(p.get("working_set")), "private_bytes": _number(p.get("private_bytes")),
               "cpu_pct": cpu,
               "group": "agora-helper-chrome" if profile else "agora" if ours(pid) else "other"}
        if profile:
            row["profile"] = profile
        rows.append(row)
    totals = []
    for group in GROUPS:
        members = [r for r in rows if r["group"] == group]
        total = {"kind": "process-total", "group": group, "count": len(members)}
        for key in ("working_set", "private_bytes", "cpu_pct"):
            known = [r[key] for r in members if r[key] is not None]
            total[key] = round(sum(known), 2) if key == "cpu_pct" else sum(known)
            total[key + "_unknown"] = len(members) - len(known)
        totals.append(total)
    return {"rows": sorted(rows, key=lambda r: (-(r["working_set"] or 0), r["pid"]))[:30],
            "totals": totals, "process_count": len(rows)}


class Reader:
    def __init__(self, kernel_pid, prefixes):
        self.kernel_pid, self.prefixes = kernel_pid, prefixes
        self.last = {"error": "Process inventory is warming up", "at": None}

    def sample(self):
        try:
            raw = collect(self.prefixes)
            previous = {int(p["pid"]): p for p in raw.get("previous", [])}
            data = snapshot(raw, self.kernel_pid, self.prefixes, previous, raw.get("elapsed", 0),
                            os.cpu_count() or 1)
            self.last = dict(data, at=time.time())
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            self.last = {"error": "Process inventory unavailable; no alternate access attempted", "at": time.time()}

    def loop(self, closed):
        while not closed.is_set():
            self.sample()
            closed.wait(30)


def response(data):
    if data.get("error"):
        return {"text": data["error"], "rows": [], "sampled_at": data.get("at")}
    rows = data["rows"] + data["totals"]
    text = [f"Sampled at {data.get('at')}; top {len(data['rows'])} of {data['process_count']} by working set.",
            "Bytes: working set / private. CPU: percent of machine; ? means unknown. Totals include all processes."]
    for r in rows:
        label = f"{r['name']} pid={r['pid']} parent={r['parent_pid']}" if r["kind"] == "process" else f"TOTAL ({r['count']})"
        text.append(f"{r['group']} {label}: {r['working_set']} / {r['private_bytes']} bytes; "
                    f"CPU {r['cpu_pct'] if r['cpu_pct'] is not None else '?'}%"
                    + (f"; profile={r['profile']}" if r.get("profile") else "")
                    + (f"; unknown counters WS/private/CPU={r['working_set_unknown']}/"
                       f"{r['private_bytes_unknown']}/{r['cpu_pct_unknown']}" if r["kind"] == "process-total" else ""))
    return {"text": "\n".join(text), "rows": rows, "sampled_at": data.get("at")}


def agora_memory(data):
    if data.get("error"):
        return {"value": "unavailable", "detail": data["error"]}
    totals = [r for r in data["totals"] if r["group"] != "other"]
    working = sum(r["working_set"] for r in totals)
    private = sum(r["private_bytes"] for r in totals)
    missing = sum(r["working_set_unknown"] + r["private_bytes_unknown"] for r in totals)
    return {"value": f"{working / 1024**3:.2f} GB",
            "detail": f"working set incl. helper Chrome; {private / 1024**3:.2f} GB private; "
                      f"{sum(r['count'] for r in totals)} processes; {missing} unknown memory counters; "
                      f"sampled at {data.get('at')} (shared pages may overlap)"}
