from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

from samples.refund_desk.agents import IntakeAgent, PolicyAgent, resolve_order
from samples.refund_desk.events import Event, handoff_event, model_reply_event, tool_result_event
from samples.refund_desk.tools import Toolbelt

Listener = Callable[[Event], None]


@dataclass
class RunResult:
    run_id: str
    events: list[Event] = field(default_factory=list)
    refunds_issued: list[dict[str, str]] = field(default_factory=list)

    def of_kind(self, kind: str) -> list[Event]:
        return [event for event in self.events if event.kind == kind]


class RefundDeskRuntime:
    """Runs the sample multi-agent flow. Emits reply and handoff events; does not halt."""

    def __init__(
        self,
        *,
        tools: Toolbelt | None = None,
        listener: Listener | None = None,
    ) -> None:
        self.tools = tools or Toolbelt()
        self.listener = listener
        self.intake = IntakeAgent()
        self.policy = PolicyAgent()

    def run(
        self,
        user_message: str,
        *,
        order_id: str | None = None,
        run_id: str | None = None,
    ) -> RunResult:
        run_id = run_id or uuid4().hex[:12]
        result = RunResult(run_id=run_id)
        order = resolve_order(user_message, order_id)

        self._emit(
            result,
            Event(
                kind="run_started",
                run_id=run_id,
                payload={"user_message": user_message, "order_id": order.order_id},
            ),
        )

        turn = 1
        intake = self.intake.act(turn=turn, user_message=user_message, order=order)
        self._emit(result, model_reply_event(run_id, intake.reply))
        if intake.handoff is None:
            raise RuntimeError("intake agent must hand off to policy")
        self._emit(result, handoff_event(run_id, intake.handoff))

        turn = 2
        policy = self.policy.act(turn=turn, handoff_value=intake.handoff.value, order=order)
        self._emit(result, model_reply_event(run_id, policy.reply))

        if policy.handoff is not None:
            self._emit(result, handoff_event(run_id, policy.handoff))
            tool_result = self.tools.call(policy.handoff.target, policy.handoff.value)
            self._emit(result, tool_result_event(run_id, tool_result))
            turn = 3
            closing = self.policy.after_tool(turn=turn, tool_value=tool_result.value)
            self._emit(result, model_reply_event(run_id, closing.reply))

        self._emit(
            result,
            Event(
                kind="run_finished",
                run_id=run_id,
                payload={"refunds_issued": list(self.tools.ledger.issued)},
            ),
        )
        result.refunds_issued = list(self.tools.ledger.issued)
        return result

    def _emit(self, result: RunResult, event: Event) -> None:
        result.events.append(event)
        if self.listener is not None:
            self.listener(event)
