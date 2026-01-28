"""Tests for data source configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pyutss.data.config import (
    _get_config_dir,
    _get_config_path,
    _load_config,
    _save_config,
    get_api_key,
    set_api_key,
    remove_api_key,
    API_KEY_ENV_VARS,
    API_KEY_DESCRIPTIONS,
)


class TestConfigPaths:
    """Tests for configuration path functions."""

    def test_get_config_dir_returns_path(self):
        """Config dir should return a Path object."""
        config_dir = _get_config_dir()
        assert isinstance(config_dir, Path)

    def test_get_config_path_returns_json(self):
        """Config path should be a .json file."""
        config_path = _get_config_path()
        assert config_path.suffix == ".json"
        assert config_path.name == "config.json"


class TestConfigFile:
    """Tests for config file operations."""

    def test_load_empty_config(self):
        """Loading non-existent config should return empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "nonexistent" / "config.json"
                config = _load_config()
                assert config == {}

    def test_save_and_load_config(self):
        """Config should be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                # Save config
                test_config = {"api_keys": {"test": "secret123"}}
                _save_config(test_config)

                # Verify file exists
                assert config_path.exists()

                # Load and verify
                loaded = _load_config()
                assert loaded == test_config


class TestApiKeyManagement:
    """Tests for API key management."""

    def test_api_key_env_vars_defined(self):
        """API key environment variables should be defined."""
        assert "jquants" in API_KEY_ENV_VARS
        assert API_KEY_ENV_VARS["jquants"] == "JQUANTS_API_KEY"

    def test_api_key_descriptions_defined(self):
        """API key descriptions should be defined."""
        assert "jquants" in API_KEY_DESCRIPTIONS
        assert "name" in API_KEY_DESCRIPTIONS["jquants"]
        assert "signup_url" in API_KEY_DESCRIPTIONS["jquants"]

    def test_get_api_key_from_env(self):
        """API key should be retrieved from environment variable."""
        with patch.dict(os.environ, {"JQUANTS_API_KEY": "test-key-123"}):
            key = get_api_key("jquants", prompt_if_missing=False)
            assert key == "test-key-123"

    def test_get_api_key_from_config(self):
        """API key should be retrieved from config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                # Clear env var
                with patch.dict(os.environ, {}, clear=True):
                    # Set key via config
                    set_api_key("jquants", "config-key-456")

                    # Retrieve it
                    key = get_api_key("jquants", prompt_if_missing=False)
                    assert key == "config-key-456"

    def test_get_api_key_env_takes_precedence(self):
        """Environment variable should take precedence over config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                # Set in config
                set_api_key("jquants", "config-key")

                # Set in env
                with patch.dict(os.environ, {"JQUANTS_API_KEY": "env-key"}):
                    key = get_api_key("jquants", prompt_if_missing=False)
                    assert key == "env-key"

    def test_get_api_key_returns_none_when_missing(self):
        """API key should return None when not set and not prompting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path
                with patch.dict(os.environ, {}, clear=True):
                    key = get_api_key("jquants", prompt_if_missing=False)
                    assert key is None

    def test_set_api_key_creates_config(self):
        """Setting API key should create config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                set_api_key("jquants", "new-key")

                assert config_path.exists()
                config = _load_config()
                assert config["api_keys"]["jquants"] == "new-key"

    def test_remove_api_key(self):
        """Removing API key should delete it from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                # Set then remove
                set_api_key("jquants", "to-remove")
                remove_api_key("jquants")

                config = _load_config()
                assert "jquants" not in config.get("api_keys", {})


class TestConfigSecurity:
    """Tests for configuration security."""

    def test_config_file_permissions(self):
        """Config file should have restrictive permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch("pyutss.data.config._get_config_path") as mock_path:
                mock_path.return_value = config_path

                _save_config({"test": "data"})

                # Check permissions (owner read/write only)
                mode = config_path.stat().st_mode & 0o777
                assert mode == 0o600
