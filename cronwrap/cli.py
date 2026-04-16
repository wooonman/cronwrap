"""CLI entry point for cronwrap."""
import argparse
import sys
from cronwrap.runner import run_command
from cronwrap.alerts import AlertConfig, maybe_alert
from cronwrap.logging_config import get_logger, log_run_result
from cronwrap.log_store import append_log, LogEntry
from datetime import datetime

logger = get_logger("cronwrap.cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Wrap any cron command with retry, alerting, and logging.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    parser.add_argument("--retries", type=int, default=0, help="Number of retries on failure")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    parser.add_argument("--job-name", default="cronwrap", help="Job name for logs/alerts")
    parser.add_argument("--log-file", default=None, help="Path to JSONL log file")
    parser.add_argument("--alert-to", default=None, help="Alert recipient email")
    parser.add_argument("--alert-from", default=None, help="Alert sender email")
    parser.add_argument("--smtp-host", default="localhost", help="SMTP host")
    parser.add_argument("--smtp-port", type=int, default=25, help="SMTP port")
    parser.add_argument("--smtp-user", default=None)
    parser.add_argument("--smtp-password", default=None)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        parser.print_help()
        sys.exit(1)

    result = run_command(command, retries=args.retries, timeout=args.timeout)
    log_run_result(logger, args.job_name, result)

    if args.log_file:
        entry = LogEntry(
            job_name=args.job_name,
            timestamp=datetime.utcnow().isoformat(),
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=result.duration,
            retries_used=result.retries_used,
        )
        append_log(args.log_file, entry)

    alert_cfg = AlertConfig(
        to_addr=args.alert_to,
        from_addr=args.alert_from,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_password=args.smtp_password,
    )
    maybe_alert(alert_cfg, args.job_name, result)

    sys.exit(result.exit_code if result.exit_code is not None else 1)


if __name__ == "__main__":
    main()
