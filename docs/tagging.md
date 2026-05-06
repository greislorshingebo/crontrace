# Job Tagging

Crontrace lets you attach arbitrary **tags** to job names so you can group,
filter, and report on related jobs without changing your crontab.

## Concepts

| Term | Meaning |
|------|---------|
| `job_name` | The identifier used when recording an execution (e.g. `backup-db`) |
| `tag` | A short, lowercase label (e.g. `prod`, `nightly`, `critical`) |

Tags are stored in a dedicated `job_tags` table inside the same SQLite database
used for execution history.  The table is created automatically on first use.

## API

### `add_tag(conn, job_name, tag)`

Attach `tag` to `job_name`.  Tags are normalised to lowercase and trimmed.
Adding a tag that already exists is a no-op.

```python
from crontrace.storage import get_connection
from crontrace.tagging import add_tag

conn = get_connection("/var/lib/crontrace/jobs.db")
add_tag(conn, "backup-db", "critical")
```

### `remove_tag(conn, job_name, tag)`

Detach a tag from a job.  No error is raised if the pair does not exist.

### `list_tags(conn, job_name) -> List[str]`

Return all tags for a job, sorted alphabetically.

```python
print(list_tags(conn, "backup-db"))  # ['critical', 'nightly']
```

### `jobs_by_tag(conn, tag) -> List[str]`

Return every job name that carries the given tag.

```python
critical_jobs = jobs_by_tag(conn, "critical")
```

### `clear_tags(conn, job_name)`

Remove **all** tags from a job in one call.

## CLI integration (planned)

Future `crontrace tag add <job> <tag>` / `crontrace tag list <job>` commands
will expose this functionality without writing Python.

## Storage

```sql
CREATE TABLE job_tags (
    job_name TEXT NOT NULL,
    tag      TEXT NOT NULL,
    PRIMARY KEY (job_name, tag)
);
```

The composite primary key guarantees uniqueness and makes lookups O(log n).
