"""CLI entry points for kite-mcp."""

import sys

from kite_mcp.auth import automated_login, get_cached_token, load_credentials


def login():
    """Perform automated Kite login and cache the access token."""
    creds = load_credentials()
    if not creds["totp_secret"]:
        print("Error: KITE_TOTP_SECRET is required for auto-login.", file=sys.stderr)
        sys.exit(1)

    token = automated_login(
        creds["api_key"],
        creds["api_secret"],
        creds["user_id"],
        creds["password"],
        creds["totp_secret"],
    )
    print(f"Login successful. Token cached for today.")


def status():
    """Check if a valid cached token exists."""
    cached = get_cached_token()
    if cached:
        print("Valid token found for today.")
    else:
        print("No valid token. Run 'kite-mcp-login' or set KITE_TOTP_SECRET for auto-login.")
        sys.exit(1)
