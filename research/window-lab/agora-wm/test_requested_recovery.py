"""Explicit recovery through the production module, using only fake windows."""
from copy import deepcopy
import ast
from pathlib import Path
import queue
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

from engine import Rect, State, solve
import test_fullscreen_delivery as delivery


class RequestedRecovery(unittest.TestCase):
    setUp = delivery.FullscreenController.setUp
    setup_rows = delivery.FullscreenController.setup_rows
    tick = delivery.FullscreenController.tick
    dispatch = delivery.FullscreenController.dispatch

    def setup_game(self):
        self.gates[:] = ['RocketLeague.exe']
        game = delivery.row('game', (-32000, -32000, 160, 28),
                            exe='C:/Games/RocketLeague.exe', ref=NS(hwnd=1),
                            state='minimised', managed=False, why='frameless; no app rule',
                            _normal=[0, 0, 3840, 2160])
        discord = delivery.row('discord', (-32000, -32000, 160, 28),
                               ref=NS(hwnd=2), state='minimised',
                               _normal=[16, 16, 950, 700])
        self.setup_rows([game, discord])

    def settle(self):
        calls = deepcopy(self.native.calls)
        for _ in range(20):
            self.tick()
        self.assertEqual(self.native.calls, calls, 'background policy touched a window')
        self.assertIsNone(self.m.share)
        self.m.lease.release.assert_not_called()

    def test_requested_restore_recovers_only_game_despite_stale_share_failure(self):
        self.setup_game()
        self.m.failures['game'] = 3
        self.m.share_note = 'Sharing timed out; observed windows retained without further native actions'
        self.m.pending['game'] = {'kind': 'minimise', 'rect': None, 'at': 0}
        result = self.dispatch('wm.restore', 'game')
        self.assertNotIn('refused', result)
        self.assertEqual(self.native.calls, [('restore', 'game'), ('focus', 'game')])
        self.assertEqual(self.native.rows[0]['state'], 'normal')
        self.assertTrue(self.native.rows[0]['focused'])
        self.assertEqual(self.native.rows[1]['state'], 'minimised')
        self.assertEqual(self.m.pending, {})
        self.settle()

    def test_bar_switches_to_discord_and_back_without_minimising_game(self):
        self.setup_game()
        self.assertNotIn('refused', self.dispatch('wm.restore', 'game', share='yes'))
        game_box = deepcopy(self.native.rows[0]['rect'])
        self.assertNotIn('refused', self.dispatch('wm.restore', 'discord', share='yes'))
        self.assertTrue(self.native.rows[1]['focused'])
        self.assertEqual(self.native.rows[0]['state'], 'normal')
        self.assertEqual(self.native.rows[0]['rect'], game_box)
        self.assertNotIn('refused', self.dispatch('wm.focus', 'game', share='yes'))
        self.assertTrue(self.native.rows[0]['focused'])
        self.assertEqual(self.native.calls, [
            ('restore', 'game'), ('focus', 'game'),
            ('restore', 'discord'), ('focus', 'discord'), ('focus', 'game')])
        self.settle()

    def test_fresh_request_gate_replaces_cached_clear_before_same_tick_layout(self):
        self.setup_game()
        # A game can start inside the half-second background gate-cache TTL.
        self.m.gate_cache = ([], self.clock)
        self.assertNotIn('refused', self.dispatch('wm.restore', 'game', share='yes'))
        self.assertEqual(self.native.calls, [('restore', 'game'), ('focus', 'game')])
        self.assertEqual(self.m.gate_cache[0], ['RocketLeague.exe'])
        self.settle()

    def test_focus_recovers_a_game_minimised_outside_the_manager(self):
        self.setup_game()
        self.assertNotIn('refused', self.dispatch('wm.focus', 'game', share='yes'))
        self.native.rows[0]['state'] = 'minimised'
        self.tick()
        self.assertNotIn('refused', self.dispatch('wm.focus', 'game', share='yes'))
        self.assertEqual(self.native.calls.count(('restore', 'game')), 2)
        self.settle()

    def test_exclusive_allows_requested_companion_and_game_but_not_background_sharing(self):
        self.setup_game()
        self.gates += ['notification gate 3', 'full-screen foreground application']
        self.assertNotIn('refused', self.dispatch('wm.restore', 'discord', share='yes'))
        self.assertNotIn('refused', self.dispatch('wm.restore', 'game', share='yes'))
        self.assertEqual(self.native.calls, [('restore', 'discord'), ('focus', 'discord'),
                                          ('restore', 'game'), ('focus', 'game')])
        with self.assertRaises(PermissionError):
            self.m.request_share(key='discord')
        self.settle()

    def test_background_actions_and_destructive_requests_stay_gated(self):
        self.setup_game()
        for verb in ('restore', 'focus', 'move', 'minimise', 'close'):
            with self.subTest(verb=verb):
                with self.assertRaises(PermissionError):
                    self.m.action(verb, 'game')
        for verb in ('minimise', 'close'):
            self.assertIn('refused', self.dispatch('wm.' + verb, 'game'))
        with self.assertRaises(PermissionError):
            self.m.action('restore', 'game', share=True)
        self.assertIn('refused', self.dispatch('wm.arrange'))
        with self.assertRaises(PermissionError):
            self.m.request_share(expect='discord.exe')
        self.assertEqual(self.native.calls, [])
        self.settle()

    def test_multiple_games_do_not_change_scope_of_named_companion_request(self):
        self.setup_game()
        self.native.rows[1]['exe'] = 'C:/Games/OtherGame.exe'
        self.m.rows = self.native.windows()
        self.gates += ['OtherGame.exe', 'notification gate 3']
        self.assertNotIn('refused', self.dispatch('wm.restore', 'discord'))
        self.assertEqual(self.native.calls, [('restore', 'discord'), ('focus', 'discord')])
        self.settle()

    def test_lock_presentation_inspection_and_unknown_gates_still_refuse(self):
        self.setup_game()
        for reason in ('notification gate 1', 'notification gate 4', 'notification gate 7',
                       'notification state unavailable', 'process inspection failed', 'unknown gate'):
            with self.subTest(reason=reason):
                self.gates[:] = ['RocketLeague.exe', reason]
                self.assertIn('refused', self.dispatch('wm.restore', 'game', share='yes'))
                self.assertEqual(self.native.calls, [])
        self.settle()

    def test_missing_owned_excluded_and_pinned_targets_refuse(self):
        self.setup_game()
        self.assertIn('refused', self.dispatch('wm.restore', 'stale-key'))
        game = deepcopy(self.native.rows[0])
        for changes in ({'owned': True}, {'managed': False, 'why': 'elevated or inaccessible'}):
            self.native.rows[0].update(changes)
            self.m.rows = self.native.windows()
            self.assertIn('refused', self.dispatch('wm.restore', 'game'))
            self.native.rows[0] = deepcopy(game)
        self.m.rows = self.native.windows()
        self.m.configure({'never': ['game']})
        self.assertIn('refused', self.dispatch('wm.restore', 'game'))
        self.m.configure({})
        self.m.pins.add('game')
        self.assertIn('refused', self.dispatch('wm.restore', 'game'))
        self.assertEqual(self.native.calls, [])

    def test_untrusted_caller_cannot_request_recovery(self):
        self.setup_game()
        result = self.w.call({'word': 'wm.restore', 'args': {'target': 'game'},
                              'caller': {'person': 'stranger'}})
        self.assertIn('refused', result)
        self.assertTrue(self.w.requests.empty())
        self.assertEqual(self.native.calls, [])

    def test_shadow_and_off_never_gain_native_capability(self):
        self.setup_game()
        for mode in ('shadow', 'off'):
            self.m.mode = mode
            self.assertIn('refused', self.dispatch('wm.restore', 'game', share='yes'))
        self.assertEqual(self.native.calls, [])

    def test_failed_native_restore_stops_without_focus_or_retry(self):
        self.setup_game()
        def refused(ref):
            self.native.calls.append(('denied-restore', 'game'))
            raise PermissionError('fixture identity changed')
        self.native.restore = refused
        self.assertIn('refused', self.dispatch('wm.restore', 'game'))
        self.assertEqual(self.native.calls, [('denied-restore', 'game')])
        self.settle()

    def test_windows_focus_denial_is_reported_without_retry(self):
        self.setup_game()
        self.native.focus = lambda ref: False
        result = self.dispatch('wm.restore', 'game')
        self.assertIn('Windows refused focus', result['text'])
        self.assertEqual(self.native.calls, [('restore', 'game')])
        self.settle()

    def test_recovery_cancels_old_share_and_motion_debt(self):
        self.setup_game()
        self.m.share = {'keys': {'game', 'discord'}, 'until': self.clock + 5}
        self.m.motion['game'] = (Rect(0, 0, 500, 500), Rect(100, 100, 500, 500), 0)
        self.assertNotIn('refused', self.dispatch('wm.restore', 'game'))
        self.assertEqual(self.m.motion, {})
        self.settle()

    def test_direct_and_bar_activation_of_arbitrary_companion_are_target_only(self):
        for share in ({}, {'share': 'yes'}):
            for word in ('wm.focus', 'wm.restore'):
                with self.subTest(share=share, word=word):
                    self.setup_game()
                    self.native.rows[1].update(app='Notes', exe='C:/Apps/Notes.exe')
                    self.m.rows = self.native.windows()
                    self.gates += ['notification gate 3']
                    self.assertNotIn('refused', self.dispatch(word, 'discord', **share))
                    self.assertEqual(self.native.calls, [('restore', 'discord'), ('focus', 'discord')])
                    self.settle()

    def test_requested_moves_never_focus_restore_or_move_neighbours(self):
        self.setup_game()
        self.gates += ['notification gate 3']
        for row in self.native.rows:
            row.update(state='normal', rect=[16, 16, 800, 600])
        self.m.rows = self.native.windows()
        for key in ('game', 'discord'):
            before = deepcopy(self.native.rows)
            self.assertNotIn('refused', self.dispatch('wm.move', key, at='100,150', size='900,700'))
            target = next(r for r in self.native.rows if r['key'] == key)
            other = next(r for r in self.native.rows if r['key'] != key)
            self.assertEqual(target['rect'], [100, 150, 900, 700])
            self.assertEqual(other, next(r for r in before if r['key'] != key))
        self.assertEqual(self.native.calls, [('place', 'game'), ('place', 'discord')])
        self.settle()

    def test_move_validation_refuses_before_any_native_effect(self):
        self.setup_game()
        self.native.rows[1].update(state='normal', rect=[16, 16, 800, 600])
        self.m.rows = self.native.windows()
        for kv in ({}, {'at': '1'}, {'at': '1,nan'}, {'at': '1,2', 'size': '0,20'},
                   {'at': '-900,0'}, {'at': '1,2', 'size': '9000,20'},
                   {'at': '1,2', 'force': 'yes'}):
            self.assertIn('refused', self.dispatch('wm.move', 'discord', **kv))
        self.assertIn('refused', self.dispatch('wm.move', 'game', at='10,10'))
        self.gates.append('process inspection failed')
        self.assertIn('refused', self.dispatch('wm.move', 'discord', at='10,10'))
        self.assertEqual(self.native.calls, [])

    def test_move_retains_size_and_does_not_retry_app_refusal(self):
        self.setup_game()
        self.native.rows[1].update(state='normal', rect=[16, 16, 800, 600])
        self.m.rows = self.native.windows()
        self.assertNotIn('refused', self.dispatch('wm.move', 'discord', at='80,90'))
        self.assertEqual(self.native.rows[1]['rect'], [80, 90, 800, 600])
        def refuse(ref, box):
            self.native.calls.append(('denied-place', 'discord'))
            raise PermissionError('fixture refuses geometry')
        self.native.place = refuse
        self.assertIn('refused', self.dispatch('wm.move', 'discord', at='100,110'))
        self.assertEqual(self.native.calls, [('place', 'discord'), ('denied-place', 'discord')])
        self.settle()

    def arm_launch(self, expect='C:/Apps/Notes.exe'):
        result = self.dispatch('wm.arrange', expect=expect)
        self.assertNotIn('refused', result)
        self.assertEqual(self.native.calls, [], 'arming alone must not touch a window')

    def new_window(self, key='notes', exe='C:/Apps/Notes.exe', **kw):
        return delivery.row(key, (40, 50, 700, 600), exe=exe, ref=NS(hwnd=3), **kw)

    def test_bar_launch_activates_only_matching_new_executable_once(self):
        self.setup_game()
        self.gates.append('notification gate 3')
        self.arm_launch()
        self.native.rows.append(self.new_window('unrelated', 'C:/Apps/Other.exe'))
        self.tick()
        self.assertEqual(self.native.calls, [])
        self.native.rows[-1]['ref'] = NS(hwnd=4)
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertEqual(self.native.calls, [('focus', 'notes')])
        self.assertEqual(self.native.rows[0]['state'], 'minimised')
        self.settle()

    def test_bar_launch_new_agora_window_uses_same_target_only_request(self):
        self.setup_game()
        self.arm_launch('agora')
        self.native.rows.append(self.new_window(exe='python.exe', agora='fixture-notes'))
        self.tick()
        self.assertEqual(self.native.calls, [('focus', 'notes')])
        self.settle()

    def test_bar_launch_timeout_does_not_activate_late_window(self):
        self.setup_game()
        self.arm_launch()
        self.clock += 6
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertEqual(self.native.calls, [])
        self.settle()

    def test_ambiguous_launch_does_not_pick_an_unrequested_window(self):
        self.setup_game()
        self.arm_launch()
        self.native.rows += [self.new_window(), self.new_window('second')]
        self.native.rows[-1]['ref'] = NS(hwnd=4)
        self.tick()
        self.assertEqual(self.native.calls, [])
        self.clock += 6
        self.settle()

    def test_launch_is_cancelled_by_hard_gate_without_later_retry(self):
        self.setup_game()
        self.arm_launch()
        self.gates.append('notification gate 1')
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertIsNone(self.m.share)
        self.gates.pop()
        self.assertEqual(self.native.calls, [])
        self.settle()

    def test_launch_native_denial_is_consumed_once(self):
        self.setup_game()
        self.arm_launch()
        def refuse(ref):
            self.native.calls.append(('denied-focus', self.native.find(ref)['key']))
            raise PermissionError('fixture identity changed')
        self.native.focus = refuse
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertEqual(self.native.calls, [('denied-focus', 'notes')])
        self.settle()

    def test_leaving_live_cancels_pending_launch_before_native_action(self):
        self.setup_game()
        self.arm_launch()
        self.m.mode = 'shadow'
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertEqual(self.native.calls, [])
        self.assertIsNone(self.m.share)

    def test_expired_or_cancelled_queued_request_cannot_focus_later(self):
        self.setup_game()
        for cancelled, deadline in ((True, float('inf')), (False, 0)):
            answer = queue.Queue()
            answer.cancelled, answer.deadline = cancelled, deadline
            self.w.requests.put(('action', ('restore', 'game', False, True), answer))
            self.tick()
            self.assertIn('refused', answer.get_nowait())
        self.assertEqual(self.native.calls, [])

    def test_game_start_during_armed_launch_cannot_admit_neighbour_reflow(self):
        self.setup_game()
        self.gates.clear()
        self.arm_launch()
        self.gates[:] = ['RocketLeague.exe']
        self.native.rows.append(self.new_window())
        self.tick()
        self.assertEqual(self.native.calls, [('focus', 'notes')])
        self.settle()

    def test_new_executable_invalidates_clear_cache_before_background_layout(self):
        self.setup_game()
        self.m.gate_cache = ([], self.clock)
        self.native.rows.append(self.new_window('newgame', 'C:/Games/NewGame.exe'))
        self.gates[:] = ['NewGame.exe']
        self.tick()
        self.assertEqual(self.native.calls, [])
        self.assertEqual(self.m.gate_cache[0], ['NewGame.exe'])
        self.settle()


