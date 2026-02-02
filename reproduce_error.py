import sys
import logging
from datetime import datetime

# Setup minimal logging to see where it fails
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("REPRO")

try:
    print("--- STEP 1: Import TastyTrade utils ---")
    import tastytrade.utils as tt_utils
    print(f"TastyTrade TZ: {tt_utils.TZ}")
    
    print("\n--- STEP 2: Import pandas_market_calendars ---")
    import pandas_market_calendars as mcal
    
    print("\n--- STEP 3: Get NYSE calendar ---")
    nyse = mcal.get_calendar("NYSE")
    print(f"NYSE Calendar: {nyse}")
    print(f"NYSE TZ: {nyse.tz}")
    
    print("\n--- STEP 4: Call now_in_new_york ---")
    now = tt_utils.now_in_new_york()
    print(f"Now in NY: {now}")

    print("\n--- STEP 5: Test pandas timezone lookup ---")
    import pandas as pd
    try:
        ts = pd.Timestamp.now(tz="America/New_York")
        print(f"Timestamp with NY tz: {ts}")
    except Exception as e:
        print(f"FAILED pandas NY lookup: {e}")

    print("\n--- STEP 6: Test known problematic key ---")
    try:
        ts = pd.Timestamp.now(tz="America/Argentina/Buenos_Aires")
        print(f"Timestamp with BA tz: {ts}")
    except Exception as e:
        print(f"FAILED pandas BA lookup: {e}")

except Exception as e:
    logger.exception("General failure in script")
    print(f"\nCRITICAL ERROR: {e}")

print("\nScript completed.")
