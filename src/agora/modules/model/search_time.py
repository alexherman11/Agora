"""Read-only Pacific calendar conversion, without installing timezone data.

Windows supplies its own dynamic timezone database. Never calls a Set* API.
If neither database is available, callers must abstain from date claims.
"""
import datetime as dt
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def pacific_date(value):
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    try:
        return value.astimezone(ZoneInfo("America/Los_Angeles")).date()
    except ZoneInfoNotFoundError:
        if sys.platform != "win32":
            raise ValueError("Pacific timezone data unavailable") from None
    import ctypes as C
    from ctypes import wintypes as W

    class SYSTEMTIME(C.Structure):
        _fields_ = [(name, W.WORD) for name in
                    ("year", "month", "weekday", "day", "hour", "minute", "second", "ms")]

    class DYNAMIC_TIME_ZONE_INFORMATION(C.Structure):
        _fields_ = [("bias", W.LONG), ("standard_name", W.WCHAR * 32),
                    ("standard_date", SYSTEMTIME), ("standard_bias", W.LONG),
                    ("daylight_name", W.WCHAR * 32), ("daylight_date", SYSTEMTIME),
                    ("daylight_bias", W.LONG), ("key", W.WCHAR * 128),
                    ("disabled", W.BYTE)]

    k = C.WinDLL("kernel32", use_last_error=True)
    enum = C.WinDLL("advapi32", use_last_error=True).EnumDynamicTimeZoneInformation
    enum.argtypes = [W.DWORD, C.POINTER(DYNAMIC_TIME_ZONE_INFORMATION)]
    enum.restype = W.DWORD
    convert = k.SystemTimeToTzSpecificLocalTimeEx
    convert.argtypes = [C.POINTER(DYNAMIC_TIME_ZONE_INFORMATION),
                        C.POINTER(SYSTEMTIME), C.POINTER(SYSTEMTIME)]
    convert.restype = W.BOOL
    zone = DYNAMIC_TIME_ZONE_INFORMATION()
    for i in range(1024):
        code = enum(i, C.byref(zone))
        if code:
            break
        if zone.key == "Pacific Standard Time":
            utc = value.astimezone(dt.timezone.utc)
            source = SYSTEMTIME(utc.year, utc.month, 0, utc.day,
                                utc.hour, utc.minute, utc.second, 0)
            local = SYSTEMTIME()
            if convert(C.byref(zone), C.byref(source), C.byref(local)):
                return dt.date(local.year, local.month, local.day)
            break
    raise ValueError("Pacific timezone conversion unavailable")
