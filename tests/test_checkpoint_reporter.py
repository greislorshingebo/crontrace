"""Tests for crontrace.checkpoint_reporter."""

from crontrace.checkpoint_reporter import (
    render_checkpoint_row,
    render_checkpoint_table,
)


def _entry(**kwargs):
    base = {
        "id": 1,
        "job_name": "backup",
        "run_id": "run-abc-123",
        "name": "start",
        "reached_at": "2024-01-15T10:00:00Z",
        "note": "beginning of job",
    }
    base.update(kwargs)
    return base


def test_render_row_contains_checkpoint_name():
    row = render_checkpoint_row(_entry(name="upload"))
    assert "upload" in row


def test_render_row_contains_run_id():
    row = render_checkpoint_row(_entry(run_id="run-xyz"))
    assert "run-xyz" in row


def test_render_row_contains_reached_at():
    row = render_checkpoint_row(_entry(reached_at="2024-06-01T08:00:00Z"))
    assert "2024-06-01T08:00:00Z" in row


def test_render_row_contains_note():
    row = render_checkpoint_row(_entry(note="files synced"))
    assert "files synced" in row


def test_render_row_none_note_shows_empty(capsys):
    row = render_checkpoint_row(_entry(note=None))
    assert row is not None  # should not crash


def test_render_row_truncates_long_name():
    long_name = "x" * 50
    row = render_checkpoint_row(_entry(name=long_name))
    assert "x" * 50 not in row  # truncated
    assert "…" in row


def test_render_table_contains_job_name():
    table = render_checkpoint_table("backup", [_entry()])
    assert "backup" in table


def test_render_table_empty_shows_placeholder():
    table = render_checkpoint_table("backup", [])
    assert "no checkpoints" in table


def test_render_table_contains_all_entries():
    entries = [
        _entry(name="start", id=1),
        _entry(name="middle", id=2),
        _entry(name="end", id=3),
    ]
    table = render_checkpoint_table("backup", entries)
    assert "start" in table
    assert "middle" in table
    assert "end" in table


def test_render_table_has_header():
    table = render_checkpoint_table("backup", [])
    assert "CHECKPOINT" in table
    assert "REACHED AT" in table
