# Alerting

`crontrace` can evaluate simple threshold-based alerts against a job's recent
execution history and surface them in the CLI or in log output.

## How it works

After fetching rows from the database (`storage.fetch_recent`), pass them to
`alerting.evaluate_alerts`.  The function returns a (possibly empty) list of
alert dictionaries that can be rendered with `alert_reporter.render_alerts`.

## Available checks

| Check | Default threshold | Description |
|---|---|---|
| `failure_rate` | 50 % | Fraction of recent runs that exited non-zero |
| `avg_duration` | 300 s | Mean wall-clock time of recent runs |

## Configuration

Thresholds can be overridden via `crontrace.ini`:

```ini
[alerting]
failure_rate_threshold = 0.3
duration_threshold_s   = 120
```

Read them with `config.get_failure_rate_threshold()` and
`config.get_duration_threshold_s()`.

## Example

```python
from crontrace import storage, alerting, alert_reporter

conn  = storage.get_connection("/var/lib/crontrace/jobs.db")
rows  = storage.fetch_recent(conn, "backup", limit=20)
alerts = alerting.evaluate_alerts(rows, failure_rate_threshold=0.25)
alert_reporter.print_alerts(alerts, job_name="backup")
```

Sample output:

```
--- Alerts for 'backup' ---
⚠️  ALERT [failure_rate]: Failure rate 40.0% exceeds threshold 25.0%
---------------------------
```
