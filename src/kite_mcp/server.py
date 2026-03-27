"""Zerodha Kite MCP Server — exposes Kite Connect as tools for AI assistants."""

import json
from typing import Annotated

from kiteconnect import exceptions as kite_exceptions
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from kite_mcp.auth import automated_login, get_authenticated_kite, load_credentials

mcp = FastMCP("kite")

# Annotation presets
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)


def _kite():
    """Return an authenticated KiteConnect instance. Auto-refreshes token on auth failure."""
    creds = load_credentials()
    kite = get_authenticated_kite(creds)

    # Validate the token is actually working by making a lightweight call
    try:
        kite.profile()
    except (kite_exceptions.TokenException, kite_exceptions.PermissionException):
        # Token is stale/invalidated — force a fresh login
        if not creds["totp_secret"]:
            raise RuntimeError(
                "Token expired and KITE_TOTP_SECRET not set. "
                "Run 'kite-mcp-login' to refresh manually."
            )
        try:
            token = automated_login(
                creds["api_key"], creds["api_secret"],
                creds["user_id"], creds["password"], creds["totp_secret"],
            )
            kite.set_access_token(token)
        except Exception as e:
            raise RuntimeError(
                f"Token expired and auto-login failed: {type(e).__name__}: {e}. "
                "Run 'kite-mcp-login' to refresh manually."
            ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to validate Kite session: {type(e).__name__}: {e}"
        ) from e

    return kite


