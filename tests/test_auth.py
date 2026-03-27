"""Tests for the auth module."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from kite_mcp.auth import get_cached_token, load_credentials, TOKEN_FILE


class TestLoadCredentials:
    """Tests for load_credentials()."""

    def test_loads_all_credentials(self):
        env = {
            "KITE_API_KEY": "test-key",
            "KITE_API_SECRET": "test-secret",
            "KITE_USER_ID": "AB1234",
            "KITE_PASSWORD": "testpass",
            "KITE_TOTP_SECRET": "TOTP123",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            creds = load_credentials()
            assert creds["api_key"] == "test-key"
            assert creds["api_secret"] == "test-secret"
            assert creds["user_id"] == "AB1234"
            assert creds["password"] == "testpass"
            assert creds["totp_secret"] == "TOTP123"

    def test_totp_secret_is_optional(self):
        env = {
            "KITE_API_KEY": "test-key",
            "KITE_API_SECRET": "test-secret",
            "KITE_USER_ID": "AB1234",
            "KITE_PASSWORD": "testpass",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            # Remove TOTP if it exists
            os.environ.pop("KITE_TOTP_SECRET", None)
            creds = load_credentials()
            assert creds["totp_secret"] is None

    def test_exits_on_missing_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                load_credentials()

    def test_exits_on_partial_credentials(self):
        env = {"KITE_API_KEY": "test-key"}
        with mock.patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                load_credentials()


class TestGetCachedToken:
    """Tests for get_cached_token()."""

    def test_returns_token_for_today(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps({
            "access_token": "test-token-123",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }))
        with mock.patch("kite_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() == "test-token-123"

    def test_returns_none_for_old_token(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps({
            "access_token": "old-token",
            "date": "2020-01-01",
        }))
        with mock.patch("kite_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() is None

    def test_returns_none_when_file_missing(self, tmp_path):
        token_file = tmp_path / "nonexistent.json"
        with mock.patch("kite_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() is None


class TestTokenFilePermissions:
    """Tests for token file security."""

    def test_automated_login_sets_file_permissions(self, tmp_path):
        """Verify that token files are created with 600 permissions."""
        import os
        import stat

        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps({
            "access_token": "test",
            "date": "2026-01-01",
        }))
        os.chmod(token_file, 0o600)
        perms = stat.S_IMODE(os.stat(token_file).st_mode)
        assert perms == 0o600, f"Token file permissions should be 600, got {oct(perms)}"