class CapacityProtection(unittest.TestCase):
    setUp = delivery.FullscreenController.setUp
    setup_rows = delivery.FullscreenController.setup_rows
    tick = delivery.FullscreenController.tick

    def pressure_plan(self, first='game'):
        # The pure solver still proposes eviction: the native seam must refuse it.
        state = State(work=Rect(0, 0, 650, 450))
        for key in (first, 'companion' if first=='game' else 'game'):
            state = solve(state, {'type': 'open', 'key': key, 'window': {
                'preferred': (600, 400), 'minimum': (400, 280)}}).state
        plan=solve(state,{'type':'noop'})
        self.assertIn(first,plan.minimise, 'fixture must actually need eviction')
        return plan

    def pressure_rows(self):
        return [delivery.row('game',(10,10,600,400),ref=NS(hwnd=1),focused=True),
                delivery.row('companion',(30,30,600,400),ref=NS(hwnd=2))]

    def test_capacity_pressure_while_gated_never_moves_or_minimises_game_or_companion(self):
        for reasons in (['game.exe'],['notification gate 3'],['full-screen foreground application']):
            for first in ('game','companion'):
                with self.subTest(reasons=reasons,oldest=first):
                    plan=self.pressure_plan(first)
                    self.gates[:]=reasons
                    self.setup_rows(self.pressure_rows(),plan.state.work)
                    before=deepcopy(self.native.rows)
                    # Check both normal ticks and a precomputed pressure plan at
                    # the common native boundary (e.g. stale work from before gate).
                    self.m.state=plan.state
                    self.m.apply(plan,{r['key']:r for r in self.native.rows})
                    for _ in range(20):self.tick()
                    self.assertEqual(self.native.calls,[])
                    self.assertEqual(self.native.rows,before)
                    self.m.lease.save.assert_not_called()

    def test_ungated_capacity_cannot_hide_unrecognised_game_or_companion(self):
        for first in ('game','companion'):
            with self.subTest(oldest=first):
                plan=self.pressure_plan(first)
                # Start under a gate to seed observation without any placement.
                self.setup_rows(self.pressure_rows(),plan.state.work)
                self.gates.clear();self.m.gate_cache=([],self.clock)
                before=deepcopy(self.native.rows)
                self.m.state=plan.state
                self.m.apply(plan,{r['key']:r for r in self.native.rows})
                for _ in range(20):self.tick()
                self.assertEqual(self.native.calls,[])
                self.assertEqual(self.native.rows,before)
                self.m.lease.save.assert_not_called()
                # Holding capacity debt must not permanently strand ordinary
                # layout after more space becomes available.
                self.m.configure({'sizes':{'ordinary':{'min_width':400/(2000-48),'min_height':280/(1200-32)}}})
                self.m.ingest(self.native.windows(),Rect(0,0,2000,1200))
                self.assertTrue(self.native.calls)
                self.assertFalse(any(c[0]=='minimise' for c in self.native.calls))
                self.assertTrue(all(r['state']=='normal' for r in self.native.rows))
                self.gates[:]=['game.exe']


