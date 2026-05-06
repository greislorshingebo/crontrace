"""Command-line interface for crontrace."""

import argparse
import sys
from pathlib import Path

from crontrace.storage import get_connection, fetch_recent
from crontrace.runner import run_job
from crontrace.formatter import format_table

DEFAULT_DB = Path.home() / ".crontrace" / "history.db"
DEFAULT_LIMIT = 20


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontrace",
        description="Lightweight cron job execution logger.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run subcommand
    run_p = sub.add_parser("run", help="Run a command and record its execution.")
    run_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute.")
    run_p.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite database.")

    # log subcommand
    log_p = sub.add_parser("log", help="Show recent execution history.")
    log_p.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite database.")
    log_p.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of records to show.")
    log_p.add_argument("--filter", dest="filter_cmd", default=None, help="Filter by command substring.")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    if not args.cmd:
        print("crontrace run: no command specified.", file=sys.stderr)
        return 2
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(str(db_path))
    exit_code = run_job(conn, args.cmd)
    conn.close()
    return exit_code


def cmd_log(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    if not db_path.exists():
        print("No history database found.", file=sys.stderr)
        return 1
    conn = get_connection(str(db_path))
    records = fetch_recent(conn, limit=args.limit, command_filter=args.filter_cmd)
    conn.close()
    print(format_table(records))
    return 0


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "log":
        return cmd_log(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
