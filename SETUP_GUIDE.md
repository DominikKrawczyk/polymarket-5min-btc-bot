# Polymarket Registration Guide
## Jak założyć konto bez www (z Francji)

## Krok 0: Generuj portfel (już zrobione)

```bash
cd /root/projects/polymarket_5min_bot
python3 setup.py gen-wallet
```

**Adres portfela:** `0xBf491634918fb6C9eA9C487a77bc6e839b27d07A`
**Zapisany w:** `secrets.json`

## Krok 1: Wyślij USDC na Polygon

Potrzebujesz:
- **~$10 USDC** (na handel)
- **~0.01 MATIC** (na gaz)

**Opcje (wybierz jedną):**

### A. Ramp (najprostsze, karta kredytowa)
https://ramp.network → kup USDC na Polygon → wyślij na adres portfela

### B. Bridge z Ethereum
Jeśli masz USDC na Ethereum:
https://portal.polygon.technology/bridge → prześlij na Polygon

### C. Transak (karta + Google Pay)
https://transak.com → USDC on Polygon → adres portfela

## Krok 2: Sprawdź saldo

```bash
python3 setup.py balance
```

Powinieneś zobaczyć:
```
MATIC: 0.0123
USDC:  10.00
```

## Krok 3: Stwórz API credentials (przez CLOB API)

```bash
python3 setup.py auth
```

To wyśle EIP-712 podpis do `POST https://clob.polymarket.com/auth/api-key`
→ dostaniesz `api_key`, `secret`, `passphrase`
→ zapisane w `api_creds.json`

## Krok 4: Handluj

```bash
python3 main.py backtest   # test na danych BTC
python3 main.py scan       # scanner
python3 main.py trade      # live trading
```

## WAŻNE

- **CLOB API działa z Francji** — www nie, ale nie potrzebujesz www
- **BTC 5-min markets nie istnieją obecnie** — backtest działa, live czeka na rynki
- **Klucz prywatny w secrets.json** — nie udostępniaj go nikomu
