# Job Checkpoints

Checkpoints allow you to record named milestones within a single job run. This is useful for long-running jobs where you want to track progress and pinpoint where a failure occurred.

## Concepts

- **job_name**: The identifier for the cron job (e.g. `"backup"`).
- **run_id**: A unique identifier for a specific execution (e.g. a UUID or timestamp string).
- **name**: The checkpoint label (e.g. `"start"`, `"upload_complete"`, `"cleanup"`).
- **note**: An optional free-text annotation for the checkpoint.

## API

### `record_checkpoint(conn, job_name, run_id, name, note=None) -> int`

Inserts a new checkpoint row and returns its row id. The `reached_at` timestamp is set automatically to the current UTC time.

```python
from crontrace.job_checkpoints import record_checkpoint
record_checkpoint(conn, "backup", "run-20240601", "files_copied", note="1200 files")
```

### `get_checkpoints(conn, job_name, run_id) -> list[dict]`

Returns all checkpoints for a specific run, ordered oldest-first.

```python
from crontrace.job_checkpoints import get_checkpoints
steps = get_checkpoints(conn, "backup", "run-20240601")
for step in steps:
    print(step["name"], step["reached_at"])
```

### `delete_checkpoint(conn, checkpoint_id) -> bool`

Deletes a checkpoint by its row id. Returns `True` if a row was removed.

### `checkpoints_for_job(conn, job_name) -> list[dict]`

Returns all checkpoints across every run for the given job, ordered newest first.

## Rendering

Use `crontrace.checkpoint_reporter` to display checkpoint data:

```python
from crontrace.checkpoint_reporter import print_checkpoints
from crontrace.job_checkpoints import checkpoints_for_job

entries = checkpoints_for_job(conn, "backup")
print_checkpoints("backup", entries)
```

Example output:

```
Checkpoints for job: backup
------------------------------------------------------------------------------------------
    ID  RUN ID                    CHECKPOINT            REACHED AT              NOTE
------------------------------------------------------------------------------------------
     1  run-20240601              start                 2024-06-01T08:00:00Z    beginning
     2  run-20240601              files_copied          2024-06-01T08:01:12Z    1200 files
     3  run-20240601              cleanup               2024-06-01T08:01:45Z
------------------------------------------------------------------------------------------
```

## Database Schema

Checkpoints are stored in the `job_checkpoints` table within the same SQLite database used by the rest of crontrace. The table is created automatically on first use.
