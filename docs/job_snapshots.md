# Job Snapshots

The **job snapshots** module lets you persist the last known execution state of
a cron job — exit code, duration, stdout, and a timestamp — in a lightweight
SQLite table.  Snapshots are useful for:

- Quickly checking what a job last produced without querying the full history.
- Feeding a diff reporter to highlight changes between runs.
- Generating status badges or dashboards that need a single authoritative
  "current state" record per job.

---

## Storage

Snapshots are stored in the `job_snapshots` table, which is created
automatically on first use.

| Column | Type | Description |
|---|---|---|
| `job_name` | TEXT PK | Unique job identifier |
| `exit_code` | INTEGER | Last exit code (0 = success) |
| `duration` | REAL | Execution duration in seconds |
| `stdout` | TEXT | Captured output (may be NULL) |
| `captured_at` | TEXT | UTC ISO-8601 timestamp |

Each job has **at most one** snapshot row.  Calling `save_snapshot` again
for the same job name replaces the previous record.

---

## API

```python
from crontrace.job_snapshots import (
    save_snapshot, get_snapshot, delete_snapshot, list_snapshots
)
```

### `save_snapshot(conn, job_name, exit_code, duration, stdout, captured_at)`

Insert or replace the snapshot for `job_name`.

```python
save_snapshot(conn, "daily-backup", 0, 14.2, "3 files archived", "2024-06-01T02:00:00")
```

### `get_snapshot(conn, job_name) -> dict | None`

Return the snapshot dict for `job_name`, or `None` if no snapshot exists.

```python
snap = get_snapshot(conn, "daily-backup")
if snap:
    print(snap["exit_code"], snap["duration"])
```

### `delete_snapshot(conn, job_name) -> bool`

Remove the snapshot.  Returns `True` if a row was deleted.

### `list_snapshots(conn) -> list[dict]`

Return all snapshots ordered alphabetically by `job_name`.

---

## Rendering

```python
from crontrace.snapshot_reporter import print_snapshots

print_snapshots(list_snapshots(conn))
```

Example output:

```
All Snapshots
----------------------------------------------------------------------
JOB                            CODE    DURATION  CAPTURED AT
----------------------------------------------------------------------
daily-backup                     OK      14.20s  2024-06-01T02:00:00
weekly-report                     1       3.05s  2024-05-28T06:00:00
----------------------------------------------------------------------
```
