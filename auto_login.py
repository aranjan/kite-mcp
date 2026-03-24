#!/usr/bin/env python3
"""Fully automated Kite login + holdings fetch. No manual intervention needed."""

import os
import json
import requests
import pyotp
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

API_KEY = os.environ["KITE_API_KEY"]
API_SECRET = os.environ["KITE_API_SECRET"]
USER_ID = os.environ["KITE_USER_ID"]
PASSWORD = os.environ["KITE_PASSWORD"]
TOTP_SECRET = os.environ["KITE_TOTP_SECRET"]
TOKEN_FILE = Path.home() / ".zerodha_kite_token.json"


def generate_totp():
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.now()


def automated_login():
    """Automate the full Kite login flow: login -> TOTP 2FA -> get request_token -> access_token."""
    session = requests.Session()

    # Step 1: Login with user_id and password
    print("Step 1: Logging in...")
    resp = session.post(
        "https://kite.zerodha.com/api/login",
        data={"user_id": USER_ID, "password": PASSWORD},
    )
    resp.raise_for_status()
    login_data = resp.json()

    if login_data.get("status") != "success":
        raise Exception(f"Login failed: {login_data}")

    request_id = login_data["data"]["request_id"]
    print(f"  Login successful. Request ID: {request_id}")

    # Step 2: Submit TOTP for 2FA
    print("Step 2: Submitting TOTP...")
    totp_code = generate_totp()
    resp = session.post(
        "https://kite.zerodha.com/api/twofa",
        data={
            "user_id": USER_ID,
            "request_id": request_id,
            "twofa_value": totp_code,
            "twofa_type": "totp",
        },
    )
    resp.raise_for_status()
    twofa_data = resp.json()

    if twofa_data.get("status") != "success":
        raise Exception(f"2FA failed: {twofa_data}")

    print("  2FA successful.")

    # Step 3: Get request_token via Kite Connect redirect
    print("Step 3: Getting request_token...")
    resp = session.get(
        f"https://kite.zerodha.com/connect/login?api_key={API_KEY}&v=3",
        allow_redirects=False,
    )

    # Follow redirects manually to capture request_token
    while resp.status_code in (301, 302, 303, 307, 308):
        redirect_url = resp.headers["Location"]
        if "request_token=" in redirect_url:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(redirect_url)
            request_token = parse_qs(parsed.query)["request_token"][0]
            print(f"  Got request_token: {request_token[:8]}...")
            break
        resp = session.get(redirect_url, allow_redirects=False)
    else:
        raise Exception("Could not extract request_token from redirect chain")

    # Step 4: Exchange request_token for access_token
    print("Step 4: Exchanging for access_token...")
    kite = KiteConnect(api_key=API_KEY)
    session_data = kite.generate_session(request_token, api_secret=API_SECRET)

    TOKEN_FILE.write_text(json.dumps({
        "access_token": session_data["access_token"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }))

    print(f"  Authenticated as: {session_data['user_name']} ({session_data['email']})")
    print(f"  Token saved to: {TOKEN_FILE}")

    return session_data["access_token"]


def fetch_holdings(access_token):
    """Fetch and display portfolio holdings."""
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(access_token)

    holdings = kite.holdings()
    total_investment = 0
    total_current = 0

    print(f"\nFound {len(holdings)} holdings:\n")
    print(f"  {'Symbol':<20} {'Qty':<6} {'Avg':>10} {'LTP':>10} {'P&L':>12} {'%':>8}")
    print("  " + "-" * 68)

    for h in holdings:
        qty = h["quantity"]
        avg = h["average_price"]
        last = h["last_price"]
        pnl = (last - avg) * qty
        pnl_pct = ((last - avg) / avg * 100) if avg else 0
        total_investment += avg * qty
        total_current += last * qty
        if qty > 0:
            print(f"  {h['tradingsymbol']:<20} {qty:<6} {avg:>10.2f} {last:>10.2f} {pnl:>12.2f} {pnl_pct:>+7.2f}%")

    total_pnl = total_current - total_investment
    total_pnl_pct = (total_pnl / total_investment * 100) if total_investment else 0

    print("  " + "-" * 68)
    print(f"  {'TOTAL':<20} {'':6} {total_investment:>10.2f} {total_current:>10.2f} {total_pnl:>12.2f} {total_pnl_pct:>+7.2f}%")

    return holdings


if __name__ == "__main__":
    access_token = automated_login()
    fetch_holdings(access_token)
