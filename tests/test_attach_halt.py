from __future__ import annotations

import threading
import time

from aidb.client import send_command
from aidb.server import start_control_server
from aidb.session import DebugSession
from samples.refund_desk.runtime import RefundDeskRuntime


def test_halt_blocks_next_model_reply_until_continue() -> None:
    session = DebugSession()
    events: list[str] = []
    barrier = threading.Event()

    def listener(event) -> None:
        events.append(event.kind)
        if event.kind == "run_started":
            session.halt()
            barrier.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert barrier.wait(timeout=2.0)
    time.sleep(0.1)
    assert "model_reply" not in events
    assert session.state == "halted"

    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert "model_reply" in events
    assert "handoff" in events
    assert result_box[0].of_kind("model_reply")
    assert result_box[0].ended_by_debug is False


def test_end_while_halted_stops_before_next_advance() -> None:
    session = DebugSession()
    events: list[str] = []
    halted = threading.Event()

    def listener(event) -> None:
        events.append(event.kind)
        if event.kind == "model_reply" and event.payload.get("agent") == "intake":
            session.halt()
            halted.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert halted.wait(timeout=2.0)
    time.sleep(0.1)
    assert events.count("model_reply") == 1
    assert "handoff" not in events

    session.end()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    result = result_box[0]
    assert result.ended_by_debug is True
    assert events.count("model_reply") == 1
    assert "handoff" not in events
    assert result.of_kind("run_finished")[-1].payload["reason"] == "session_ended"


def test_attach_over_tcp_halt_and_continue() -> None:
    session = DebugSession()
    server = start_control_server(session, host="127.0.0.1", port=0)
    events: list[str] = []
    halted = threading.Event()

    def listener(event) -> None:
        events.append(event.kind)
        if event.kind == "run_started":
            # Halt before this listener returns so the next advance gate blocks.
            response = send_command(
                "halt",
                host=server.host,
                port=server.port,
                token=server.token,
            )
            assert response["ok"] is True
            assert response["state"] == "halted"
            halted.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    try:
        thread = threading.Thread(target=run)
        thread.start()
        assert halted.wait(timeout=2.0)
        time.sleep(0.1)
        assert "model_reply" not in events

        status = send_command(
            "status",
            host=server.host,
            port=server.port,
            token=server.token,
        )
        assert status["state"] == "halted"

        cont = send_command(
            "continue",
            host=server.host,
            port=server.port,
            token=server.token,
        )
        assert cont["ok"] is True
        assert cont["state"] == "running"
        thread.join(timeout=2.0)
        assert not thread.is_alive()
        assert result_box[0].of_kind("handoff")
    finally:
        server.stop()


def test_control_requires_token() -> None:
    session = DebugSession()
    server = start_control_server(session, host="127.0.0.1", port=0)
    try:
        denied = send_command("status", host=server.host, port=server.port)
        assert denied["ok"] is False
        assert "token" in denied["error"]
        ok = send_command(
            "status",
            host=server.host,
            port=server.port,
            token=server.token,
        )
        assert ok["ok"] is True
    finally:
        server.stop()
