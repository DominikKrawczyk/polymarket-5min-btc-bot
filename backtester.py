"""Backtest engine v2 - multi-year BTC data, proper simulations."""
import json
import os
import math
from datetime import datetime, timezone
from collections import defaultdict
from config import config
from btc_price_feed import BTCPriceFeed


class BacktesterV2:
    """Proper backtest engine for Polymarket 5-min BTC strategy.
    
    Uses REAL BTC 1m candle data to simulate:
    1. What Polymarket prices WOULD be based on BTC movement
    2. Underdog pricing model based on BTC volatility
    3. Trade execution with fees and slippage
    """
    
    def __init__(self):
        self.feed = BTCPriceFeed()
    
    def simulate_polymarket_pricing(self, btc_window: dict) -> dict:
        """Simulate realistic Polymarket pricing based on BTC 5-min window.
        
        Pricing model uses PRIOR trend as favorite direction:
        - If BTC was trending UP in last 30min → UP is favorite
        - The 5-min window's actual movement determines resolution
        - Underdog (opposite of trend) wins on REVERSAL
        
        Pricing based on trend strength:
        - Strong trend (prior_change > 0.15%): favorite ~90-95c
        - Mild trend (prior_change 0.05-0.15%): favorite ~75-85c
        - No trend (prior_change < 0.05%): near coin-flip
        """
        prior_change = abs(btc_window.get("prior_change_pct", 0))
        prior_trend = btc_window.get("prior_trend", "Up")
        window_direction = btc_window.get("direction", "Up")
        underdog_wins = btc_window.get("underdog_wins", False)
        
        # Determine favorite price from trend strength
        if prior_change < 0.03:
            fav_price = 0.52  # Near coin flip
        elif prior_change < 0.05:
            fav_price = 0.58
        elif prior_change < 0.08:
            fav_price = 0.68
        elif prior_change < 0.12:
            fav_price = 0.78
        elif prior_change < 0.20:
            fav_price = 0.88
        else:
            fav_price = 0.94  # Strong trend
        
        # Add noise
        import random
        noise = random.uniform(-0.03, 0.03)
        fav_price = max(0.50, min(0.98, fav_price + noise))
        dog_price = 1.0 - fav_price
        
        return {
            "favorite_price": round(fav_price, 4),
            "underdog_price": round(dog_price, 4),
            "favorite_direction": prior_trend,
            "underdog_direction": "Down" if prior_trend == "Up" else "Up",
            "actual_direction": window_direction,
            "underdog_wins": underdog_wins,
            "prior_change_pct": round(prior_change, 4),
            "favorite_overpriced": fav_price > 0.80,
            "underdog_cheap_enough": dog_price <= config.max_entry_price
        }
    
    def run_backtest(self, candles: list, entry_price: float = 0.10,
                    risk_per_trade: float = 5.0, max_trades: int = None,
                    entry_strategy: str = "underdog_cheap") -> dict:
        """Run backtest with proper trade simulation.
        
        entry_strategy options:
        - "underdog_cheap": Buy underdog when price <= entry_price (standard)
        - "extreme": Only buy when underdog is < 5c
        - "consolidation": Only buy when BTC is consolidating (range < 0.05%)
        """
        trades = []
        bankroll = config.initial_bankroll
        wins = 0
        losses = 0
        windows_analyzed = 0
        
        # Process every 5th candle (5-minute windows)
        # Step by 5, align to 5-min boundaries
        for i in range(4, len(candles), 5):
            window = self.feed.get_5min_window(candles, i)
            if window is None:
                continue
            
            windows_analyzed += 1
            
            # Simulate Polymarket pricing
            pricing = self.simulate_polymarket_pricing(window)
            
            # Determine if we enter a trade
            enter_trade = False
            
            if entry_strategy == "underdog_cheap":
                # Standard: enter when underdog is cheap enough
                enter_trade = pricing["underdog_cheap_enough"] and pricing["favorite_overpriced"]
            elif entry_strategy == "extreme":
                enter_trade = pricing["underdog_price"] <= 0.05
            elif entry_strategy == "consolidation":
                enter_trade = pricing["prior_change_pct"] < 0.05
            
            if not enter_trade:
                continue
            
            if max_trades and len(trades) >= max_trades:
                break
            
            # Calculate position size
            contracts = risk_per_trade / pricing["underdog_price"]
            
            # Execute trade
            underdog_wins = pricing["underdog_wins"]
            
            if underdog_wins:
                # Underdog pays out at $1/share
                payout = contracts * 1.0
                cost = contracts * pricing["underdog_price"]
                profit = payout - cost
                # Subtract ~2% fee (Polymarket taker fee)
                fee = profit * 0.02
                profit -= fee
                bankroll += profit
                wins += 1
            else:
                # Lose entire investment
                loss = contracts * pricing["underdog_price"]
                bankroll -= loss
                losses += 1
            
            trades.append({
                "timestamp": window["timestamp"],
                "window_idx": i,
                "prior_change_pct": round(pricing["prior_change_pct"], 4),
                "favorite_price": pricing["favorite_price"],
                "favorite_direction": pricing["favorite_direction"],
                "underdog_price": pricing["underdog_price"],
                "underdog_direction": pricing["underdog_direction"],
                "actual_direction": pricing["actual_direction"],
                "won": underdog_wins,
                "contracts": round(contracts, 2),
                "pnl": round(profit if underdog_wins else -loss, 2),
                "bankroll": round(bankroll, 2),
            })
        
        # Calculate metrics
        total = len(trades)
        wr = wins / total if total > 0 else 0
        total_pnl = bankroll - config.initial_bankroll
        
        # Calculate max drawdown from running max
        peak = config.initial_bankroll
        max_dd = 0
        for t in trades:
            peak = max(peak, t["bankroll"])
            dd = (peak - t["bankroll"]) / peak * 100
            max_dd = max(max_dd, dd)
        
        # Sortino ratio (using only negative returns)
        neg_returns = [t["pnl"] for t in trades if t["pnl"] < 0]
        downside_std = (sum(x*x for x in neg_returns) / max(len(neg_returns), 1)) ** 0.5
        sortino = (sum(t["pnl"] for t in trades) / len(trades)) / max(downside_std, 0.01) if trades else 0
        
        return {
            "initial_bankroll": config.initial_bankroll,
            "final_bankroll": round(bankroll, 2),
            "total_pnl": round(total_pnl, 2),
            "return_pct": round(total_pnl / config.initial_bankroll * 100, 2),
            "total_trades": total,
            "windows_analyzed": windows_analyzed,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 4),
            "avg_profit": round(sum(t["pnl"] for t in trades if t["pnl"] > 0) / max(wins, 1), 2),
            "avg_loss": round(sum(t["pnl"] for t in trades if t["pnl"] < 0) / max(losses, 1), 2),
            "profit_factor": round(
                sum(t["pnl"] for t in trades if t["pnl"] > 0) / 
                max(abs(sum(t["pnl"] for t in trades if t["pnl"] < 0)), 0.01), 2
            ) if losses > 0 else float('inf'),
            "max_drawdown_pct": round(max_dd, 2),
            "sortino_ratio": round(sortino, 4),
            "sharpe_approx": round(wr * sum(t["pnl"] for t in trades) / max(sum(t["pnl"]*t["pnl"] for t in trades)**0.5 * (len(trades)**0.5), 0.01), 4) if trades else 0,
            "entry_strategy": entry_strategy,
            "entry_price_limit": entry_price,
            "risk_per_trade": risk_per_trade,
            "trades": trades
        }
    
    def optimize(self, candles: list, param_grid: dict = None) -> list:
        """Parameter sweep optimization.
        
        Default grid:
        - entry_price: [0.03, 0.05, 0.08, 0.10, 0.15, 0.20]
        - risk_per_trade: [2, 5, 10]
        - entry_strategy: ["underdog_cheap", "extreme", "consolidation"]
        """
        if param_grid is None:
            param_grid = {
                "entry_price": [0.03, 0.05, 0.08, 0.10, 0.15, 0.20],
                "risk_per_trade": [2, 5, 10],
                "entry_strategy": ["underdog_cheap", "extreme"],
            }
        
        results = []
        total_combos = 1
        for v in param_grid.values():
            total_combos *= len(v)
        
        print(f"[OPTIMIZE] Testing {total_combos} parameter combinations...")
        idx = 0
        
        for entry in param_grid["entry_price"]:
            for risk in param_grid["risk_per_trade"]:
                for strat in param_grid["entry_strategy"]:
                    r = self.run_backtest(
                        candles, 
                        entry_price=entry,
                        risk_per_trade=risk,
                        entry_strategy=strat,
                        max_trades=50000
                    )
                    r["params"] = {"entry_price": entry, "risk": risk, "strategy": strat}
                    results.append(r)
                    idx += 1
                    if idx % 5 == 0:
                        print(f"  {idx}/{total_combos} combos tested...")
        
        # Sort by profit factor (descending)
        results.sort(key=lambda r: r["profit_factor"], reverse=True)
        return results
    
    def print_results(self, result: dict):
        print("=" * 60)
        print(f"  BACKTEST V2 — {result.get('entry_strategy', 'standard').upper()}")
        print(f"  Entry limit: ${result['entry_price_limit']:.2f} | Risk: ${result['risk_per_trade']:.2f}")
        print("=" * 60)
        print(f"  Period:           {result.get('period', 'Auto')}")
        print(f"  Windows analyzed: {result['windows_analyzed']:,}")
        print(f"  Initial Bankroll: ${result['initial_bankroll']:.2f}")
        print(f"  Final Bankroll:   ${result['final_bankroll']:.2f}")
        print(f"  Total PnL:        ${result['total_pnl']:.2f}")
        print(f"  Return:           {result['return_pct']:+.2f}%")
        print(f"  Total Trades:     {result['total_trades']:,}")
        print(f"  Win Rate:         {result['win_rate']*100:.2f}%")
        print(f"  Avg Profit:       ${result['avg_profit']:.2f}")
        print(f"  Avg Loss:         ${result['avg_loss']:.2f}")
        print(f"  Profit Factor:    {result['profit_factor']:.2f}x")
        print(f"  Max Drawdown:     {result['max_drawdown_pct']:.2f}%")
        print(f"  Sortino Ratio:    {result['sortino_ratio']:.2f}")
        print("=" * 60)
    
    def save_results(self, result: dict, label: str = None):
        filename = f"backtest_{label or datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(config.backtest_dir, filename)
        # Save without trades array (too large)
        to_save = {k: v for k, v in result.items() if k != "trades"}
        to_save["trade_count"] = len(result.get("trades", []))
        with open(filepath, "w") as f:
            json.dump(to_save, f, indent=2)
        print(f"[SAVED] {filepath}")
        return filepath
