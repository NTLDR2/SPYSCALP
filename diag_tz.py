import zoneinfo
import pandas_market_calendars as mcal
from tastytrade.utils import now_in_new_york
import logging

logging.basicConfig(level=logging.DEBUG)

print("Checking ZoneInfo for US/Eastern...")
try:
    zi = zoneinfo.ZoneInfo("US/Eastern")
    print(f"Success: {zi}")
except Exception as e:
    print(f"FAILED ZoneInfo(US/Eastern): {e}")

print("\nChecking ZoneInfo for America/New_York...")
try:
    zi = zoneinfo.ZoneInfo("America/New_York")
    print(f"Success: {zi}")
except Exception as e:
    print(f"FAILED ZoneInfo(America/New_York): {e}")

print("\nChecking pandas_market_calendars for NYSE...")
try:
    nyse = mcal.get_calendar("NYSE")
    print(f"Success: {nyse}")
    print(f"NYSE TZ: {nyse.tz}")
except Exception as e:
    print(f"FAILED mcal.get_calendar(NYSE): {e}")

print("\nChecking tastytrade now_in_new_york()...")
try:
    now = now_in_new_york()
    print(f"Success: {now}")
except Exception as e:
    print(f"FAILED now_in_new_york(): {e}")

print("\nTesting known problematic key America/Argentina/Buenos_Aires...")
try:
    zi = zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")
    print(f"Success: {zi}")
except Exception as e:
    print(f"FAILED ZoneInfo(America/Argentina/Buenos_Aires): {e}")

print("\nChecking pytz for America/New_York...")
try:
    import pytz
    tz = pytz.timezone("America/New_York")
    print(f"Success: {tz}")
except Exception as e:
    print(f"FAILED pytz.timezone(America/New_York): {e}")

print("\nChecking tzlocal.get_localzone()...")
try:
    import tzlocal
    tz = tzlocal.get_localzone()
    print(f"Success local zone: {tz}")
except Exception as e:
    print(f"FAILED tzlocal.get_localzone(): {e}")

print("\nChecking pytz for America/Argentina/Buenos_Aires...")
try:
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    print(f"Success: {tz}")
except Exception as e:
    print(f"FAILED pytz.timezone(America/Argentina/Buenos_Aires): {e}")
