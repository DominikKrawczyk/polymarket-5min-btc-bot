
"""Polymarket 5-Min BTC Bot Configuration."""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # --- Polymarket ---
    clob_api_url: str = "https://clob.polymarket.com"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    chain_id: int = 137  # Polygon
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws"
    
    # --- Strategy ---
    max_entry_price: float = 0.20       # Max price to pay for underdog (20 cents)
    min_favorite_price: float = 0.80    # Min price for favorite (80+ cents)
    underdog_win_rate: float = 0.33     # Expected underdog win rate
    kelly_fraction: float = 0.25        # Kelly fraction for position sizing
    max_risk_per_trade: float = 5.0     # Max $ risk per trade
    initial_bankroll: float = 100.0     # Starting bankroll
    
    # --- Scanner ---
    scan_duration_days: int = 14        # Run scanner for 2 weeks
    scan_interval_seconds: int = 30     # Check every 30 seconds
    
    # --- Trading ---
    trade_on_scan_complete: bool = False
    min_scan_records: int = 500         # Min records before trading
    
    # --- Paths ---
    data_dir: str = os.path.join(os.path.dirname(__file__), "data")
    backtest_dir: str = os.path.join(os.path.dirname(__file__), "backtests")
    
    def __post_init__(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backtest_dir, exist_ok=True)

config = Config()
