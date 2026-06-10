# Polymarket CLOB API Audit Report

## Sources Consulted

1. **CLOB API direct** — `https://clob.polymarket.com/` (verified live)
2. **Gamma API** — `https://gamma-api.polymarket.com/` (verified live)
3. **py-clob-client** — `https://github.com/Polymarket/py-clob-client` (archived)
4. **py-sdk** — `https://github.com/Polymarket/py-sdk` (current official SDK, beta)
5. **Official docs** — `https://docs.polymarket.com/api` (404/Mintlify error, not accessible)

---

## 1. CLOB API Endpoints (Comprehensive)

### Public / Level 0 (no auth required)

| Method | Endpoint | Params | Description |
|--------|----------|--------|-------------|
| GET | `/` | — | Health check (returns `"OK"`) |
| GET | `/time` | — | Server timestamp (unix epoch) |
| GET | `/markets` | `?limit=N&next_cursor=X&tag=T` | List markets (paginated, 1000 per page) |
| GET | `/markets/{condition_id}` | — | Single market by condition ID |
| GET | `/simplified-markets` | `?limit=N&next_cursor=X` | Simplified market list (lightweight) |
| GET | `/sampling-markets` | `?next_cursor=X` | Sampling-enabled markets |
| GET | `/sampling-simplified-markets` | `?next_cursor=X` | Simplified sampling markets |
| GET | `/book` | `?token_id=X` | Order book for a single token |
| GET | `/books` | (POST) | Order books for multiple tokens (POST with body) |
| GET | `/midpoint` | `?token_id=X` | Midpoint price |
| GET | `/midpoints` | (POST) | Midpoints for multiple tokens |
| GET | `/price` | `?token_id=X&side=BUY|SELL` | Best price for side |
| GET | `/prices` | (POST) | Prices for multiple tokens |
| GET | `/spread` | `?token_id=X` | Bid-ask spread |
| GET | `/spreads` | (POST) | Spreads for multiple tokens |
| GET | `/last-trade-price` | `?token_id=X` | Last trade price |
| GET | `/last-trades-prices` | (POST) | Last trades for multiple tokens |
| GET | `/tick-size` | `?token_id=X` | `{"minimum_tick_size": 0.01}` |
| GET | `/neg-risk` | `?token_id=X` | `{"neg_risk": false}` |
| GET | `/fee-rate` | `?token_id=X` | `{"base_fee": 0}` |
| GET | `/prices-history` | `?market=X&interval=1w|1d|6h|1h&startTs=&endTs=` | Price history |
| POST | `/midpoints` | `[{"token_id":"..."}]` | Batch midpoint |
| POST | `/books` | `[{"token_id":"..."}]` | Batch order books |
| POST | `/prices` | `[{"token_id":"...","side":"BUY"}]` | Batch prices |
| POST | `/last-trades-prices` | `[{"token_id":"..."}]` | Batch last trades |

### Level 1 Auth (requires private key)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/api-key` | Create API credentials |
| GET | `/auth/derive-api-key` | Derive existing API credentials |
| POST | `/order` | Create & sign order (via `create_order` on client) |

### Level 2 Auth (requires private key + API creds)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/order` | Place signed order |
| POST | `/orders` | Place multiple orders |
| DELETE | `/order` | Cancel single order (`{"orderID":"..."}`) |
| DELETE | `/orders` | Cancel multiple orders |
| DELETE | `/cancel-all` | Cancel ALL orders |
| DELETE | `/cancel-market-orders` | Cancel by market/asset |
| GET | `/data/orders` | Get user's orders |
| GET | `/data/order/{id}` | Get single order |
| GET | `/data/trades` | Get user's trades |
| GET | `/auth/api-keys` | List API keys |
| DELETE | `/auth/api-key` | Delete API key |
| GET | `/auth/ban-status/closed-only` | Check closed-only mode |
| POST | `/auth/readonly-api-key` | Create readonly key |
| GET | `/auth/readonly-api-keys` | List readonly keys |
| DELETE | `/auth/readonly-api-key` | Delete readonly key |
| GET | `/auth/validate-readonly-api-key?address=&key=` | Validate readonly key |
| GET | `/balance-allowance` | Get balance & allowance |
| GET | `/balance-allowance/update` | Update balance allowance |
| GET | `/notifications` | Get notifications |
| DELETE | `/notifications` | Drop notifications |
| GET | `/order-scoring` | Check if order is scoring |
| POST | `/orders-scoring` | Check if orders are scoring |
| POST | `/v1/heartbeats` | Send heartbeat (10s timeout auto-cancel) |
| GET | `/builder/trades` | Get builder's trades |

