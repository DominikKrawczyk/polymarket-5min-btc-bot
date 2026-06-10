"""Polymarket 5-Min BTC Bot - Main Entry Point v2.

Modes:
  - fetch-data [years]: Download BTC 1m candles from Binance
  - list-data: Show available BTC data files
  - backtest [year|month]: Run backtest on historical data
  - optimize: Parameter sweep optimization
  - scan: Run scanner mode
  - trade: Live trading mode
  - status: Show data fetch status
"""
import sys
import os
import time
import glob
from datetime import datetime, timezone

from config import config
from btc_price_feed import BTCPriceFeed
from backtester import BacktesterV2


def find_btc_data() -> str:
    """Find the largest BTC data file."""
    files = glob.glob(os.path.join(config.data_dir, "btc*.csv"))
    if not files:
        return None
    files.sort(key=os.path.getsize, reverse=True)
    return files[0]


def cmd_list_data():
    files = glob.glob(os.path.join(config.data_dir, "btc*.csv"))
    if not files:
        print("[MAIN] No BTC data files found.")
        return
    for f in sorted(files, key=os.path.getsize):
        size_mb = os.path.getsize(f) / 1024 / 1024
        lines = sum(1 for _ in open(f)) - 1  # minus header
        days = lines / (24 * 60)
        print(f"  {os.path.basename(f):40s} {size_mb:6.1f} MB  {lines:>8,} candles ({days:.0f} days)")


def cmd_backtest():
    """Run backtest on available BTC data."""
    years_str = sys.argv[2] if len(sys.argv) > 2 else None
    data_path = find_btc_data()
    
    if not data_path:
        print("[MAIN] No BTC data found! Run 'python3 fetch_years_data.py 3' first.")
        return
    
    # Check data fetch progress
    size_mb = os.path.getsize(data_path) / 1024 / 1024
    lines = sum(1 for _ in open(data_path)) - 1
    days_data = lines / (24 * 60)
    print(f"[MAIN] Loading: {data_path}")
    print(f"[MAIN] File: {size_mb:.1f} MB, {lines:,} candles ({days_data:.1f} days)")
    
    candles = BTCPriceFeed.csv_to_klines(data_path)
    print(f"[MAIN] Loaded {len(candles):,} candles")
    print(f"[MAIN] Date range: {candles[0]['timestamp']} → {candles[-1]['timestamp']}")
    
    bt = BacktesterV2()
    
    variants = [
        {"entry": 0.05, "risk": 5, "strat": "underdog_cheap", "label": "5c entry, $5 risk"},
        {"entry": 0.10, "risk": 5, "strat": "underdog_cheap", "label": "10c entry, $5 risk"},
        {"entry": 0.15, "risk": 5, "strat": "underdog_cheap", "label": "15c entry, $5 risk"},
        {"entry": 0.05, "risk": 10, "strat": "underdog_cheap", "label": "5c entry, $10 risk"},
        {"entry": 0.20, "risk": 5, "strat": "underdog_cheap", "label": "20c entry, $5 risk"},
        {"entry": 0.05, "risk": 5, "strat": "extreme", "label": "EXTREME: <5c only, $5 risk"},
        {"entry": 0.10, "risk": 5, "strat": "consolidation", "label": "CONSOL: range<0.05%, 10c, $5"},
    ]
    
    all_results = []
    for v in variants:
        print(f"\n{'='*60}")
        print(f"  VARIANT: {v['label']}")
        print(f"{'='*60}")
        
        result = bt.run_backtest(
            candles,
            entry_price=v["entry"],
            risk_per_trade=v["risk"],
            entry_strategy=v["strat"],
            max_trades=100000
        )
        result["period"] = f"{candles[0]['timestamp'][:10]} → {candles[-1]['timestamp'][:10]}"
        bt.print_results(result)
        bt.save_results(result, v["label"].replace(" ", "_").replace("$", "").replace("<", "lt"))
        all_results.append(result)
    
    # Summary table
    print(f"\n{'='*60}")
    print("  BACKTEST SUMMARY — ALL VARIANTS")
    print(f"{'='*60}")
    print(f"  {'Variant':30s} {'WR':>6s} {'Return':>10s} {'PF':>6s} {'MaxDD':>6s} {'Trades':>7s}")
    print(f"  {'-'*30} {'-'*6} {'-'*10} {'-'*6} {'-'*6} {'-'*7}")
    for r in all_results:
        label = r.get('entry_strategy', '?').replace('_', ' ').title()
        print(f"  {label:30s} {r['win_rate']*100:>5.1f}% {r['return_pct']:>+9.0f}% {r['profit_factor']:>5.1f}x {r['max_drawdown_pct']:>5.1f}% {r['total_trades']:>7,}")
    print()


