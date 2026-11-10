"""The couple of questions after first sign-in, read from data.

`content/questions.json` holds them so a leader can change the wording, the
choices or the order without touching code. The loader refuses a question
that asks where someone lives: a home's location appears only if a member
adds it themselves, inside the place.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TYPES = ("text", "choice", "choices")
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
FORBIDDEN = re.compile(r"\b(address|street|house number|home location|where (?:do )?you live|"
                       r"zip|postcode|postal code)\b", re.I)


class QuestionsError(ValueError):
    pass


@dataclass
class Question:
    key: str
    label: str
    type: str
    help: str = ""
    required: bool = False
    max: int = 80
    options: list[dict] = field(default_factory=list)
    prefill: str = ""
    placeholder: str = ""

    def clean(self, raw) -> tuple[object, str | None]:
        """(value, problem). `raw` is a str, or a list of str for "choices"."""
        if self.type == "text":
            value = " ".join(str(raw or "").split())
            if not value:
                return "", ("Please fill this in." if self.required else None)
            if len(value) > self.max:
                return value, f"Keep it under {self.max} characters."
            return value, None
        allowed = {o["value"] for o in self.options}
        if self.type == "choice":
            value = str(raw or "")
            if not value:
                return "", ("Please pick one." if self.required else None)
            return (value, None) if value in allowed else ("", "Please pick one of the choices.")
        values = [v for v in (raw or []) if v in allowed]
        values = sorted(set(values), key=[o["value"] for o in self.options].index)
        if self.required and not values:
            return values, "Please pick at least one."
        return values, None


@dataclass
class Questions:
    version: int
    intro: str
    questions: list[Question]

    def by_key(self, key: str) -> Question | None:
        return next((q for q in self.questions if q.key == key), None)


def parse(doc: dict) -> Questions:
    if not isinstance(doc, dict) or not isinstance(doc.get("questions"), list):
        raise QuestionsError("questions.json needs a list called 'questions'")
    seen, out = set(), []
    for i, q in enumerate(doc["questions"]):
        where = f"question {i + 1}"
        if not isinstance(q, dict):
            raise QuestionsError(f"{where} is not an object")
        key, label, qtype = q.get("key", ""), q.get("label", ""), q.get("type", "")
        if not KEY_RE.match(str(key)) or key in seen:
            raise QuestionsError(f"{where}: key must be unique, lower case, like 'help'")
        if not isinstance(label, str) or not label.strip():
            raise QuestionsError(f"{where}: needs a label")
        if qtype not in TYPES:
            raise QuestionsError(f"{where}: type must be one of {', '.join(TYPES)}")
        text = " ".join(str(q.get(k, "")) for k in ("label", "help", "placeholder", "key"))
        text += " " + " ".join(str(o.get("label", "")) for o in q.get("options", []) if isinstance(o, dict))
        if FORBIDDEN.search(text.replace("_", " ")):
            raise QuestionsError(f"{where}: we never ask where someone lives "
                                 "(a home's location appears only if a member adds it)")
        options = q.get("options", [])
        if qtype != "text":
            if not isinstance(options, list) or not options or not all(
                    isinstance(o, dict) and o.get("value") and o.get("label") for o in options):
                raise QuestionsError(f"{where}: choices need options with value and label")
            if len({o["value"] for o in options}) != len(options):
                raise QuestionsError(f"{where}: option values must differ")
        seen.add(key)
        out.append(Question(key=key, label=label.strip(), type=qtype, help=str(q.get("help", "")),
                            required=bool(q.get("required", False)), max=int(q.get("max", 80)),
                            options=list(options) if qtype != "text" else [],
                            prefill=str(q.get("prefill", "")),
                            placeholder=str(q.get("placeholder", ""))))
    name = next((q for q in out if q.key == "display_name"), None)
    if name is None or name.type != "text" or not name.required:
        raise QuestionsError("there must be a required text question with key 'display_name' "
                             "(real names are shown in chat)")
    return Questions(version=int(doc.get("version", 1)), intro=str(doc.get("intro", "")),
                     questions=out)


def load(path: Path) -> Questions:
    return parse(json.loads(Path(path).read_text(encoding="utf-8")))
