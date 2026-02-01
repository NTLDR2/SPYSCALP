import random
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict

try:
    from tastytrade import Session
    from tastytrade.instruments import NestedOptionChain, OptionType
    from tastytrade.market_data import get_market_data, get_market_data_by_type
    from tastytrade.order import InstrumentType
    HAS_TT_SDK = True
except ImportError:
    HAS_TT_SDK = False

class QuoteProvider:
    """Base class for quote providers."""
    def get_quote(self, symbol: str) -> dict:
        raise NotImplementedError

    def get_option_chain(self, symbol: str) -> list:
        raise NotImplementedError

class MockQuoteProvider(QuoteProvider):
    """Mock provider for testing without API keys."""
    
    def get_quote(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "last": round(490.0 + random.uniform(-1, 1), 2),
            "change": round(random.uniform(-0.5, 0.5), 2),
            "volume": random.randint(1000000, 5000000),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

    def get_option_chain(self, symbol: str) -> list:
        # Generate some mock options
        options = []
        base_price = 490
        expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        for i in range(-5, 6):
            strike = base_price + i
            # Call
            options.append({
                "strike": strike,
                "type": "CALL",
                "bid": round(random.uniform(1, 5), 2),
                "ask": round(random.uniform(1, 5), 2),
                "expiry": expiry
            })
            # Put
            options.append({
                "strike": strike,
                "type": "PUT",
                "bid": round(random.uniform(1, 5), 2),
                "ask": round(random.uniform(1, 5), 2),
                "expiry": expiry
            })
        return options

class TastyTradeQuoteProvider(QuoteProvider):
    """Real provider using TastyTrade API."""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, timezone: str = "America/New_York"):
        if not HAS_TT_SDK:
            raise ImportError("tastytrade SDK not installed")
        
        # Set the global timezone for the SDK
        try:
            import tastytrade.utils
            from zoneinfo import ZoneInfo
            tastytrade.utils.TZ = ZoneInfo(timezone)
            logging.info(f"TastyTrade SDK timezone set to: {timezone}")
        except Exception as e:
            logging.error(f"Failed to set TastyTrade timezone: {e}")

        self.session = Session(
            provider_secret=client_secret,
            refresh_token=refresh_token
        )
        # Note: client_id is often part of the refresh token flow but Session class 
        # specifically asks for provider_secret (client_secret) and refresh_token.
        # client_id is usually used to get the refresh token.

    def get_quote(self, symbol: str) -> dict:
        try:
            # We assume it's an equity for SPY
            data = get_market_data(self.session, symbol, InstrumentType.EQUITY)
            return {
                "symbol": symbol,
                "last": float(data.last) if data.last else 0.0,
                "change": float(data.last - data.prev_close) if data.last and data.prev_close else 0.0,
                "volume": int(data.volume) if data.volume else 0,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            logging.error(f"Error fetching quote for {symbol}: {e}")
            return {}

    def get_option_chain(self, symbol: str) -> list:
        try:
            # Get the nested chain
            chains = NestedOptionChain.get(self.session, symbol)
            if not chains:
                return []
            
            # Use the first chain (usually the main one)
            chain = chains[0]
            
            # Get the first expiration for simplicity/example
            # In a real app, we might want to filter or let the user choose
            if not chain.expirations:
                return []
                
            expiration = chain.expirations[0]
            expiry_str = expiration.expiration_date.strftime("%Y-%m-%d")
            
            # Prepare all symbols to fetch market data in one go
            call_symbols = [strike.call_streamer_symbol for strike in expiration.strikes]
            put_symbols = [strike.put_streamer_symbol for strike in expiration.strikes]
            
            # Fetch market data for all options
            # Note: combined limit is 100, we might need to chunk if strikes > 50
            all_symbols = call_symbols + put_symbols
            # For simplicity, we'll just take the first few if it's too many
            if len(all_symbols) > 100:
                all_symbols = all_symbols[:100]
            
            market_data_list = get_market_data_by_type(self.session, options=all_symbols)
            data_map = {md.symbol: md for md in market_data_list}
            
            options = []
            for strike in expiration.strikes:
                # Calls
                call_md = data_map.get(strike.call_streamer_symbol)
                options.append({
                    "strike": float(strike.strike_price),
                    "type": "CALL",
                    "bid": float(call_md.bid) if call_md and call_md.bid else 0.0,
                    "ask": float(call_md.ask) if call_md and call_md.ask else 0.0,
                    "expiry": expiry_str
                })
                # Puts
                put_md = data_map.get(strike.put_streamer_symbol)
                options.append({
                    "strike": float(strike.strike_price),
                    "type": "PUT",
                    "bid": float(put_md.bid) if put_md and put_md.bid else 0.0,
                    "ask": float(put_md.ask) if put_md and put_md.ask else 0.0,
                    "expiry": expiry_str
                })
            
            return options
        except Exception as e:
            logging.error(f"Error fetching option chain for {symbol}: {e}")
            return []
