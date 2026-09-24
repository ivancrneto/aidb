from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from samples.refund_desk.catalog import DEFAULT_ORDER_ID, DEFAULT_ORDERS, Order
from samples.refund_desk.events import Handoff, ModelReply


@dataclass(frozen=True)
class Decision:
    reply: ModelReply
    handoff: Handoff | None


class IntakeAgent:
    name = "intake"

    def act(self, *, turn: int, user_message: str, order: Order) -> Decision:
        content = (
            f"Customer asked: {user_message.strip()} "
            f"I extracted {order.order_id} ({order.item}). "
            "Handing this to the policy agent."
        )
        return Decision(
            reply=ModelReply(agent=self.name, content=content, turn=turn),
            handoff=Handoff(
                kind="agent",
                source=self.name,
                target="policy",
                value={
                    "order_id": order.order_id,
                    "item": order.item,
                    "reason": _reason_from_message(user_message),
                    "user_message": user_message,
                },
            ),
        )


class PolicyAgent:
    name = "policy"

    def act(self, *, turn: int, handoff_value: dict[str, Any], order: Order) -> Decision:
        reason = str(handoff_value.get("reason") or "unspecified")
        prior = handoff_value.get("prior_reply")
        prior_bit = f" Prior reply: {prior}." if prior else ""
        if order.within_window:
            content = (
                f"{order.order_id} is {order.age_days} days old and the item is {order.item}. "
                f"Reason: {reason}.{prior_bit} Policy allows a full refund of ${order.amount}. "
                "I will hand this to the issue_refund tool."
            )
            return Decision(
                reply=ModelReply(agent=self.name, content=content, turn=turn),
                handoff=Handoff(
                    kind="tool",
                    source=self.name,
                    target="issue_refund",
                    value={"order_id": order.order_id, "amount": order.amount},
                ),
            )
        content = (
            f"{order.order_id} is {order.age_days} days old, outside the "
            f"{order.window_days}-day window. Reason: {reason}.{prior_bit} Refund denied."
        )
        return Decision(
            reply=ModelReply(agent=self.name, content=content, turn=turn),
            handoff=None,
        )

    def after_tool(self, *, turn: int, tool_value: dict[str, Any]) -> Decision:
        content = (
            f"Refund {tool_value['refund_id']} for ${tool_value['amount']} "
            f"on {tool_value['order_id']} is recorded. Side effects were mocked."
        )
        return Decision(
            reply=ModelReply(agent=self.name, content=content, turn=turn),
            handoff=None,
        )


def resolve_order(user_message: str, order_id: str | None) -> Order:
    chosen = order_id or _order_id_from_message(user_message) or DEFAULT_ORDER_ID
    try:
        return DEFAULT_ORDERS[chosen]
    except KeyError as exc:
        raise ValueError(f"unknown order: {chosen}") from exc


def _order_id_from_message(message: str) -> str | None:
    token = message.upper()
    for order_id in DEFAULT_ORDERS:
        if order_id in token:
            return order_id
    return None


def _reason_from_message(message: str) -> str:
    lowered = message.lower()
    if "broken" in lowered or "damaged" in lowered:
        return "damaged"
    if "late" in lowered:
        return "late_delivery"
    return "customer_request"
