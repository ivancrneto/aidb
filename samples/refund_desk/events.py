from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

EventKind = Literal["run_started", "model_reply", "handoff", "tool_result", "run_finished"]
HandoffKind = Literal["agent", "tool"]


@dataclass(frozen=True)
class ModelReply:
    agent: str
    content: str
    turn: int


@dataclass(frozen=True)
class Handoff:
    kind: HandoffKind
    source: str
    target: str
    value: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    tool: str
    mocked: bool
    value: dict[str, Any]


@dataclass(frozen=True)
class Event:
    kind: EventKind
    run_id: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "run_id": self.run_id, "payload": self.payload}


def model_reply_event(run_id: str, reply: ModelReply) -> Event:
    return Event(kind="model_reply", run_id=run_id, payload=asdict(reply))


def handoff_event(run_id: str, handoff: Handoff) -> Event:
    return Event(kind="handoff", run_id=run_id, payload=asdict(handoff))


def tool_result_event(run_id: str, result: ToolResult) -> Event:
    return Event(kind="tool_result", run_id=run_id, payload=asdict(result))


def run_finished_event(
    run_id: str,
    *,
    refunds_issued: list[Any],
    reason: str | None = None,
) -> Event:
    payload: dict[str, Any] = {"refunds_issued": refunds_issued}
    if reason is not None:
        payload["reason"] = reason
    return Event(kind="run_finished", run_id=run_id, payload=payload)
