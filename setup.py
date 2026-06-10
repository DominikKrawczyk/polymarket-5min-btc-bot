"""Polymarket Setup — generates wallet, tests API, creates credentials.
Run this from France VPS. CLOB API works from everywhere."""
import json, os, sys
from eth_account import Account
from eth_account.messages import encode_defunct
from config import config
import requests


def cmd_gen_wallet():
    """Generate a new Polygon wallet for Polymarket."""
    import secrets
    priv = '0x' + secrets.token_hex(32)
    acct = Account.from_key(priv)
    
    data = {
        'address': acct.address,
        'private_key': priv,
        'chain_id': 137
    }
    with open(config.secrets_file, 'w') as f:
        json.dump(data, f)
    
    print("=" * 55)
    print("  NOWY PORTFEL POLYMARKET")
    print("=" * 55)
    print(f"  Adres:  {acct.address}")
    print()
    print("  ⚠️  skopiuj i ZAPISZ ten adres!")
    print("  ⚠️  Wyślij na niego USDC (Polygon)!")
    print()
    print("  Most USDC na Polygon:")
    print("  https://portal.polygon.technology/bridge")
    print()
    print("  Lub kup bezpośrednio:")
    print("  https://ramp.network (USDC → Polygon)")
    print("  https://transak.com (USDC → Polygon)")
    return acct.address


def cmd_test_api():
    """Test if CLOB API works from this server."""
    clob = config.clob_api_url
    tests = [
        ("/", "Health check"),
        ("/time", "Server time"),
        ("/markets?limit=2", "List markets"),
    ]
    print("=== TEST CLOB API ===")
    for path, desc in tests:
        try:
            r = requests.get(f"{clob}{path}", timeout=10)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"  {status} {desc}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  ❌ {desc}: {e}")
    
    print()
    print("=== TEST AUTH ENDPOINT ===")
    wallet = config.get_wallet()
    if not wallet:
        print("  ❌ No wallet. Run 'setup.py gen-wallet' first")
        return
    
    # Try creating API key
    try:
        r = requests.post(
            f"{clob}/auth/api-key",
            json={"address": wallet['address']},
            timeout=10
        )
        if r.status_code == 422:
            # Need funding first - expected
            print(f"  ⏳ Auth endpoint reachable (422: needs wallet funding)")
            print(f"  📌 Wyślij USDC na: {wallet['address']}")
            print(f"  📌 Potem: POST /auth/api-key z podpisem EIP-712")
        else:
            print(f"  Response: HTTP {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"  ❌ Auth error: {e}")


def cmd_balance():
    """Check wallet balance on Polygon."""
    wallet = config.get_wallet()
    if not wallet:
        print("No wallet. Run 'setup.py gen-wallet' first")
        return
    
    addr = wallet['address']
    print(f"=== BALANCE: {addr} ===")
    
    # Check MATIC balance via Polygon RPC (public)
    rpc = "https://polygon-rpc.com"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [addr, "latest"],
        "id": 1
    }
    try:
        r = requests.post(rpc, json=payload, timeout=10)
        bal_wei = int(r.json().get('result', '0x0'), 16)
        bal_matic = bal_wei / 1e18
        print(f"  MATIC: {bal_matic:.4f}")
        if bal_matic < 0.01:
            print("  ⚠️  Potrzebujesz MATIC na gaz (0.01+ MATIC)")
            print("  → https://portal.polygon.technology/bridge")
    except Exception as e:
        print(f"  ❌ RPC error: {e}")
    
    # Check USDC balance
    usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    usdc_payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": usdc_contract,
            "data": f"0x70a08231000000000000000000000000{addr[2:]}"
        }, "latest"],
        "id": 2
    }
    try:
        r = requests.post(rpc, json=usdc_payload, timeout=10)
        bal_usdc = int(r.json().get('result', '0x0'), 16) / 1e6
        print(f"  USDC:  {bal_usdc:.2f}")
    except Exception as e:
        print(f"  ❌ USDC check error: {e}")


def cmd_auth():
    """Create API credentials via CLOB API (EIP-712 signing)."""
    wallet = config.get_wallet()
    if not wallet:
        print("No wallet. Run 'setup.py gen-wallet' first")
        return
    
    from eth_account.messages import encode_typed_data
    
    # EIP-712 domain and types for Polymarket API key creation
    # This is the exact format required by Polymarket CLOB
    domain = {
        "name": "Polymarket",
        "version": "1",
        "chainId": 137,
        "verifyingContract": "0x0000000000000000000000000000000000000000"
    }
    
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "CreateApiKey": [
            {"name": "address", "type": "address"},
            {"name": "timestamp", "type": "uint256"},
        ]
    }
    
    import time
    timestamp = int(time.time())
    
    message = {
        "address": wallet['address'],
        "timestamp": timestamp
    }
    
    try:
        # Sign EIP-712 typed data
        signable = encode_typed_data(domain, types, message)
        signed = Account.sign_message(signable, wallet['private_key'])
        signature = signed.signature.hex()
        
        print(f"=== CREATING API CREDENTIALS ===")
        print(f"  Address:   {wallet['address']}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Signature: {signature[:40]}...")
        
        # Send to CLOB API
        clob = config.clob_api_url
        payload = {
            "address": wallet['address'],
            "timestamp": timestamp,
            "signature": signature
        }
        
        r = requests.post(f"{clob}/auth/api-key", json=payload, timeout=15)
        print(f"  Response: HTTP {r.status_code}")
        
        if r.status_code == 201:
            creds = r.json()
            print(f"  ✅ API KEY:    {creds.get('api_key','?')}")
            print(f"  ✅ API SECRET: {creds.get('secret','?')}")
            print(f"  ✅ PASSPHRASE: {creds.get('passphrase','?')}")
            
            # Save credentials
            creds_file = os.path.join(os.path.dirname(config.secrets_file), "api_creds.json")
            with open(creds_file, 'w') as f:
                json.dump(creds, f)
            print(f"  ✅ Credentials saved to {creds_file}")
        elif r.status_code == 422:
            print(f"  ❌ {r.json().get('message', r.text[:200])}")
            print("  → Wallet needs funding. Wyślij USDC na Polygon.")
        else:
            print(f"  ❌ {r.text[:300]}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 setup.py [gen-wallet|test-api|balance|auth]")
        print()
        print("  gen-wallet  — Generate Polygon wallet")
        print("  test-api    — Test CLOB API access")
        print("  balance     — Check wallet balance")
        print("  auth        — Create API credentials (EIP-712)")
        sys.exit(1)
    
    cmd = sys.argv[1]
    commands = {
        "gen-wallet": cmd_gen_wallet,
        "test-api": cmd_test_api,
        "balance": cmd_balance,
        "auth": cmd_auth,
    }
    
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown: {cmd}")
