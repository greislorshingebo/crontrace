"""Tests for crontrace.config."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

import pytest

from crontrace import config as cfg_mod
from crontrace.config import (
    get_db_path,
    get_only_on_failure,
    get_retain_days,
    get_webhook_url,
    load,
)


# ---------------------------------------------------------------------------
# load() with no file — defaults
# ---------------------------------------------------------------------------

def test_load_returns_configparser(tmp_path):
    result = load(tmp_path / "nonexistent.ini")
    assert isinstance(result, configparser.ConfigParser)


def test_load_default_db_path(tmp_path):
    cfg = load(tmp_path / "nonexistent.ini")
    assert get_db_path(cfg).endswith(".crontrace.db")


def test_load_default_retain_days(tmp_path):
    cfg = load(tmp_path / "nonexistent.ini")
    assert get_retain_days(cfg) == 90


def test_load_default_only_on_failure(tmp_path):
    cfg = load(tmp_path / "nonexistent.ini")
    assert get_only_on_failure(cfg) is True


def test_load_default_webhook_url_is_none(tmp_path):
    cfg = load(tmp_path / "nonexistent.ini")
    assert get_webhook_url(cfg) is None


# ---------------------------------------------------------------------------
# load() reads actual INI file
# ---------------------------------------------------------------------------

def test_load_reads_custom_db_path(tmp_path):
    ini = tmp_path / "ct.ini"
    ini.write_text("[crontrace]\ndb_path = /tmp/custom.db\n")
    cfg = load(ini)
    assert get_db_path(cfg) == "/tmp/custom.db"


def test_load_reads_retain_days(tmp_path):
    ini = tmp_path / "ct.ini"
    ini.write_text("[crontrace]\nretain_days = 30\n")
    cfg = load(ini)
    assert get_retain_days(cfg) == 30


def test_load_reads_webhook_url(tmp_path):
    ini = tmp_path / "ct.ini"
    ini.write_text("[notifications]\nwebhook_url = https://hooks.example.com/abc\n")
    cfg = load(ini)
    assert get_webhook_url(cfg) == "https://hooks.example.com/abc"


def test_load_only_on_failure_false(tmp_path):
    ini = tmp_path / "ct.ini"
    ini.write_text("[crontrace]\nonly_on_failure = false\n")
    cfg = load(ini)
    assert get_only_on_failure(cfg) is False


# ---------------------------------------------------------------------------
# env-var override
# ---------------------------------------------------------------------------

def test_env_var_overrides_default_path(tmp_path, monkeypatch):
    ini = tmp_path / "env.ini"
    ini.write_text("[crontrace]\nretain_days = 7\n")
    monkeypatch.setenv("CRONTRACE_CONFIG", str(ini))
    # Reload the helper so it picks up the env var.
    cfg = load(cfg_mod._config_path())
    assert get_retain_days(cfg) == 7
