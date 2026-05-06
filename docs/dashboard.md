# Dashboard

The `crontrace.dashboard` module renders a compact, human-readable terminal
overview of one or more cron jobs, combining summary statistics with active
alerts in a single output string.

## Functions

### `render_job_panel(job_name, rows, *, failure_rate_threshold, avg_duration_threshold) -> str`

Builds a panel for a single job.

| Parameter | Default | Description |
|---|---|---|
| `job_name` | — | Name of the cron job |
| `rows` | — | List of execution record dicts |
| `failure_rate_threshold` | `0.5` | Fraction of failures that triggers an alert |
| `avg_duration_threshold` | `300.0` | Average duration in seconds that triggers an alert |

The panel includes:
- A header with the job name
- A summary block (success rate, run count, avg duration) from `render_summary`
- An optional **Alerts** section when thresholds are exceeded

### `render_dashboard(jobs, *, failure_rate_threshold, avg_duration_threshold) -> str`

Renders panels for every `(job_name, rows)` pair in `jobs`, separated by
horizontal rules.

Returns `"No jobs to display."` when the list is empty.

## CLI integration

The dashboard output can be piped directly to `less` or written to a log file:

```bash
crontrace log --format dashboard 2>&1 | less
```

## Example output

```
============================================================
  Job: backup
============================================================
Job       : backup
Runs      : 24
Success   : 23 (95.8%)
Fail      : 1  (4.2%)
Avg dur   : 12.4 s
Last run  : 2024-06-01T03:00:01  OK

------------------------------------------------------------
============================================================
  Job: sync
============================================================
Job       : sync
Runs      : 10
Success   : 4  (40.0%)
Fail      : 6  (60.0%)
Avg dur   : 8.1 s
Last run  : 2024-06-01T04:00:01  FAIL

Alerts:
⚠  [failure_rate] sync — failure rate 60.0% exceeds threshold 50.0%
```
