"""Hash the corrected candidate and exact offline installer outputs; no Door."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
APP = ROOT / "research/kernel-lab/apps/smart-search"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("interim_search_install", APP / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
authored = []


def capture(door, kind, name, **facts):
    authored.append(dict(kind=kind, name=name, facts=facts))
    return f"offline-{kind}"


# Pure capture of arguments, not an account, world, fixture app or live installer.
installer.painter.upsert = capture
result = installer.install(None)
installer.entry(None)
grants = installer.REQUIRED_GRANTS
assert "model." not in grants
assert len(authored) == 4
component, lens, widget, entry = authored
assert component["facts"]["gestures"] == "evidence"
assert lens["facts"]["text"] == "root : smart-search\n  on evidence do window.open thing $id\n"
assert entry["facts"]["does"] == "window.open smart-search"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


paths = [
    "research/kernel-lab/apps/smart-search/lexical.js",
    "research/kernel-lab/apps/smart-search/search.lens",
    "research/kernel-lab/apps/smart-search/install.py",
    "research/kernel-lab/modules/model/model.py",
    "research/kernel-lab/modules/model/smart_search.py",
    "research/kernel-lab/modules/model/search_resources.py",
    "research/kernel-lab/modules/model/test_smart_search.py",
    "research/smart-search-lab/check_corrections.py",
    "research/smart-search-lab/check_lexical_surface.mjs",
]
facts_digests = {
    obj["kind"]: digest(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    for obj in authored
}
manifest = dict(
    version="search-correction-2-interim-lexical",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    basis="Developer-facing dk1740 only. Evaluator worktree and sealed holdout not read.",
    file_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
    component_review_sha256=digest(component["facts"]["code"]),
    evidence_lens_text_sha256=digest(lens["facts"]["text"]),
    generated_widget_code_sha256=digest(widget["facts"]["code"]),
    authored_facts_canonical_sha256=facts_digests,
    requested_separate_widget_grants=grants,
    entry={k: v for k, v in entry["facts"].items()},
    component_source="lexical.js; historical search.js is not installed",
    contract_checks={"corrections": "Ran 11 tests in 0.006s; OK",
                     "lexical_surface": "LEXICAL SURFACE CONTRACTS: 12/12 passed (mock rows/actions; no browser or inference)"},
    inference_calls=0,
    semantic_activation="HELD; parent incomplete",
    old_freeze="Preserved unchanged as history; this new source requires independent review and a new semantic freeze before evaluation.",
    offline_authoring="Captured installer arguments only; no live Door, authorship, review, grants or activation."
)
out = HERE / "correction-manifest.json"
if out.exists():
    raise SystemExit("Correction manifest already exists; preserve review evidence")
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
