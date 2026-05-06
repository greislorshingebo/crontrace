# Job Summary & Statistics

The `crontrace summarizer` and `report` modules provide aggregate statistics
over a job's execution history stored in the SQLite database.

## Summarizer (`crontrace/summarizer.py`)

`summarize(rows)` accepts a list of rows returned by `fetch_recent` and
returns a dictionary with the following keys:

| Key | Type | Description |
|---|---|---|
| `total` | int | Total number of recorded runs |
| `successes` | int | Runs that exited with code `0` |
| `failures` | int | Runs that exited with a non-zero code |
| `success_rate` | float \| None | Fraction of successful runs (`None` if no runs) |
| `avg_duration` | float \| None | Mean duration in seconds |
| `min_duration` | float \| None | Shortest run in seconds |
| `max_duration` | float \| None | Longest run in seconds |
| `last_exit` | int \| None | Exit code of the most recent run |

### Example

```python
from crontrace.storage import get_connection, fetch_recent
from crontrace.summarizer import summarize

conn = get_connection("/var/lib/crontrace/jobs.db")
rows = fetch_recent(conn, job_name="backup", limit=50)
stats = summarize(rows)
print(f"Success rate: {stats['success_rate']:.1%}")
```

## Report (`crontrace/report.py`)

`render_summary(job_name, rows)` returns a formatted multi-line string
suitable for printing to a terminal.

```
------------------------------------
  Job: backup
------------------------------------
  Total runs:       10
  Successes:        9
  Failures:         1
  Success rate:     90.0%
  Avg duration:     12.34s
  Min duration:     8.10s
  Max duration:     18.72s
  Last status:      OK
------------------------------------
```

## CLI integration

The `crontrace log` command will display the summary block automatically
when the `--summary` flag is provided (planned for a future release).
