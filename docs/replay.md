# Replay

The `crontrace.replay` module lets you re-execute any historical cron job run
by its execution ID, optionally persisting the result as a new record.

## Why replay?

- **Incident recovery** – quickly re-run a failed backup or sync job without
  editing your crontab.
- **Auditing** – verify that a fixed command now exits cleanly and keep the
  evidence in the log.
- **Testing** – replay a known command in a staging environment without
  reconfiguring schedules.

## API

### `fetch_execution(db_path, execution_id) -> dict | None`

Returns the execution record for the given `rowid`, or `None` if it does not
exist.

```python
from crontrace.replay import fetch_execution

entry = fetch_execution("/var/lib/crontrace/jobs.db", 17)
if entry:
    print(entry["command"], entry["exit_code"])
```

### `replay_execution(db_path, execution_id, record=True) -> int`

Re-runs the command stored in the execution record and returns the new exit
code.

| Parameter      | Type   | Default | Description                                      |
|----------------|--------|---------|--------------------------------------------------|
| `db_path`      | `str`  | —       | Path to the SQLite database.                     |
| `execution_id` | `int`  | —       | `rowid` of the execution to replay.              |
| `record`       | `bool` | `True`  | Persist the new run to the `executions` table.   |

Raises `ValueError` if `execution_id` is not found.

```python
from crontrace.replay import replay_execution

code = replay_execution("/var/lib/crontrace/jobs.db", 17)
print("Exit code:", code)
```

## CLI integration

Replay support can be wired into `crontrace/cli.py` as a `replay` sub-command:

```
crontrace replay --id 17
crontrace replay --id 17 --no-record
```

## Notes

- The replayed command is executed via `subprocess.run(shell=True)`, identical
  to how `runner.run_job` works.
- When `record=True` the new row carries the **replay** timestamp and duration;
  the original row is never modified.
- Use `crontrace log` to find the `rowid` of the execution you want to replay.
