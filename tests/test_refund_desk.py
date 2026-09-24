from __future__ import annotations

import io
import json
import socket
import sys
from pathlib import Path

import pytest

from samples.refund_desk.app import main, run_refund_desk
from samples.refund_desk.runtime import RefundDeskRuntime
from samples.refund_desk.tools import Toolbelt


ROOT = Path(__file__).resolve().parents[1]


def test_happy_path_emits_model_reply_and_handoff() -> None:
    result = RefundDeskRuntime().run(
        "Please refund ORD-1001. The headphones arrived broken."
    )

    replies = result.of_kind("model_reply")
    handoffs = result.of_kind("handoff")

    assert replies, "expected at least one model reply"
    assert handoffs, "expected at least one handoff"
    assert replies[0].payload["agent"] == "intake"
    assert handoffs[0].payload == {
        "kind": "agent",
        "source": "intake",
        "target": "policy",
        "value": {
            "order_id": "ORD-1001",
            "item": "headphones",
            "reason": "damaged",
            "user_message": "Please refund ORD-1001. The headphones arrived broken.",
            "prior_reply": replies[0].payload["content"],
        },
    }
    assert any(event.payload["kind"] == "tool" for event in handoffs)
    assert result.refunds_issued == [
        {
            "refund_id": "RF-0001",
            "order_id": "ORD-1001",
            "amount": "89.00",
            "status": "recorded",
        }
    ]
    assert result.of_kind("tool_result")[0].payload["mocked"] is True


def test_denied_order_has_reply_and_agent_handoff_without_tool() -> None:
    result = RefundDeskRuntime().run("Refund ORD-2099, it arrived late.")

    assert result.of_kind("model_reply")
    assert result.of_kind("handoff")[0].payload["kind"] == "agent"
    assert all(event.payload["kind"] != "tool" for event in result.of_kind("handoff"))
    assert result.refunds_issued == []
    assert "Refund denied" in result.of_kind("model_reply")[-1].payload["content"]


def test_issue_refund_stays_in_process_ledger() -> None:
    tools = Toolbelt()
    result = RefundDeskRuntime(tools=tools).run(
        "Please refund ORD-1001. The headphones arrived broken."
    )

    assert tools.ledger.issued == result.refunds_issued
    assert len(tools.ledger.issued) == 1


def test_cli_prints_reply_and_handoff_without_debugger_ui() -> None:
    buffer = io.StringIO()
    result = run_refund_desk(stream=buffer)
    output = buffer.getvalue()

    assert "[model_reply]" in output
    assert "[handoff]" in output
    assert "debugger" not in output.lower()
    assert result.of_kind("model_reply")
    assert result.of_kind("handoff")


def test_order_flag_uses_matching_default_message(monkeypatch: pytest.MonkeyPatch) -> None:
    printed = io.StringIO()
    monkeypatch.setattr(sys, "stdout", printed)

    assert main(["--order", "ORD-2099"]) == 0
    output = printed.getvalue()
    assert "order=ORD-2099" in output
    assert "Please refund ORD-2099. The camera arrived late." in output
    assert "ORD-1001" not in output
    assert "[model_reply]" in output
    assert "[handoff]" in output


def test_explicit_message_keeps_text_when_order_also_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    printed = io.StringIO()
    monkeypatch.setattr(sys, "stdout", printed)
    explicit = "Please refund ORD-1001. The headphones arrived broken."

    assert main(["--order", "ORD-2099", "--message", explicit]) == 0
    output = printed.getvalue()
    assert explicit in output
    assert "The camera arrived late." not in output


def test_main_exits_zero_and_does_not_bind_a_port(monkeypatch: pytest.MonkeyPatch) -> None:
    printed = io.StringIO()
    monkeypatch.setattr(sys, "stdout", printed)

    def refuse_bind(*_args, **_kwargs):
        raise AssertionError("sample app must not bind a port or open a debugger UI")

    monkeypatch.setattr(socket.socket, "bind", refuse_bind)
    monkeypatch.delitem(sys.modules, "webbrowser", raising=False)

    assert main([]) == 0
    assert "[model_reply]" in printed.getvalue()
    assert "[handoff]" in printed.getvalue()
    assert "webbrowser" not in sys.modules


def test_json_format_is_one_event_per_line() -> None:
    buffer = io.StringIO()
    run_refund_desk(fmt="json", stream=buffer)
    rows = [json.loads(line) for line in buffer.getvalue().splitlines()]
    kinds = [row["kind"] for row in rows]
    assert "model_reply" in kinds
    assert "handoff" in kinds


def test_sample_tree_has_no_debugger_ui_package() -> None:
    sample_root = ROOT / "samples" / "refund_desk"
    ui_markers = ("flask", "fastapi", "streamlit", "webbrowser", "http.server")
    for path in sample_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for marker in ui_markers:
            assert marker not in text, f"{path} should not reference {marker}"
