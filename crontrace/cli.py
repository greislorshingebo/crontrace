"""Command-line interface for crontrace."""

from __future__ import annotations

import argparse
import os
import sys

from crontrace.exporter import export_csv, export_json
from crontrace.formatter import format_table
from crontrace.pruner import prune_old_records
from crontrace.runner import run_job
from crontrace.storage import fetch_recent, get_connection

DEFAULT_DB = os.path.expanduser("~/.crontrace.db")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontrace",
        description="Lightweight cron job execution logger.",
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database.")
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run a command and record its execution.")
    run_p.add_argument("job", help="Job name / label.")
    run_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute.")

    # log
    log_p = sub.add_parser("log", help="Show recent execution history.")
    log_p.add_argument("-n", "--limit", type=int, default=20, help="Number of records.")
    log_p.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format.",
    )

    # prune
    prune_p = sub.add_parser("prune", help="Delete records older than N days.")
    prune_p.add_argument("days", type=int, help="Retention period in days.")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    conn = get_connection(args.db)
    exit_code = run_job(conn, args.job, cmd)
    conn.close()
    return exit_code


def cmd_log(args: argparse.Namespace) -> int:
    conn = get_connection(args.db)
    rows = fetch_recent(conn, limit=args.limit)
    conn.close()

    fmt = getattr(args, "format", "table")
    if fmt == "json":
        print(export_json(rows))
    elif fmt == "csv":
        print(export_csv(rows), end="")
    else:
        print(format_table(rows))
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    conn = get_connection(args.db)
    removed = prune_old_records(conn, args.days)
    conn.close()
    print(f"Pruned {removed} record(s) older than {args.days} day(s).")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "log":
        sys.exit(cmd_log(args))
    elif args.command == "prune":
        sys.exit(cmd_prune(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
