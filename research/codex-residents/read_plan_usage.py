"""Read the installed CLI's ChatGPT quota once; starts no thread or model turn."""
from pathlib import Path
from codex_resident import deny, emit_plan_usage, output
from codex_worker import runtime_config
from openai_codex.client import CodexClient


if __name__ == "__main__":
    with CodexClient(runtime_config(Path.cwd()), approval_handler=deny) as client:
        client.initialize()
        emit_plan_usage(client, output)
