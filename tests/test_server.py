"""Tests for the server module."""

import json
from unittest import mock

from kite_mcp.server import mcp, place_order


class TestToolRegistration:
    """Verify all 14 tools are registered."""

    EXPECTED_TOOLS = [
        "kite_login",
        "get_holdings",
        "get_positions",
        "get_orders",
        "get_margins",
        "get_quote",
        "get_ohlc",
        "get_historical_data",
        "get_instruments",
        "place_order",
        "modify_order",
        "cancel_order",
        "get_gtt_triggers",
        "place_gtt",
    ]

    def test_all_tools_registered(self):
        tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
        for expected in self.EXPECTED_TOOLS:
            assert expected in tool_names, f"Tool '{expected}' not registered"

    def test_tool_count(self):
        tools = mcp._tool_manager.list_tools()
        assert len(tools) == 14

    def test_tools_have_descriptions(self):
        for tool in mcp._tool_manager.list_tools():
            assert tool.description, f"Tool '{tool.name}' has no description"


class TestOrderValidation:
    """Test input validation for place_order."""

    def test_rejects_zero_quantity(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=0, order_type="MARKET", product="CNC",
        ))
        assert result["status"] == "error"
        assert "Quantity" in result["message"]

    def test_rejects_negative_quantity(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=-10, order_type="MARKET", product="CNC",
        ))
        assert result["status"] == "error"

    def test_rejects_invalid_transaction_type(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="HOLD",
            quantity=10, order_type="MARKET", product="CNC",
        ))
        assert result["status"] == "error"
        assert "transaction_type" in result["message"]

    def test_rejects_invalid_product(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="MARKET", product="INVALID",
        ))
        assert result["status"] == "error"
        assert "product" in result["message"]

    def test_rejects_invalid_order_type(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="FOK", product="CNC",
        ))
        assert result["status"] == "error"
        assert "order_type" in result["message"]

    def test_rejects_limit_without_price(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="LIMIT", product="CNC",
        ))
        assert result["status"] == "error"
        assert "price" in result["message"]

    def test_rejects_sl_without_trigger_price(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="SL", product="CNC", price=1400.0,
        ))
        assert result["status"] == "error"
        assert "trigger_price" in result["message"]

    def test_rejects_negative_price(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="MARKET", product="CNC", price=-100.0,
        ))
        assert result["status"] == "error"
        assert "negative" in result["message"].lower()

    def test_rejects_invalid_variety(self):
        result = json.loads(place_order(
            tradingsymbol="RELIANCE", exchange="NSE", transaction_type="BUY",
            quantity=10, order_type="MARKET", product="CNC", variety="invalid",
        ))
        assert result["status"] == "error"
        assert "variety" in result["message"]


class TestQuoteFallback:
    def test_fallback_returns_valid_json(self):
        """Verify _quote_fallback returns parseable JSON."""
        from kite_mcp.server import _quote_fallback
        from unittest import mock

        mock_kite = mock.MagicMock()
        mock_kite.holdings.return_value = [
            {"tradingsymbol": "RELIANCE", "last_price": 1400, "average_price": 1200, "quantity": 10}
        ]
        mock_kite.positions.return_value = {"net": []}

        result = _quote_fallback(mock_kite, ["NSE:RELIANCE"])
        parsed = json.loads(result)
        assert "NSE:RELIANCE" in parsed
        assert parsed["NSE:RELIANCE"]["last_price"] == 1400

    def test_fallback_handles_unknown_stock(self):
        """Verify fallback returns error for stocks not in holdings."""
        from kite_mcp.server import _quote_fallback
        from unittest import mock

        mock_kite = mock.MagicMock()
        mock_kite.holdings.return_value = []
        mock_kite.positions.return_value = {"net": []}

        result = _quote_fallback(mock_kite, ["NSE:UNKNOWN"])
        parsed = json.loads(result)
        assert "error" in parsed["NSE:UNKNOWN"]
