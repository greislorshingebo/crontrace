"""Configuration loader for crontrace.

Reads an optional INI-style config file (default: ~/.crontrace.ini or
the path given by the CRONTRACE_CONFIG env var) and exposes typed helpers
used by the CLI and notifier.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Optional

_DEFAULT_CONFIG_PATH = Path.home() / ".crontrace.ini"
_ENV_VAR = "CRONTRACE_CONFIG"

_DEFAULTS: dict[str, dict[str, str]] = {
    "crontrace": {
        "db_path": str(Path.home() / ".crontrace.db"),
        "retain_days": "90",
        "only_on_failure": "true",
    },
    "notifications": {
        "webhook_url": "",
    },
}


def _config_path() -> Path:
    """Return the config file path, honouring the env-var override."""
    env = os.environ.get(_ENV_VAR, "")
    return Path(env) if env else _DEFAULT_CONFIG_PATH


def load(path: Optional[Path] = None) -> configparser.ConfigParser:
    """Load and return a ConfigParser with built-in defaults applied."""
    cfg = configparser.ConfigParser()
    # Seed defaults so missing keys never raise.
    for section, values in _DEFAULTS.items():
        cfg[section] = values

    target = path or _config_path()
    if target.exists():
        cfg.read(target)
    return cfg


def get_db_path(cfg: configparser.ConfigParser) -> str:
    return cfg.get("crontrace", "db_path")


def get_retain_days(cfg: configparser.ConfigParser) -> int:
    return cfg.getint("crontrace", "retain_days")


def get_only_on_failure(cfg: configparser.ConfigParser) -> bool:
    return cfg.getboolean("crontrace", "only_on_failure")


def get_webhook_url(cfg: configparser.ConfigParser) -> Optional[str]:
    url = cfg.get("notifications", "webhook_url", fallback="").strip()
    return url if url else None
