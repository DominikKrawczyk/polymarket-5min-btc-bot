#!/usr/bin/env python3
"""Fetch YEARS of BTC 1m candles from Binance — SAVES INCREMENTALLY."""
import csv, json, sys, time, os, requests
from datetime import datetime, timezone

YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else f"/root/polymarket_5min_bot/data/btc_1m_{YEARS}yr.csv"
TEMP_OUTPUT = OUTPUT.replace('.csv', '_partial.csv')

URL = "https://api.binance.com/api/v3/klines"
LIMIT = 1000
TOTAL_NEEDED = YEARS * 365 * 24 * 60

end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
all_klines = []
req_count = 0
save_counter = 0
SAVE_EVERY = 50000  # Save every 50K candles

print(f"[BTC] Fetching {YEARS}yr BTC 1m data ({TOTAL_NEEDED:,} candles)", flush=True)
print(f"[BTC] Target: {OUTPUT}", flush=True)
print(f"[BTC] Temp:   {TEMP_OUTPUT}", flush=True)

def save_progress(klines, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for k in klines:
            ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc)
            w.writerow([ts.isoformat(), k[1], k[2], k[3], k[4], k[5]])

while len(all_klines) < TOTAL_NEEDED:
    params = {"symbol": "BTCUSDT", "interval": "1m", "limit": LIMIT, "endTime": end_time}
    try:
        resp = requests.get(URL, params=params, timeout=30)
        resp.raise_for_status()
        klines = resp.json()
    except Exception as e:
        print(f"\n[ERR] {e}", flush=True)
        time.sleep(5)
        continue
    
    if not klines:
        break
    
    # Remove overlap with existing data
    if all_klines and klines:
        while klines and klines[0][0] >= all_klines[0][0]:
            klines.pop(0)
    if not klines:
        break
    
    all_klines = klines + all_klines
    end_time = all_klines[0][0] - 1
    req_count += 1
    
    # Progress
    pct = len(all_klines) / TOTAL_NEEDED * 100
    days_data = len(all_klines) / (24 * 60)
    print(f"\r  [{pct:5.1f}%] {len(all_klines):>8,} candles ({days_data:.0f}d) | {req_count} req", end="", flush=True)
    
    # Save incrementally
    if len(all_klines) - save_counter >= SAVE_EVERY:
        save_progress(all_klines, TEMP_OUTPUT)
        save_counter = len(all_klines)
        print(f" [SAVED]", end="", flush=True)
    
    if len(klines) < LIMIT:
        print(f"\n[DONE] Reached beginning of data", flush=True)
        break
    
    time.sleep(0.35)

# Final save
save_progress(all_klines, OUTPUT)
mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"\n[DONE] {len(all_klines):,} candles → {OUTPUT} ({mb:.1f} MB)", flush=True)
print(f"[DONE] Covering {len(all_klines)/(24*60):.1f} days", flush=True)
