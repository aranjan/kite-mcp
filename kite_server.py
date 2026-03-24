#!/usr/bin/env python3
"""Zerodha Kite MCP Server — exposes Kite Connect as tools for Claude."""

import os
import json
import requests
import pyotp
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

API_KEY = os.environ["KITE_API_KEY"]
API_SECRET = os.environ["KITE_API_SECRET"]
USER_ID = os.environ["KITE_USER_ID"]
PASSWORD = os.environ["KITE_PASSWORD"]
TOTP_SECRET = os.environ["KITE_TOTP_SECRET"]
TOKEN_FILE = Path.home() / ".zerodha_kite_token.json"

app = Server("kite-server")


def get_authenticated_kite():
    """Return an authenticated KiteConnect instance, auto-logging in if needed."""
    kite = KiteConnect(api_key=API_KEY)

    # Check if we have a valid token for today
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
            kite.set_access_token(data["access_token"])
            return kite

    # Auto-login
    access_token = automated_login()
    kite.set_access_token(access_token)
    return kite


def automated_login():
    """Full automated login: credentials -> TOTP -> request_token -> access_token."""
    session = requests.Session()

    resp = session.post(
        "https://kite.zerodha.com/api/login",
        data={"user_id": USER_ID, "password": PASSWORD},
    )
    resp.raise_for_status()
    login_data = resp.json()
    if login_data.get("status") != "success":
        raise Exception(f"Login failed: {login_data}")

    request_id = login_data["data"]["request_id"]

    totp_code = pyotp.TOTP(TOTP_SECRET).now()
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

    resp = session.get(
        f"https://kite.zerodha.com/connect/login?api_key={API_KEY}&v=3",
        allow_redirects=False,
    )

    from urllib.parse import urlparse, parse_qs

    while resp.status_code in (301, 302, 303, 307, 308):
        redirect_url = resp.headers["Location"]
        if "request_token=" in redirect_url:
            parsed = urlparse(redirect_url)
            request_token = parse_qs(parsed.query)["request_token"][0]
            break
        resp = session.get(redirect_url, allow_redirects=False)
    else:
        raise Exception("Could not extract request_token from redirect chain")

    kite = KiteConnect(api_key=API_KEY)
    session_data = kite.generate_session(request_token, api_secret=API_SECRET)

    TOKEN_FILE.write_text(json.dumps({
        "access_token": session_data["access_token"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }))

    return session_data["access_token"]


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="kite_login",
            description="Authenticate with Zerodha Kite. Auto-generates TOTP and logs in. Call this if other tools fail with auth errors.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_holdings",
            description="Get all holdings in the portfolio with quantity, average price, last price, and P&L.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_positions",
            description="Get current day's positions (both day and net).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_orders",
            description="Get all orders placed today.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_margins",
            description="Get account margins/funds available for trading (equity and commodity segments).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_quote",
            description="Get live market quote for one or more instruments. Use NSE: prefix for stocks (e.g., NSE:RELIANCE, NSE:INFY).",
            inputSchema={
                "type": "object",
                "properties": {
                    "instruments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of instruments like ['NSE:RELIANCE', 'NSE:INFY']",
                    }
                },
                "required": ["instruments"],
            },
        ),
        Tool(
            name="get_ohlc",
            description="Get OHLC (open, high, low, close) and last price for instruments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "instruments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of instruments like ['NSE:RELIANCE', 'NSE:INFY']",
                    }
                },
                "required": ["instruments"],
            },
        ),
        Tool(
            name="get_historical_data",
            description="Get historical candle data for an instrument. Interval can be: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute.",
            inputSchema={
                "type": "object",
                "properties": {
                    "instrument_token": {
                        "type": "integer",
                        "description": "Numeric instrument token (use get_instruments to find it)",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Candle interval: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute",
                    },
                },
                "required": ["instrument_token", "from_date", "to_date", "interval"],
            },
        ),
        Tool(
            name="get_instruments",
            description="Get list of tradeable instruments for an exchange. Use to find instrument_token for historical data. Exchange: NSE, BSE, NFO, BFO, CDS, MCX.",
            inputSchema={
                "type": "object",
                "properties": {
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name: NSE, BSE, NFO, BFO, CDS, MCX",
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional: filter instruments by trading symbol (case-insensitive substring match)",
                    },
                },
                "required": ["exchange"],
            },
        ),
        Tool(
            name="place_order",
            description="Place a buy or sell order. Returns order ID on success. Use variety='regular' for normal orders, 'amo' for after-market orders.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tradingsymbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., RELIANCE, INFY)",
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange: NSE or BSE",
                    },
                    "transaction_type": {
                        "type": "string",
                        "description": "BUY or SELL",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares",
                    },
                    "order_type": {
                        "type": "string",
                        "description": "MARKET, LIMIT, SL, or SL-M",
                    },
                    "product": {
                        "type": "string",
                        "description": "CNC (delivery), MIS (intraday), or NRML (F&O normal)",
                    },
                    "price": {
                        "type": "number",
                        "description": "Price for LIMIT/SL orders. Not needed for MARKET orders.",
                    },
                    "trigger_price": {
                        "type": "number",
                        "description": "Trigger price for SL/SL-M orders.",
                    },
                    "variety": {
                        "type": "string",
                        "description": "Order variety: regular, amo (after-market). Default: regular",
                    },
                },
                "required": ["tradingsymbol", "exchange", "transaction_type", "quantity", "order_type", "product"],
            },
        ),
        Tool(
            name="modify_order",
            description="Modify a pending order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to modify"},
                    "quantity": {"type": "integer", "description": "New quantity"},
                    "price": {"type": "number", "description": "New price"},
                    "order_type": {"type": "string", "description": "New order type: MARKET, LIMIT, SL, SL-M"},
                    "trigger_price": {"type": "number", "description": "New trigger price"},
                    "variety": {"type": "string", "description": "Order variety: regular, amo. Default: regular"},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="cancel_order",
            description="Cancel a pending order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to cancel"},
                    "variety": {"type": "string", "description": "Order variety: regular, amo. Default: regular"},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="get_gtt_triggers",
            description="Get all active GTT (Good Till Triggered) triggers.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="place_gtt",
            description="Place a GTT (Good Till Triggered) order. Supports single and two-leg (OCO) triggers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trigger_type": {
                        "type": "string",
                        "description": "single or two-leg (OCO)",
                    },
                    "tradingsymbol": {"type": "string", "description": "Trading symbol"},
                    "exchange": {"type": "string", "description": "Exchange: NSE or BSE"},
                    "trigger_values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Trigger price(s). One for single, two for OCO [stoploss, target].",
                    },
                    "last_price": {"type": "number", "description": "Current market price of the instrument"},
                    "orders": {
                        "type": "array",
                        "description": "Order legs. Each: {transaction_type, quantity, price, order_type, product}",
                    },
                },
                "required": ["trigger_type", "tradingsymbol", "exchange", "trigger_values", "last_price", "orders"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        kite = get_authenticated_kite()

        if name == "kite_login":
            access_token = automated_login()
            return [TextContent(type="text", text="Login successful. Access token refreshed.")]

        elif name == "get_holdings":
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
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_positions":
            positions = kite.positions()
            return [TextContent(type="text", text=json.dumps(positions, indent=2, default=str))]

        elif name == "get_orders":
            orders = kite.orders()
            return [TextContent(type="text", text=json.dumps(orders, indent=2, default=str))]

        elif name == "get_margins":
            margins = kite.margins()
            return [TextContent(type="text", text=json.dumps(margins, indent=2, default=str))]

        elif name == "get_quote":
            instruments = arguments["instruments"]
            quotes = kite.quote(instruments)
            return [TextContent(type="text", text=json.dumps(quotes, indent=2, default=str))]

        elif name == "get_ohlc":
            instruments = arguments["instruments"]
            ohlc = kite.ohlc(instruments)
            return [TextContent(type="text", text=json.dumps(ohlc, indent=2, default=str))]

        elif name == "get_historical_data":
            data = kite.historical_data(
                instrument_token=arguments["instrument_token"],
                from_date=arguments["from_date"],
                to_date=arguments["to_date"],
                interval=arguments["interval"],
            )
            return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "get_instruments":
            instruments = kite.instruments(arguments["exchange"])
            search = arguments.get("search", "").upper()
            if search:
                instruments = [i for i in instruments if search in i["tradingsymbol"].upper()]
            # Limit results to avoid huge responses
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
            return [TextContent(type="text", text=msg)]

        elif name == "place_order":
            order_params = {
                "tradingsymbol": arguments["tradingsymbol"],
                "exchange": arguments["exchange"],
                "transaction_type": arguments["transaction_type"],
                "quantity": arguments["quantity"],
                "order_type": arguments["order_type"],
                "product": arguments["product"],
                "variety": arguments.get("variety", "regular"),
            }
            if arguments.get("price") is not None:
                order_params["price"] = arguments["price"]
            if arguments.get("trigger_price") is not None:
                order_params["trigger_price"] = arguments["trigger_price"]

            variety = order_params.pop("variety")
            order_id = kite.place_order(variety=variety, **order_params)
            return [TextContent(type="text", text=json.dumps({"status": "success", "order_id": order_id}))]

        elif name == "modify_order":
            params = {}
            if arguments.get("quantity") is not None:
                params["quantity"] = arguments["quantity"]
            if arguments.get("price") is not None:
                params["price"] = arguments["price"]
            if arguments.get("order_type") is not None:
                params["order_type"] = arguments["order_type"]
            if arguments.get("trigger_price") is not None:
                params["trigger_price"] = arguments["trigger_price"]

            variety = arguments.get("variety", "regular")
            order_id = kite.modify_order(variety=variety, order_id=arguments["order_id"], **params)
            return [TextContent(type="text", text=json.dumps({"status": "success", "order_id": order_id}))]

        elif name == "cancel_order":
            variety = arguments.get("variety", "regular")
            order_id = kite.cancel_order(variety=variety, order_id=arguments["order_id"])
            return [TextContent(type="text", text=json.dumps({"status": "success", "order_id": order_id}))]

        elif name == "get_gtt_triggers":
            triggers = kite.get_gtts()
            return [TextContent(type="text", text=json.dumps(triggers, indent=2, default=str))]

        elif name == "place_gtt":
            trigger_id = kite.place_gtt(
                trigger_type=kite.GTT_TYPE_SINGLE if arguments["trigger_type"] == "single" else kite.GTT_TYPE_OCO,
                tradingsymbol=arguments["tradingsymbol"],
                exchange=arguments["exchange"],
                trigger_values=arguments["trigger_values"],
                last_price=arguments["last_price"],
                orders=arguments["orders"],
            )
            return [TextContent(type="text", text=json.dumps({"status": "success", "trigger_id": trigger_id}))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
