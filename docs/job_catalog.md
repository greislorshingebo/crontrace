# Job Catalog

The **job catalog** lets you register known cron jobs with metadata such as
command, schedule expression, description, and owner.  It is separate from the
execution history — the catalog is a directory of *what* jobs exist, while
`storage.py` records *when* they ran.

## API

### `register_job(conn, job_name, command, schedule, description, owner)`

Insert a new job or update an existing one (upsert by `job_name`).

```python
from crontrace.job_catalog import register_job
register_job(conn, "backup", "/usr/local/bin/backup.sh",
             schedule="0 2 * * *", owner="ops")
```

### `get_job(conn, job_name) -> dict | None`

Return a single catalog entry as a dict, or `None` if not found.

### `list_jobs(conn) -> list[dict]`

Return all registered jobs ordered alphabetically by `job_name`.

### `deregister_job(conn, job_name) -> bool`

Remove a job from the catalog.  Returns `True` if a row was deleted.

## Rendering

```python
from crontrace.catalog_reporter import render_catalog_table
print(render_catalog_table(list_jobs(conn)))
```

Sample output:

```
JOB NAME                  COMMAND                           SCHEDULE        OWNER         DESCRIPTION
----------------------------------------------------------------------------------------------------
backup                    /usr/local/bin/backup.sh          0 2 * * *       ops           nightly backup
cleanup                   /usr/local/bin/cleanup.sh         30 3 * * 0      ops
```

## Schema

| Column        | Type | Notes                      |
|---------------|------|----------------------------|
| `job_name`    | TEXT | Primary key                |
| `command`     | TEXT | Shell command to execute   |
| `schedule`    | TEXT | Cron expression (optional) |
| `description` | TEXT | Free-text description      |
| `owner`       | TEXT | Responsible team or person |
| `created_at`  | TEXT | UTC timestamp, auto-set    |
