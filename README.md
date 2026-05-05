# crontrace

Lightweight wrapper that logs cron job execution history with exit codes and durations.

## Installation

```bash
pip install crontrace
```

## Usage

Wrap any cron command with `crontrace` to automatically record its execution history:

```bash
# In your crontab
* * * * * crontrace -- /path/to/your/script.sh
```

Logs are stored in `~/.crontrace/history.log` by default and include the command, timestamp, exit code, and duration.

```bash
# View recent job history
crontrace history

# Example output
2024-01-15 03:00:01  /path/to/script.sh  exit=0  duration=1.24s
2024-01-15 02:00:01  /path/to/script.sh  exit=1  duration=0.87s

# Specify a custom log file
crontrace --log /var/log/myjobs.log -- /path/to/script.sh

# Show only failed jobs
crontrace history --failed
```

### Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--log` | `~/.crontrace/history.log` | Path to log file |
| `--tag` | *(none)* | Optional label for the job |
| `--timeout` | *(none)* | Kill job after N seconds |

```bash
# Tag a job for easier filtering
crontrace --tag backup -- /usr/local/bin/backup.sh
crontrace history --tag backup
```

## Requirements

- Python 3.7+

## License

MIT © [crontrace contributors](LICENSE)