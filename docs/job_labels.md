# Job Labels

Labels attach arbitrary **key=value** metadata to a job, making it easy to
filter, group, and query jobs by properties like `team`, `env`, or `tier`.

## API

### `set_label(conn, job_name, key, value)`
Insert or replace a single label.  Keys are normalised to lowercase.

### `set_labels_bulk(conn, job_name, labels)`
Set multiple labels in one call from a `{key: value}` dict.

### `get_label(conn, job_name, key) -> str | None`
Return the value for a specific key, or `None` if not set.

### `get_labels(conn, job_name) -> dict`
Return all labels for a job as a `{key: value}` mapping.

### `delete_label(conn, job_name, key) -> bool`
Remove a label by key.  Returns `True` when a row was actually deleted.

### `jobs_by_label(conn, key, value) -> list[str]`
Find all jobs that carry a particular `key=value` pair.

## Example

```python
from crontrace.storage import get_connection
from crontrace.job_labels import set_labels_bulk, get_labels, jobs_by_label

conn = get_connection("crontrace.db")

set_labels_bulk(conn, "backup-db", {"team": "infra", "env": "prod"})
set_labels_bulk(conn, "send-report", {"team": "data", "env": "prod"})

print(get_labels(conn, "backup-db"))
# {'env': 'prod', 'team': 'infra'}

print(jobs_by_label(conn, "env", "prod"))
# ['backup-db', 'send-report']
```

## Rendering

```python
from crontrace.label_reporter import print_label_table

print_label_table("backup-db", get_labels(conn, "backup-db"))
```

Output:

```
Labels for job: backup-db
------------------------------------------------------
  KEY                   VALUE
------------------------------------------------------
  env                   prod
  team                  infra
```

## Notes

- Keys are stored case-insensitively (normalised to lowercase).
- Setting the same key twice replaces the previous value.
- Labels are stored in a dedicated `job_labels` table created automatically
  on first use.
