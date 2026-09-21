from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from aidb.client import send_command


def _add_connection_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Control host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Control port printed by the sample app",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aidb",
        description="Attach to a live aidb debug control port and halt, continue, or end the run.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("attach", "Interactive halt/continue/end/status loop"),
        ("halt", "Halt the live run at the next controlled stop"),
        ("continue", "Continue a halted run"),
        ("end", "End the debug session and stop the run"),
        ("status", "Print the current session state"),
    ):
        command = sub.add_parser(name, help=help_text)
        _add_connection_flags(command)
    return parser


def _print_response(response: dict) -> None:
    sys.stdout.write(json.dumps(response, sort_keys=True) + "\n")


def _attach_loop(host: str, port: int) -> int:
    sys.stdout.write(
        f"attached to {host}:{port}\n"
        "commands: halt | continue | end | status | quit\n"
    )
    sys.stdout.flush()
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            sys.stdout.write("\n")
            return 0
        if not line:
            continue
        if line in {"quit", "exit", "q"}:
            return 0
        op = "continue" if line in {"continue", "cont", "c"} else line
        if op not in {"halt", "continue", "end", "status"}:
            sys.stdout.write("unknown command\n")
            continue
        try:
            response = send_command(op, host=host, port=port)
        except OSError as exc:
            sys.stdout.write(f"error: {exc}\n")
            return 1
        _print_response(response)
        if op == "end":
            return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "attach":
        return _attach_loop(args.host, args.port)
    response = send_command(args.command, host=args.host, port=args.port)
    _print_response(response)
    return 0 if response.get("ok") else 1
