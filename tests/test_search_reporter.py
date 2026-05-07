"""Focused tests for crontrace.search_reporter formatting helpers."""

from __future__ import annotations

from crontrace.search_reporter import render_search_results, print_search_results


def _make_row(
    job_name: str = "myjob",
    started_at: str = "2024-01-01T00:00:00",
    exit_code: int = 0,
    duration_s: float = 1.5,
    stdout: str = "",
    stderr: str = "",
) -> dict:
    return dict(
        job_name=job_name,
        started_at=started_at,
        exit_code=exit_code,
        duration_s=duration_s,
        stdout=stdout,
        stderr=stderr,
    )


def test_render_contains_job_name():
    rows = [_make_row(job_name="nightly-sync")]
    out = render_search_results(rows)
    assert "nightly-sync" in out


def test_render_contains_exit_code():
    rows = [_make_row(exit_code=2)]
    out = render_search_results(rows)
    assert "2" in out


def test_render_contains_duration():
    rows = [_make_row(duration_s=3.75)]
    out = render_search_results(rows)
    assert "3.75s" in out


def test_render_none_duration_shows_dash():
    row = _make_row()
    row["duration_s"] = None
    out = render_search_results([row])
    assert "—" in out


def test_render_query_description_shown():
    out = render_search_results([], query_description="exit_code=1")
    assert "exit_code=1" in out


def test_render_separator_present():
    out = render_search_results([_make_row()])
    assert "---" in out


def test_print_search_results_outputs_to_stdout(capsys):
    rows = [_make_row(job_name="print-test")]
    print_search_results(rows, "unit test")
    captured = capsys.readouterr()
    assert "print-test" in captured.out
    assert "unit test" in captured.out
