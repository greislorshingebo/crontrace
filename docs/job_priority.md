# Job Priority

`crontrace` lets you assign a **priority level** to each registered job.
Priorities are used by dashboards, alerting, and schedule runners to decide
execution order and notification urgency.

## Priority Levels

| Level      | Icon | Description                                |
|------------|------|--------------------------------------------|
| `critical` | 🔴   | Must run; page on failure                  |
| `high`     | 🟠   | Important; alert on failure                |
| `normal`   | 🟡   | Default level for all jobs                 |
| `low`      | ⚪   | Best-effort; suppress routine notifications|

## API

```python
from crontrace.job_priority import set_priority, get_priority, delete_priority, list_priorities

# Assign a priority
set_priority(conn, "backup-db", "critical")

# Read it back (returns DEFAULT_PRIORITY when not set)
level = get_priority(conn, "backup-db")   # "critical"

# Remove the override
deleted = delete_priority(conn, "backup-db")  # True

# List all jobs with explicit priorities
rows = list_priorities(conn)
# [{"job_name": "backup-db", "priority": "critical", "updated_at": "..."}]
```

## Rendering

```python
from crontrace.priority_reporter import print_priority_table

print_priority_table(rows)
```

Example output:

```
JOB                             PRIORITY      UPDATED AT
--------------------------------------------------------------
backup-db                       🔴 critical   2024-06-01T02:00:00
cleanup-logs                    🟠 high       2024-06-01T01:00:00
```

## Validation

Passing an unknown priority string raises `ValueError`.
