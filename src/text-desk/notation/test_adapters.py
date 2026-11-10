"""adapters.py, offline: reading adapter texts, filling templates, and what outside words can never do."""
import unittest
from pathlib import Path

import adapters

TWITCH = (Path(__file__).resolve().parents[2] / "desktop" / "twitch.adapter").read_text(encoding="utf-8")
PROPS = {"name": "twitch", "into": "a12319", "channel": "dr_bizzlebop", "on": "yes", "random": "12345"}


def arrive(plan, line):
    for rule in plan["each"]:
        fields = adapters.items_of(rule, line)
        if fields is not None:
            return [adapters.fill(a, fields, PROPS) for a in rule["acts"]], fields
    return None, None


class Twitch(unittest.TestCase):
    def setUp(self):
        self.plan = adapters.parse(TWITCH)

    def test_reads(self):
        self.assertEqual(self.plan["connect"], "wss://irc-ws.chat.twitch.tv:443")
        self.assertEqual([adapters.send_text(s, PROPS) for s in self.plan["open"]][2:],
                         ["NICK justinfan12345", "JOIN #dr_bizzlebop"])
        self.assertEqual(len(self.plan["each"]), 2)

    def test_ping(self):
        rx, reply = self.plan["answers"][0]
        m = rx.search("PING :tmi.twitch.tv")
        self.assertEqual(adapters.send_text(reply, {**PROPS, **m.groupdict()}), "PONG :tmi.twitch.tv")

    def test_message(self):
        line = ("@badge-info=;color=#FF69B4;display-name=dr_bizzlebop;id=ec17;mod=0 "
                ":dr_bizzlebop!dr_bizzlebop@x.tmi.twitch.tv PRIVMSG #dr_bizzlebop :test message!")
        acts, fields = arrive(self.plan, line)
        self.assertEqual(fields["id"], "ec17")
        self.assertEqual(acts, ['do append a12319 line="dr_bizzlebop: test message!" words="test message!" '
                                'user="dr_bizzlebop" color="#FF69B4" twitch_id="ec17"'])

    def test_notice(self):
        line = ("@display-name=Moth;id=n1;msg-id=sub;system-msg=Moth\\ssubscribed\\sat\\sTier\\s1. "
                ":tmi.twitch.tv USERNOTICE #dr_bizzlebop :hi all")
        acts, _ = arrive(self.plan, line)
        self.assertIn('line="★ Moth subscribed at Tier 1. hi all"', acts[0])
        self.assertIn('kind="notice"', acts[0])

    def test_outside_words_stay_words(self):
        # a viewer tries to close the quote, start a second command, call people and fill a blank
        nasty = 'x" ; do rewrite a5080 text="gone @jeff $into \\'
        line = f"@color=;display-name=eve;id=z :eve!e@x PRIVMSG #c :{nasty}"
        acts, _ = arrive(self.plan, line)
        self.assertEqual(len(acts), 1)
        act = acts[0]
        self.assertTrue(act.startswith('do append a12319 line="eve: x\\" ; do rewrite'))
        self.assertIn("\\$into \\\\", act)            # $ and \ escaped, so nothing is filled or swallowed
        self.assertNotIn("\n", act)
        # every quote the viewer typed is escaped: the unescaped quotes are only the template's own
        unescaped, slash = 0, False
        for c in act:
            unescaped += c == '"' and not slash
            slash = c == "\\" and not slash
        self.assertEqual(unescaped, 10)

    def test_display_name_cannot_open_with_at(self):
        with self.assertRaises(adapters.Refused):
            adapters.fill('$who said hi', {"who": "@jeff"}, PROPS)


class Rules(unittest.TestCase):
    def test_outside_field_never_outside_quotes(self):
        with self.assertRaises(adapters.Refused):
            adapters.fill("do append $words line=\"x\"", {"words": "a5080"}, PROPS)

    def test_prop_target_must_be_an_id(self):
        with self.assertRaises(adapters.Refused):
            adapters.fill('do append $into line="x"', {}, {**PROPS, "into": "a1 ; do trash a2"})

    def test_notify_and_task_lines_are_just_world_lines(self):
        plan = adapters.parse("poll https://example.org/x.json every 60\nitems data\n"
                           "each '.'\n  key \"$id\"\n  notify \"New: $title\"\n"
                           "  do create $tasks kind=task title=\"$title\"\n")
        fields = adapters.items_of(plan["each"][0], None, adapters.flat({"id": 1, "title": "Fix $it"}))
        acts = [adapters.fill(a, fields, {**PROPS, "tasks": "f155"}) for a in plan["each"][0]["acts"]]
        self.assertEqual(acts, ['notify "New: Fix \\$it"', 'do create f155 kind=task title="Fix \\$it"'])
        self.assertEqual(plan["every"], 60)

    def test_poll_floor(self):
        self.assertEqual(adapters.parse("poll https://e.org every 1\neach '.'\n  do append $into line=\"x\"")["every"],
                         adapters.MIN_POLL)

    def test_mail_login_is_only_named(self):
        with self.assertRaises(adapters.Refused):
            adapters.parse('imap imap.gmail.com\nlogin "alex@x.com" "hunter2"\neach \'.\'\n  do append $into line="x"')
        plan = adapters.parse('imap imap.gmail.com every 60\nlogin "env:GMAIL_ADDRESS" "env:GMAIL_APP_PASSWORD"\n'
                           'each \'.\'\n  key "$id"\n  do append $into line="$from_name: $subject"')
        fields = adapters.items_of(plan["each"][0], None, {"from_name": "Ana", "subject": "Lunch?", "id": "<1@x>"})
        self.assertEqual(adapters.fill(plan["each"][0]["acts"][0], fields, PROPS),
                         'do append a12319 line="Ana: Lunch?"')

    def test_refusals_name_the_line(self):
        for text, said in (("connect wss://a\nconnect2 x", "line 2"), ("each '('", "does not read"),
                           ("connect wss://a", "at least one each"), ("each '.'\n  do append $into line=\"x",
                                                                     "open quote")):
            with self.assertRaises(adapters.Refused) as e:
                adapters.parse(text)
            self.assertIn(said, str(e.exception))

    def test_head_props(self):
        head = 'a12 note "twitch" · name=twitch on=yes status=live: connected to x status_at=22 Oct 19:40 · 9w'
        self.assertEqual(adapters.head_props(head)["status"], "live: connected to x")
        self.assertEqual(adapters.head_props(head)["on"], "yes")

    def test_approval_reads_the_last_hand(self):
        class W:
            def __init__(self, h):
                self.h = h

            def text(self, line, who="adapters"):
                return self.h
        h = "e1 create a9 by claude\ne2 prop a9 on=yes by alex\ne3 prop a9 status=live by twitch"
        self.assertTrue(adapters.approved(W(h), "a9", "twitch"))
        self.assertFalse(adapters.approved(W(h + "\ne4 replace a9 old=x new=y by rowan"), "a9", "twitch"))
        self.assertFalse(adapters.approved(W("e1 create a9 by claude"), "a9", "twitch"))


if __name__ == "__main__":
    unittest.main()
