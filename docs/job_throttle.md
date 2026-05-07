# Job Throttle

The `crontrace.job_throttle` module provides a lightweight rate-limiting guard
that prevents a cron job from executing more frequently than a configured
minimum interval.

Throttle state is stored in the same SQLite database used by the rest of
crontrace, so it persists across process restarts and reboots.

---

## Table

A `job_throttle` table is created automatically on first use:

| Column     | Type | Description                          |
|------------|------|--------------------------------------|
| `job_name` | TEXT | Primary key – name of the cron job   |
| `last_run` | TEXT | ISO-8601 UTC timestamp of last run   |

---

## API

### `record_run(conn, job_name)`

Persists the current UTC timestamp as the last run time for `job_name`.
Call this immediately after a job successfully starts (or completes,
depending on your semantics).

```python
from crontrace.job_throttle import record_run
record_run(conn, "daily-backup")
```

### `get_last_run(conn, job_name) -> str | None`

Returns the ISO-8601 UTC timestamp of the most recent recorded run, or
`None` if the job has never been recorded.

### `is_throttled(conn, job_name, min_interval_seconds) -> bool`

Returns `True` if the job ran within the last `min_interval_seconds`.
Use this as a guard before executing a job:

```python
from crontrace.job_throttle import is_throttled, record_run

if is_throttled(conn, "hourly-sync", min_interval_seconds=3600):
    print("Job ran too recently – skipping.")
else:
    record_run(conn, "hourly-sync")
    # ... run the job ...
```

### `clear_throttle(conn, job_name)`

Deletes the throttle record for `job_name`.  Useful for manual resets or
test teardown.

```python
from crontrace.job_throttle import clear_throttle
clear_throttle(conn, "daily-backup")
```

---

## Integration with `runner.py`

Pass the shared connection from `storage.get_connection()` to any throttle
call so all crontrace components share the same database file:

```python
from crontrace.storage import get_connection
from crontrace.job_throttle import is_throttled, record_run

conn = get_connection("/var/lib/crontrace/jobs.db")
if not is_throttled(conn, "report-gen", min_interval_seconds=300):
    record_run(conn, "report-gen")
    run_job("report-gen", "python generate_report.py", conn)
```
