# kite-mcp

MCP server for [Zerodha Kite](https://kite.zerodha.com/) — trade Indian stocks via Claude and other AI assistants.

## Features

14 tools for complete trading control:

| Tool | Description |
|------|-------------|
| `kite_login` | Auto-authenticate with TOTP |
| `get_holdings` | Portfolio holdings with P&L |
| `get_positions` | Today's intraday/delivery positions |
| `get_orders` | Today's order history |
| `get_margins` | Available funds and margins |
| `get_quote` | Live market quotes |
| `get_ohlc` | Open, high, low, close data |
| `get_historical_data` | Historical candle data |
| `get_instruments` | Search tradeable instruments |
| `place_order` | Place buy/sell orders |
| `modify_order` | Modify pending orders |
| `cancel_order` | Cancel pending orders |
| `get_gtt_triggers` | View GTT triggers |
| `place_gtt` | Place GTT (stoploss/target) orders |

## Quick Start

### 1. Install

```bash
pip install kite-mcp
```

### 2. Get Kite Connect credentials

You need a [Kite Connect](https://developers.kite.trade/) API app. From your app, note:
- **API Key**
- **API Secret**

You also need:
- **User ID** — your Zerodha client ID (e.g., AB1234)
- **Password** — your Zerodha login password
- **TOTP Secret** — the base32 seed from your external authenticator app setup (for fully automated login)

### 3. Configure Claude Desktop

Add this to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "kite": {
      "command": "kite-mcp",
      "env": {
        "KITE_API_KEY": "your-api-key",
        "KITE_API_SECRET": "your-api-secret",
        "KITE_USER_ID": "your-user-id",
        "KITE_PASSWORD": "your-password",
        "KITE_TOTP_SECRET": "your-totp-secret"
      }
    }
  }
}
```

Restart Claude Desktop. You can now ask Claude things like:
- "Show my portfolio holdings"
- "Buy 50 Reliance at market price"
- "What's Infosys trading at?"

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `KITE_API_KEY` | Yes | Kite Connect API key |
| `KITE_API_SECRET` | Yes | Kite Connect API secret |
| `KITE_USER_ID` | Yes | Zerodha client ID |
| `KITE_PASSWORD` | Yes | Zerodha login password |
| `KITE_TOTP_SECRET` | No | TOTP base32 seed for auto-login. Without this, you must run `kite-mcp-login` manually each day. |

## Manual Login

If you don't have a TOTP secret, you can log in manually each day:

```bash
kite-mcp-login
```

This caches the access token for the rest of the day.

## Development

```bash
git clone https://github.com/amitranjan/kite-mcp.git
cd kite-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## License

MIT
