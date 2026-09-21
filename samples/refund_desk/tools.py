from __future__ import annotations

from typing import Any

from samples.refund_desk.events import ToolResult


class MockRefundLedger:
    """In-memory refund store. Side effects stay mocked; nothing leaves process."""

    def __init__(self) -> None:
        self.issued: list[dict[str, str]] = []

    def issue_refund(self, *, order_id: str, amount: str) -> ToolResult:
        refund_id = f"RF-{len(self.issued) + 1:04d}"
        record = {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": amount,
            "status": "recorded",
        }
        self.issued.append(record)
        return ToolResult(
            tool="issue_refund",
            mocked=True,
            value=record,
        )


class Toolbelt:
    def __init__(self, ledger: MockRefundLedger | None = None) -> None:
        self.ledger = ledger or MockRefundLedger()

    def call(self, name: str, value: dict[str, Any]) -> ToolResult:
        if name != "issue_refund":
            raise KeyError(f"unknown mocked tool: {name}")
        return self.ledger.issue_refund(
            order_id=value["order_id"],
            amount=value["amount"],
        )
