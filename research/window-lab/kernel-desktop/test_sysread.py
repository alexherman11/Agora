"""Hidden read-only integration and failure-path checks; no windows are created."""

import ctypes as C
from ctypes import wintypes as W
import json
import math
import threading
import time
import unittest
from unittest.mock import patch

import sysread as s


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.reader = s.Reader()

    def pct(self, value):
        self.assertIsInstance(value, (int, float))
        self.assertTrue(math.isfinite(value))
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 100)

    def validate(self, name, value):
        if value is None:
            return
        if name == "cpu":
            self.assertIsInstance(value, float)
            self.pct(value)
        elif name == "memory":
            self.assertEqual(set(value), {"pct", "used_gb", "total_gb"})
            self.pct(value["pct"])
            for key in value:
                self.assertIsInstance(value[key], float)
            self.assertGreater(value["total_gb"], 0)
            self.assertGreaterEqual(value["used_gb"], 0)
            self.assertLessEqual(value["used_gb"], value["total_gb"])
        elif name == "network":
            self.assertEqual(set(value), {"down", "up"})
            for rate in value.values():
                self.assertIsInstance(rate, (int, float))
                self.assertTrue(math.isfinite(rate))
                self.assertGreaterEqual(rate, 0)
        elif name in ("volume", "battery"):
            flag = "muted" if name == "volume" else "charging"
            self.assertEqual(set(value), {"pct", flag})
            self.assertIs(type(value["pct"]), int)
            self.pct(value["pct"])
            self.assertIs(type(value[flag]), bool)
        elif name == "focused":
            self.assertEqual(set(value), {"program", "title"})
            self.assertTrue(value["program"])
            self.assertIsInstance(value["title"], str)
        elif name == "apps":
            self.assertIsInstance(value, list)
            self.assertEqual(value, sorted(value, key=lambda x: (-x["count"], x["program"])))
            self.assertEqual(len({v["program"] for v in value}), len(value))
            for app in value:
                self.assertEqual(set(app), {"program", "count"})
                self.assertIsInstance(app["program"], str)
                self.assertNotIn(app["program"], self.reader.exclude)
                self.assertIs(type(app["count"]), int)
                self.assertGreater(app["count"], 0)

    def test_live_readings_and_latency(self):
        for name in ("cpu", "memory", "network", "volume", "battery", "focused", "apps"):
            with self.subTest(reading=name):
                start = time.perf_counter()
                value = getattr(self.reader, name)()
                elapsed = time.perf_counter() - start
                self.assertLess(elapsed, .2, (name, elapsed))
                self.validate(name, value)
                # This machine must actually deliver its fundamental counters.
                if name in ("cpu", "memory", "network"):
                    self.assertIsNotNone(value)

    def test_read_all_json_and_latency(self):
        start = time.perf_counter()
        result = self.reader.read_all()
        self.assertLess(time.perf_counter() - start, .2)
        self.assertEqual(set(result), {"cpu", "memory", "network", "volume",
                                      "battery", "focused", "apps", "at"})
        json.dumps(result, allow_nan=False)
        for name in ("cpu", "memory", "network", "volume", "battery"):
            if result[name] is not None:
                self.assertIsInstance(result[name]["text"], str)
        self.assertLess(abs(result["at"] - time.time()), 1)

    def test_cpu_known_deltas(self):
        with patch.object(s, "_times", side_effect=[(100, 200, 100), (120, 260, 140)]), \
                patch.object(s.time, "sleep") as sleep:
            self.assertEqual(self.reader.cpu(), 80.0)
            sleep.assert_called_once_with(.1)
        with patch.object(s, "_times", return_value=(120, 260, 140)):
            self.assertIsNone(self.reader.cpu())  # no elapsed counter ticks

    def test_failures_return_none(self):
        cases = {"cpu": "_times", "memory": "_memory", "network": "_get_table",
                 "volume": "_coinit", "battery": "_power", "focused": "_foreground",
                 "apps": "_enum"}
        for method, api in cases.items():
            with self.subTest(method=method), patch.object(s, api, side_effect=OSError("test")):
                self.assertIsNone(getattr(self.reader, method)())

    def test_network_layout_and_adapter_changes(self):
        self.assertEqual(C.sizeof(s._IfRow), 1352)
        self.assertEqual(s._IfTable.rows.offset, 8)

        class Table(C.Structure):
            _fields_ = [("count", W.ULONG), ("rows", s._IfRow * 3)]

        table = Table()
        table.count = 3
        for i, row in enumerate(table.rows):
            row.luid, row.status, row.type = i + 1, 1, 6
            row.in_octets, row.out_octets = 100, 50
        table.rows[1].type = 24  # loopback must not contribute
        table.rows[2].status = 2  # down must not contribute

        def get_table(out):
            C.cast(out, C.POINTER(s._P))[0] = C.addressof(table)
            return 0

        with patch.object(s, "_get_table", side_effect=get_table), \
                patch.object(s, "_free_table") as free, \
                patch.object(s.time, "perf_counter", side_effect=[1., 3., 4., 5.]):
            self.assertEqual(self.reader.network(), {"down": 0., "up": 0.})
            table.rows[0].in_octets += 400
            table.rows[0].out_octets += 100
            table.rows[1].in_octets += 999999
            self.assertEqual(self.reader.network(), {"down": 200., "up": 50.})
            table.rows[0].in_octets = 0  # reset
            table.rows[0].out_octets = 0
            self.assertEqual(self.reader.network(), {"down": 0., "up": 0.})
            table.rows[0].luid = 99  # new adapter
            table.rows[0].in_octets = 999999
            self.assertEqual(self.reader.network(), {"down": 0., "up": 0.})
            self.assertEqual(free.call_count, 4)

    def test_battery_absent_unknown_and_charging(self):
        def status(out):
            C.cast(out, C.POINTER(s._Power))[0] = power
            return True
        power = s._Power()
        with patch.object(s, "_power", side_effect=status):
            for flag in (128, 255):
                power.flags = flag
                self.assertIsNone(self.reader.battery())
            power.flags, power.pct = 8, 80
            self.assertEqual(self.reader.battery(), {"pct": 80, "charging": True})
            power.pct = 255
            self.assertIsNone(self.reader.battery())

    def test_com_sta_and_cleanup_on_failure(self):
        # Exercise both owned MTA initialization and an existing STA apartment.
        for hr in (0, 1, -2147417850):  # S_OK, S_FALSE, RPC_E_CHANGED_MODE
            def create(*args):
                C.cast(args[-1], C.POINTER(s._P))[0] = 123
                return 0

            def com(obj, slot, *args):
                return -2147467259 if slot == 4 else 0  # endpoint failure

            with self.subTest(hr=hr), patch.object(s, "_coinit", return_value=hr), \
                    patch.object(s, "_create", side_effect=create), \
                    patch.object(s, "_com", side_effect=com) as call, \
                    patch.object(s, "_couninit") as uninit:
                self.assertIsNone(self.reader.volume())
                self.assertEqual(call.call_args_list[-1].args[1], 2)  # Release
                self.assertEqual(uninit.call_count, int(hr >= 0))

    def test_window_filters_grouping_and_exclusions(self):
        # Synthetic HWNDs exercise every filter without creating any windows.
        def enumerate_windows(callback, _):
            return all(callback(hwnd, 0) for hwnd in range(1, 11))

        def cloak(hwnd, attr, out, size):
            self.assertEqual(attr, 14)
            C.cast(out, C.POINTER(W.DWORD))[0] = int(hwnd == 5)
            return 0

        names = {6: "python", 7: "chrome", 8: "chrome", 9: "zeta", 10: "alpha"}
        with patch.object(s, "_enum", side_effect=enumerate_windows), \
                patch.object(s, "_visible", side_effect=lambda h: h != 1), \
                patch.object(s, "_owner", side_effect=lambda h, _: int(h == 2)), \
                patch.object(s, "_style", side_effect=lambda h, _: 0x80 if h == 3 else 0), \
                patch.object(s, "_title", side_effect=lambda h: "" if h == 4 else "Title"), \
                patch.object(s, "_cloaked", side_effect=cloak), \
                patch.object(s, "_program", side_effect=lambda h: names.get(h)):
            self.assertEqual(self.reader.apps(), [
                {"program": "chrome", "count": 2}, {"program": "alpha", "count": 1},
                {"program": "zeta", "count": 1}])
            self.assertIn({"program": "python", "count": 1}, s.Reader(exclude=()).apps())

    def test_process_and_table_cleanup_on_failure(self):
        with patch.object(s, "_pid", return_value=1) as pid, \
                patch.object(s, "_open_process", return_value=123), \
                patch.object(s, "_image", return_value=False), \
                patch.object(s, "_close") as close:
            def assign_pid(hwnd, out):
                C.cast(out, C.POINTER(W.DWORD))[0] = 10
                return 1
            pid.side_effect = assign_pid
            self.assertIsNone(s._program(1))
            close.assert_called_once_with(123)

        def fail_with_allocation(out):
            C.cast(out, C.POINTER(s._P))[0] = 123
            return 1
        with patch.object(s, "_get_table", side_effect=fail_with_allocation), \
                patch.object(s, "_free_table") as free:
            self.assertIsNone(self.reader.network())
            self.assertEqual(free.call_count, 1)

    def test_second_thread_50_calls_and_handles(self):
        get_count = s._bind(s._kernel, "GetProcessHandleCount", W.BOOL,
                            W.HANDLE, C.POINTER(W.DWORD))
        current = s._bind(s._kernel, "GetCurrentProcess", W.HANDLE)

        def handles():
            count = W.DWORD()
            self.assertTrue(get_count(current(), C.byref(count)))
            return count.value

        # Warm up COM/RPC's process caches before measuring persistent handles.
        self.reader.read_all()
        errors, measurements = [], []

        def worker():
            try:
                self.reader.read_all()
                before = handles()
                for _ in range(50):
                    result = self.reader.read_all()
                    self.assertIsInstance(result, dict)
                    json.dumps(result, allow_nan=False)
                measurements.extend((before, handles()))
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(20)
        self.assertFalse(thread.is_alive(), "worker did not finish")
        self.assertEqual(errors, [])
        before, after = measurements
        self.assertLessEqual(after - before, 5, (before, after))
        print(f"\n50 worker calls: handles {before} -> {after}")


if __name__ == "__main__":
    unittest.main()