### RFQ Endpoints (Level 2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rfq/request` | Create RFQ request |
| DELETE | `/rfq/request` | Cancel RFQ request |
| GET | `/rfq/data/requests` | Get RFQ requests |
| POST | `/rfq/quote` | Create RFQ quote |
| DELETE | `/rfq/quote` | Cancel RFQ quote |
| GET | `/rfq/data/requester/quotes` | Quotes for requester |
| GET | `/rfq/data/quoter/quotes` | Quotes for quoter |
| GET | `/rfq/data/best-quote` | Best quote |
| POST | `/rfq/request/accept` | Accept RFQ request |
| POST | `/rfq/quote/approve` | Approve RFQ quote |
| GET | `/rfq/config` | RFQ config |

---

## 2. Authentication System

Three levels:

### Level 0 — Public / Read-Only
- No authentication
- Access to: markets, orderbooks, prices, midpoint, tick-size, etc.

### Level 1 — Signer Auth
- Requires wallet **private key**
- EIP-712 signing for API key creation/derivation
- Can create and **sign** orders locally
- Cannot yet POST orders

### Level 2 — Full Auth
- Level 1 + **API credentials** (api_key, api_secret, api_passphrase)
- Credentials created via `POST /auth/api-key` or derived via `GET /auth/derive-api-key`
- All trading, cancel, balance operations
- HMAC-SHA256 signatures on all requests using secret + passphrase

### Signature Types
- `0` — EOA (MetaMask, hardware wallets)
- `1` — Email/Magic wallet (delegated signing)
- `2` — Browser wallet proxy
- `3` — Poly 1271 (smart contract wallets)

---

## 3. Data Structures

### Market (from `/markets`):
```json
{
  "condition_id": "0x...",
  "question_id": "0x...",
  "question": "Will BTC reach $100K?",
  "description": "...",
  "market_slug": "...",
  "end_date_iso": "2024-01-01T00:00:00Z",
  "game_start_time": "...",
  "seconds_delay": 3,
  "fpmm": "0x...",
  "minimum_order_size": 15,
  "minimum_tick_size": 0.01,
  "maker_base_fee": 0,
  "taker_base_fee": 0,
  "neg_risk": false,
  "neg_risk_market_id": "",
  "neg_risk_request_id": "",
  "enable_order_book": true,
  "active": true,
  "closed": false,
  "accepting_orders": true,
  "tokens": [
    {
      "token_id": "uint256-as-string",
      "outcome": "Up",
      "price": 0.65,
      "winner": false
    },
    {
      "token_id": "uint256-as-string",
      "outcome": "Down",
      "price": 0.35,
      "winner": false
    }
  ],
  "tags": ["All", "Crypto"],
  "rewards": {"rates": null, "min_size": 0, "max_spread": 0}
}
```

### Gamma API Market (richer data):
```json
{
  "id": "540817",
  "question": "...",
  "conditionId": "0x...",
  "slug": "...",
  "outcomes": "[\"Yes\", \"No\"]",
  "outcomePrices": "[\"0.51\", \"0.49\"]",
  "clobTokenIds": "[token_id_yes, token_id_no]",
  "volume": "823151.27",
  "liquidity": "18242.56",
  "volume24hr": "500.91",
  "negRisk": false,
  "acceptingOrders": true,
  "active": true,
  "closed": false,
  "events": [{
    "id": "23784",
    "title": "...",
    "slug": "...",
    "active": true
  }]
}
```

### Order Book (`/book?token_id=X`):
```json
{
  "market": "0x...",
  "asset_id": "token_id_string",
  "timestamp": "...",
  "bids": [{"price": "0.05", "size": "1000"}],
  "asks": [{"price": "0.06", "size": "800"}],
  "min_order_size": "15",
  "tick_size": "0.01",
  "last_trade_price": "0.055",
  "neg_risk": false,
  "hash": "..."
}
```

