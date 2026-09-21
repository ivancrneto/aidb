from __future__ import annotations

import argparse
from collections.abc import Sequence

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
) -> RunResult:
    runtime = RefundDeskRuntime(
        listener=lambda event: print_event(event, fmt=fmt, stream=stream),
    )
    return runtime.run(user_message, order_id=order_id)


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
    run_refund_desk(
        message_for_args(args.message, args.order_id),
        order_id=args.order_id,
        fmt=args.fmt,
    )
    return 0
