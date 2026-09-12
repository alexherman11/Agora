"""Small forward-compatible envelopes around the installed managed-account SDK.
Never interpret unknown runtime items as completed work or discard a real failure.
"""

from types import SimpleNamespace

from pydantic import BaseModel


class ThreadIdentity(BaseModel):
    id: str


class ThreadEnvelope(BaseModel):
    thread: ThreadIdentity
    model: str


def payload(event):
    value = getattr(event, "payload", SimpleNamespace())
    raw = getattr(value, "params", None)
    if not isinstance(raw, dict):
        return value

    def convert(item):
        if isinstance(item, dict):
            values = {k: convert(v) for k, v in item.items()}
            for old, new in (
                ("itemId", "item_id"),
                ("threadId", "thread_id"),
                ("turnId", "turn_id"),
            ):
                if old in values:
                    values[new] = values[old]
            return SimpleNamespace(**values)
        if isinstance(item, list):
            return [convert(v) for v in item]
        return item

    return convert(raw)
