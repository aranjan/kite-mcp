# kite-mcp

[![PyPI version](https://badge.fury.io/py/kite-mcp.svg)](https://pypi.org/project/kite-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for [Zerodha Kite](https://kite.zerodha.com/) -- trade Indian stocks through natural conversation with any [MCP-compatible](https://modelcontextprotocol.io/) AI assistant.

## Why an MCP server instead of a Python library?

Traditional Kite wrappers require you to write Python code to trade. With kite-mcp, you just talk:

```
You:       "Buy 50 Reliance at market price"
Assistant: checks quote, verifies funds, asks for confirmation, places order

You:       "How's my portfolio doing?"
Assistant: fetches holdings, calculates P&L, summarizes gainers and losers

You:       "Set a stop-loss on my HAL position at 3400"
Assistant: places a GTT trigger for you
```

No code. No scripts. No terminal. Just conversation.

kite-mcp connects any MCP-compatible AI assistant directly to your Zerodha account with 14 trading tools, automated TOTP login, and auto-retry on expired tokens.

## How it works

```
You (natural language) --> AI Assistant --> kite-mcp (MCP server) --> Zerodha Kite API
```

Your AI assistant interprets your intent, maps stock names to symbols (e.g., "Infosys" to NSE:INFY), checks your funds, and executes trades -- all through the MCP protocol. The server handles authentication automatically, including daily token refresh via TOTP.

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
| `get_historical_data` | Historical candle data (minute to daily) |
| `get_instruments` | Search tradeable instruments across NSE, BSE, NFO, MCX |
| `place_order` | Place buy/sell orders (market, limit, stop-loss) |
| `modify_order` | Modify pending orders |
| `cancel_order` | Cancel pending orders |
| `get_gtt_triggers` | View Good Till Triggered orders |
| `place_gtt` | Place GTT single or OCO (stoploss + target) triggers |

**Key capabilities:**
- Fully automated login -- TOTP generated on the fly, no manual intervention
- Auto-retry on stale tokens -- re-authenticates transparently if a token expires mid-session
- Supports delivery (CNC), intraday (MIS), and F&O (NRML) orders
- After-market orders (AMO) supported

## Compatible with

Works with any MCP-compatible client, including:

| Client | Platform |
|--------|----------|
| [Claude Desktop](https://claude.ai/download) | macOS, Windows |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Terminal (macOS, Linux, Windows) |
| [Cursor](https://cursor.sh/) | macOS, Windows, Linux |
| [Windsurf](https://codeium.com/windsurf) | macOS, Windows, Linux |
| [Continue](https://continue.dev/) | VS Code, JetBrains |
| Any MCP-compatible client | See [MCP clients list](https://modelcontextprotocol.io/clients) |

## Quick Start

### 1. Install

```bash
pip install kite-mcp
```

### 2. Get your credentials

You need a [Kite Connect](https://developers.kite.trade/) API app. From your app dashboard, note your **API Key** and **API Secret**.

You also need:
- **User ID** -- your Zerodha client ID (e.g., AB1234)
- **Password** -- your Zerodha login password
- **TOTP Secret** (recommended) -- the base32 seed from setting up an external authenticator app for Zerodha 2FA. This enables fully automated login with no manual steps.

<details>
<summary>How to get your TOTP secret</summary>

1. Log in to **console.zerodha.com**
2. Go to **My Profile** > **Security** > **2FA Settings**
3. Switch to an **external authenticator app** (Google Authenticator, Authy, etc.)
4. When the QR code appears, look for a **"Can't scan? Copy this key"** link
5. That key is your TOTP secret -- save it before completing setup
6. Enter the 6-digit code from your authenticator to finish

</details>

### 3. Configure your MCP client

Add this to your MCP client configuration. The config location depends on your client -- refer to your client's documentation for the exact path.

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

Restart your MCP client. You're ready to trade.

### 4. Try it out

Open a new chat and try:

- "Show my portfolio holdings"
- "What's Tata Motors trading at?"
- "Buy 10 Infosys at market price"
- "How much cash do I have available?"
- "Cancel my last pending order"
- "Show my top gainers and losers"

The AI assistant understands stock names in plain English -- no need to use trading symbols.

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
export KITE_API_KEY=your-api-key
export KITE_API_SECRET=your-api-secret
export KITE_USER_ID=your-user-id
export KITE_PASSWORD=your-password
kite-mcp-login
```

This caches the access token for the rest of the day. The MCP server will use the cached token until it expires.

## Use Cases

- **Daily portfolio monitoring** -- "Give me a summary of my portfolio with top gainers and losers"
- **Quick trades** -- "Buy 50 Reliance" / "Sell all my Yes Bank"
- **Research + action** -- "What's the 52-week high of HDFC Bank? Should I add more at current levels?"
- **Risk management** -- "Set a stop-loss GTT on my BDL position at 1100"
- **Scheduled reports** -- Combine with MCP scheduled tasks to get a daily portfolio summary at 9am
- **Slack integration** -- Pair with Slack MCP to receive portfolio alerts in your Slack channel

## Development

```bash
git clone https://github.com/aranjan/kite-mcp.git
cd kite-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Security

- Credentials are passed via environment variables -- never stored in code
- Access tokens are cached locally at `~/.zerodha_kite_token.json` and expire daily
- The server runs locally on your machine -- no data is sent to third-party servers
- All communication with Zerodha uses HTTPS

## License

MIT
