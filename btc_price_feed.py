"""BTC price data retrieval for backtesting."""
import csv
import time
from datetime import datetime, timezone
import requests


class BTCPriceFeed:
    """Fetches and stores BTC price data for backtesting."""

    @staticmethod
    def fetch_1m_klines(symbol="BTCUSDT", days=365, limit=1000):
        """Fetch 1-minute BTC candles from Binance API."""
        url = "https://api.binance.com/api/v3/klines"
        end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        all_klines = []
        fetched_days = 0
        
        while fetched_days < days:
            params = {"symbol": symbol, "interval": "1m", "limit": min(limit, 1000), "endTime": end_time}
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                klines = resp.json()
            except Exception as e:
                print(f"[WARN] Binance API error: {e}")
                break
            if not klines:
                break
            all_klines = klines + all_klines
            fetched_days += len(klines) / (24 * 60)
            end_time = klines[0][0] - 1
            if len(klines) < limit:
                break
            time.sleep(0.3)
        print(f"[BTC] Fetched {len(all_klines)} 1m candles ({len(all_klines)/(24*60):.1f} days)")
        return all_klines

    @staticmethod
    def klines_to_csv(klines, filepath):
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            for k in klines:
                ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc)
                writer.writerow([ts.isoformat(), k[1], k[2], k[3], k[4], k[5]])
        print(f"[BTC] Saved {len(klines)} candles to {filepath}")

    @staticmethod
    def csv_to_klines(filepath):
        candles = []
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"])
                })
        return candles

    @staticmethod
    def get_5min_window(candles, idx):
        """Get the 5-min window data ending at idx.
        
        Returns OHLC + trend direction from BEFORE this window.
        
        The "favorite" direction is the trend leading INTO this window
        (using the 30 minutes before). The actual resolution is the
        5-min window's real movement.
        """
        start = max(0, idx - 4)
        window = candles[start:idx + 1]
        if len(window) < 5:
            return None
        
        # Determine PRIOR trend direction (last 30 min before window)
        prior_start = max(0, idx - 34)
        prior_window = candles[prior_start:start]
        if len(prior_window) >= 10:
            prior_trend = "Up" if prior_window[-1]["close"] > prior_window[0]["open"] else "Down"
            prior_change_pct = (prior_window[-1]["close"] - prior_window[0]["open"]) / prior_window[0]["open"] * 100
        else:
            prior_trend = "Up" if window[0]["close"] > window[-1]["close"] else "Down"
            prior_change_pct = 0
        
        # Window's actual movement
        window_open = window[0]["open"]
        window_close = window[-1]["close"]
        window_direction = "Up" if window_close > window_open else "Down"
        window_change_pct = (window_close - window_open) / window_open * 100
        
        # Range (volatility)
        window_high = max(c["high"] for c in window)
        window_low = min(c["low"] for c in window)
        window_range_pct = (window_high - window_low) / window_open * 100
        
        return {
            "open": window_open,
            "high": window_high,
            "low": window_low,
            "close": window_close,
            "timestamp": window[-1]["timestamp"],
            "direction": window_direction,
            "change_pct": round(window_change_pct, 4),
            "range_pct": round(window_range_pct, 4),
            "prior_trend": prior_trend,
            "prior_change_pct": round(prior_change_pct, 4),
            "favorite_direction": prior_trend,  # Crowd expects trend to continue
            "actual_direction": window_direction,  # What actually happened
            "underdog_wins": window_direction != prior_trend,  # Underdog wins on reversal
        }
