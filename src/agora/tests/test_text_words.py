"""Hidden scratch-world acceptance for dk2132. No windows or live-world writes."""
import sys
import time
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel import scratch
from kernel.kernel import Actor, Kernel, Tx
from kernel.text_templates import section


def quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class TextWords(unittest.TestCase):
    def setUp(self):
        self.folder = scratch.TemporaryDirectory(prefix="text-words-")
        self.k = Kernel(self.folder.name, {"tag": "dk", "name": "Fixture",
                                         "steward": {"account": "alex", "name": "Alex"}})
        self.alex = self.k.actor_for(self.k.accounts["alex"])
        self.jeff = self.k.actor_for(self.alex.person, agent="JEFF")
        sable = self.k.join("sable", "Sable", invite={"admitted": "member"})["person"]
        self.sable = self.k.actor_for(sable, agent="Sable")

    def tearDown(self):
        # Rules finish before their private world is removed.
        with self.k.lock:
            self.folder.cleanup()

    def say(self, line, actor=None, ok=True, **kwargs):
        out = self.k.run(actor or self.alex, line, **kwargs)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def note(self, text, actor=None, kind="note", name="Plans"):
        return self.say(f"make kind={kind} name={quote(name)} text={quote(text)}",
                        actor)["made"][0]

    def value(self, thing, field="text"):
        return self.k.state.get(thing, field, "")

    def fixture_fact(self, thing, field, value):
        tx = Tx(self.k)
        tx.part("fixture", thing, "hidden fixture only")
        tx.set(thing, field, value)
        self.k._commit(tx, by=self.alex.id, words="hidden fixture only")

    def test_jeff_appends_one_short_dated_line_to_long_charter(self):
        original = "Alex's rules.\n\n" + ("Keep this rule exactly. \U0001f600\n" * 180) + "\n"
        charter = self.note(original, self.jeff, "charter", "Alex's standing rules")
        line = f'text.append {charter} text="- Dated addition. (4 Nov)"'
        self.assertLess(len(line), 100)
        out = self.say(line, self.jeff)
        self.assertEqual(self.value(charter), original + "- Dated addition. (4 Nov)")
        self.assertLess(len(out["text"]), 200)
        self.assertEqual(self.k.log.records[-1]["by"], self.jeff.id)
        self.assertTrue(self.say(f"edits {charter}", self.jeff)["rows"])

    def test_sable_adds_new_heading_to_large_book_then_appends_under_it(self):
        original = "# Agent Book\n\n" + ("Existing words.\n" * 7000)
        book = self.note(original, self.alex, "document", "Agent Book")
        # Match the live shared book: Alex owns it. A resident needs an owner's
        # authorization, not an implicit grant from the new text words.
        self.say(f'append {book} heading="New section" text=denied', self.sable, ok=False)
        self.say('look set')
        self.say('word-set set may="maker or lead or leaders"')
        self.say(f'set {book} lead={self.sable.person}')
        out = self.say(f'text.append {book} heading="New section" text="First line\\nSecond line"', self.sable)
        self.assertTrue(out["rows"][0]["heading_created"])
        self.assertTrue(self.value(book).startswith(original))
        self.assertEqual(section(self.value(book), "New section"), "First line\nSecond line")
        self.say(f'text.append {book} heading="New section" text="Third line"', self.sable)
        self.assertEqual(section(self.value(book), "New section"), "First line\nSecond line\nThird line")

    def test_lead_still_needs_the_worlds_set_permission(self):
        note = self.note("first")
        self.say(f"set {note} lead={self.sable.person}")
        self.say(f"append {note} text=denied", self.sable, ok=False)
        self.assertEqual(self.value(note), "first")

    def test_replace_exact_matches_refuses_missing_without_mutation(self):
        note = self.note("Hello world; world \U0001f600.")
        out = self.say(f'replace {note} old=world new=desk')
        self.assertEqual(self.value(note), "Hello desk; desk \U0001f600.")
        self.assertEqual(out["rows"][0]["count"], 2)
        before = self.k.state.snapshot(), len(self.k.log.records)
        body = Path(self.folder.name, "bodies", f"{note}.text.loro").read_bytes()
        out = self.say(f'text.replace {note} old=missing new=oops', ok=False)
        self.assertIn("not found", out["text"])
        self.assertEqual(before, (self.k.state.snapshot(), len(self.k.log.records)))
        self.assertEqual(body, Path(self.folder.name, "bodies", f"{note}.text.loro").read_bytes())
        self.say(f'replace {note} old=desk new=')
        self.assertEqual(self.value(note), "Hello ;  \U0001f600.")

    def test_heading_edits_preserve_other_sections_and_fenced_headings(self):
        prefix = "# Book\r\n\r\n## Target ###\r\n\r\n"
        body = "Before \U0001f600\r\n```text\r\n## Fake\r\n```\r\n"
        suffix = "\r\n### Child\r\nchild text\r\n\r\n## Other\r\nBefore\r\n"
        note = self.note(prefix + body + suffix)
        self.say(f'append {note} heading=Target text=Added')
        self.assertEqual(self.value(note), prefix + body.rstrip("\r\n") + "\nAdded\r\n" + suffix)
        self.say(f'replace {note} heading=Target old=Before new=After')
        self.assertTrue(self.value(note).endswith(suffix))
        self.say(f'text.replace {note} heading=Target new="Entire new body"')
        self.assertEqual(self.value(note), prefix + "Entire new body\r\n" + suffix)

    def test_missing_duplicate_and_empty_heading_checks(self):
        note = self.note("## Same\none\n## Same\ntwo\n")
        for line in (f'append {note} heading=Same text=x',
                     f'replace {note} heading=Same new=x',
                     f'replace {note} heading=Missing new=x',
                     f'append {note} heading="" text=x'):
            self.say(line, ok=False)
        self.assertEqual(self.value(note), "## Same\none\n## Same\ntwo\n")

    def test_empty_sections_and_heading_without_final_newline(self):
        for original, heading, expected in (
            ("## Empty\n## Next\nnext", "Empty", "## Empty\nvalue\n## Next\nnext"),
            ("## Empty", "Empty", "## Empty\nvalue"),
            ("## Empty\n\n## Next\nnext", "Empty", "## Empty\nvalue\n## Next\nnext"),
        ):
            with self.subTest(original=original):
                note = self.note(original)
                self.say(f'append {note} heading={heading} text=value')
                self.assertEqual(self.value(note), expected)

    def test_invalid_arguments_and_nontext_fields_refuse(self):
        note = self.note("unchanged")
        for settings in ("old= new=x", "old=unchanged", "new=x", "old=unchanged new=x typo=yes"):
            self.say(f"replace {note} {settings}", ok=False)
        for settings in ('text=""', "heading=Foo", "text=x field=../text", "text=x field=kind"):
            self.say(f"append {note} {settings}", ok=False)
        self.fixture_fact(note, "count", 42)
        self.say(f"append {note} text=x field=count", ok=False)
        self.say(f"append {note} text=x field=made_by", ok=False)
        self.assertEqual(self.value(note), "unchanged")

    def test_other_text_fields_and_literal_escapes(self):
        note = self.note("main")
        self.say(f'append {note} field=notes text="one\\ntwo\\tthree"')
        self.assertEqual(self.value(note, "notes"), "one\ntwo\tthree")
        self.say(f"append {note} field=notes text={quote(r'literal \\n and C:\path')}")
        self.assertTrue(self.value(note, "notes").endswith(r"literal \n and C:\path"))
        self.assertEqual(self.value(note), "main")

    def test_undo_and_restart_keep_fact_and_history(self):
        note = self.note("first")
        out = self.say(f"append {note} text=second")
        self.say(f'undo {out["records"][0]}')
        self.assertEqual(self.value(note), "first")
        self.say(f"append {note} text=third")
        self.k = Kernel(self.folder.name)
        self.assertEqual(self.value(note), "first\nthird")
        self.assertTrue(self.say(f"edits {note}")["rows"])

    def test_members_cannot_edit_someone_elses_note_or_hidden_text(self):
        note = self.note("private")
        self.say(f"look {note}", self.sable)
        self.say(f"append {note} text=oops", self.sable, ok=False)
        self.say(f"replace {note} old=private new=oops", self.sable, ok=False)
        self.assertEqual(self.value(note), "private")
        own = self.note("hidden", self.sable)
        self.fixture_fact(own, "sees.text", "leaders")
        self.say(f'append {own} text=oops', self.sable, ok=False)

    def test_buttons_use_same_word_and_stale_paint_refuses(self):
        note = self.note("first")
        button = self.say(f'make kind=button label="Add line" does={quote(f"text.append {note} text=second")}')["made"][0]
        self.say(f"press {button}")
        self.assertEqual(self.value(note), "first\nsecond")
        rev = self.k.state.rev[note]
        self.say(f"append {note} text=third")
        self.say(f"append {note} text=stale", saw={note: rev}, ok=False)
        self.assertEqual(self.value(note), "first\nsecond\nthird")

    def test_modules_need_both_grants_and_each_scope_applies(self):
        note = self.note("first")
        book = self.note("book", kind="document")
        mid = self.say(f'module helper run={quote("[\"unused\"]")} grants="look set"')["made"][0]
        module = Actor(mid, self.alex.person, "module", module=mid, caller=self.alex)
        self.say(f"append {note} text=denied", module, ok=False)
        self.say(f'grant {mid} words=text.append only=kind:note')
        self.say(f"append {note} text=allowed", module)
        self.say(f"append {book} text=denied", module, ok=False)
        self.assertEqual(self.value(note), "first\nallowed")
        self.assertEqual(self.value(book), "book")

    def test_consecutive_agents_append_to_current_text(self):
        note = self.note("first")
        self.say(f"look {note}", self.jeff)
        self.say(f"append {note} text=second")
        self.say(f"append {note} text=third", self.jeff)
        self.assertEqual(self.value(note), "first\nsecond\nthird")

    def test_composed_verb_reads_prior_steps_and_undo_is_one_act(self):
        note = self.note("first")
        steps = f"append {note} text=second; replace {note} old=second new=third; append {note} text=last"
        self.say(f'verb grow steps={quote(steps)} help="Grow"')
        self.say("grow")
        self.assertEqual(self.value(note), "first\nthird\nlast")
        self.say("undo")
        self.assertEqual(self.value(note), "first")

    def test_rule_can_append_without_rewriting_text(self):
        note = self.note("first")
        self.say(f'make kind=rule on=post do={quote(f"append {note} text=heard")}')
        self.say('post "A hidden fixture trigger"')
        deadline = time.monotonic() + 3
        while self.value(note) == "first" and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(self.value(note), "first\nheard")

    def test_verb_can_replace_back_to_original_value(self):
        note = self.note("first")
        steps = f"replace {note} old=first new=second; replace {note} old=second new=first"
        self.say(f'verb roundtrip steps={quote(steps)} help="Round trip"')
        self.say("roundtrip")
        self.assertEqual(self.value(note), "first")
        self.say("undo")
        self.assertEqual(self.value(note), "first")

    def test_receipts_help_and_noop(self):
        note = self.note("same")
        out = self.say(f"replace {note} old=same new=same")
        self.assertFalse(out["rows"][0]["changed"])
        self.assertFalse(out["records"])
        self.assertNotIn("[r?]", out["text"])
        for word in ("append", "replace", "text.append", "text.replace"):
            self.assertIn("heading", self.say("help " + word)["text"])

    def test_one_named_section_of_long_note_changes_and_neighbors_stay_exact(self):
        prefix = "# Book\n\n## Earlier\n" + "Keep this exactly.\n" * 3000 + "\n## Updates\n\n"
        suffix = "\n\n## Later\n" + "Keep this too.\n" * 4000
        note = self.note(prefix + "Original body." + suffix, name="Our notes")
        self.say('text.append "Our notes" heading="Updates" text="A new line"')
        self.assertEqual(self.value(note), prefix + "Original body.\nA new line" + suffix)
        self.say('text.replace "Our notes" heading="Updates" new="The replacement section body"')
        self.assertEqual(self.value(note), prefix + "The replacement section body" + suffix)
        self.say("undo")
        self.assertEqual(self.value(note), prefix + "Original body.\nA new line" + suffix)


if __name__ == "__main__":
    unittest.main()
