"""The Loro wrapper: a text body you can edit and anchor into; the only file that knows Loro.
Never: never lets a Loro type out, never logs a keystroke, never writes except via verbs.attach."""

from __future__ import annotations

import base64
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

import loro

from kernel import verbs
from kernel.schema import FacetRecord
from kernel.store import Store

IDLE_SECONDS = 3.0  # a burst ends when the author pauses this long
BURST_BYTES = 4096  # or when this much has changed
QUOTE_CHARS = 40


@dataclass(frozen=True)
class Locator:
    """Where an anchor points: two CRDT positions, the revision it was made against, a quote."""

    entity: str
    start: str  # encoded position id
    end: str
    revision: int
    quote: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> Locator:
        return cls(**{k: record[k] for k in ("entity", "start", "end", "revision", "quote")})


@dataclass(frozen=True)
class Resolution:
    """Where an anchor resolves now. Unresolvable anchors name their recorded revision instead."""

    start: int | None
    end: int | None
    revision: int
    exact: bool  # the quoted text is still exactly there

    @property
    def live(self) -> bool:
        return self.start is not None


class TextDoc:
    """One entity's core.text, open for editing. Edits accumulate here; bursts flush as events."""

    def __init__(
        self,
        world: Store,
        actor: str,
        entity: str,
        *,
        idle: float = IDLE_SECONDS,
        burst: int = BURST_BYTES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        record = world.facet(entity, "core.text")
        if record is None:
            raise verbs.VerbError(f"{entity} has no core.text; attach one before editing")
        self._world, self._actor, self._entity = world, actor, entity
        self._idle, self._burst, self._clock = idle, burst, clock
        self._doc = loro.LoroDoc()
        snapshot = record.body.get("snapshot")
        if snapshot:
            self._doc.import_(base64.b64decode(snapshot))
        if self._text().to_string() != record.body.get("text", ""):
            # plain text was attached after (or instead of) a snapshot: the body wins
            self._text().delete(0, self._text().len_unicode)
            self._text().insert(0, record.body.get("text", ""))
        self._doc.commit()
        self.revision = record.revision
        self._pending = 0
        self._last_edit: float | None = None

    # -- editing ------------------------------------------------------------------

    def plaintext(self) -> str:
        return self._text().to_string()

    def insert(self, pos: int, text: str) -> None:
        self._text().insert(pos, text)
        self._doc.commit()
        self._touch(len(text.encode("utf-8")))

    def delete(self, pos: int, length: int) -> None:
        self._text().delete(pos, length)
        self._doc.commit()
        self._touch(length)

    @property
    def dirty(self) -> bool:
        return self._last_edit is not None

    def tick(self) -> FacetRecord | None:
        """Flush if the author has gone idle. Call from any loop that owns the doc."""
        if self.dirty and self._clock() - self._last_edit >= self._idle:
            return self.flush()
        return None

    def flush(self) -> FacetRecord | None:
        """Record the burst as one text-edited event. The only write this file ever makes."""
        if not self.dirty:
            return None
        snapshot = base64.b64encode(self._doc.export(loro.ExportMode.Snapshot())).decode("ascii")
        record = verbs.attach(
            self._world,
            self._actor,
            self._entity,
            "core.text",
            {"text": self.plaintext(), "snapshot": snapshot},
        )
        self.revision = record.revision
        self._pending, self._last_edit = 0, None
        return record

    def close(self) -> FacetRecord | None:
        return self.flush()

    # -- anchors ------------------------------------------------------------------

    def anchor(self, start: int, end: int) -> Locator:
        """Name a range so it survives edits. The quote is a fallback, not the locator."""
        text = self.plaintext()
        if not 0 <= start <= end <= len(text):
            raise ValueError(f"range {start}:{end} is outside the text (length {len(text)})")
        head = self._text().get_cursor(start, loro.Side.Left)
        tail = self._text().get_cursor(end, loro.Side.Left)
        return Locator(
            entity=self._entity,
            start=base64.b64encode(head.encode()).decode("ascii"),
            end=base64.b64encode(tail.encode()).decode("ascii"),
            revision=self.revision,
            quote=text[start:end][:QUOTE_CHARS],
        )

    def resolve(self, locator: Locator) -> Resolution:
        """Follow a locator to the current text, or to its recorded revision if the place is gone.

        The head cursor rides the range's first character, the tail cursor the character after
        it: an edit inside stretches the range, and deleting the range unseats the head.
        """
        head = self._doc.get_cursor_pos(loro.Cursor.decode(base64.b64decode(locator.start)))
        tail = self._doc.get_cursor_pos(loro.Cursor.decode(base64.b64decode(locator.end)))
        if head.update is not None or tail.update is not None:
            return Resolution(None, None, locator.revision, False)
        start, end = head.current.pos, tail.current.pos
        if end < start:
            return Resolution(None, None, locator.revision, False)
        exact = self.plaintext()[start:end][:QUOTE_CHARS] == locator.quote
        return Resolution(start, end, self.revision, exact)

    # -- internals ----------------------------------------------------------------

    def _text(self) -> loro.LoroText:
        return self._doc.get_text("text")

    def _touch(self, size: int) -> None:
        self._pending += size
        self._last_edit = self._clock()
        if self._pending >= self._burst:
            self.flush()
