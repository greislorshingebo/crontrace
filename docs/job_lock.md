# Job Locking

`crontrace` can prevent overlapping executions of the same cron job using a
simple advisory lock backed by the same SQLite database used for execution
history.

## How It Works

Before a job starts, `acquire_lock` attempts to insert a row into the
`job_locks` table keyed on the job name.  Because the column has a `PRIMARY KEY`
constraint, a second attempt for the same job name fails silently and returns
`False`, signalling that the job is already running.

When the job finishes (or errors), `release_lock` deletes the row so the next
run can proceed.

## API

```python
from crontrace.job_lock import acquire_lock, release_lock, get_lock_info, is_locked
```

### `acquire_lock(conn, job_name, pid, now_utc) -> bool`

Try to lock *job_name*.  Returns `True` on success, `False` if already locked.

| Parameter | Type | Description |
|-----------|------|-------------|
| `conn` | `sqlite3.Connection` | Open database connection |
| `job_name` | `str` | Unique name of the cron job |
| `pid` | `int` | PID of the current process |
| `now_utc` | `str` | ISO-8601 timestamp recorded with the lock |

### `release_lock(conn, job_name) -> None`

Remove the lock for *job_name*.  Safe to call even when no lock exists.

### `get_lock_info(conn, job_name) -> dict | None`

Return `{"job_name", "pid", "acquired"}` for the current lock, or `None`.

### `is_locked(conn, job_name) -> bool`

Convenience wrapper — returns `True` when a lock row is present.

## Integration with `run_job`

When the `--no-overlap` flag is passed to `crontrace run`, the CLI acquires a
lock before spawning the subprocess and releases it in a `finally` block:

```
$ crontrace run --no-overlap --name backup -- /usr/bin/backup.sh
```

If the job is already running the command exits immediately with code `75`
(`EX_TEMPFAIL`) and logs a warning.

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS job_locks (
    job_name  TEXT PRIMARY KEY,
    pid       INTEGER NOT NULL,
    acquired  TEXT NOT NULL
);
```
