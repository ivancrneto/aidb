from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any, Callable
from uuid import uuid4

from aidb.session import DebugSession, SessionEnded
from samples.refund_desk.agents import IntakeAgent, PolicyAgent, resolve_order
from samples.refund_desk.events import (
    Event,
    Handoff,
    handoff_event,
    model_reply_event,
    run_finished_event,
    tool_result_event,
)
from samples.refund_desk.tools import Toolbelt

Listener = Callable[[Event], None]


@dataclass
class RunResult:
    run_id: str
    events: list[Event] = field(default_factory=list)
    refunds_issued: list[dict[str, str]] = field(default_factory=list)
    ended_by_debug: bool = False

    def of_kind(self, kind: str) -> list[Event]:
        return [event for event in self.events if event.kind == kind]


class RefundDeskRuntime:
    """Runs the sample multi-agent flow. Optional debug session can halt advances."""

    def __init__(
        self,
        *,
        tools: Toolbelt | None = None,
        listener: Listener | None = None,
        debug: DebugSession | None = None,
        pace_seconds: float = 0.0,
    ) -> None:
        self.tools = tools or Toolbelt()
        self.listener = listener
        self.debug = debug
        self.pace_seconds = pace_seconds
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

        try:
            turn = 1
            intake = self.intake.act(turn=turn, user_message=user_message, order=order)
            reply_payload = self._emit_advance(
                result, model_reply_event(run_id, intake.reply)
            )
            if intake.handoff is None:
                raise RuntimeError("intake agent must hand off to policy")

            # Next step after a model reply consumes the (possibly edited) reply.
            prior_reply = _reply_content(reply_payload)
            handoff = _handoff_with_prior_reply(intake.handoff, prior_reply)
            handoff_payload = self._emit_advance(result, handoff_event(run_id, handoff))

            turn = 2
            policy = self.policy.act(
                turn=turn,
                handoff_value=_handoff_value(handoff_payload),
                order=order,
            )
            self._emit_advance(result, model_reply_event(run_id, policy.reply))

            if policy.handoff is not None:
                tool_handoff_payload = self._emit_advance(
                    result, handoff_event(run_id, policy.handoff)
                )
                target, value = _handoff_target_value(tool_handoff_payload)
                tool_result = self.tools.call(target, value)
                self._emit(result, tool_result_event(run_id, tool_result))
                turn = 3
                closing = self.policy.after_tool(turn=turn, tool_value=tool_result.value)
                self._emit_advance(result, model_reply_event(run_id, closing.reply))
        except SessionEnded:
            result.ended_by_debug = True
            self._emit(
                result,
                run_finished_event(
                    run_id,
                    refunds_issued=list(self.tools.ledger.issued),
                    reason="session_ended",
                ),
            )
            result.refunds_issued = list(self.tools.ledger.issued)
            return result

        self._emit(
            result,
            run_finished_event(
                run_id,
                refunds_issued=list(self.tools.ledger.issued),
            ),
        )
        result.refunds_issued = list(self.tools.ledger.issued)
        return result

    def _emit_advance(self, result: RunResult, event: Event) -> dict[str, Any]:
        if self.debug is not None:
            self.debug.gate_before_advance()
        self._emit(result, event)
        effective = dict(event.payload)
        if self.debug is not None:
            effective = self.debug.gate_after_event(
                event.kind,
                run_id=event.run_id,
                payload=event.payload,
            )
            if effective != event.payload:
                result.events[-1] = Event(
                    kind=event.kind,
                    run_id=event.run_id,
                    payload=effective,
                )
        if self.pace_seconds > 0:
            time.sleep(self.pace_seconds)
        return effective

    def _emit(self, result: RunResult, event: Event) -> None:
        result.events.append(event)
        if self.listener is not None:
            self.listener(event)


def _handoff_with_prior_reply(handoff: Handoff, prior_reply: str) -> Handoff:
    return replace(
        handoff,
        value={**handoff.value, "prior_reply": prior_reply},
    )


def _reply_content(payload: dict[str, Any]) -> str:
    content = payload.get("content", "")
    if not isinstance(content, str):
        raise ValueError("model_reply payload must include string 'content'")
    return content


def _handoff_value(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("value", {})
    if not isinstance(value, dict):
        raise ValueError("handoff payload must include object 'value'")
    return dict(value)


def _handoff_target_value(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    target = payload.get("target", "")
    value = payload.get("value", {})
    if not isinstance(target, str) or not target:
        raise ValueError("handoff payload must include non-empty string 'target'")
    if not isinstance(value, dict):
        raise ValueError("handoff payload must include object 'value'")
    return target, dict(value)
