"""Record existing evidence and frozen-file integrity; no inference or test reruns."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
manifest = json.loads((HERE / "freeze-manifest.json").read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
current = {p: sha(ROOT / p) for p in manifest["sha256"]}
changed = [p for p, h in current.items() if h != manifest["sha256"][p]]
assert changed == ["research/kernel-lab/modules/model/model.py"], changed
sys.path.insert(0, str(ROOT / "research/kernel-lab/modules/model"))
import smart_search as S

corpus = json.loads((HERE / "development-corpus.json").read_text(encoding="utf-8"))
prompt_hash = hashlib.sha256(
    S.prompt("QUERY_PLACEHOLDER", S.descriptors(corpus)).encode("utf-8")
).hexdigest()
assert prompt_hash == manifest["prompt_template_sha256"]
gate_epoch = 1793681351.0982292
evidence = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "Ready for independent review; not semantic acceptance or activation",
    "evidence_basis": "Prior observed outputs recorded in this worker session; not rerun here",
    "house_review": {
        "commit": "f14f92af2d992f2ba81aa8a82fddad061b8a1479",
        "checks": [
            {"scope": "chat and paint health", "printed": "23 passed in 1.16s",
             "report_sha256": "696bf4f6c01e030fb89479f6ea4a734b4390057893d21ff457a7bc32d779e4a4"},
            {"scope": "hidden desktop", "printed": "23 passed in 56.86s",
             "report_sha256": "d7ae8ccf056eb5e2191fa4164c37ba7c61bfb45934680137137f93f53cc66e93"}
        ],
        "tested_search_semantics": False,
        "covers_current_amendments": False
    },
    "prior_worker_pytest": {
        "printed": "2 failed, 22 passed, 2 warnings, 7 errors, 16 subtests passed in 2.58s",
        "failure_1": "Quota persistence default temp write denied; no retry or relocation",
        "errors_7": "Default pytest temp-fixture setup denied; no retry or relocation",
        "failure_2": "Pacific download-week ZoneInfo unavailable: pinned Python lacks tzdata",
        "response": "Read-only Win32 timezone fallback added; failed test not rerun",
        "cache_warnings": "WinError 5 creating pytest cache directories; no cleanup workaround"
    },
    "mocked_surface_contracts": {
        "printed": "SURFACE CONTRACTS: 6/6 passed (mock readings, no inference or browser)",
        "command": "node research/smart-search-lab/check_surface.mjs",
        "semantic_proof": False,
        "harness_note": "Initial assertion corrected to await async event completion; no product tuning"
    },
    "read_only_timezone_diagnostic": [
        ["2026-07-01T07:00:00+00:00", "2026-07-01"],
        ["2026-01-01T07:00:00+00:00", "2025-12-31"],
        ["2026-11-02T07:30:00+00:00", "2026-11-01"]
    ],
    "recorded_readiness": {
        "checked_at": gate_epoch,
        "checked_at_utc": datetime.fromtimestamp(gate_epoch, timezone.utc).isoformat(),
        "safe": False, "gaming_reasons": [], "idle_seconds": 0,
        "available_GiB": 4.5, "loaded": [],
        "requirements": "30 seconds idle, gaming gate clear, >=8 GiB free, no resident model for cold smoke",
        "inference_attempted": False,
        "current_status": "Historical snapshot only; not rechecked by this closeout"
    },
    "synthetic_inference": {
        "calls": 0, "semantic_quality": "unmeasured", "latency": "unmeasured",
        "prepared_smoke": {"records": 5, "prompt_characters": 1340, "lexical_ids": []},
        "supported_word_observed": "model.ask",
        "model_search_observed": "absent; not called",
        "held_out_evaluation": "not run; no independent cases received by builder"
    },
    "freeze": {
        "manifest": "freeze-manifest.json", "records": 36,
        "current_sha256": current, "prompt_template_sha256": prompt_hash,
        "changed_since_freeze": changed,
        "amendment": "Memory-only broker guard; prompt, corpus, retrieval and UI frozen hashes unchanged",
        "added_guard_sha256": sha(ROOT / "research/kernel-lab/modules/model/search_resources.py")
    },
    "resolver": "JEFF coordinates existing House independent checks, safe idle broker opportunity, serial review/landing and narrowly scoped activation; no new worker",
    "safe_now": ["Evidence review", "Source review", "Manifest verification",
                 "Independent blind case authoring without builder exposure"],
    "activation_contract": "ACTIVATION.md in research/kernel-lab/apps/smart-search; gates first, reviewed exact component digest, existing broker lifecycle/budgets, separate narrow widget grants, one ordinary window.open entry; no activation executed",
    "lookup_refusal": "Invalid dk829 optional chat lookup abandoned by JEFF instruction; no retry or alternate route",
    "no_commit_push_install_activation_or_settings_change": True
}
(HERE / "completion-evidence.json").write_text(
    json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Recorded prior evidence; frozen corpus/prompt/retrieval/UI integrity verified.")
print("Historical gate UTC:", evidence["recorded_readiness"]["checked_at_utc"])
