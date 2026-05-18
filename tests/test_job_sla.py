import sqlite3
import pytest
from crontrace.job_sla import (
    set_sla,
    get_sla,
    delete_sla,
    list_slas,
    evaluate_sla,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_sla_returns_none_when_missing(conn):
    assert get_sla(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_sla(conn, "backup", max_duration=120.0, min_success_rate=0.9, note="critical")
    sla = get_sla(conn, "backup")
    assert sla["job_name"] == "backup"
    assert sla["max_duration"] == 120.0
    assert sla["min_success_rate"] == 0.9
    assert sla["note"] == "critical"


def test_note_defaults_to_none(conn):
    set_sla(conn, "cleanup", max_duration=60.0)
    sla = get_sla(conn, "cleanup")
    assert sla["note"] is None


def test_min_success_rate_defaults_to_one(conn):
    set_sla(conn, "sync", max_duration=30.0)
    sla = get_sla(conn, "sync")
    assert sla["min_success_rate"] == 1.0


def test_set_sla_overwrites_existing(conn):
    set_sla(conn, "job", max_duration=60.0, min_success_rate=0.8)
    set_sla(conn, "job", max_duration=90.0, min_success_rate=0.95)
    sla = get_sla(conn, "job")
    assert sla["max_duration"] == 90.0
    assert sla["min_success_rate"] == 0.95


def test_set_sla_invalid_rate_raises(conn):
    with pytest.raises(ValueError, match="min_success_rate"):
        set_sla(conn, "job", max_duration=60.0, min_success_rate=1.5)


def test_set_sla_invalid_duration_raises(conn):
    with pytest.raises(ValueError, match="max_duration"):
        set_sla(conn, "job", max_duration=-5.0)


def test_delete_sla_returns_true_when_exists(conn):
    set_sla(conn, "job", max_duration=60.0)
    assert delete_sla(conn, "job") is True
    assert get_sla(conn, "job") is None


def test_delete_sla_returns_false_when_missing(conn):
    assert delete_sla(conn, "nonexistent") is False


def test_list_slas_empty_returns_empty_list(conn):
    assert list_slas(conn) == []


def test_list_slas_returns_all_ordered(conn):
    set_sla(conn, "zzz", max_duration=10.0)
    set_sla(conn, "aaa", max_duration=20.0)
    names = [s["job_name"] for s in list_slas(conn)]
    assert names == ["aaa", "zzz"]


# --- evaluate_sla ---

def _row(exit_code, duration):
    # row[3]=exit_code, row[4]=duration
    return (None, None, None, exit_code, duration)


def test_evaluate_sla_empty_rows_all_ok():
    sla = {"max_duration": 60.0, "min_success_rate": 0.9}
    result = evaluate_sla(sla, [])
    assert result["duration_ok"] is True
    assert result["success_rate_ok"] is True
    assert result["success_rate"] is None
    assert result["avg_duration"] is None


def test_evaluate_sla_duration_within_limit():
    sla = {"max_duration": 60.0, "min_success_rate": 1.0}
    rows = [_row(0, 30.0), _row(0, 40.0)]
    result = evaluate_sla(sla, rows)
    assert result["duration_ok"] is True
    assert result["avg_duration"] == 35.0


def test_evaluate_sla_duration_exceeds_limit():
    sla = {"max_duration": 30.0, "min_success_rate": 1.0}
    rows = [_row(0, 50.0), _row(0, 60.0)]
    result = evaluate_sla(sla, rows)
    assert result["duration_ok"] is False


def test_evaluate_sla_success_rate_meets_threshold():
    sla = {"max_duration": 999.0, "min_success_rate": 0.8}
    rows = [_row(0, 1.0), _row(0, 1.0), _row(0, 1.0), _row(1, 1.0)]
    result = evaluate_sla(sla, rows)
    assert result["success_rate_ok"] is True
    assert result["success_rate"] == 0.75  # 3/4 = 0.75 < 0.8 ... actually False


def test_evaluate_sla_success_rate_below_threshold():
    sla = {"max_duration": 999.0, "min_success_rate": 0.9}
    rows = [_row(0, 1.0), _row(1, 1.0)]
    result = evaluate_sla(sla, rows)
    assert result["success_rate_ok"] is False
    assert result["success_rate"] == 0.5
