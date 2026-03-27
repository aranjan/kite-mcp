# CLAUDE.md - Project Context for kite-mcp

## Project Overview

kite-mcp is an MCP (Model Context Protocol) server for Zerodha Kite Connect that enables trading Indian stocks through natural conversation with any MCP-compatible AI assistant.

- **Author:** Amit Ranjan (aranjan)
- **Repository:** https://github.com/aranjan/kite-mcp
- **PyPI:** https://pypi.org/project/kite-mcp/
- **Smithery:** https://smithery.ai/server/@aranjan/kite-mcp
- **License:** MIT

## Architecture

```
User (natural language) -> AI Assistant -> kite-mcp (MCP/stdio) -> Zerodha Kite API
```

- Built with **FastMCP** (from the `mcp` Python package)
- Runs as a **stdio** server (local, not hosted)
- Auto-authenticates using TOTP via `pyotp`
- Token cached at `~/.zerodha_kite_token.json` (expires daily)

## Broader System Context

kite-mcp is part of a multi-broker trading system:

```
Claude Desktop
  ├── kite-mcp          → Zerodha portfolio + orders (auto TOTP)
  ├── zerodha-official   → Free quotes for any NSE stock (browser OAuth)
  ├── icici-mcp         → ICICI Direct portfolio + orders (Playwright TOTP)
  ├── finance MCP       → Technical analysis (RSI, MACD, Bollinger, MA)
  └── Slack MCP         → Post to #kite-portfolio
```

**Related projects:**
- `~/icici-mcp/` — ICICI Direct MCP server (separate repo)
- `~/finance-mcp-wrapper.py` — Async wrapper for finance-mcp-server
- `~/trading-agent-prompt.md` — Scheduled task prompts for daily/EOD/weekly reports
- `~/test_claude_config.py` — Validates Claude Desktop config
- `~/improvements-26-march.md` — Planned improvements backlog

## Project Structure

```
~/kite-mcp/
  src/kite_mcp/
    __init__.py       # Version string
    auth.py           # Shared auth: load_credentials, automated_login, get_authenticated_kite
    server.py         # FastMCP server with 14 @mcp.tool() decorated tools
    cli.py            # CLI entry points: login(), status()
  tests/
    test_auth.py      # 7 tests for auth module
    test_server.py    # 3 tests for tool registration
    test_cli.py       # 2 tests for CLI
  pyproject.toml      # Hatchling build, entry points: kite-mcp, kite-mcp-login
  smithery.yaml       # Smithery directory config
  CHANGELOG.md
  CONTRIBUTING.md
  SECURITY.md
  LICENSE             # MIT
  README.md
  logo.svg
  promotion-activities.md  # Marketing plan with draft posts
  .github/
    workflows/ci.yml  # CI: ruff lint, syntax, imports, tests across Python 3.10-3.13
    ISSUE_TEMPLATE/   # Bug report + feature request templates
    pull_request_template.md
```

## Key Files

- **src/kite_mcp/auth.py** -- all authentication logic. `get_authenticated_kite()` tries cached token first, then auto-login if TOTP available. `automated_login()` POSTs to Kite login/twofa endpoints, generates TOTP with pyotp, follows redirects to get request_token, exchanges for access_token.
- **src/kite_mcp/server.py** -- all 14 tools. `_kite()` helper validates token with `kite.profile()` and auto-retries on `TokenException`. Tools use `Annotated` type hints for parameter descriptions and `ToolAnnotations` for read-only/write/destructive hints.
- **src/kite_mcp/cli.py** -- `login()` and `status()` for standalone CLI use.

## 14 MCP Tools

| Tool | Annotation | Description |
|------|-----------|-------------|
| kite_login | WRITE | Auto-authenticate with TOTP |
| get_holdings | READ_ONLY | Portfolio holdings with P&L |
| get_positions | READ_ONLY | Day and net positions |
| get_orders | READ_ONLY | Today's orders |
| get_margins | READ_ONLY | Available funds (may 504 at market open) |
| get_quote | READ_ONLY | Live quotes (falls back to holdings data on personal apps) |
| get_ohlc | READ_ONLY | OHLC data (falls back to holdings data on personal apps) |
| get_historical_data | READ_ONLY | Historical candles |
| get_instruments | READ_ONLY | Search tradeable instruments |
| place_order | WRITE | Place buy/sell orders |
| modify_order | WRITE | Modify pending orders |
| cancel_order | DESTRUCTIVE | Cancel pending orders |
| get_gtt_triggers | READ_ONLY | View GTT triggers |
| place_gtt | WRITE | Place GTT orders |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| KITE_API_KEY | Yes | Kite Connect API key |
| KITE_API_SECRET | Yes | Kite Connect API secret |
| KITE_USER_ID | Yes | Zerodha client ID |
| KITE_PASSWORD | Yes | Zerodha login password |
| KITE_TOTP_SECRET | No | Base32 TOTP seed for auto-login |

