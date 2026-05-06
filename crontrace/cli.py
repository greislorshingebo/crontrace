"""Command-line interface for crontrace."""

from __future__ import annotations

import argparse
import os
import sys

from crontrace.formatter import format_table
from crontrace.pruner import prune_old_records
from crontrace.runner import run_job
from crontrace.storage import fetch_recent

DEFAULT_DB = os.path.expanduser("~/.crontrace.db")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontrace",
        description="Lightweight cron job execution logger.",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        metavar="PATH",
        help="Path to the SQLite database (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- run ---
    p_run = sub.add_parser("run", help="Run a command and record the result.")
    p_run.add_argument("job_name", help="Logical name for this cron job.")
    p_run.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute.")

    # --- log ---
    p_log = sub.add_parser("log", help="Show recent execution history.")
    p_log.add_argument("--job", default=None, metavar="NAME", help="Filter by job name.")
    p_log.add_argument(
        "--limit", type=int, default=20, metavar="N", help="Number of rows (default: 20)"
    )

    # --- prune ---
    p_prune = sub.add_parser("prune", help="Delete old execution records.")
    p_prune.add_argument(
        "--days",
        type=int,
        default=30,
        metavar="N",
        help="Remove records older than N days (default: 30)",
    )
    p_prune.add_argument(
        "--job", default=None, metavar="NAME", help="Limit pruning to a specific job."
    )

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    if not args.cmd:
        print("crontrace run: no command specified.", file=sys.stderr)
        return 2
    return run_job(args.db, args.job_name, args.cmd)


def cmd_log(args: argparse.Namespace) -> int:
    rows = fetch_recent(args.db, limit=args.limit, job_name=args.job)
    print(format_table(rows))
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    deleted = prune_old_records(args.db, days=args.days, job_name=args.job)
    label = f"job '{args.job}'" if args.job else "all jobs"
    print(f"Pruned {deleted} record(s) older than {args.days} day(s) for {label}.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    dispatch = {"run": cmd_run, "log": cmd_log, "prune": cmd_prune}
    exit_code = dispatch[args.command](args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
