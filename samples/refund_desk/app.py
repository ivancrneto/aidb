from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from aidb.server import start_control_server
from aidb.session import DebugSession
from samples.refund_desk.printer import print_event
from samples.refund_desk.runtime import RefundDeskRuntime, RunResult

DEFAULT_MESSAGE = "Please refund ORD-1001. The headphones arrived broken."

ORDER_MESSAGES = {
    "ORD-1001": DEFAULT_MESSAGE,
    "ORD-2099": "Please refund ORD-2099. The camera arrived late.",
}


def run_refund_desk(
    user_message: str = DEFAULT_MESSAGE,
    *,
    order_id: str | None = None,
    fmt: str = "text",
    stream=None,
    debug: DebugSession | None = None,
    pace_seconds: float = 0.0,
) -> RunResult:
    runtime = RefundDeskRuntime(
        listener=lambda event: print_event(event, fmt=fmt, stream=stream),
        debug=debug,
        pace_seconds=pace_seconds,
    )
    return runtime.run(user_message, order_id=order_id)


def _tcp_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid port: {value!r}") from exc
    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError(
            f"port must be between 0 and 65535 (got {port})"
        )
    return port


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m samples.refund_desk",
        description=(
            "Run the in-repo refund-desk sample. This is a mocked multi-agent app. "
            "It does not open or require a debugger UI."
        ),
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Customer request for the intake agent",
    )
    parser.add_argument(
        "--order",
        dest="order_id",
        default=None,
        help="Override order id (ORD-1001 approved, ORD-2099 denied)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=("text", "json"),
        default="text",
        help="Event output format (default: text)",
    )
    parser.add_argument(
        "--debug-port",
        type=_tcp_port,
        default=None,
        metavar="PORT",
        help=(
            "Listen for aidb attach on 127.0.0.1:PORT (0 = ephemeral). "
            "Localhost only — safe default for a public repo. "
            "Enables halt / break-reply / continue / end for a live run."
        ),
    )
    parser.add_argument(
        "--pace",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Pause after each model reply or handoff so a debugger can attach (default: 0)",
    )
    return parser


def message_for_args(message: str | None, order_id: str | None) -> str:
    # Only fill a convenience message when --message was omitted. An explicit
    # --message keeps its text even when it matches DEFAULT_MESSAGE.
    if message is not None:
        return message
    if order_id:
        return ORDER_MESSAGES.get(order_id, f"Please refund {order_id}.")
    return DEFAULT_MESSAGE


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    debug: DebugSession | None = None
    stop_server = None
    if args.debug_port is not None:
        debug = DebugSession()
        bound = start_control_server(debug, host="127.0.0.1", port=args.debug_port)
        stop_server = bound.stop
        sys.stderr.write(
            f"[debug] listening on {bound.host}:{bound.port}\n"
            f"[debug] token={bound.token}\n"
            f"[debug] attach with: python -m aidb attach --port {bound.port} "
            f"--token {bound.token}\n"
        )
        sys.stderr.flush()
    try:
        run_refund_desk(
            message_for_args(args.message, args.order_id),
            order_id=args.order_id,
            fmt=args.fmt,
            debug=debug,
            pace_seconds=args.pace,
        )
    finally:
        if stop_server is not None:
            stop_server()
    return 0