## Local Setup

- **Project:** ~/kite-mcp/
- **Venv:** ~/kite-mcp/venv/ (Python 3.14)
- **Installed editable:** `pip install -e .`
- **Entry points:** ~/kite-mcp/venv/bin/kite-mcp, ~/kite-mcp/venv/bin/kite-mcp-login
- **Claude Desktop config:** ~/Library/Application Support/Claude/claude_desktop_config.json
  - Command: /Users/arn/kite-mcp/venv/bin/kite-mcp
  - Env vars configured with credentials
- **Log file:** ~/.kite-mcp.log
- **Audit log:** ~/.trading-audit.log

## Credentials Storage

- Kite credentials: environment variables in ~/.bashrc and Claude Desktop config
- Kite access token: ~/.zerodha_kite_token.json (auto-refreshed daily)
- PyPI recovery codes: ~/.config/pypi/recovery_codes.txt (chmod 600)

## Pre-push Checklist

Always run before pushing:
```bash
cd ~/kite-mcp
./venv/bin/ruff check src/          # Lint
./venv/bin/pytest tests/ -v         # Tests
python3 ~/test_claude_config.py     # Config validation (if config changed)
```

## Build and Publish

```bash
# Build
cd ~/kite-mcp && rm -rf dist/ && ./venv/bin/python -m build

# Publish to PyPI
./venv/bin/twine upload dist/* -u __token__ -p <PYPI_API_TOKEN>

# Remember to:
# 1. Bump version in pyproject.toml and src/kite_mcp/__init__.py
# 2. Update CHANGELOG.md
# 3. Run ruff + pytest before committing
# 4. git commit and push
# 5. Create GitHub release: gh release create vX.Y.Z
```

## Testing

```bash
cd ~/kite-mcp && ./venv/bin/pytest tests/ -v
```

25 tests covering auth, server tool registration, order validation, quote fallback, and CLI.

## Known Limitations

- **Personal Kite Connect apps** don't have market data API access. get_quote and get_ohlc fall back to holdings/positions data for stocks you own. The zerodha-official MCP (mcp.kite.trade) provides free quotes for any stock as an alternative.
- **Kite access tokens expire daily.** With KITE_TOTP_SECRET set, the server auto-refreshes. Without it, run `kite-mcp-login` manually each morning.
- **get_margins may 504 at market open** (9:15 AM IST) due to API congestion. Scheduled tasks should run at 9:20 AM to avoid this.
- **Smithery quality score (35/100)** -- Smithery can't discover tools because the server needs real credentials to start. Expected for credential-dependent servers.
- **Logging to ~/.kite-mcp.log** (rotating, 5MB, 3 backups)
- **Trade audit log at ~/.trading-audit.log** (JSON lines, chmod 600)

## Known Issues with Scheduled Tasks

- **Slack channel search intermittent** -- #kite-portfolio sometimes not found. Hardcode channel name in prompts instead of searching.
- **get_margins 504 at market open** -- schedule tasks at 9:20 AM, not 9:15 AM
- **Co-work tasks need tool permissions** -- first run of each task requires manual approval. Add all tools to "Always Allowed".

## Distribution Status

| Platform | Status |
|----------|--------|
| PyPI | Live (v0.1.6) |
| GitHub | Public, github.com/aranjan/kite-mcp |
| Smithery | Listed |
| awesome-mcp-servers | PR #3891 |
| Official MCP servers | PR #3704 |
| Glama | Submitted for review |
| Product Hunt | Posted |

## Scheduled Tasks (Co-work)

Three scheduled tasks use this MCP along with icici-mcp and finance MCP:
1. **Daily trading agent** -- Weekdays 9:20 AM IST -- full portfolio report
2. **EOD trading review** -- Weekdays 3:35 PM IST -- market close review
3. **Weekly portfolio digest** -- Fridays 4:00 PM IST -- week in review

Prompts saved at: `~/trading-agent-prompt.md`

## Roadmap

- Option chain data for F&O traders
- Basket orders
- Mutual fund tools
- Watchlist management
- Portfolio analytics / diversification tool
- Webhook/streaming for real-time alerts
- Multiple Zerodha account support
