# cronwrap

A lightweight CLI wrapper that adds retry logic, alerting, and logging to any cron job.

---

## Installation

```bash
pip install cronwrap
```

---

## Usage

Wrap any command by prefixing it with `cronwrap`:

```bash
cronwrap --retries 3 --alert email@example.com -- /path/to/your/script.sh
```

**Common options:**

| Flag | Description |
|------|-------------|
| `--retries N` | Retry the command up to N times on failure |
| `--alert EMAIL` | Send an alert email if the job fails |
| `--log FILE` | Append output to a log file |
| `--timeout SECS` | Kill the job if it exceeds a time limit |

**Example crontab entry:**

```
0 2 * * * cronwrap --retries 3 --log /var/log/backup.log --alert ops@example.com -- /usr/local/bin/backup.sh
```

If the wrapped command exits with a non-zero status, `cronwrap` will:
1. Retry the specified number of times
2. Log stdout/stderr to the specified log file
3. Send an alert notification on final failure

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

This project is licensed under the [MIT License](LICENSE).