### Order Types
- **GTC** — Good 'Til Cancelled (default)
- **GTD** — Good 'Til Date (requires `expiration`)
- **FOK** — Fill Or Kill (for market orders)
- **FAK** — Fill And Kill (immediate, partial fill ok)

### Order Structure (signed off-chain):
```json
{
  "order": {
    "token_id": "...",
    "side": "BUY",
    "price": "0.01",
    "size": "100.0",
    "fee_rate_bps": 0,
    "nonce": 0,
    "expiration": 0,
    "taker": "0x0000...0000",
    "maker": "0x...",
    "signer": "0x...",
    "signature": "0x...",
    "signature_type": 0,
    "salt": 0,
    "timestamp": 0,
    "chain_id": 137,
    "exchange_address": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
  },
  "orderType": "GTC",
  "owner": "api_key_string"
}
```

---

## 4. Order Placement Flow

1. **Initialize client** with `host`, `key` (private key), `chain_id` (137=Polygon, 80002=Amoy)
2. **Create/derive API creds**: `client.create_or_derive_api_creds()` → `ApiCreds(api_key, api_secret, api_passphrase)`
3. **Set creds**: `client.set_api_creds(creds)`
4. **Build order**:
   - **Limit**: `OrderArgs(token_id, price, size, side)` → `client.create_order(args)` → `SignedOrder`
   - **Market buy**: `MarketOrderArgs(token_id, amount=USDC_$, side=BUY)`
   - **Market sell**: `MarketOrderArgs(token_id, amount=SHARES, side=SELL)`
5. **Post order**: `client.post_order(signed_order, OrderType.GTC)`
6. **Monitor**: `client.get_orders()`, `client.get_order(id)`

### Important: Token Allowances
Before trading, must approve token spend:
- **USDC** (`0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` on Polygon)
- **Conditional tokens** (`0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` on Polygon)
- Approve for exchange contracts:
  - Main: `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E`
  - NegRisk: `0xC5d563A36AE78145C45a50134d48A1215220f80a`
  - NegRisk adapter: `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296`

