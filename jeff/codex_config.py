"""Account-backed JEFF runtime policy, pinned to the installed Codex SDK.
Never: never read credentials or enable a computer environment for JEFF.
"""

import os

from openai_codex.client import CodexConfig
from openai_codex.generated.v2_all import ConfigReadResponse

# These switches remove ambient capabilities; environments=[] additionally prevents
# registration of shell, apply_patch and view_image (including hidden handlers).
DISABLED_FEATURES = """
apps connectors plugins remote_plugin recommended_plugins plugin_hooks hooks codex_hooks
shell_tool unified_exec shell_snapshot apply_patch_freeform view_image
js_repl js_repl_tools_only code_mode code_mode_only
computer_use browser_use browser_use_external in_app_browser
multi_agent multi_agent_v2 collab collaboration_modes goals token_budget
memories memory_tool external_agent_memory_import chronicle
image_generation imagegenext workspace_dependencies
web_search web_search_cached web_search_request standalone_web_search
tool_search search_tool skill_search tool_suggest deferred_executor
request_permissions request_permissions_tool request_rule current_time_reminder
default_mode_request_user_input skill_mcp_dependency_install sleep_tool
""".split()


def runtime_config(cwd):
    overrides = [f"features.{name}=false" for name in DISABLED_FEATURES]
    overrides += [
        # Astra uses Codex's isolated tool-composition host. It can call only
        # registered tools; the computer environment and JS REPL stay absent.
        "features.code_mode_host=true",
        'web_search="disabled"',
        "tools.update_plan.enabled=false",
        "tools.experimental_request_user_input.enabled=false",
        "project_doc_max_bytes=0",
        "skills.include_instructions=false",
        "skills.bundled.enabled=false",
        "features.skip_host_skill_discovery=true",
        "orchestrator.skills.enabled=false",
        "orchestrator.mcp.enabled=false",
        "memories.generate_memories=false",
        "memories.use_memories=false",
        "include_environment_context=false",
        "include_apps_instructions=false",
        "include_permissions_instructions=false",
        "include_collaboration_mode_instructions=false",
        "analytics.enabled=false",
        'history.persistence="none"',
        'developer_instructions=""',
        "notify=[]",
    ]
    return CodexConfig(
        codex_bin=os.environ.get("AGORA_CODEX_BIN") or None,
        cwd=cwd,
        config_overrides=tuple(overrides),
        client_name="agora_jeff",
        client_title="Agora JEFF",
    )


def thread_config(client):
    """Disable every inherited MCP server without changing the user's config."""
    effective = client.request(
        "config/read", {}, response_model=ConfigReadResponse
    ).config.model_dump()
    return {
        "mcp_servers": {name: {"enabled": False} for name in (effective.get("mcp_servers") or {})}
    }
