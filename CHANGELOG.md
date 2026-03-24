# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2026-03-24

### Added
- Quote fallback for personal Kite Connect apps -- get_quote and get_ohlc now fall back to holdings/positions data when the market data API is unavailable
- CONTRIBUTING.md with development setup and new tool guide
- GitHub Actions CI across Python 3.10-3.13
- Smithery config (smithery.yaml) for directory listing
- 12 tests covering auth, server tool registration, and CLI
- Logo

### Changed
- Centered README header with logo and badges
- Compatible with section listing MCP clients

## [0.1.1] - 2026-03-24

### Changed
- Removed vendor-specific references from all docs and code
- Fixed GitHub repository URLs
- Improved README with positioning, conversation examples, TOTP setup guide, use cases, and security section
- Added PyPI and MIT license badges

## [0.1.0] - 2026-03-24

### Added
- Initial release
- 14 MCP tools: kite_login, get_holdings, get_positions, get_orders, get_margins, get_quote, get_ohlc, get_historical_data, get_instruments, place_order, modify_order, cancel_order, get_gtt_triggers, place_gtt
- Fully automated TOTP login with daily token caching
- Auto-retry on stale/invalidated tokens
- CLI entry points: `kite-mcp` (server) and `kite-mcp-login` (standalone auth)
- Support for delivery (CNC), intraday (MIS), and F&O (NRML) orders
- After-market order (AMO) support
- GTT single and OCO (two-leg) trigger support
