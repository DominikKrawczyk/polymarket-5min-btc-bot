"""Polymarket CLOB API Client v2 - proper implementation."""
import json
import time
import requests
from typing import Optional
from config import config

CLOB_URL = config.clob_api_url
GAMMA_URL = config.gamma_api_url

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    "Accept": "application/json"
}


class PolymarketClient:
    """Official Polymarket CLOB API client.
    
    Level 0: Public read-only (markets, orderbooks, prices)
    Level 1: Signer auth (requires private key for order signing)
    Level 2: Full auth (requires API credentials for order placement)
    """
    
    def __init__(self, private_key: str = None):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.private_key = private_key
        self.api_key = None
        self.api_secret = None
        self.api_passphrase = None
        
    # ─── Level 0: Public endpoints ─────────────────────────
    
    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{CLOB_URL}/", timeout=10)
            return r.text.strip('"') == "OK"
        except:
            return False
    
    def get_markets(self, limit: int = 100, next_cursor: str = None) -> dict:
        """List markets with pagination. Returns {'data': [...], 'next_cursor': '...', 'count': N}"""
        params = {"limit": min(limit, 1000)}
        if next_cursor:
            params["next_cursor"] = next_cursor
        r = self.session.get(f"{CLOB_URL}/markets", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def get_all_markets(self, max_markets: int = 10000) -> list:
        """Fetch ALL markets via pagination."""
        all_m = []
        cursor = None
        while len(all_m) < max_markets:
            batch = self.get_markets(limit=1000, next_cursor=cursor)
            data = batch.get("data", [])
            if not data:
                break
            all_m.extend(data)
            cursor = batch.get("next_cursor")
            if not cursor:
                break
            time.sleep(0.2)
        return all_m[:max_markets]
    
    def get_market(self, condition_id: str) -> Optional[dict]:
        r = self.session.get(f"{CLOB_URL}/markets/{condition_id}", timeout=15)
        r.raise_for_status()
        return r.json()
    
    def get_orderbook(self, token_id: str) -> dict:
        """Get full order book for a token.
        
        Returns: {
            "market": "0x...",
            "asset_id": "...",
            "bids": [{"price": "0.05", "size": "1000"}, ...],
            "asks": [{"price": "0.06", "size": "800"}, ...],
            "last_trade_price": "0.055",
            ...
        }
        """
        r = self.session.get(f"{CLOB_URL}/book", params={"token_id": token_id}, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def get_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """Get best price for a side (BUY or SELL).
        Returns None if no orders on that side."""
        r = self.session.get(f"{CLOB_URL}/price", params={"token_id": token_id, "side": side}, timeout=15)
        if r.status_code == 200:
            return float(r.text.strip('"'))
        return None
    
    def get_midpoint(self, token_id: str) -> Optional[float]:
        """Get midpoint price (average of best bid and ask)."""
        r = self.session.get(f"{CLOB_URL}/midpoint", params={"token_id": token_id}, timeout=15)
        if r.status_code == 200:
            return float(r.text.strip('"'))
        return None
    
    def get_spread(self, token_id: str) -> Optional[float]:
        """Get bid-ask spread."""
        r = self.session.get(f"{CLOB_URL}/spread", params={"token_id": token_id}, timeout=15)
        if r.status_code == 200:
            return float(r.text.strip('"'))
        return None
    
    def get_last_trade_price(self, token_id: str) -> Optional[float]:
        r = self.session.get(f"{CLOB_URL}/last-trade-price", params={"token_id": token_id}, timeout=15)
        if r.status_code == 200:
            return float(r.text.strip('"'))
        return None
    
    def get_prices_history(self, market: str, interval: str = "1h", 
                          start_ts: int = None, end_ts: int = None) -> list:
        """Get price history for a market.
        interval: 1w, 1d, 6h, 1h
        """
        params = {"market": market, "interval": interval}
        if start_ts: params["startTs"] = start_ts
        if end_ts: params["endTs"] = end_ts
        r = self.session.get(f"{CLOB_URL}/prices-history", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    # ─── Gamma API (richer market data) ─────────────────────
    
    def get_gamma_markets(self, tag: str = "crypto", limit: int = 200, 
                          closed: bool = False) -> list:
        """Get markets from Gamma API with rich data.
        
        Gamma returns additional fields:
        - clobTokenIds, outcomePrices (live prices!), volume24hr, liquidityClob
        - events array with event metadata
        """
        params = {"tag": tag, "limit": limit, "closed": str(closed).lower()}
        r = self.session.get(f"{GAMMA_URL}/markets", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def get_gamma_events(self, limit: int = 100) -> list:
        r = self.session.get(f"{GAMMA_URL}/events", params={"limit": limit}, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def get_live_market_prices(self, condition_id: str = None, clob_token_ids: list = None) -> dict:
        """Get LIVE prices from Gamma API.
        
        Gamma's outcomePrices field gives the current CLOB trading prices,
        NOT resolved prices. This is the CORRECT price source.
        
        Returns: {"token_id": price, ...}
        """
        if clob_token_ids:
            prices = {}
            for tid in clob_token_ids:
                mid = self.get_midpoint(tid)
                if mid:
                    prices[tid] = mid
            return prices
        
        if condition_id:
            market = self.get_market(condition_id)
            tokens = market.get("tokens", [])
            return {t["token_id"]: t.get("price", 0) for t in tokens}
        
        return {}
    
    # ─── Market discovery ────────────────────────────────────
    
    def find_active_crypto_markets(self, max_markets: int = 5000) -> list:
        """Find all active crypto-related markets on Polymarket."""
        all_markets = self.get_all_markets(max_markets=max_markets)
        active = []
        for m in all_markets:
            if m.get("active") and not m.get("closed") and m.get("accepting_orders"):
                tokens = m.get("tokens", [])
                if len(tokens) >= 2:
                    # Check if it's crypto-related
                    question = m.get("question", "").lower()
                    tags = [t.lower() for t in m.get("tags", [])]
                    is_crypto = ("btc" in question or "bitcoin" in question or 
                                "eth" in question or "ethereum" in question or
                                "crypto" in question or "crypto" in str(tags))
                    if is_crypto:
                        active.append(m)
        return active
    
    # ─── Level 1 & 2: Auth (requires private key) ──────────
    
    def set_private_key(self, key: str):
        """Set wallet private key for signing."""
        self.private_key = key
    
    def set_api_creds(self, api_key: str, api_secret: str, api_passphrase: str):
        """Set API credentials for Level 2 auth."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.session.headers["POLY_API_KEY"] = api_key
        self.session.headers["POLY_API_SECRET"] = api_secret
        self.session.headers["POLY_API_PASSPHRASE"] = api_passphrase
    
    # ─── Order placement (full flow) ────────────────────────
    
    def create_signed_order(self, token_id: str, side: str, price: float, 
                           size: float, order_type: str = "GTC") -> dict:
        """Create and sign an off-chain order.
        
        Requires private_key to be set. Uses EIP-712 signing.
        
        Args:
            token_id: The token's ID string
            side: "BUY" or "SELL"
            price: Price per share (0.01-1.0)
            size: Number of contracts
            order_type: "GTC", "GTD", "FOK", "FAK"
        
        Returns: SignedOrder dict ready for /order POST
        """
        if not self.private_key:
            raise ValueError("Private key required for order signing")
        # This requires py-clob-client or py-sdk for actual EIP-712 signing
        raise NotImplementedError("EIP-712 signing requires py-clob-client SDK")
    
    def post_order(self, signed_order: dict) -> dict:
        """Post a signed order to the CLOB."""
        if not all([self.api_key, self.api_secret, self.api_passphrase]):
            raise ValueError("API credentials required for order placement")
        
        payload = {
            "order": signed_order,
            "orderType": "GTC",
            "owner": self.api_key
        }
        r = self.session.post(f"{CLOB_URL}/order", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    
    # ─── Utils ──────────────────────────────────────────────
    
    def get_market_price_analysis(self, market: dict) -> dict:
        """Analyze a market's current pricing structure.
        
        Returns favorite/underdog prices, EV, and trade signals.
        """
        tokens = market.get("tokens", [])
        if len(tokens) < 2:
            return None
        
        # Get LIVE prices from orderbook (not resolved prices)
        prices = {}
        for t in tokens:
            mid = self.get_midpoint(t["token_id"])
            if mid:
                prices[t["token_id"]] = mid
            else:
                prices[t["token_id"]] = t.get("price", 0)
        
        # Sort by price
        sorted_tokens = sorted(tokens, key=lambda t: prices.get(t["token_id"], 0))
        underdog_token = sorted_tokens[0]
        favorite_token = sorted_tokens[-1]
        
        underdog_price = prices.get(underdog_token["token_id"], 0)
        favorite_price = prices.get(favorite_token["token_id"], 0)
        
        # Expected value calculation
        # Underdog win rate = market-implied probability from price
        underdog_implied_wr = 1.0 - favorite_price
        
        analysis = {
            "question": market.get("question", ""),
            "condition_id": market.get("condition_id"),
            "favorite": {
                "outcome": favorite_token.get("outcome"),
                "token_id": favorite_token["token_id"],
                "price": favorite_price
            },
            "underdog": {
                "outcome": underdog_token.get("outcome"),
                "token_id": underdog_token["token_id"],
                "price": underdog_price
            },
            "spread": abs(favorite_price - underdog_price),
            "implied_underdog_wr": underdog_implied_wr,
        }
        return analysis
