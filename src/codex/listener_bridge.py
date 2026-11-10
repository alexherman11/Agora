"""Reconnect the bundled app-tools bridge to a verified installed Codex pipe.

No app database reads or writes. Pipe ownership is checked before using the
unchanged MCP bridge, and fallback endpoints are probed read-only for our chat.
"""

import ctypes
import fnmatch
import os
from ctypes import wintypes as W
from pathlib import Path

from desk_notifier import app_call, save

PIPE_ENV = "CODEX_APP_TOOLS_PIPE_PATH"
PIPE_ROOT = "\\\\.\\pipe\\"


def pipe_executable(path):
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
    k.CreateFileW.restype = W.HANDLE
    k.GetNamedPipeServerProcessId.argtypes = [W.HANDLE, ctypes.POINTER(W.ULONG)]
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
    k.CloseHandle.argtypes = [W.HANDLE]
    pipe = k.CreateFileW(path, 0xC0000000, 0, None, 3, 0, None)
    if pipe == W.HANDLE(-1).value:
        raise OSError("App pipe is unavailable")
    process = None
    try:
        pid = W.ULONG()
        if not k.GetNamedPipeServerProcessId(pipe, ctypes.byref(pid)):
            raise ctypes.WinError(ctypes.get_last_error())
        process = k.OpenProcess(0x1000, False, pid.value)
        buffer = ctypes.create_unicode_buffer(32768)
        size = W.DWORD(len(buffer))
        if not process or not k.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value
    finally:
        if process:
            k.CloseHandle(process)
        k.CloseHandle(pipe)


def trusted_executable(path, config):
    return fnmatch.fnmatchcase(
        path.replace("\\", "/").casefold(), config["bridge_executable_pattern"].casefold()
    )


def resolve(config, owner=pipe_executable, names=None, call=app_call):
    names = names if names is not None else os.listdir(PIPE_ROOT)
    available = {PIPE_ROOT + n for n in names if n.startswith("codex-browser-use-")}
    preferred = [config.get("pipe"), os.environ.get(PIPE_ENV)]
    candidates = list(dict.fromkeys([p for p in preferred if p in available] + sorted(available)))
    for pipe in candidates:
        try:
            if not trusted_executable(owner(pipe), config):
                continue
            candidate = {**config, "bridge_env": {PIPE_ENV: pipe}, "bridge_timeout": 5}
            call(
                candidate,
                "read_thread",
                {"threadId": config["thread"], "turnLimit": 1, "maxOutputCharsPerItem": 1},
            )
            return candidate, pipe
        except (OSError, RuntimeError, TimeoutError):
            continue
    raise RuntimeError("Codex app is unavailable; queued Desk messages are preserved")


def deliver(config, name, arguments, config_path=None):
    candidate, pipe = resolve(config)
    if config_path and config.get("pipe") != pipe:
        save(Path(config_path), {**config, "pipe": pipe})
    candidate["bridge_timeout"] = 30
    return app_call(candidate, name, arguments)
