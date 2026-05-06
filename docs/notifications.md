# Notifications

`crontrace` can alert you when a cron job exits with a non-zero status code.
Two channels are supported out of the box:

| Channel | When triggered |
|---------|----------------|
| **stdout** | Always (captured by cron mailer or redirected log) |
| **Webhook** | When `webhook_url` is configured |

---

## Configuration

Create (or edit) `~/.crontrace.ini`:

```ini
[crontrace]
# Notify only when a job fails (exit code != 0).  Set to false to
# receive a notification for every run.
only_on_failure = true

[notifications]
# Leave blank to disable webhook notifications.
webhook_url = https://hooks.example.com/your-token-here
```

The config file path can be overridden with the `CRONTRACE_CONFIG`
environment variable:

```sh
export CRONTRACE_CONFIG=/etc/crontrace/production.ini
```

---

## Webhook payload

A `POST` request is sent with a JSON body:

```json
{
  "job": "backup-db",
  "exit_code": 1,
  "duration_seconds": 4.217,
  "started_at": "2024-01-15T03:00:01",
  "status": "FAIL"
}
```

### Compatible services

- **Slack** — use an [Incoming Webhook](https://api.slack.com/messaging/webhooks)
  URL (note: Slack expects a `text` key, so a small proxy/adapter is needed).
- **Discord** — Webhooks accept arbitrary JSON; map `status` → `content`.
- **Alertmanager / custom HTTP endpoint** — works with the payload as-is.

---

## Programmatic usage

```python
from crontrace.notifier import dispatch

dispatch(
    job_name="backup-db",
    exit_code=exit_code,
    duration=elapsed,
    started_at=started_at_iso,
    webhook_url="https://hooks.example.com/token",
    only_on_failure=True,
)
```