class NativeRestoreContract(unittest.TestCase):
    def test_native_restore_checks_identity_and_reports_failure_to_start(self):
        # Compile the production method alone; no Win32 module initialization,
        # real handles, desktop observations or native calls.
        path = Path(__file__).with_name('win32_host.py')
        tree = ast.parse(path.read_text(encoding='utf-8'))
        native = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Native')
        method = next(n for n in native.body if isinstance(n, ast.FunctionDef) and n.name == 'restore')
        api = Mock()
        namespace = {'u': api, 'C': NS(get_last_error=lambda: 5)}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
        instance = Mock()
        ref = NS(hwnd=123)
        api.ShowWindowAsync.return_value = 0
        with self.assertRaises(OSError):
            namespace['restore'](instance, ref)
        instance.check.assert_called_once_with(ref)
        api.ShowWindowAsync.assert_called_once_with(123, 4)
        api.reset_mock()
        instance.check.side_effect = PermissionError('reused identity')
        with self.assertRaises(PermissionError):
            namespace['restore'](instance, ref)
        api.ShowWindowAsync.assert_not_called()
        instance.check.side_effect = None
        api.ShowWindowAsync.return_value = 1
        namespace['restore'](instance, ref)
        api.ShowWindowAsync.assert_called_once_with(123, 4)


if __name__ == '__main__':
    unittest.main()
