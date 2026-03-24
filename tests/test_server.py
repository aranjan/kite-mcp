"""Tests for the server module."""

from kite_mcp.server import mcp


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
