from __future__ import annotations

import threading
import time

from aidb.client import send_command
from aidb.server import start_control_server
from aidb.session import DebugSession
from samples.refund_desk.runtime import RefundDeskRuntime


def test_break_after_model_reply_exposes_reply_until_continue() -> None:
    """AC-B1.1: stop after a model reply, inspect it, run does not continue until resume."""
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
    events: list[str] = []
    stopped = threading.Event()

    def listener(event) -> None:
        events.append(event.kind)
        if event.kind == "model_reply" and event.payload.get("agent") == "intake":
            # Listener runs before gate_after_event waits; poll stop from another thread.
            stopped.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert stopped.wait(timeout=2.0)

    deadline = time.time() + 2.0
    while time.time() < deadline and session.state != "halted":
        time.sleep(0.01)
    assert session.state == "halted"
    stop = session.stop
    assert stop is not None
    assert stop["kind"] == "model_reply"
    assert stop["payload"]["agent"] == "intake"
    assert "headphones" in stop["payload"]["content"].lower() or "ORD-1001" in stop[
        "payload"
    ]["content"]
    time.sleep(0.05)
    assert events.count("model_reply") == 1
    assert "handoff" not in events

    session.set_break("model_reply", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert result_box[0].of_kind("handoff")
    assert result_box[0].ended_by_debug is False


def test_resume_without_edit_keeps_original_reply() -> None:
    """AC-B1.2: resume without editing continues using the original reply."""
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
    held_intake = threading.Event()
    handoff_values: list[dict] = []

    def listener(event) -> None:
        if event.kind == "model_reply" and event.payload.get("agent") == "intake":
            held_intake.set()
        if event.kind == "handoff" and event.payload.get("source") == "intake":
            handoff_values.append(dict(event.payload["value"]))

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert held_intake.wait(timeout=2.0)
    deadline = time.time() + 2.0
    while time.time() < deadline and session.stop is None:
        time.sleep(0.01)
    original = session.stop
    assert original is not None
    original_content = original["payload"]["content"]

    # Resume without editing (TKT-C1 owns edit). Clear sticky break so policy can finish.
    session.set_break("model_reply", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert handoff_values
    # Intake handoff is derived from the original (unedited) reply path.
    assert handoff_values[0]["order_id"] == "ORD-1001"
    intake_replies = [
        e.payload["content"]
        for e in result_box[0].of_kind("model_reply")
        if e.payload.get("agent") == "intake"
    ]
    assert intake_replies == [original_content]


def test_break_reply_over_tcp_status_includes_stop() -> None:
    session = DebugSession()
    server = start_control_server(session, host="127.0.0.1", port=0)
    held = threading.Event()

    def listener(event) -> None:
        if event.kind == "model_reply" and event.payload.get("agent") == "intake":
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
            on="model_reply",
            enabled=True,
        )
        assert armed["ok"] is True
        assert "model_reply" in armed["breaks"]

        thread = threading.Thread(target=run)
        thread.start()
        assert held.wait(timeout=2.0)

        deadline = time.time() + 2.0
        status = None
        while time.time() < deadline:
            status = send_command("status", host=server.host, port=server.port)
            if status.get("state") == "halted" and status.get("stop"):
                break
            time.sleep(0.02)
        assert status is not None
        assert status["state"] == "halted"
        assert status["stop"]["kind"] == "model_reply"
        assert status["stop"]["payload"]["agent"] == "intake"

        inspect = send_command("inspect", host=server.host, port=server.port)
        assert inspect["stop"]["payload"]["content"] == status["stop"]["payload"]["content"]

        send_command(
            "break",
            host=server.host,
            port=server.port,
            on="model_reply",
            enabled=False,
        )
        cont = send_command("continue", host=server.host, port=server.port)
        assert cont["ok"] is True
        assert cont["state"] == "running"
        assert "stop" not in cont
        thread.join(timeout=2.0)
        assert not thread.is_alive()
        assert result_box[0].of_kind("handoff")
    finally:
        server.stop()


def test_control_server_rejects_non_localhost_bind() -> None:
    session = DebugSession()
    try:
        start_control_server(session, host="0.0.0.0", port=0)
        raise AssertionError("expected ValueError for non-localhost bind")
    except ValueError as exc:
        assert "localhost" in str(exc)
