# Job Archiver

The **job archiver** moves old execution records out of the live `executions`
table into a dedicated `job_archive` table.  This keeps query times fast while
preserving historical data for audit or compliance purposes.

## Functions

### `archive_executions(conn, job_name, older_than) -> int`

Moves all rows for *job_name* whose `started_at` is earlier than the ISO-8601
timestamp *older_than* into `job_archive`.  Returns the number of rows moved.

```python
from crontrace.storage import get_connection
from crontrace.job_archiver import archive_executions

conn = get_connection("/var/lib/crontrace/jobs.db")
moved = archive_executions(conn, "backup-db", "2024-01-01T00:00:00")
print(f"Archived {moved} record(s).")
```

### `fetch_archive(conn, job_name, limit=50) -> list[dict]`

Returns archived records for *job_name*, newest first.  Each dict contains:
`id`, `job_name`, `started_at`, `duration`, `exit_code`, `stdout`,
`archived_at`.

### `purge_archive(conn, job_name=None) -> int`

Permanently deletes rows from `job_archive`.  Pass *job_name* to scope the
deletion, or omit it to wipe the entire archive.  Returns the row count.

## Reporter

```python
from crontrace.archive_reporter import print_archive_table

rows = fetch_archive(conn, "backup-db")
print_archive_table("backup-db", rows)
```

Example output:

```
Archive: backup-db  (3 record(s))
-------------------------------------------------------------------------------------
JOB                       STARTED                 DURATION    STATUS     ARCHIVED
-------------------------------------------------------------------------------------
backup-db                 2024-01-15T02:00:01     0.83s       OK         2024-02-01T00:00:00
backup-db                 2024-01-14T02:00:02     1.12s       FAIL(1)    2024-02-01T00:00:00
```

## Notes

- The `job_archive` table is created automatically on first use.
- Archiving is transactional: rows are inserted before being deleted from
  `executions`, so a crash cannot cause data loss.
- Use `crontrace prune` for time-based deletion from the live table; use the
  archiver when you want to *retain* old data in a separate store.
