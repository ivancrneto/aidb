from __future__ import annotations

import threading
import time

from aidb.client import send_command
from aidb.server import start_control_server
from aidb.session import DebugSession
from samples.refund_desk.runtime import RefundDeskRuntime
from samples.refund_desk.tools import Toolbelt


def _wait_halted(session: DebugSession, *, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline and session.state != "halted":
        time.sleep(0.01)
    assert session.state == "halted"


def test_break_on_agent_handoff_exposes_value_until_continue() -> None:
    """AC-B2.1: stop on agent handoff, inspect value, continue."""
    session = DebugSession()
    session.set_break("handoff", enabled=True)
    events: list[str] = []
    held = threading.Event()

    def listener(event) -> None:
        events.append(event.kind)
        if (
            event.kind == "handoff"
            and event.payload.get("kind") == "agent"
            and event.payload.get("source") == "intake"
        ):
            held.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert held.wait(timeout=2.0)
    _wait_halted(session)

    stop = session.stop
    assert stop is not None
    assert stop["kind"] == "handoff"
    assert stop["payload"]["kind"] == "agent"
    assert stop["payload"]["target"] == "policy"
    assert stop["payload"]["value"]["order_id"] == "ORD-1001"
    time.sleep(0.05)
    # Nested policy agent has not proceeded yet.
    assert events.count("model_reply") == 1
    assert events.count("handoff") == 1
    assert "tool_result" not in events

    session.set_break("handoff", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert result_box[0].of_kind("tool_result")
    assert result_box[0].ended_by_debug is False


def test_break_on_tool_handoff_blocks_tool_until_continue() -> None:
    """AC-B2.2: while held at a tool handoff, the tool does not proceed."""
    session = DebugSession()
    session.set_break("handoff", enabled=True)
    tools = Toolbelt()
    held_tool = threading.Event()

    def listener(event) -> None:
        if (
            event.kind == "handoff"
            and event.payload.get("kind") == "tool"
            and event.payload.get("target") == "issue_refund"
        ):
            held_tool.set()

    runtime = RefundDeskRuntime(tools=tools, debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()

    # Sticky break hits the agent handoff first; resume until the tool handoff.
    deadline = time.time() + 3.0
    while time.time() < deadline and not held_tool.is_set():
        if session.state == "halted":
            stop = session.stop
            if stop and stop["payload"].get("kind") == "agent":
                session.continue_run()
        time.sleep(0.02)

    assert held_tool.wait(timeout=1.0)
    _wait_halted(session)
    stop = session.stop
    assert stop is not None
    assert stop["payload"]["kind"] == "tool"
    assert stop["payload"]["value"]["order_id"] == "ORD-1001"
    assert len(tools.ledger.issued) == 0
    time.sleep(0.05)
    assert len(tools.ledger.issued) == 0

    session.set_break("handoff", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert len(tools.ledger.issued) == 1
    assert result_box[0].of_kind("tool_result")


def test_break_handoff_over_tcp_status_includes_stop() -> None:
    session = DebugSession()
    server = start_control_server(session, host="127.0.0.1", port=0)
    held = threading.Event()

    def listener(event) -> None:
        if event.kind == "handoff" and event.payload.get("source") == "intake":
            held.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    try:
        armed = send_command(
            "break",
            host=server.host,
            port=server.port,
            token=server.token,
            on="handoff",
            enabled=True,
        )
        assert armed["ok"] is True
        assert "handoff" in armed["breaks"]

        thread = threading.Thread(target=run)
        thread.start()
        assert held.wait(timeout=2.0)

        deadline = time.time() + 2.0
        status = None
        while time.time() < deadline:
            status = send_command(
                "status",
                host=server.host,
                port=server.port,
                token=server.token,
            )
            if (
                status.get("state") == "halted"
                and status.get("stop", {}).get("kind") == "handoff"
            ):
                break
            time.sleep(0.02)
        assert status is not None
        assert status["stop"]["payload"]["target"] == "policy"

        send_command(
            "break",
            host=server.host,
            port=server.port,
            token=server.token,
            on="handoff",
            enabled=False,
        )
        cont = send_command(
            "continue",
            host=server.host,
            port=server.port,
            token=server.token,
        )
        assert cont["ok"] is True
        thread.join(timeout=2.0)
        assert not thread.is_alive()
        assert result_box[0].of_kind("handoff")
    finally:
        server.stop()
