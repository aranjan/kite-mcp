"""Shared authentication module for Kite MCP server."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pyotp
import requests
from kiteconnect import KiteConnect

TOKEN_FILE = Path.home() / ".zerodha_kite_token.json"


def load_credentials() -> dict:
    """Load credentials from environment variables.

    Returns a dict with keys: api_key, api_secret, user_id, password, totp_secret.
    Raises SystemExit if required variables are missing.
    """
    required = {
        "KITE_API_KEY": "api_key",
        "KITE_API_SECRET": "api_secret",
        "KITE_USER_ID": "user_id",
        "KITE_PASSWORD": "password",
    }
    creds = {}
    missing = []

    for env_var, key in required.items():
        val = os.environ.get(env_var)
        if not val:
            missing.append(env_var)
        creds[key] = val or ""

    if missing:
        print(
            f"Error: Missing required environment variables: {', '.join(missing)}\n"
            "Set them in your shell or in your MCP client's env config.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    creds["totp_secret"] = os.environ.get("KITE_TOTP_SECRET")
    return creds


def get_cached_token() -> str | None:
    """Return today's cached access token, or None if expired/missing."""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return data["access_token"]
    return None


def automated_login(
    api_key: str,
    api_secret: str,
    user_id: str,
    password: str,
    totp_secret: str,
) -> str:
    """Full automated login: credentials -> TOTP 2FA -> request_token -> access_token.

    Returns the access_token and saves it to TOKEN_FILE.
    """
    session = requests.Session()

    # Step 1: Login with credentials
    resp = session.post(
        "https://kite.zerodha.com/api/login",
        data={"user_id": user_id, "password": password},
    )
    resp.raise_for_status()
    login_data = resp.json()
    if login_data.get("status") != "success":
        raise RuntimeError(f"Login failed: {login_data}")

    request_id = login_data["data"]["request_id"]

    # Step 2: Submit TOTP
    totp_code = pyotp.TOTP(totp_secret).now()
    resp = session.post(
        "https://kite.zerodha.com/api/twofa",
        data={
            "user_id": user_id,
            "request_id": request_id,
            "twofa_value": totp_code,
            "twofa_type": "totp",
        },
    )
    resp.raise_for_status()
    twofa_data = resp.json()
    if twofa_data.get("status") != "success":
        raise RuntimeError(f"2FA failed: {twofa_data}")

    # Step 3: Get request_token via redirect
    resp = session.get(
        f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3",
        allow_redirects=False,
    )

    request_token = None
    while resp.status_code in (301, 302, 303, 307, 308):
        redirect_url = resp.headers["Location"]
        if "request_token=" in redirect_url:
            parsed = urlparse(redirect_url)
            request_token = parse_qs(parsed.query)["request_token"][0]
            break
        resp = session.get(redirect_url, allow_redirects=False)

    if not request_token:
        raise RuntimeError("Could not extract request_token from redirect chain")

    # Step 4: Exchange for access_token
    kite = KiteConnect(api_key=api_key)
    session_data = kite.generate_session(request_token, api_secret=api_secret)

    TOKEN_FILE.write_text(
        json.dumps(
            {
                "access_token": session_data["access_token"],
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
    )
    os.chmod(TOKEN_FILE, 0o600)

    return session_data["access_token"]


def get_authenticated_kite(creds: dict) -> KiteConnect:
    """Return an authenticated KiteConnect instance.

    Tries cached token first. If expired, auto-logs in if TOTP secret is available.
    """
    kite = KiteConnect(api_key=creds["api_key"])

    cached = get_cached_token()
    if cached:
        kite.set_access_token(cached)
        return kite

    if creds["totp_secret"]:
        token = automated_login(
            creds["api_key"],
            creds["api_secret"],
            creds["user_id"],
            creds["password"],
            creds["totp_secret"],
        )
        kite.set_access_token(token)
        return kite

    raise RuntimeError(
        "No valid cached token and KITE_TOTP_SECRET is not set. "
        "Either set KITE_TOTP_SECRET for auto-login, or run 'kite-mcp-login' first."
    )
