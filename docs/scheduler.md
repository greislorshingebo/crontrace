# Scheduler

Crontrace ships a lightweight scheduler module that lets you **validate**,
**inspect**, and **persist** cron expressions alongside your job history.

## Modules

| Module | Purpose |
|---|---|
| `crontrace.scheduler` | Parse and query cron expressions |
| `crontrace.schedule_store` | Persist named schedules in the SQLite DB |

---

## `crontrace.scheduler`

### `is_valid_expression(expression: str) -> bool`

Returns `True` when *expression* is a syntactically valid 5-field cron string.

```python
from crontrace.scheduler import is_valid_expression

is_valid_expression("0 * * * *")   # True
is_valid_expression("bad value")   # False
```

### `next_run(expression, base=None) -> datetime`

Returns the **next** UTC `datetime` after *base* (defaults to now).

```python
from crontrace.scheduler import next_run

print(next_run("0 9 * * 1"))  # next Monday at 09:00 UTC
```

### `prev_run(expression, base=None) -> datetime`

Returns the **most recent** scheduled UTC `datetime` before *base*.

### `describe_schedule(expression, n=3) -> list[str]`

Returns the next *n* ISO-8601 UTC run times as strings — handy for
displaying a human-readable preview.

```python
from crontrace.scheduler import describe_schedule

for ts in describe_schedule("*/30 * * * *", n=5):
    print(ts)
```

### `time_until_next_run(expression, base=None) -> timedelta`

Returns a `timedelta` representing how long until the next scheduled run
after *base* (defaults to now). Useful for displaying countdowns or
implementing sleep-based scheduling loops.

```python
from crontrace.scheduler import time_until_next_run

delta = time_until_next_run("0 9 * * 1")
print(f"Next run in {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m")
```

---

## `crontrace.schedule_store`

Schedules are stored in the same SQLite database used for execution history
(controlled by `[crontrace] db_path` in `~/.config/crontrace/config.ini`).

### Saving a schedule

```python
from crontrace.schedule_store import upsert_schedule

upsert_schedule("/var/lib/crontrace/jobs.db", "daily-backup", "0 2 * * *")
```

### Retrieving a schedule

```python
from crontrace.schedule_store import fetch_schedule

expr = fetch_schedule("/var/lib/crontrace/jobs.db", "daily-backup")
print(expr)  # "0 2 * * *"
```

### Listing all schedules

```python
from crontrace.schedule_store import list_schedules

for row in list_schedules("/var/lib/crontrace/jobs.db"):
    print(row["job_name"], row["expression"])
```

### Deleting a schedule

```python
from crontrace.schedule_store import delete_schedule

delete_schedule("/var/lib/crontrace/jobs.db", "old-job")
```

---

## Dependency

The scheduler module requires the [`croniter`](https://pypi.org/project/croniter/)
package.  Add it to your environment with:

```bash
pip install croniter
```
