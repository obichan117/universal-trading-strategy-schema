"""Configuration management for data sources.

Handles API key storage and retrieval with interactive prompts on first use.
Config is stored in ~/.config/pyutss/config.json (or ~/.pyutss/config.json).

Usage:
    from pyutss.data.config import get_api_key, set_api_key, configure

    # Get API key (prompts if not set)
    key = get_api_key("jquants")

    # Set API key programmatically
    set_api_key("jquants", "your-api-key")

    # Interactive configuration
    configure()  # Prompts for all available API keys
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


# Config file location
def _get_config_dir() -> Path:
    """Get the configuration directory path."""
    # Try XDG config dir first (Linux/Mac standard)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "pyutss"

    # Fall back to ~/.config/pyutss or ~/.pyutss
    home = Path.home()
    config_dir = home / ".config" / "pyutss"
    if config_dir.parent.exists():
        return config_dir
    return home / ".pyutss"


def _get_config_path() -> Path:
    """Get the configuration file path."""
    return _get_config_dir() / "config.json"


def _load_config() -> dict[str, Any]:
    """Load configuration from file."""
    config_path = _get_config_path()
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    # Set restrictive permissions (owner read/write only)
    os.chmod(config_path, 0o600)


# API key management
API_KEY_ENV_VARS = {
    "jquants": "JQUANTS_API_KEY",
}

API_KEY_DESCRIPTIONS = {
    "jquants": {
        "name": "J-Quants",
        "description": "Required for Japanese stock data via J-Quants",
        "signup_url": "https://jpx-jquants.com/",
        "instructions": "Sign up at J-Quants, go to Dashboard, and copy your API key.",
    },
}


def get_api_key(source: str, prompt_if_missing: bool = True) -> str | None:
    """Get API key for a data source.

    Checks in order:
    1. Environment variable
    2. Config file
    3. Interactive prompt (if prompt_if_missing=True and running in terminal)

    Args:
        source: Data source name (e.g., "jquants")
        prompt_if_missing: Whether to prompt user if key not found

    Returns:
        API key string or None if not available
    """
    # Check environment variable first
    env_var = API_KEY_ENV_VARS.get(source)
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value

    # Check config file
    config = _load_config()
    api_keys = config.get("api_keys", {})
    if source in api_keys:
        return api_keys[source]

    # Prompt if allowed and running interactively
    if prompt_if_missing and _is_interactive():
        return _prompt_for_api_key(source)

    return None


def set_api_key(source: str, api_key: str) -> None:
    """Set API key for a data source.

    Args:
        source: Data source name
        api_key: API key value
    """
    config = _load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][source] = api_key
    _save_config(config)

    # Also set environment variable for current session
    env_var = API_KEY_ENV_VARS.get(source)
    if env_var:
        os.environ[env_var] = api_key


def remove_api_key(source: str) -> None:
    """Remove API key for a data source.

    Args:
        source: Data source name
    """
    config = _load_config()
    api_keys = config.get("api_keys", {})
    if source in api_keys:
        del api_keys[source]
        config["api_keys"] = api_keys
        _save_config(config)


def _is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_for_api_key(source: str) -> str | None:
    """Prompt user for API key interactively.

    Args:
        source: Data source name

    Returns:
        API key if provided, None if skipped
    """
    info = API_KEY_DESCRIPTIONS.get(source, {})
    name = info.get("name", source)
    description = info.get("description", "")
    signup_url = info.get("signup_url", "")
    instructions = info.get("instructions", "")

    print()
    print("=" * 60)
    print(f"  {name} API Key Required")
    print("=" * 60)
    if description:
        print(f"\n{description}")
    if signup_url:
        print(f"\nSign up: {signup_url}")
    if instructions:
        print(f"\n{instructions}")
    print()

    try:
        api_key = input("Enter your API key (or press Enter to skip): ").strip()
        if api_key:
            save = input("Save this key for future use? [Y/n]: ").strip().lower()
            if save != "n":
                set_api_key(source, api_key)
                config_path = _get_config_path()
                print(f"API key saved to {config_path}")
            else:
                # Set for current session only
                env_var = API_KEY_ENV_VARS.get(source)
                if env_var:
                    os.environ[env_var] = api_key
            return api_key
        else:
            print(f"Skipped. You can set it later with: pyutss.data.config.set_api_key('{source}', 'your-key')")
            return None
    except (EOFError, KeyboardInterrupt):
        print("\nSkipped.")
        return None


def configure(sources: list[str] | None = None) -> None:
    """Interactive configuration for API keys.

    Prompts for API keys for all specified sources (or all available if None).

    Args:
        sources: List of source names to configure, or None for all
    """
    if sources is None:
        sources = list(API_KEY_DESCRIPTIONS.keys())

    print()
    print("=" * 60)
    print("  pyutss Data Source Configuration")
    print("=" * 60)
    print()

    for source in sources:
        current_key = get_api_key(source, prompt_if_missing=False)
        info = API_KEY_DESCRIPTIONS.get(source, {})
        name = info.get("name", source)

        if current_key:
            masked = current_key[:4] + "..." + current_key[-4:] if len(current_key) > 8 else "***"
            print(f"{name}: configured ({masked})")
            update = input("  Update this key? [y/N]: ").strip().lower()
            if update == "y":
                _prompt_for_api_key(source)
        else:
            print(f"{name}: not configured")
            _prompt_for_api_key(source)
        print()

    print("Configuration complete!")
    print(f"Config file: {_get_config_path()}")


def show_config() -> None:
    """Display current configuration status."""
    print()
    print("pyutss Configuration")
    print("=" * 40)
    print(f"Config file: {_get_config_path()}")
    print()

    for source, info in API_KEY_DESCRIPTIONS.items():
        name = info.get("name", source)
        key = get_api_key(source, prompt_if_missing=False)
        if key:
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
            status = f"configured ({masked})"
        else:
            status = "not configured"
        print(f"  {name}: {status}")
    print()
