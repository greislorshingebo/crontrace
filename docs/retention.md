# Retention Policies

`crontrace` can enforce a **row-count limit** on the executions table so the
database does not grow unbounded on busy systems.

## Module: `crontrace.retention`

### `get_storage_stats(conn) -> dict`

Returns a snapshot of the current table state:

| Key | Type | Description |
|---|---|---|
| `total_rows` | `int` | Number of records in the table |
| `oldest` | `str \| None` | ISO-8601 timestamp of the oldest record |
| `newest` | `str \| None` | ISO-8601 timestamp of the most recent record |

### `enforce_row_limit(conn, max_rows) -> int`

Deletes the **oldest** rows until the table contains at most `max_rows`
records.  Returns the number of rows deleted (0 if already within limit).

Raises `ValueError` if `max_rows` is not a positive integer.

### `retention_summary(conn, max_rows) -> dict`

Combines `get_storage_stats` output with limit metadata:

| Key | Description |
|---|---|
| `total_rows` | Current row count |
| `oldest` / `newest` | Timestamp range |
| `max_rows` | The configured limit |
| `rows_over_limit` | How many rows exceed the limit (0 if within) |
| `within_limit` | `True` when no pruning is needed |

## CLI integration

The `prune` command (see `crontrace/cli.py`) calls `enforce_row_limit` after
time-based pruning when `--max-rows` is supplied:

```
crontrace prune --retain-days 30 --max-rows 10000
```

## Configuration

Add `max_rows` to `~/.config/crontrace/config.ini`:

```ini
[retention]
max_rows = 50000
```

Read it via `crontrace.config.load()` and pass the value to
`enforce_row_limit` during scheduled maintenance runs.

## Example

```python
from crontrace.storage import get_connection
from crontrace.retention import enforce_row_limit, retention_summary

with get_connection("/var/lib/crontrace/jobs.db") as conn:
    summary = retention_summary(conn, max_rows=20_000)
    if not summary["within_limit"]:
        removed = enforce_row_limit(conn, max_rows=20_000)
        print(f"Pruned {removed} old records.")
```
