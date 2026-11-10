"""Read-only Codex resident readiness: no model turn, login, token copy or repin."""

import argparse
import hashlib
import json
import tempfile
import threading
from dataclasses import replace
from pathlib import Path

from codex_resident import PROFILE, build_config, deny, require_subscription
from openai_codex.client import CodexClient
from openai_codex.generated.v2_all import ModelListResponse


def preflight(model, reasoning):
    lock = json.loads(Path(__file__).with_name("runtime-lock.json").read_text(encoding="utf-8"))
    binary = Path(lock["binary"])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != lock["binary_sha256"]:
        raise RuntimeError("Pinned runtime changed; preflight never updates pins")
    if not PROFILE.is_dir():
        raise RuntimeError("Resident profile is absent; a separately approved sign-in is needed")
    with tempfile.TemporaryDirectory(prefix="resident-preflight-") as directory:
        config = build_config(directory, str(binary), PROFILE, model=model)
        # Query the runtime's normal catalog, not our reviewed metadata fixture.
        config = replace(
            config,
            config_overrides=tuple(
                x for x in config.config_overrides if not x.startswith("model_catalog_json=")
            ),
        )
        with CodexClient(config, approval_handler=deny) as client:
            timer = threading.Timer(40, client.close)
            timer.daemon = True
            timer.start()
            try:
                client.initialize()
                auth = require_subscription(client)
                params, found = {"includeHidden": False}, None
                seen = set()
                while True:
                    page = client.request("model/list", params, response_model=ModelListResponse)
                    found = next((m for m in page.data if m.model == model), None)
                    if found or not page.next_cursor:
                        break
                    if page.next_cursor in seen:
                        raise RuntimeError("Model catalog pagination did not advance")
                    seen.add(page.next_cursor)
                    params["cursor"] = page.next_cursor
                if not found:
                    raise RuntimeError(
                        f"{model} is not offered by this runtime; no substitute selected"
                    )
                options = found.model_dump(by_alias=True, mode="json").get(
                    "supportedReasoningEfforts", []
                )
                efforts = [x["reasoningEffort"] for x in options]
                if reasoning not in efforts:
                    raise RuntimeError(
                        f"Requested reasoning {reasoning} is not offered for {model}"
                    )
                return {
                    "authentication": auth,
                    "model": model,
                    "reasoning": reasoning,
                    "runtime": lock["version"],
                    "sdk": lock["sdk"],
                    "turns_sent": 0,
                    "availability": "listed by local runtime; inference entitlement not exercised",
                }
            finally:
                timer.cancel()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-6.1-sol")
    parser.add_argument("--reasoning", default="medium")
    args = parser.parse_args()
    try:
        print(json.dumps(preflight(args.model, args.reasoning), indent=2))
        return 0
    except Exception as exc:
        # SDK exceptions can include raw transport data; don't print them.
        message = str(exc) if type(exc) is RuntimeError else type(exc).__name__
        print(json.dumps({"ready": False, "reason": message, "turns_sent": 0}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
