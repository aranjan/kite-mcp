"""Tests for the CLI module."""

import os
from unittest import mock

import pytest

from kite_mcp.cli import login, status


class TestLogin:
    """Tests for the login CLI command."""

    def test_exits_without_totp_secret(self):
        env = {
            "KITE_API_KEY": "key",
            "KITE_API_SECRET": "secret",
            "KITE_USER_ID": "AB1234",
            "KITE_PASSWORD": "pass",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                login()


class TestStatus:
    """Tests for the status CLI command."""

    def test_exits_when_no_token(self, tmp_path):
        token_file = tmp_path / "nonexistent.json"
        with mock.patch("kite_mcp.auth.TOKEN_FILE", token_file):
            with pytest.raises(SystemExit):
                status()
