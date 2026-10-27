import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock
import watchdog


class WatchdogSafety(unittest.TestCase):
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
