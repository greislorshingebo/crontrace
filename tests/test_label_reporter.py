"""Tests for crontrace.label_reporter."""

from crontrace.label_reporter import render_label_row, render_label_table


def test_render_label_row_contains_key(dummy=None):
    row = render_label_row("env", "prod")
    assert "env" in row


def test_render_label_row_contains_value():
    row = render_label_row("team", "infra")
    assert "infra" in row


def test_render_label_row_truncates_long_key():
    long_key = "a" * 40
    row = render_label_row(long_key, "val")
    assert "…" in row


def test_render_label_row_truncates_long_value():
    long_val = "v" * 50
    row = render_label_row("key", long_val)
    assert "…" in row


def test_render_label_table_contains_job_name():
    table = render_label_table("backup-db", {"env": "prod"})
    assert "backup-db" in table


def test_render_label_table_contains_key_and_value():
    table = render_label_table("backup-db", {"env": "prod", "team": "infra"})
    assert "env" in table
    assert "prod" in table
    assert "team" in table
    assert "infra" in table


def test_render_label_table_empty_labels_shows_placeholder():
    table = render_label_table("myjob", {})
    assert "no labels" in table


def test_render_label_table_non_empty_shows_header():
    table = render_label_table("myjob", {"k": "v"})
    assert "KEY" in table
    assert "VALUE" in table


def test_render_label_table_sorted_keys():
    table = render_label_table("myjob", {"zzz": "last", "aaa": "first"})
    idx_aaa = table.index("aaa")
    idx_zzz = table.index("zzz")
    assert idx_aaa < idx_zzz
