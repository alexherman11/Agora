"""Freeze corrected dependency + interim bytes for independent re-review only."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
APP = ROOT / "research/kernel-lab/apps/smart-search"
old_path = HERE / "correction-manifest.json"
old = json.loads(old_path.read_text(encoding="utf-8"))
paths = [
    "research/kernel-lab/kernel/words.py",
    "research/kernel-lab/kernel/kernel.py",
    "research/kernel-lab/kernel/store.py",
    "research/kernel-lab/kernel/lines.py",
    "research/kernel-lab/kernel/history.py",
    "research/kernel-lab/apps/smart-search/lexical.js",
    "research/kernel-lab/apps/smart-search/search.lens",
    "research/kernel-lab/apps/smart-search/install.py",
    "research/kernel-lab/painter/install.py",
    "research/kernel-lab/widgets/common.js",
    "research/kernel-lab/painter/primitives.js",
    "research/kernel-lab/painter/themed.js",
    "research/kernel-lab/painter/quarantine.js",
    "research/kernel-lab/painter/isolation.js",
    "research/kernel-lab/painter/painter.js",
    "research/smart-search-lab/correction-manifest.json",
    "research/smart-search-lab/check_search_projection.py",
    "research/smart-search-lab/freeze_projection_review.py",
]
sha = lambda b: hashlib.sha256(b).hexdigest()
hashes = {p: sha((ROOT / p).read_bytes()) for p in paths}
for path in paths:
    if path.startswith("research/kernel-lab/apps/smart-search/"):
        assert hashes[path] == old["file_sha256"][path], path
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("projection_review_install", APP / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
widget_digest = sha(installer.painter.widget_source(board_look=False).encode("utf-8"))
assert widget_digest == old["generated_widget_code_sha256"]
manifest = dict(
    version="search-projection-correction-3",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    rejection="User-reported independent review dk1757 rejected the prior lexical interim",
    scope="Corrected kernel dependency plus unchanged evidence-only interim, not release approval",
    file_sha256=hashes,
    normalized_text_sha256={p: sha((ROOT / p).read_text(encoding="utf-8").encode("utf-8"))
                            for p in paths},
    normalization="Raw bytes are exact worktree freeze; normalized UTF-8/LF hashes also supplied for House reconciliation. Any changed candidate needs independent re-review.",
    interim_manifest_sha256=sha(old_path.read_bytes()),
    component_review_sha256=old["component_review_sha256"],
    evidence_lens_text_sha256=old["evidence_lens_text_sha256"],
    generated_widget_code_sha256=widget_digest,
    requested_separate_widget_grants=old["requested_separate_widget_grants"],
    new_regression=dict(
        command="Pinned Python -B research/smart-search-lab/check_search_projection.py",
        before="Ran 8 tests in 0.007s; FAILED (failures=6)",
        after="Ran 8 tests in 0.004s; OK",
        basis="Actual Kernel.shown + search/find on synthetic in-memory State; persistent Kernel constructor never called",
    ),
    independent_feature_approval=False,
    generic_house_metadata_is_feature_approval=False,
    semantic_activation="HELD; parent incomplete",
    inference_calls=0,
    denied_fixture_retries=0,
    overlap="kernel/words.py is shared with Board/Documents; only search() changed. kernel/kernel.py projection, community-app/board/board.py and Documents/file processing untouched. JEFF/House must reconcile shared dependency serially and re-freeze on drift.",
)
out = HERE / "projection-review-manifest.json"
if out.exists():
    raise SystemExit("Already frozen; preserve review evidence")
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Frozen", out.name)
print("Corrected kernel words.py SHA-256:", hashes["research/kernel-lab/kernel/words.py"])
print("Prior interim manifest SHA-256:", manifest["interim_manifest_sha256"])
print("Generated widget digest unchanged:", widget_digest)
