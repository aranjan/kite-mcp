# Contributing to kite-mcp

Thanks for your interest in contributing! Here's how to get started.

## Development setup

```bash
git clone https://github.com/aranjan/kite-mcp.git
cd kite-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Making changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Test locally -- make sure `kite-mcp` starts and `kite-mcp-login` works
4. Commit with a clear message describing what changed and why
5. Open a pull request

## What to work on

- Check [open issues](https://github.com/aranjan/kite-mcp/issues) for bugs and feature requests
- New tools (e.g., option chain data, mutual funds, basket orders)
- Better error messages and edge case handling
- Documentation improvements
- Tests

## Code style

- Keep it simple -- avoid unnecessary abstractions
- Use type hints for function parameters and return types
- Follow existing patterns in the codebase

## Adding a new tool

1. Add your tool function in `src/kite_mcp/server.py` with the `@mcp.tool()` decorator
2. Use type hints -- FastMCP generates the schema from them automatically
3. Return a JSON string
4. Use `_kite()` to get an authenticated KiteConnect instance
5. Update the tools table in `README.md`
6. Add the change to `CHANGELOG.md`

Example:

```python
@mcp.tool()
def get_trades(order_id: str) -> str:
    """Get trades for a specific order."""
    kite = _kite()
    return json.dumps(kite.trades(order_id), indent=2, default=str)
```

## Reporting bugs

Use the [bug report template](https://github.com/aranjan/kite-mcp/issues/new?template=bug_report.md). Include your Python version, kite-mcp version, and any error output.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
