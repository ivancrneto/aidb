from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from aidb.client import ControlClientError, send_command


def _break_fields(on: str, *, enabled: bool) -> dict:
    return {"on": on, "enabled": enabled}


def _add_connection_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Control host (default: 127.0.0.1; public repo: keep localhost-only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Control port printed by the sample app",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("AIDB_CONTROL_TOKEN"),
        help="Shared control token from the sample app (or AIDB_CONTROL_TOKEN)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aidb",
        description=(
            "Attach to a live aidb debug control port (localhost) and halt, "
            "break after model replies or handoffs, continue, or end the run."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("attach", "Interactive halt/break-reply/break-handoff/continue/end loop"),
        ("halt", "Halt the live run at the next controlled stop"),
        ("break-reply", "Stop after each model reply so the reply can be inspected"),
        ("clear-break-reply", "Disable stop-after model reply breaks"),
        ("break-handoff", "Stop on each tool or agent handoff for inspect"),
        ("clear-break-handoff", "Disable stop-on handoff breaks"),
        ("continue", "Continue a halted run (without editing the stopped value)"),
        ("end", "End the debug session and stop the run"),
        ("status", "Print session state, breaks, and stopped value if any"),
        ("inspect", "Alias for status (shows stopped reply or handoff when held)"),
    ):
        command = sub.add_parser(name, help=help_text)
        _add_connection_flags(command)
    return parser


def _print_response(response: dict) -> None:
    sys.stdout.write(json.dumps(response, sort_keys=True) + "\n")


def _dispatch(op: str, host: str, port: int, token: str, **fields) -> dict:
    return send_command(op, host=host, port=port, token=token, **fields)


def _require_token(token: str | None) -> str | None:
    if token:
        return None
    return "missing --token (or AIDB_CONTROL_TOKEN); copy it from the sample app stderr"


def _command_to_op(command: str) -> tuple[str, dict]:
    if command == "break-reply":
        return "break", _break_fields("model_reply", enabled=True)
    if command == "clear-break-reply":
        return "break", _break_fields("model_reply", enabled=False)
    if command == "break-handoff":
        return "break", _break_fields("handoff", enabled=True)
    if command == "clear-break-handoff":
        return "break", _break_fields("handoff", enabled=False)
    return command, {}


def _attach_loop(host: str, port: int, token: str) -> int:
    sys.stdout.write(
        f"attached to {host}:{port}\n"
        "commands: halt | break-reply | clear-break-reply | break-handoff | "
        "clear-break-handoff | continue (cont/c) | end | status | inspect | quit\n"
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
        if line in {"continue", "cont", "c"}:
            op, fields = "continue", {}
        elif line in {"break-reply", "break"}:
            op, fields = _command_to_op("break-reply")
        elif line in {"clear-break-reply", "clear-break"}:
            op, fields = _command_to_op("clear-break-reply")
        elif line in {"break-handoff"}:
            op, fields = _command_to_op("break-handoff")
        elif line in {"clear-break-handoff"}:
            op, fields = _command_to_op("clear-break-handoff")
        elif line in {"inspect", "status"}:
            op, fields = line, {}
        elif line in {"halt", "end"}:
            op, fields = line, {}
        else:
            sys.stdout.write("unknown command\n")
            continue
        try:
            response = _dispatch(op, host, port, token, **fields)
        except (OSError, ControlClientError) as exc:
            sys.stdout.write(f"error: {exc}\n")
            return 1
        _print_response(response)
        if op == "end":
            return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    missing = _require_token(args.token)
    if missing:
        sys.stdout.write(f"error: {missing}\n")
        return 1

    if args.command == "attach":
        return _attach_loop(args.host, args.port, args.token)

    op, fields = _command_to_op(args.command)

    try:
        response = _dispatch(op, args.host, args.port, args.token, **fields)
    except (OSError, ControlClientError) as exc:
        sys.stdout.write(f"error: {exc}\n")
        return 1
    _print_response(response)
    return 0 if response.get("ok") else 1