def cmd_optimize():
    """Run parameter sweep optimization."""
    data_path = find_btc_data()
    if not data_path:
        print("[MAIN] No BTC data found!")
        return
    
    lines = sum(1 for _ in open(data_path)) - 1
    print(f"[MAIN] Data: {data_path} ({lines:,} candles)")
    
    candles = BTCPriceFeed.csv_to_klines(data_path)
    print(f"[MAIN] Loaded {len(candles):,} candles")
    
    bt = BacktesterV2()
    
    param_grid = {
        "entry_price": [0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25],
        "risk_per_trade": [2, 5, 10],
        "entry_strategy": ["underdog_cheap", "extreme"],
    }
    
    results = bt.optimize(candles, param_grid)
    
    print(f"\n{'='*80}")
    print("  OPTIMIZATION RESULTS — TOP 10")
    print(f"{'='*80}")
    print(f"  {'Rank':5s} {'Entry':>6s} {'Risk':>5s} {'Strat':18s} {'WR':>6s} {'Return':>12s} {'PF':>6s} {'MaxDD':>6s} {'Trades':>7s}")
    print(f"  {'-'*5} {'-'*6} {'-'*5} {'-'*18} {'-'*6} {'-'*12} {'-'*6} {'-'*6} {'-'*7}")
    
    for i, r in enumerate(results[:10]):
        p = r["params"]
        print(f"  {i+1:4d}. {p['entry_price']:>5.2f}  ${p['risk']:>3.0f}  {p['strategy']:18s} {r['win_rate']*100:>5.1f}% {r['return_pct']:>+10.0f}% {r['profit_factor']:>5.1f}x {r['max_drawdown_pct']:>5.1f}% {r['total_trades']:>7,}")
    
    print(f"\n  Best config:")
    best = results[0]["params"]
    print(f"    entry_price={best['entry_price']}, risk=${best['risk']}, strategy='{best['strategy']}'")
    print()


def cmd_status():
    """Show data fetch status."""
    print(f"[MAIN] Data directory: {config.data_dir}")
    files = glob.glob(os.path.join(config.data_dir, "btc*.csv"))
    if not files:
        print("[MAIN] No data files. Data fetch may still be running...")
        print("[MAIN] Run 'python3 fetch_years_data.py 3' to start")
        return
    
    for f in sorted(files, key=os.path.getsize, reverse=True):
        size_mb = os.path.getsize(f) / 1024 / 1024
        lines = sum(1 for _ in open(f)) - 1
        hours = lines / 60
        days = hours / 24
        print(f"  {os.path.basename(f):40s} {size_mb:6.1f} MB  {lines:>9,} candles ({days:.1f} days)")
    
    # Check background process
    print()
    print("[MAIN] To check data fetch progress:")
    print("  process(action='poll')")
    print("  process(action='log')")


def cmd_scan():
    from scanner import DogScanner
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    scanner = DogScanner()
    end_time = time.time() + (duration * 86400)
    try:
        while time.time() < end_time:
            print(f"\n[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            result = scanner.scan_once()
            print(f"  Markets found: {result['markets_found']}")
            time.sleep(config.scan_interval_seconds)
    except KeyboardInterrupt:
        print("\n[MAIN] Scanner stopped")
    scanner.summary()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    commands = {
        "list-data": cmd_list_data,
        "backtest": cmd_backtest,
        "optimize": cmd_optimize,
        "status": cmd_status,
        "scan": cmd_scan,
    }
    
    cmd = sys.argv[1]
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
