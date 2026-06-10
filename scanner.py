
"""5-Min Dog Scanner - scans Polymarket for underdog pricing.
Records real orderbook prices to validate edge before going live."""
import json
import time
import csv
import os
from datetime import datetime, timezone
from config import config
from polymarket_client import PolymarketClient

class DogScanner:
    """Scan-only logger: records underdog prices on Polymarket."""
    
    def __init__(self):
        self.client = PolymarketClient()
        self.log_path = os.path.join(config.data_dir, "scanner_log.csv")
        self._init_log()
    
    def _init_log(self):
        """Initialize CSV log if not exists."""
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "market_question", "btc_direction",
                    "favorite_outcome", "favorite_price",
                    "underdog_outcome", "underdog_price",
                    "best_ask", "best_bid", "mid_price", "resolution_hint"
                ])
            print(f"[SCANNER] Log initialized: {self.log_path}")
    
    def scan_once(self) -> dict:
        """Scan current Polymarket state and log findings."""
        scan_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markets_found": 0,
            "underdog_price": None,
            "favorite_price": None,
        }
        
        # Try to find BTC up/down markets
        try:
            btc_markets = self.client.get_btc_updown_markets()
            
            if not btc_markets:
                print("[SCANNER] No BTC up/down markets found via Gamma API")
                # Fallback: scan all active CLOB markets
                all_markets = self.client.get_markets(tag="All", limit=500)
                btc_updown = []
                for m in all_markets:
                    q = m.get("question", "")
                    if ("BTC" in q.upper() or "BITCOIN" in q) and m.get("active") and not m.get("closed"):
                        tokens = m.get("tokens", [])
                        if len(tokens) == 2 and tokens[0].get("outcome","").lower() in ("up","down","yes","no"):
                            btc_updown.append(m)
                btc_markets_data = btc_updown
            else:
                btc_markets_data = []
                for ev in btc_markets:
                    btc_markets_data.extend(ev.get("markets", []))
            
            scan_result["markets_found"] = len(btc_markets_data)
            
            for market in btc_markets_data[:10]:  # Process top markets
                tokens = market.get("tokens", [])
                if len(tokens) < 2:
                    continue
                
                # Determine favorite (higher priced) and underdog (lower priced)
                t0_price = tokens[0].get("price", 0)
                t1_price = tokens[1].get("price", 0)
                
                if t0_price >= t1_price:
                    fav_token, dog_token = tokens[0], tokens[1]
                else:
                    fav_token, dog_token = tokens[1], tokens[0]
                
                # Get real orderbook prices
                fav_book = self.client.get_market_price(fav_token.get("token_id"))
                dog_book = self.client.get_market_price(dog_token.get("token_id"))
                
                entry = {
                    "timestamp": scan_result["timestamp"],
                    "market_question": market.get("question", ""),
                    "btc_direction": "N/A",
                    "favorite_outcome": fav_token.get("outcome", ""),
                    "favorite_price": fav_book["mid"] if fav_book else t0_price,
                    "underdog_outcome": dog_token.get("outcome", ""),
                    "underdog_price": dog_book["mid"] if dog_book else t1_price,
                    "best_ask": dog_book["best_ask"] if dog_book else "",
                    "best_bid": dog_book["best_bid"] if dog_book else "",
                    "mid_price": dog_book["mid"] if dog_book else "",
                    "resolution_hint": "N/A"
                }
                
                # Log entry
                with open(self.log_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        entry["timestamp"], entry["market_question"],
                        entry["btc_direction"], entry["favorite_outcome"],
                        entry["favorite_price"], entry["underdog_outcome"],
                        entry["underdog_price"], entry["best_ask"],
                        entry["best_bid"], entry["mid_price"],
                        entry["resolution_hint"]
                    ])
                
                scan_result["underdog_price"] = entry["underdog_price"]
                scan_result["favorite_price"] = entry["favorite_price"]
                
                print(f"  Market: {market.get('question','?')[:60]}")
                print(f"    Favorite: {entry['favorite_outcome']} @ {entry['favorite_price']:.4f}")
                print(f"    Underdog: {entry['underdog_outcome']} @ {entry['underdog_price']:.4f}")
                
        except Exception as e:
            print(f"[SCANNER] Error during scan: {e}")
            import traceback
            traceback.print_exc()
        
        return scan_result
    
    def summary(self) -> dict:
        """Print summary of all scans."""
        if not os.path.exists(self.log_path):
            return {"records": 0, "avg_underdog_price": 0, "avg_favorite_price": 0}
        
        with open(self.log_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {"records": 0}
        
        dog_prices = [float(r["underdog_price"]) for r in rows if r["underdog_price"]]
        fav_prices = [float(r["favorite_price"]) for r in rows if r["favorite_price"]]
        
        summary = {
            "records": len(rows),
            "avg_underdog_price": sum(dog_prices) / len(dog_prices) if dog_prices else 0,
            "avg_favorite_price": sum(fav_prices) / len(fav_prices) if fav_prices else 0,
            "min_underdog": min(dog_prices) if dog_prices else 0,
            "max_underdog": max(dog_prices) if dog_prices else 0,
            "pct_underdog_below_20c": sum(1 for p in dog_prices if p <= 0.20) / len(dog_prices) * 100 if dog_prices else 0,
            "pct_underdog_below_10c": sum(1 for p in dog_prices if p <= 0.10) / len(dog_prices) * 100 if dog_prices else 0,
        }
        
        print("\n=== SCANNER SUMMARY ===")
        print(f"Total records: {summary['records']}")
        print(f"Avg underdog price: {summary['avg_underdog_price']:.4f}")
        print(f"Avg favorite price: {summary['avg_favorite_price']:.4f}")
        print(f"Underdog range: {summary['min_underdog']:.4f} - {summary['max_underdog']:.4f}")
        print(f"Underdog <= 20c: {summary['pct_underdog_below_20c']:.1f}%")
        print(f"Underdog <= 10c: {summary['pct_underdog_below_10c']:.1f}%")
        print("=====================\n")
        
        return summary