@mcp.tool(annotations=WRITE)
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


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=READ_ONLY)
def get_positions() -> str:
    """Get current day's positions (both day and net)."""
    kite = _kite()
    return json.dumps(kite.positions(), indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_orders() -> str:
    """Get all orders placed today."""
    kite = _kite()
    return json.dumps(kite.orders(), indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_margins() -> str:
    """Get account margins/funds available for trading (equity and commodity segments)."""
    kite = _kite()
    return json.dumps(kite.margins(), indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_quote(
    instruments: Annotated[list[str], "List of instruments with exchange prefix, e.g. ['NSE:RELIANCE', 'NSE:INFY']"],
) -> str:
    """Get live market quote for one or more instruments. Use NSE: prefix for stocks (e.g., NSE:RELIANCE, NSE:INFY). Falls back to holdings/positions data if the market data API is not available."""
    kite = _kite()
    try:
        return json.dumps(kite.quote(instruments), indent=2, default=str)
    except Exception:
        return _quote_fallback(kite, instruments)


@mcp.tool(annotations=READ_ONLY)
def get_ohlc(
    instruments: Annotated[list[str], "List of instruments with exchange prefix, e.g. ['NSE:RELIANCE', 'NSE:INFY']"],
) -> str:
    """Get OHLC (open, high, low, close) and last price for instruments. Falls back to holdings/positions data if the market data API is not available."""
    kite = _kite()
    try:
        return json.dumps(kite.ohlc(instruments), indent=2, default=str)
    except Exception:
        return _quote_fallback(kite, instruments)


def _quote_fallback(kite, instruments: list[str]) -> str:
    """Build price data from holdings and positions when the quote API is unavailable."""
    holdings = kite.holdings()
    positions = kite.positions()

    price_map = {}
    for h in holdings:
        symbol = h["tradingsymbol"]
        price_map[symbol] = {
            "last_price": h["last_price"],
            "average_price": h["average_price"],
            "quantity": h["quantity"],
            "pnl": round((h["last_price"] - h["average_price"]) * h["quantity"], 2),
            "source": "holdings",
        }
    for p in positions.get("net", []):
        symbol = p["tradingsymbol"]
        if symbol not in price_map or p.get("last_price"):
            price_map[symbol] = {
                "last_price": p["last_price"],
                "average_price": p["average_price"],
                "quantity": p["quantity"],
                "pnl": p.get("pnl", 0),
                "source": "positions",
            }

    result = {}
    for inst in instruments:
        symbol = inst.split(":")[-1] if ":" in inst else inst
        if symbol in price_map:
            result[inst] = price_map[symbol]
        else:
            result[inst] = {"error": f"{symbol} not found in holdings or positions. Market data API not available on personal apps."}

    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_historical_data(
    instrument_token: Annotated[int, "Numeric instrument token (use get_instruments to find it)"],
    from_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    to_date: Annotated[str, "End date in YYYY-MM-DD format"],
    interval: Annotated[str, "Candle interval: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute"],
) -> str:
    """Get historical candle data for an instrument. Interval can be: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute."""
    kite = _kite()
    data = kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )
    return json.dumps(data, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_instruments(
    exchange: Annotated[str, "Exchange name: NSE, BSE, NFO, BFO, CDS, MCX"],
    search: Annotated[str, "Optional: filter instruments by trading symbol (case-insensitive substring match)"] = "",
) -> str:
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


@mcp.tool(annotations=WRITE)
def place_order(
    tradingsymbol: Annotated[str, "Trading symbol, e.g. RELIANCE, INFY"],
    exchange: Annotated[str, "Exchange: NSE or BSE"],
    transaction_type: Annotated[str, "BUY or SELL"],
    quantity: Annotated[int, "Number of shares"],
    order_type: Annotated[str, "MARKET, LIMIT, SL, or SL-M"],
    product: Annotated[str, "CNC (delivery), MIS (intraday), or NRML (F&O normal)"],
    price: Annotated[float | None, "Price for LIMIT/SL orders. Not needed for MARKET orders."] = None,
    trigger_price: Annotated[float | None, "Trigger price for SL/SL-M orders."] = None,
    variety: Annotated[str, "Order variety: regular, amo (after-market). Default: regular"] = "regular",
) -> str:
    """Place a buy or sell order. Returns order ID on success. Use variety='regular' for normal orders, 'amo' for after-market orders."""
    # Input validation
    if quantity <= 0:
        return json.dumps({"status": "error", "message": "Quantity must be greater than 0"})
    if transaction_type.upper() not in ("BUY", "SELL"):
        return json.dumps({"status": "error", "message": f"Invalid transaction_type: {transaction_type}. Must be BUY or SELL"})
    if product.upper() not in ("CNC", "MIS", "NRML"):
        return json.dumps({"status": "error", "message": f"Invalid product: {product}. Must be CNC, MIS, or NRML"})
    if order_type.upper() not in ("MARKET", "LIMIT", "SL", "SL-M"):
        return json.dumps({"status": "error", "message": f"Invalid order_type: {order_type}. Must be MARKET, LIMIT, SL, or SL-M"})
    if order_type.upper() in ("LIMIT", "SL") and (price is None or price <= 0):
        return json.dumps({"status": "error", "message": f"{order_type} orders require a price > 0"})
    if order_type.upper() in ("SL", "SL-M") and (trigger_price is None or trigger_price <= 0):
        return json.dumps({"status": "error", "message": f"{order_type} orders require a trigger_price > 0"})
    if price is not None and price < 0:
        return json.dumps({"status": "error", "message": "Price cannot be negative"})
    if variety not in ("regular", "amo"):
        return json.dumps({"status": "error", "message": f"Invalid variety: {variety}. Must be regular or amo"})

    kite = _kite()
    params = {
        "tradingsymbol": tradingsymbol,
        "exchange": exchange,
        "transaction_type": transaction_type.upper(),
        "quantity": quantity,
        "order_type": order_type.upper(),
        "product": product.upper(),
    }
    if price is not None:
        params["price"] = price
    if trigger_price is not None:
        params["trigger_price"] = trigger_price
    order_id = kite.place_order(variety=variety, **params)
    return json.dumps({"status": "success", "order_id": order_id})


@mcp.tool(annotations=WRITE)
def modify_order(
    order_id: Annotated[str, "Order ID to modify"],
    quantity: Annotated[int | None, "New quantity"] = None,
    price: Annotated[float | None, "New price"] = None,
    order_type: Annotated[str | None, "New order type: MARKET, LIMIT, SL, SL-M"] = None,
    trigger_price: Annotated[float | None, "New trigger price"] = None,
    variety: Annotated[str, "Order variety: regular, amo. Default: regular"] = "regular",
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


@mcp.tool(annotations=DESTRUCTIVE)
def cancel_order(
    order_id: Annotated[str, "Order ID to cancel"],
    variety: Annotated[str, "Order variety: regular, amo. Default: regular"] = "regular",
) -> str:
    """Cancel a pending order."""
    kite = _kite()
    oid = kite.cancel_order(variety=variety, order_id=order_id)
    return json.dumps({"status": "success", "order_id": oid})


@mcp.tool(annotations=READ_ONLY)
def get_gtt_triggers() -> str:
    """Get all active GTT (Good Till Triggered) triggers."""
    kite = _kite()
    return json.dumps(kite.get_gtts(), indent=2, default=str)


@mcp.tool(annotations=WRITE)
def place_gtt(
    trigger_type: Annotated[str, "Trigger type: single or two-leg (OCO)"],
    tradingsymbol: Annotated[str, "Trading symbol, e.g. RELIANCE"],
    exchange: Annotated[str, "Exchange: NSE or BSE"],
    trigger_values: Annotated[list[float], "Trigger price(s). One for single, two for OCO [stoploss, target]."],
    last_price: Annotated[float, "Current market price of the instrument"],
    orders: Annotated[list[dict], "Order legs. Each: {transaction_type, quantity, price, order_type, product}"],
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
