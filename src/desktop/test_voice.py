"""test_voice (a8901): the home base's voice with a fake engine, every path. No microphone, no sound, no world.

    python src/desktop/test_voice.py
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "text-desk" / "notation"))
import voice  # noqa: E402
import host_verbs  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class Case(unittest.TestCase):
    def make(self, gate=None, jeff="idle"):
        self.clock, self.eng, self.published = Clock(), voice.FakeEngine(), []
        self.jeff = jeff
        self.v = voice.Voice(self.eng, publish=self.published.append, gate=gate, clock=self.clock,
                             jeff=lambda: self.jeff)
        return self.v

    def state(self):
        return self.v.rows()[0]

    def finals(self):
        return [r for r in self.v.rows() if r["kind"] == "final"]

    def says(self):
        return [c for c in self.eng.calls if c[0] == "say"]


class Listening(Case):
    def test_tentative_words_show_and_never_act(self):
        self.make()
        self.v.listen()
        self.eng.hear("show me")
        self.eng.hear("show me the board")
        self.assertEqual(self.state()["state"], "listening")
        self.assertEqual(self.state()["tentative"], "show me the board")
        self.assertEqual(self.finals(), [])                      # nothing to send
        self.assertEqual(self.says(), [])                        # nothing said

    def test_final_once_with_its_own_id_and_the_readback(self):
        self.make()
        self.v.listen()
        u = self.state()["utterance"]
        self.eng.hear("show me the")
        self.eng.finish("Show me the board")
        f = self.finals()
        self.assertEqual([(x["utterance"], x["words"]) for x in f], [(u, "Show me the board")])
        self.assertEqual(self.state()["tentative"], "")
        self.assertEqual(self.says(), [("say", f"heard-{u}", "Heard: Show me the board", "device")])
        self.assertNotEqual(self.state()["utterance"], u)       # the next utterance has another id
        self.assertEqual(len(self.finals()), 1)                  # read again: still one

    def test_cancel_mid_utterance_sends_nothing(self):
        self.make()
        self.v.listen()
        self.eng.hear("delete every")
        self.assertIn("stopped", self.v.stop("pressed"))
        self.eng.finish("delete everything")                    # a late final after the stop
        self.assertEqual(self.finals(), [])
        self.assertEqual(self.state()["state"], "off")
        self.assertEqual(self.state()["tentative"], "")
        self.assertIn(("stop",), self.eng.calls)

    def test_two_utterances_close_together_are_two(self):
        self.make()
        self.v.listen()
        self.eng.finish("play some music")
        self.clock.t += 0.3
        self.eng.finish("and show the board")
        f = self.finals()
        self.assertEqual([x["words"] for x in f], ["play some music", "and show the board"])
        self.assertEqual(len({x["utterance"] for x in f}), 2)

    def test_silence_ends_it(self):
        self.make()
        self.v.listen()
        self.clock.t += 3.0
        self.v.tick()
        self.assertEqual(self.state()["state"], "listening")
        self.eng.hear("hello")                                  # heard: the silence counts again from here
        self.clock.t += 3.5
        self.v.tick()
        self.assertEqual(self.state()["state"], "listening")
        self.clock.t += voice.SILENCE
        self.v.tick()
        self.assertEqual((self.state()["state"], self.state()["why"]), ("off", "silence"))

    def test_a_game_or_hidden_home_base_stops_a_listening(self):
        why = {"now": None}
        self.make(gate=lambda: why["now"])
        self.v.listen()
        why["now"] = "Windows says held back: a full-screen game (Direct3D) runs"
        self.v.tick()
        self.assertEqual(self.state()["state"], "off")
        self.assertIn("game", self.state()["why"])

    def test_engine_end_or_error_says_so(self):
        self.make()
        self.v.listen()
        self.eng.event({"ev": "stopped", "why": "the speech child ended"})
        self.assertEqual((self.state()["state"], self.state()["why"]), ("off", "the speech child ended"))


class Consent(Case):
    def test_refused_consent_never_listens(self):
        self.make(gate=lambda: "Alex has not allowed it yet (the first press asks him)")
        with self.assertRaises(voice.Refused):
            self.v.listen()
        with self.assertRaises(voice.Refused):
            self.v.say("m1", "hello")
        self.assertEqual([c for c in self.eng.calls if c[0] in ("listen", "say")], [])

    def test_host_verb_refuses_before_any_child_is_started(self):
        hud = SimpleNamespace(settings={"voice": "off"}, shown=True, door="http://x", a=SimpleNamespace(world="w", who="alex"))
        with mock.patch.object(voice, "SapiEngine") as sapi:
            got = host_verbs.call(hud, "voice.listen")
            self.assertTrue(got.startswith("ERR voice.listen: voice is off"), got)
            hud.settings["voice"] = "on"
            with mock.patch.object(voice, "consent_of", return_value=""), \
                    mock.patch("notify.state", return_value="shown"):
                got = host_verbs.call(hud, "voice.listen")
            self.assertIn("has not allowed it yet", got)
            with mock.patch.object(voice, "consent_of", return_value="never"), \
                    mock.patch("notify.state", return_value="shown"):
                self.assertIn("off for good", host_verbs.call(hud, "voice.listen"))
            with mock.patch.object(voice, "consent_of", return_value="allowed"), \
                    mock.patch("notify.state", return_value="held back: a full-screen game (Direct3D) runs"):
                self.assertIn("game", host_verbs.call(hud, "voice.listen"))
            hud.shown = False
            self.assertIn("hidden", host_verbs.call(hud, "voice.listen"))
            self.assertEqual(host_verbs.call(hud, "voice.stop"), "ok not listening, and the voice is quiet")
            sapi.assert_not_called()
            self.assertFalse(hasattr(hud, "voice"))

    def test_host_verb_listens_once_all_gates_pass(self):
        hud = SimpleNamespace(settings={"voice": "on"}, shown=True, door="http://x", a=SimpleNamespace(world="w", who="alex"))
        eng = voice.FakeEngine()
        with mock.patch.object(voice, "SapiEngine", return_value=eng), \
                mock.patch.object(voice, "consent_of", return_value="allowed"), \
                mock.patch("notify.state", return_value="shown"), mock.patch("witnessed.write"):
            self.assertEqual(host_verbs.call(hud, "voice.listen"), "ok listening (the microphone is lit)")
            self.assertEqual(eng.calls, [("device",), ("listen", "mic")])      # a9138: named first
            self.assertEqual(host_verbs.call(hud, "voice.say", 'm12 "Done: the board is open."'),
                             "ok reading m12 aloud")
            self.assertEqual(host_verbs.call(hud, "voice.say", "m12 Done: the board is open."), "ok already read m12")
            self.assertTrue(host_verbs.call(hud, "voice.stop").startswith("ok stopped listening"))
        self.assertIn("voice.listen", [r["name"] for r in host_verbs.rows()])


class TheVoice(Case):
    def test_stop_during_jeffs_voice_by_speaking_clicking_or_the_mic(self):
        self.make()
        self.v.listen()
        self.v.say("m40", "I have opened the board and put the three cards waiting on you at the top")
        self.assertEqual(self.state()["aloud"], "yes")
        self.eng.hear("opened the board and put the three cards")       # its own voice coming back: not him
        self.assertEqual(self.state()["aloud"], "yes")
        self.eng.hear("wait stop")                                       # him: the voice stops at once
        self.assertEqual(self.state()["aloud"], "no")
        self.assertIn(("hush",), self.eng.calls)
        self.v.say("m41", "Here is the second answer")
        self.assertEqual(self.v.hush(), "the voice stopped")             # a click anywhere (voice.hush)
        self.v.stop()
        self.v.say("m42", "And a third")
        self.v.listen()                                                  # pressing the microphone
        self.assertEqual(self.state()["aloud"], "no")

    def test_readback_echo_is_not_a_second_line(self):
        self.make()
        self.v.listen()
        self.eng.finish("play some music")
        self.eng.finish("heard play some music")                         # the readback through the microphone
        self.assertEqual([f["words"] for f in self.finals()], ["play some music"])

    def test_each_line_is_read_once_and_long_ones_are_cut(self):
        self.make()
        self.v.say("m7", "word " * 400)
        text = self.says()[-1][2]
        self.assertLessEqual(len(text), voice.MAX_WORDS + 40)
        self.assertTrue(text.endswith("The rest is in the Conversation."))
        self.assertEqual(self.v.say("m7", "again"), "already read m7")
        with self.assertRaises(voice.Refused):
            self.v.say("", "no id")


class JeffsState(Case):
    def test_finishing_then_answering_as_the_house_says(self):
        self.make(jeff="working")
        self.v.listen()
        self.eng.finish("show me the board")
        self.assertEqual(self.finals()[0]["jeff"], "JEFF is finishing an answer; yours is next")
        self.jeff = "idle"
        self.assertEqual(self.finals()[0]["jeff"], "sent to JEFF")
        self.jeff = "working"
        self.assertEqual(self.finals()[0]["jeff"], "JEFF is answering")

    def test_idle_then_answering(self):
        self.make(jeff="idle")
        self.v.listen()
        self.eng.finish("hello")
        self.assertEqual(self.finals()[0]["jeff"], "sent to JEFF")
        self.jeff = "working"
        self.assertEqual(self.finals()[0]["jeff"], "JEFF is answering")

    def test_kept_rows_go_after_keep(self):
        self.make()
        self.v.listen()
        self.eng.finish("hello")
        self.clock.t += voice.KEEP + 1
        self.assertEqual(self.finals(), [])


class TheMicrophone(Case):
    """a9138: the lit state names the microphone; with none, Talk says so and does not light."""

    def test_lit_names_the_microphone_it_listens_on(self):
        self.make()
        self.eng.mic = "Microphone (Wireless Controller)"
        self.v.listen()
        s = self.state()
        self.assertEqual((s["state"], s["device"], s["mic"]), ("listening", "Microphone (Wireless Controller)", "found"))
        self.assertEqual(self.eng.calls[:2], [("device",), ("listen", "mic")])     # named before anything listens
        self.assertTrue(self.published[-1][0]["device"])                         # in the rows the lens reads

    def test_no_input_device_says_so_and_does_not_light(self):
        self.make()
        self.eng.mic = ""
        r = self.v.listen()
        s = self.state()
        self.assertIn("no microphone", r)
        self.assertEqual((s["state"], s["mic"], s["why"]), ("off", "none", "no microphone found"))
        self.assertNotIn(("listen", "mic"), self.eng.calls)                       # nothing was asked to listen
        self.eng.mic = "Microphone (USB Headset)"                                 # plugged in: the next press lights
        self.v.listen()
        self.assertEqual((self.state()["state"], self.state()["mic"]), ("listening", "found"))

    def test_a_name_that_cannot_be_read_still_lights_and_says_so(self):
        self.make()
        self.eng.mic = None
        self.v.listen()
        self.assertEqual(self.state()["device"], "a microphone Windows did not name")

    def test_the_child_saying_no_microphone_at_listen_turns_it_off(self):
        self.make()
        self.v.listen()
        self.eng.event({"ev": "error", "where": "listen", "why": "no microphone"})
        self.assertEqual((self.state()["state"], self.state()["mic"]), ("off", "none"))

    def test_the_child_renaming_it_while_listening_shows_the_new_name(self):
        self.make()
        self.v.listen()
        self.eng.event({"ev": "device", "name": "Microphone (AudioRelay)"})
        self.assertEqual(self.state()["device"], "Microphone (AudioRelay)")

    def test_the_lens_shows_the_name_and_the_no_microphone_chip(self):
        lens = (HERE / "voice" / "home-voice.lens").read_text(encoding="utf-8")
        self.assertIn('"Listening on $v.device', lens)
        self.assertIn("of witnessed:voice kind=state state=listening as v", lens)
        self.assertIn('"Talk · no microphone"', lens)
        self.assertIn("count(witnessed:voice kind=state mic=none)", lens)


class Echo(unittest.TestCase):
    def test_echo(self):
        self.assertTrue(voice.echo("the board is open", "Done: the board is open now."))
        self.assertFalse(voice.echo("stop please", "Done: the board is open now."))
        self.assertFalse(voice.echo("", "anything"))


if __name__ == "__main__":
    unittest.main()
