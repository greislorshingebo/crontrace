# Job Annotations

Annotations let you attach free-text notes to individual job executions stored
in the crontrace database.  This is useful for recording why a job was
re-triggered, noting an incident, or leaving a reminder for future operators.

## Storage

Annotations are kept in the `execution_annotations` table which is created
automatically on first use.  Each row links to an execution via `exec_id` and
also stores the `job_name` for efficient look-ups without joins.

## API

### `add_annotation(conn, exec_id, job_name, note) -> int`

Attaches *note* to the execution identified by *exec_id*.  Leading and trailing
whitespace is stripped.  An empty (or whitespace-only) note raises `ValueError`.
Returns the rowid of the new annotation.

```python
from crontrace.storage import get_connection
from crontrace.job_annotations import add_annotation

conn = get_connection("/var/lib/crontrace/jobs.db")
add_annotation(conn, exec_id=42, job_name="backup", note="Manually triggered after disk swap")
```

### `get_annotations(conn, exec_id) -> list[dict]`

Returns all annotations for a single execution, ordered oldest first.  Each
dict contains: `id`, `exec_id`, `job_name`, `note`, `created_at`.

### `annotations_for_job(conn, job_name) -> list[dict]`

Returns every annotation ever written for *job_name* across all executions,
ordered newest first.  Useful for a quick audit trail.

### `delete_annotation(conn, annotation_id) -> bool`

Removes the annotation with the given primary key.  Returns `True` if a row
was deleted, `False` if the id did not exist.

## Example: listing annotations in the CLI

```bash
# Future CLI integration — run the job and annotate it
crontrace run --name backup /usr/local/bin/backup.sh
crontrace annotate --exec-id 42 "Post-incident rerun"
crontrace annotations --job backup
```

## Notes

- Annotations are **not** deleted when a job execution is pruned; clean them
  up with `delete_annotation` if needed.
- `exec_id` values correspond to the `id` column in the `executions` table
  produced by `crontrace/storage.py`.