### Contract Configs (Polygon mainnet, chain_id=137):
| Contract | Standard | NegRisk |
|----------|----------|---------|
| Exchange | `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` | `0xC5d563A36AE78145C45a50134d48A1215220f80a` |
| USDC | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` | same |
| Conditional Tokens | `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` | same |

---

## 5. NegRisk Markets

NegRisk (negative risk) markets use a **separate exchange contract** but the same USDC and conditional token contracts. Flagged by `neg_risk: true` on the market object.

Key details:
- `/neg-risk?token_id=X` returns `{"neg_risk": bool}`
- NegRisk exchange: `0xC5d563A36AE78145C45a50134d48A1215220f80a`
- NegRisk adapter: `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296`
- BTC 5-min up/down markets, if they exist on Polymarket, would likely use NegRisk

---

## 6. BTC 5-Minute Up/Down Markets

**Status: No active BTC 5-minute up/down markets found on the live API.**

The search was conducted via:
1. `/markets` (all 1000 markets, no active BTC 5-min found)
2. Gamma API `/markets` (Crypto tag, no BTC 5-min found)
3. Gamma API `/events` (no BTC 5-min events)
4. Only 4 BTC markets found total, all resolved/closed

The historical BTC up/down 5-minute markets (described in the PolyMarket video) were likely part of a specific season/event and are **no longer active**. The bot's `get_btc_updown_markets()` function will return empty results against the live API.

---

## 7. Bot Code Audit — Issues Found

### CRITICAL: polymarket_client.py

| # | Issue | Code | Fix Required |
|---|-------|------|-------------|
| 1 | **No auth implemented** | No private key, no API creds, no signing — only uses `requests.Session()` | Must add wallet key, `py-clob-client` or `py-sdk` for auth |
| 2 | **`get_btc_updown_markets()` uses wrong API** | Hitting `/events` with tag params | Gamma API `/events` doesn't filter by `tag` query param; should use `/markets?tag=crypto` |
| 3 | **No `threading` in `get_market_price`** | Sequential orderbook fetches | Each token's orderbook is fetched separately; should parallelize or batch |
| 4 | **No error handling for empty orderbook** | Assumes `bids[0]` and `asks[0]` exist | Will crash on empty books |
| 5 | **Prices hardcoded from market tokens** | Using `tokens[0]["price"]` from market object | This is the resolved price (0 or 1), not the live CLOB price; must use `/book` or `/price` |
| 6 | **`tag` param on `/markets` not working** | `GET /markets?tag=All` | The CLOB `/markets` endpoint doesn't accept a `tag` parameter — returns 200 but ignores it |

### CRITICAL: trader.py

| # | Issue | Code | Fix Required |
|---|-------|------|-------------|
| 7 | **No actual order placement** | `execute_trade()` only logs trades | Needs full auth flow + `client.post_order()` |
| 8 | **Uses `tokens[0]["price"]` for live pricing** | Lines 42-52 | These are resolved prices (0 or 1), not live CLOB prices |
| 9 | **No `py-clob-client` or `py-sdk` dependency** | Uses raw requests | Must install `py-clob-client` or `polymarket-client` |

### HIGH: scanner.py

| # | Issue | Code | Fix Required |
|---|-------|------|-------------|
| 10 | **Fallback to CLOB markets has no BTC 5-min up/down** | Lines 48-56 | The CLOB has no active 5-min BTC markets; fallback won't find anything |
| 11 | **Logs both market price and orderbook price** | Lines 80-81, 87-90 | Mixed data sources — market price (0/1) vs orderbook mid-price |
| 12 | **Only processes first 10 markets** | `btc_markets_data[:10]` | Fine for debugging but means many markets missed |

### MEDIUM: backtester.py

| # | Issue | Code | Fix Required |
|---|-------|------|-------------|
| 13 | **Simulated pricing not based on any real data** | `simulate_market_prices()` returns hardcoded (0.95, 0.05) | No real orderbook data was collected; results are meaningless |
| 14 | **Random win rate with seeded randomness** | Lines 89-95 | Not a proper backtest — just random number generation |

### LOW: config.py

| # | Issue | Code | Fix Required |
|---|-------|------|-------------|
| 15 | **WebSocket URL not used** | `polymarket_ws_url` defined but never implemented | Could be used for live orderbook streaming |
| 16 | **No wallet config** | No private key, API creds, or signature type | Cannot actually trade without these |

---

## 8. Official SDK Migration Path

The **py-clob-client** is **archived and no longer maintained**. The new official SDK is **`polymarket-client`** via `pip install --pre polymarket-client`.

```python
# New SDK API (beta)
from polymarket import Market, PublicClient

with PublicClient() as client:
    market: Market = client.get_market(url="https://polymarket.com/event/...")
```

However, the py-clob-client is still functional for the CLOB REST API and has more comprehensive documentation. The new SDK is in beta with limited documentation.

---

## 9. Gamma API (for market discovery)

Base URL: `https://gamma-api.polymarket.com`

| Endpoint | Description |
|----------|-------------|
| `GET /markets?tag=crypto&limit=200&closed=false` | List active markets by tag |
| `GET /markets/{id}` | Single market (rich data) |
| `GET /events?limit=100` | List events (groups of markets) |
| `GET /events/{id}` | Single event with its markets |
| `GET /neg-risk?limit=100` | NegRisk markets |

Gamma API markets have additional fields like `clobTokenIds`, `outcomePrices`, `volume24hr`, `liquidityClob` that the CLOB markets don't provide.

---

## Summary

The bot code has **fundamental architectural issues**:

1. **No authentication** — Cannot place any real orders. Needs wallet private key + API credentials + proper signing flow.

2. **Wrong price source** — Using resolved market prices (0 or 1) instead of live CLOB order book prices. The tokens' `price` field in the market object is the resolved price, not the current trading price.

3. **No BTC 5-min markets exist** — The specific market type the bot targets doesn't currently exist on Polymarket. The historical markets from the viral video are no longer active.

4. **Backtest is simulated** — No real data was used; just random number generation with hardcoded assumptions.

5. **No SDK dependency** — Building raw requests instead of using `py-clob-client` or the new `polymarket-client` SDK.

### Required Fixes (Priority Order)

1. Add `py-clob-client` or `polymarket-client` dependency
2. Implement full auth flow (private key → API creds → L2 auth)
3. Fix price fetching to use `/book` or `/price` endpoints
4. Find actual active markets to trade on (verify market existence first)
5. Add proper token allowance management
6. Implement actual order placement with `post_order()`
