import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock
from manager import Manager
import watchdog


class WatchdogSafety(unittest.TestCase):
    def lease_data(self):
        return {'windows':[{
            'ref':{'hwnd':i,'process':{'pid':i,'created':99,'exe':exe},'thread':7,'cls':'fixture'},
            'cookie':11,'placement':{'normal':[20,30,600,400]},'dwm':{'33':2,'34':42},
            'restore_geometry':True
        } for i,exe in enumerate(('game.exe','companion.exe'),1)]}

    def test_off_while_gated_releases_game_and_companion_without_window_changes(self):
        for mode in ('off','shadow'):
            for reasons in (['game.exe'],['full-screen foreground application'],
                            ['notification gate 3'],['process inspection failed'],OSError('inspection failed')):
                with self.subTest(mode=mode,reasons=reasons),tempfile.TemporaryDirectory() as folder:
                    path=Path(folder)/'lease.json'
                    watchdog.write(path,self.lease_data())
                    native=Mock()
                    manager=Manager(native,folder,gate_fn=lambda:[])
                    manager.mode='live';manager.lease=watchdog.Lease(path)
                    native.reset_mock()
                    gate=Mock(side_effect=reasons) if isinstance(reasons,Exception) else Mock(return_value=reasons)
                    with patch.object(watchdog,'gate',gate),patch.object(watchdog,'Native',return_value=native), \
                            patch.object(watchdog,'same',return_value=True), \
                            patch.object(watchdog.u,'GetPropW',return_value=11), \
                            patch.object(watchdog.u,'RemovePropW') as remove:
                        manager.switch(mode)  # actual off -> Lease.release -> shared recovery
                        self.assertEqual(native.mock_calls,[], 'no placement, style, minimise or focus')
                        self.assertEqual(remove.call_count,2)
                        self.assertIsNone(manager.lease)
                        self.assertFalse(native.mutating)
                        data=json.loads(path.read_text())
                        self.assertTrue(data['released'])
                        self.assertTrue(all('without window changes' in e['outcome'] for e in data['windows']))
                        # No deferred restoration when the gate later clears.
                        gate.side_effect=None;gate.return_value=[]
                        self.assertEqual(watchdog.release_all(path,native),[])
                        self.assertEqual(native.mock_calls,[])
                        self.assertEqual(remove.call_count,2)

    def test_clear_release_restores_geometry_and_style_but_not_border_only_geometry(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lease.json';data=self.lease_data()
            data['windows'][1]['restore_geometry']=False
            watchdog.write(path,data);native=Mock()
            with patch.object(watchdog,'gate',return_value=[]),patch.object(watchdog,'same',return_value=True), \
                    patch.object(watchdog.u,'GetPropW',return_value=11),patch.object(watchdog.u,'RemovePropW') as remove:
                result=watchdog.release_all(path,native)
            self.assertEqual([r['outcome'] for r in result],['restored','restored'])
            native.restore_placement.assert_called_once_with(
                watchdog.WindowRef(**data['windows'][0]['ref']),data['windows'][0]['placement'])
            self.assertEqual(native.style.call_count,2)
            self.assertEqual(remove.call_count,2)

    def test_gate_appearing_during_release_stops_remaining_window_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lease.json';watchdog.write(path,self.lease_data());native=Mock()
            with patch.object(watchdog,'gate',side_effect=[[],['game.exe']]), \
                    patch.object(watchdog,'same',return_value=True),patch.object(watchdog.u,'GetPropW',return_value=11), \
                    patch.object(watchdog.u,'RemovePropW') as remove:
                result=watchdog.release_all(path,native)
            native.restore_placement.assert_called_once()
            native.style.assert_called_once()
            self.assertEqual(remove.call_count,2)
            self.assertEqual(result[0]['outcome'],'restored')
            self.assertIn('without window changes',result[1]['outcome'])

    def test_atomic_replace_retries_transient_windows_reader_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lease.json';path.write_text('{"old":true}')
            real=watchdog.os.replace;calls=[]
            def replace(a,b):
                calls.append(1)
                if len(calls)<3:
                    self.assertEqual(json.loads(path.read_text()),{'old':True})
                    raise PermissionError('reader denies delete sharing')
                real(a,b)
            with patch.object(watchdog.os,'replace',replace):watchdog.write(path,{'new':True})
            self.assertEqual(json.loads(path.read_text()),{'new':True})
            self.assertEqual(len(calls),3)

    def test_reused_process_identity_and_missing_cookie_never_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lease.json';native=Mock()
            entry={'ref':{'hwnd':123,'process':{'pid':1,'created':99,'exe':'fixture.exe'},'thread':7,'cls':'fixture'},
                'cookie':11,'placement':{},'dwm':{}}
            for matching in (True,False):
                watchdog.write(path,{'windows':[entry]})
                with patch.object(watchdog,'same',return_value=matching),patch.object(watchdog.u,'GetPropW',return_value=12):
                    result=watchdog.release_all(path,native)
                native.restore_placement.assert_not_called();native.style.assert_not_called()
                self.assertIn('untouched',result[0]['outcome'])
                self.assertEqual(watchdog.release_all(path,native),[])


if __name__=='__main__':unittest.main()
