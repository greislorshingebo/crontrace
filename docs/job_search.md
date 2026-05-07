# Job Search

`crontrace` provides flexible search utilities for querying execution history
stored in the SQLite database.

## Functions

### `search_by_name(conn, pattern)`
Returns all executions whose `job_name` contains `pattern`
(case-insensitive substring match).

### `search_by_exit_code(conn, code)`
Returns all executions that finished with the given integer exit code.
Useful for quickly finding all failed (`code != 0`) or successful (`code == 0`)
runs.

### `search_output(conn, term)`
Searches the `stdout` and `stderr` columns for `term`.
Helpful when you remember a keyword from a job's output but not its name.

### `search_combined(conn, *, name, exit_code, output_term)`
Combines any subset of the above filters with AND semantics.
All keyword arguments are optional; omitting one means that filter is skipped.

## Rendering

Use `search_reporter.render_search_results(rows, query_description)` to
produce a human-readable table:

```
Search: name~backup
JOB                       STARTED               CODE   DURATION
---------------------------------------------------------------
backup-db                 2024-05-01T02:00:00      0      4.21s
backup-files              2024-05-01T02:05:00      0      7.83s
---------------------------------------------------------------
2 result(s)
```

## CLI integration

The `cmd_search` command in `cli.py` exposes these helpers:

```
crontrace search --name backup
crontrace search --exit-code 1
crontrace search --output "error"
crontrace search --name backup --exit-code 0
```
