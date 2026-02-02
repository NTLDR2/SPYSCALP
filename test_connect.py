
import sys
import os
import logging
from pathlib import Path

# Fix path to allow importing from current directory
sys.path.append(os.getcwd())

# Setup basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_connection():
    print("----------------------------------------------------------------")
    print("Testing TastyTrade Connection...")
    print("----------------------------------------------------------------")
    
    # Locate configuration
    config_path = Path("nuitka_dist/SPYSCALP.conf") # Based on user's file structure
    if not config_path.exists():
        # Fallback to check CWD just in case
        config_path = Path("SPYSCALP.conf")
    
    if not config_path.exists():
        print(f"ERROR: Configuration file not found at {config_path.absolute()}")
        return False

    print(f"Found configuration: {config_path.absolute()}")
    
    # Read manually since ConfigManager is in main.py and relies on CWD constant
    creds = {}
    try:
        with open(config_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == "tt-client-secret": creds["secret"] = val
                    elif key == "tt-client-ID": creds["id"] = val
                    elif key == "tt-refresh-token": creds["token"] = val
                    elif key == "tt-timezone": creds["timezone"] = val
    except Exception as e:
        print(f"ERROR: Failed to parse config: {e}")
        return False
        
    if not creds.get("secret") or not creds.get("token"):
        print("ERROR: Credentials missing in config file.")
        return False
        
    print("Credentials loaded successfully.")
    
    try:
        from quotes import TastyTradeQuoteProvider
    except ImportError as e:
        print(f"ERROR: Failed to import TastyTradeQuoteProvider: {e}")
        return False
        
    try:
        print("Initializing session...")
        provider = TastyTradeQuoteProvider(
            creds.get("id", ""), 
            creds["secret"], 
            creds["token"],
            timezone=creds.get("timezone", "America/New_York")
        )
        print("Session initialized.")
        
        print("Fetching SPY quote...")
        quote = provider.get_quote("SPY")
        print(f"Quote received: {quote}")
        
        if not quote:
            print("WARNING: Quote was empty (market might be closed or data unavailable).")
        
        print("Fetching SPY Option Chain...")
        chain = provider.get_option_chain("SPY")
        print(f"Option chain received: {len(chain)} options retrieved.")
        if chain:
             print(f"Sample option: {chain[0]}")
        
        print("----------------------------------------------------------------")
        print("SUCCESS: Connection verified and data received.")
        return True
        
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
