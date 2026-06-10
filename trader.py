"""5-Min Dog Sniper - Live Trader.
Buys the underdog on Polymarket 5-min BTC up/down markets."""
import json
import time
import os
from datetime import datetime, timezone
from config import config
from polymarket_client import PolymarketClient


class UnderdogTrader:
    """Live trading bot for the underdog strategy."""

    def __init__(self, bankroll: float = None):
        self.client = PolymarketClient()
        self.bankroll = bankroll or config.initial_bankroll
        self.trade_log = []
        self.active_condition_ids = set()

    def find_opportunity(self) -> dict:
        """Scan for live underdog trading opportunity."""
        opportunity = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "found": False,
            "market": None,
            "underdog_price": None,
            "favorite_price": None,
            "ev": None,
            "kelly_size": 0,
        }

        btc_markets = self.client.get_btc_updown_markets()
        markets_data = []
        for ev in btc_markets:
            markets_data.extend(ev.get("markets", []))

        for market in markets_data:
            tokens = market.get("tokens", [])
            if len(tokens) < 2:
                continue

            t0_price = tokens[0].get("price", 0)
            t1_price = tokens[1].get("price", 0)

            if t0_price >= t1_price:
                fav_token, dog_token = tokens[0], tokens[1]
                fav_price = t0_price
                dog_price = t1_price
            else:
                fav_token, dog_token = tokens[1], tokens[0]
                fav_price = t1_price
                dog_price = t0_price

            if dog_price <= config.max_entry_price and fav_price >= config.min_favorite_price:
                expected_win_rate = config.underdog_win_rate
                profit_when_win = 1.0 - dog_price
                loss_when_lose = dog_price

                ev = (expected_win_rate * profit_when_win) - \
                    ((1 - expected_win_rate) * loss_when_lose)

                b = profit_when_win / loss_when_lose if loss_when_lose > 0 else 0
                kelly_f = (expected_win_rate * b - (1 - expected_win_rate)) / b if b > 0 else 0
                kelly_f = max(0, kelly_f) * config.kelly_fraction

                opportunity = {
                    "timestamp": opportunity["timestamp"],
                    "found": True,
                    "market": market,
                    "underdog_token_id": dog_token.get("token_id"),
                    "favorite_token_id": fav_token.get("token_id"),
                    "underdog_outcome": dog_token.get("outcome"),
                    "favorite_outcome": fav_token.get("outcome"),
                    "underdog_price": dog_price,
                    "favorite_price": fav_price,
                    "ev": round(ev, 4),
                    "kelly_size": round(kelly_f, 4),
                    "condition_id": market.get("condition_id"),
                }
                break

        return opportunity

    def calculate_position_size(self, opportunity: dict) -> float:
        """Calculate position size based on Kelly."""
        if not opportunity.get("found"):
            return 0

        kelly = opportunity.get("kelly_size", 0)
        if kelly <= 0:
            print("[TRADER] EV is negative or zero - skipping trade")
            return 0

        position = self.bankroll * kelly
        position = min(position, config.max_risk_per_trade /
                       opportunity.get("underdog_price", 1))
        return round(position, 2)

    def execute_trade(self, opportunity: dict) -> dict:
        """Execute a trade on Polymarket.

        In real operation, this would:
        1. Create an order on the CLOB
        2. Sign it with the user's wallet
        3. Submit to the API
        4. Monitor for fill

        For the scanner phase, we just log the opportunity.
        """
        position_size = self.calculate_position_size(opportunity)

        trade = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "signal" if config.trade_on_scan_complete else "scan_only",
            "underdog": opportunity.get("underdog_outcome"),
            "entry_price": opportunity.get("underdog_price"),
            "favorite_price": opportunity.get("favorite_price"),
            "position_size": position_size,
            "ev": opportunity.get("ev"),
            "kelly": opportunity.get("kelly_size"),
            "condition_id": opportunity.get("condition_id"),
            "executed": config.trade_on_scan_complete and position_size > 0,
        }

        self.trade_log.append(trade)
        self._log_trade(trade)

        if trade["executed"]:
            cost = position_size * trade["entry_price"]
            self.bankroll -= cost
            print(f"[TRADER] EXECUTED: Buy {trade['underdog']} @ ${trade['entry_price']:.4f} for ${cost:.2f}")
        else:
            print(f"[TRADER] SIGNAL:   Buy {trade['underdog']} @ ${trade['entry_price']:.4f} (scan only)")

        return trade

    def _log_trade(self, trade: dict):
        """Log trade to file."""
        log_path = os.path.join(config.data_dir, "trades_log.json")
        existing = []
        if os.path.exists(log_path):
            with open(log_path) as f:
                try:
                    existing = json.load(f)
                except Exception:
                    existing = []
        existing.append(trade)
        with open(log_path, "w") as f:
            json.dump(existing, f, indent=2)

    def run_once(self) -> dict:
        """Scan and potentially trade in one cycle."""
        opportunity = self.find_opportunity()
        if opportunity["found"]:
            print(f"\n=== TRADING OPPORTUNITY FOUND ===")
            q = opportunity['market']['question'][:60] if opportunity.get('market') else '?'
            print(f"Market: {q}")
            print(f"Underdog: {opportunity['underdog_outcome']} @ {opportunity['underdog_price']:.4f}")
            print(f"Favorite: {opportunity['favorite_outcome']} @ {opportunity['favorite_price']:.4f}")
            print(f"EV: {opportunity['ev']:.4f}")
            print(f"Kelly: {opportunity['kelly_size']:.2%}")

            trade = self.execute_trade(opportunity)
            return trade
        else:
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n[TRADER] No opportunity found at {now}")
            return {"found": False}
