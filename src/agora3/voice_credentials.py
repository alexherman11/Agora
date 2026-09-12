"""Load the voice-only API credential from the operator's protected configuration.
Never put credentials into native objects, model context, browser responses or logs.
"""

import ctypes
import os
from pathlib import Path

from agora3.world import Refusal


def configured(directory):
    return (
        bool(os.environ.get("AGORA_VOICE_API_KEY"))
        or (Path(directory) / "voice-key.dpapi").is_file()
    )


def load_key(directory):
    """Windows files use current-user DPAPI; other deployments can supply an environment key."""
    value = os.environ.get("AGORA_VOICE_API_KEY")
    if value:
        return value.strip()
    path = Path(directory) / "voice-key.dpapi"
    if not path.is_file():
        raise Refusal("Voice is not configured. Set the server's voice API credential first.")
    if os.name != "nt":
        raise Refusal("This voice credential belongs to Windows. Set AGORA_VOICE_API_KEY here.")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    try:
        encrypted = bytes.fromhex(path.read_text(encoding="utf-8-sig").strip())
        buffer = (ctypes.c_ubyte * len(encrypted)).from_buffer_copy(encrypted)
        source, result = Blob(len(encrypted), buffer), Blob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        if not crypt.CryptUnprotectData(
            ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)
        ):
            raise ValueError("Unprotect failed")
        try:
            return ctypes.string_at(result.data, result.size).decode("utf-16-le").strip()
        finally:
            ctypes.memset(result.data, 0, result.size)
            kernel.LocalFree(result.data)
    except Exception:
        raise Refusal(
            "The voice credential could not be unlocked by this Windows account."
        ) from None
