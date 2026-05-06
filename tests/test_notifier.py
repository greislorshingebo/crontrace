"""Tests for crontrace.notifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from crontrace.notifier import (
    _build_payload,
    dispatch,
    notify_stdout,
    notify_webhook,
)

STARTED = "2024-01-15T08:00:00"


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

def test_build_payload_ok():
    p = _build_payload("backup", 0, 1.5, STARTED)
    assert p["job"] == "backup"
    assert p["exit_code"] == 0
    assert p["status"] == "OK"
    assert p["duration_seconds"] == 1.5
    assert p["started_at"] == STARTED


def test_build_payload_fail():
    p = _build_payload("backup", 1, 0.25, STARTED)
    assert p["status"] == "FAIL"
    assert p["exit_code"] == 1


def test_build_payload_duration_rounded():
    p = _build_payload("job", 0, 1.123456789, STARTED)
    assert p["duration_seconds"] == 1.123


# ---------------------------------------------------------------------------
# notify_stdout
# ---------------------------------------------------------------------------

def test_notify_stdout_prints(capsys):
    notify_stdout("myjob", 2, 3.0, STARTED)
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "myjob" in out
    assert "exit=2" in out


def test_notify_stdout_ok_exit(capsys):
    notify_stdout("myjob", 0, 1.0, STARTED)
    out = capsys.readouterr().out
    assert "OK" in out


# ---------------------------------------------------------------------------
# notify_webhook
# ---------------------------------------------------------------------------

def test_notify_webhook_success():
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        result = notify_webhook("http://example.com/hook", "job", 1, 2.0, STARTED)

    assert result is True
    args, _ = mock_open.call_args
    req = args[0]
    body = json.loads(req.data.decode())
    assert body["job"] == "job"
    assert body["exit_code"] == 1


def test_notify_webhook_network_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = notify_webhook("http://bad.host/hook", "job", 1, 1.0, STARTED)
    assert result is False


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

def test_dispatch_suppresses_success_by_default(capsys):
    dispatch("job", 0, 1.0, STARTED)
    out = capsys.readouterr().out
    assert out == ""


def test_dispatch_shows_failure(capsys):
    dispatch("job", 1, 1.0, STARTED)
    out = capsys.readouterr().out
    assert "FAIL" in out


def test_dispatch_calls_webhook_on_failure():
    with patch("crontrace.notifier.notify_webhook") as mock_wh:
        dispatch("job", 1, 1.0, STARTED, webhook_url="http://hook.test/")
    mock_wh.assert_called_once()


def test_dispatch_no_webhook_when_no_url():
    with patch("crontrace.notifier.notify_webhook") as mock_wh:
        dispatch("job", 1, 1.0, STARTED, webhook_url=None)
    mock_wh.assert_not_called()


def test_dispatch_only_on_failure_false_notifies_success(capsys):
    dispatch("job", 0, 1.0, STARTED, only_on_failure=False)
    out = capsys.readouterr().out
    assert "OK" in out
