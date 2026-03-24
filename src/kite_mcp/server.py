"""Zerodha Kite MCP Server — exposes Kite Connect as tools for AI assistants."""

import json

from kiteconnect import exceptions as kite_exceptions
from mcp.server.fastmcp import FastMCP

from kite_mcp.auth import automated_login, get_authenticated_kite, load_credentials

mcp = FastMCP("kite")


def _kite():
    """Return an authenticated KiteConnect instance. Auto-refreshes token on auth failure."""
    creds = load_credentials()
    kite = get_authenticated_kite(creds)

    # Validate the token is actually working by making a lightweight call
    try:
        kite.profile()
    except (kite_exceptions.TokenException, kite_exceptions.PermissionException):
        # Token is stale/invalidated — force a fresh login
        if creds["totp_secret"]:
            token = automated_login(
                creds["api_key"], creds["api_secret"],
                creds["user_id"], creds["password"], creds["totp_secret"],
            )
            kite.set_access_token(token)
        else:
            raise RuntimeError("Token expired and KITE_TOTP_SECRET not set. Run 'kite-mcp-login'.")

    return kite


@mcp.tool()
def kite_login() -> str:
    """Authenticate with Zerodha Kite. Auto-generates TOTP and logs in. Call this if other tools fail with auth errors."""
    creds = load_credentials()
    if not creds["totp_secret"]:
        return "Error: KITE_TOTP_SECRET is not set. Cannot auto-login."
    automated_login(
        creds["api_key"], creds["api_secret"],
        creds["user_id"], creds["password"], creds["totp_secret"],
    )
    return "Login successful. Access token refreshed."


@mcp.tool()
def get_holdings() -> str:
    """Get all holdings in the portfolio with quantity, average price, last price, and P&L."""
    kite = _kite()
    holdings = kite.holdings()
    total_inv = sum(h["average_price"] * h["quantity"] for h in holdings)
    total_cur = sum(h["last_price"] * h["quantity"] for h in holdings)
    result = {
        "count": len(holdings),
        "total_investment": round(total_inv, 2),
        "total_current_value": round(total_cur, 2),
        "total_pnl": round(total_cur - total_inv, 2),
        "total_pnl_pct": round((total_cur - total_inv) / total_inv * 100, 2) if total_inv else 0,
        "holdings": [
            {
                "symbol": h["tradingsymbol"],
                "quantity": h["quantity"],
                "avg_price": h["average_price"],
                "last_price": h["last_price"],
                "pnl": round((h["last_price"] - h["average_price"]) * h["quantity"], 2),
                "pnl_pct": round((h["last_price"] - h["average_price"]) / h["average_price"] * 100, 2) if h["average_price"] else 0,
            }
            for h in holdings if h["quantity"] > 0
        ],
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def get_positions() -> str:
    """Get current day's positions (both day and net)."""
    kite = _kite()
    return json.dumps(kite.positions(), indent=2, default=str)


@mcp.tool()
def get_orders() -> str:
    """Get all orders placed today."""
    kite = _kite()
    return json.dumps(kite.orders(), indent=2, default=str)


@mcp.tool()
def get_margins() -> str:
    """Get account margins/funds available for trading (equity and commodity segments)."""
    kite = _kite()
    return json.dumps(kite.margins(), indent=2, default=str)


@mcp.tool()
def get_quote(instruments: list[str]) -> str:
    """Get live market quote for one or more instruments. Use NSE: prefix for stocks (e.g., NSE:RELIANCE, NSE:INFY)."""
    kite = _kite()
    return json.dumps(kite.quote(instruments), indent=2, default=str)


@mcp.tool()
def get_ohlc(instruments: list[str]) -> str:
    """Get OHLC (open, high, low, close) and last price for instruments."""
    kite = _kite()
    return json.dumps(kite.ohlc(instruments), indent=2, default=str)


@mcp.tool()
def get_historical_data(instrument_token: int, from_date: str, to_date: str, interval: str) -> str:
    """Get historical candle data for an instrument. Interval can be: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute."""
    kite = _kite()
    data = kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def get_instruments(exchange: str, search: str = "") -> str:
    """Get list of tradeable instruments for an exchange. Use to find instrument_token for historical data. Exchange: NSE, BSE, NFO, BFO, CDS, MCX."""
    kite = _kite()
    instruments = kite.instruments(exchange)
    if search:
        instruments = [i for i in instruments if search.upper() in i["tradingsymbol"].upper()]
    result = [
        {
            "instrument_token": i["instrument_token"],
            "tradingsymbol": i["tradingsymbol"],
            "name": i.get("name", ""),
            "exchange": i["exchange"],
            "lot_size": i.get("lot_size", 1),
            "instrument_type": i.get("instrument_type", ""),
        }
        for i in instruments[:50]
    ]
    total = len(instruments)
    msg = json.dumps(result, indent=2, default=str)
    if total > 50:
        msg += f"\n\n(Showing 50 of {total} results. Use a more specific search to narrow down.)"
    return msg


@mcp.tool()
def place_order(
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    order_type: str,
    product: str,
    price: float | None = None,
    trigger_price: float | None = None,
    variety: str = "regular",
) -> str:
    """Place a buy or sell order. Returns order ID on success. Use variety='regular' for normal orders, 'amo' for after-market orders."""
    kite = _kite()
    params = {
        "tradingsymbol": tradingsymbol,
        "exchange": exchange,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": order_type,
        "product": product,
    }
    if price is not None:
        params["price"] = price
    if trigger_price is not None:
        params["trigger_price"] = trigger_price
    order_id = kite.place_order(variety=variety, **params)
    return json.dumps({"status": "success", "order_id": order_id})


@mcp.tool()
def modify_order(
    order_id: str,
    quantity: int | None = None,
    price: float | None = None,
    order_type: str | None = None,
    trigger_price: float | None = None,
    variety: str = "regular",
) -> str:
    """Modify a pending order."""
    kite = _kite()
    params = {}
    if quantity is not None:
        params["quantity"] = quantity
    if price is not None:
        params["price"] = price
    if order_type is not None:
        params["order_type"] = order_type
    if trigger_price is not None:
        params["trigger_price"] = trigger_price
    oid = kite.modify_order(variety=variety, order_id=order_id, **params)
    return json.dumps({"status": "success", "order_id": oid})


@mcp.tool()
def cancel_order(order_id: str, variety: str = "regular") -> str:
    """Cancel a pending order."""
    kite = _kite()
    oid = kite.cancel_order(variety=variety, order_id=order_id)
    return json.dumps({"status": "success", "order_id": oid})


@mcp.tool()
def get_gtt_triggers() -> str:
    """Get all active GTT (Good Till Triggered) triggers."""
    kite = _kite()
    return json.dumps(kite.get_gtts(), indent=2, default=str)


@mcp.tool()
def place_gtt(
    trigger_type: str,
    tradingsymbol: str,
    exchange: str,
    trigger_values: list[float],
    last_price: float,
    orders: list[dict],
) -> str:
    """Place a GTT (Good Till Triggered) order. Supports single and two-leg (OCO) triggers."""
    kite = _kite()
    from kiteconnect import KiteConnect as KC

    tt = KC.GTT_TYPE_SINGLE if trigger_type == "single" else KC.GTT_TYPE_OCO
    tid = kite.place_gtt(
        trigger_type=tt,
        tradingsymbol=tradingsymbol,
        exchange=exchange,
        trigger_values=trigger_values,
        last_price=last_price,
        orders=orders,
    )
    return json.dumps({"status": "success", "trigger_id": tid})


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
