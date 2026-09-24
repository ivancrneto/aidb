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


def test_edit_model_reply_consumed_by_next_step() -> None:
    """AC-C1.1: edit stopped model reply; next step (handoff/policy) uses the edit."""
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
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

    thread = threading.Thread(target=run)
    thread.start()
    assert held.wait(timeout=2.0)
    _wait_halted(session)

    edited = "EDITED_INTAKE_REPLY: customer insists on store credit."
    session.edit(content=edited)
    assert session.stop is not None
    assert session.stop["payload"]["content"] == edited

    session.set_break("model_reply", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    result = result_box[0]
    intake_event = next(
        e for e in result.of_kind("model_reply") if e.payload.get("agent") == "intake"
    )
    assert intake_event.payload["content"] == edited
    handoff = next(
        e for e in result.of_kind("handoff") if e.payload.get("source") == "intake"
    )
    assert handoff.payload["value"]["prior_reply"] == edited
    policy_reply = next(
        e for e in result.of_kind("model_reply") if e.payload.get("agent") == "policy"
    )
    assert edited in policy_reply.payload["content"]


def test_edit_handoff_value_consumed_by_next_step() -> None:
    """AC-C1.2: edit stopped handoff value; tool/agent next step uses the edit."""
    session = DebugSession()
    session.set_break("handoff", enabled=True)
    tools = Toolbelt()
    held_tool = threading.Event()

    def listener(event) -> None:
        if event.kind == "handoff" and event.payload.get("kind") == "tool":
            held_tool.set()

    runtime = RefundDeskRuntime(tools=tools, debug=session, listener=listener)
    result_box: list = []

    def run() -> None:
        result_box.append(
            runtime.run("Please refund ORD-1001. The headphones arrived broken.")
        )

    thread = threading.Thread(target=run)
    thread.start()

    deadline = time.time() + 3.0
    while time.time() < deadline and not held_tool.is_set():
        if session.state == "halted":
            stop = session.stop
            if stop and stop["payload"].get("kind") == "agent":
                # Edit agent handoff reason; policy should consume it.
                if stop["payload"]["source"] == "intake":
                    value = dict(stop["payload"]["value"])
                    value["reason"] = "EDITED_REASON_water_damage"
                    session.edit(value=value)
                session.continue_run()
        time.sleep(0.02)

    assert held_tool.wait(timeout=1.0)
    _wait_halted(session)
    # Edit tool handoff amount before the tool runs.
    stop = session.stop
    assert stop is not None
    value = dict(stop["payload"]["value"])
    value["amount"] = "12.34"
    session.edit(value=value)

    session.set_break("handoff", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    result = result_box[0]
    policy_reply = next(
        e
        for e in result.of_kind("model_reply")
        if e.payload.get("agent") == "policy" and e.payload.get("turn") == 2
    )
    assert "EDITED_REASON_water_damage" in policy_reply.payload["content"]
    assert tools.ledger.issued[0]["amount"] == "12.34"
    tool_event = result.of_kind("tool_result")[0]
    assert tool_event.payload["value"]["amount"] == "12.34"


def test_resume_without_edit_keeps_original_values() -> None:
    """AC-C1.3: leaving the value unchanged continues with the original."""
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
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

    thread = threading.Thread(target=run)
    thread.start()
    assert held.wait(timeout=2.0)
    _wait_halted(session)
    original = session.stop["payload"]["content"]  # type: ignore[index]

    session.set_break("model_reply", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    result = result_box[0]
    intake_event = next(
        e for e in result.of_kind("model_reply") if e.payload.get("agent") == "intake"
    )
    assert intake_event.payload["content"] == original
    handoff = next(
        e for e in result.of_kind("handoff") if e.payload.get("source") == "intake"
    )
    assert handoff.payload["value"]["prior_reply"] == original


def test_edit_over_tcp() -> None:
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
        send_command(
            "break",
            host=server.host,
            port=server.port,
            token=server.token,
            on="model_reply",
            enabled=True,
        )
        thread = threading.Thread(target=run)
        thread.start()
        assert held.wait(timeout=2.0)

        deadline = time.time() + 2.0
        while time.time() < deadline:
            status = send_command(
                "status",
                host=server.host,
                port=server.port,
                token=server.token,
            )
            if status.get("state") == "halted" and status.get("stop"):
                break
            time.sleep(0.02)

        edited = "TCP_EDITED_REPLY"
        edited_resp = send_command(
            "edit",
            host=server.host,
            port=server.port,
            token=server.token,
            content=edited,
        )
        assert edited_resp["ok"] is True
        assert edited_resp["stop"]["payload"]["content"] == edited

        send_command(
            "break",
            host=server.host,
            port=server.port,
            token=server.token,
            on="model_reply",
            enabled=False,
        )
        send_command(
            "continue",
            host=server.host,
            port=server.port,
            token=server.token,
        )
        thread.join(timeout=2.0)
        assert not thread.is_alive()
        handoff = next(
            e
            for e in result_box[0].of_kind("handoff")
            if e.payload.get("source") == "intake"
        )
        assert handoff.payload["value"]["prior_reply"] == edited
    finally:
        server.stop()


def test_redundant_continue_preserves_pending_edit() -> None:
    """A second continue must not clobber a pending edited resume payload."""
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
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

    thread = threading.Thread(target=run)
    thread.start()
    assert held.wait(timeout=2.0)
    _wait_halted(session)

    edited = "PRESERVED_AFTER_DOUBLE_CONTINUE"
    session.edit(content=edited)
    session.set_break("model_reply", enabled=False)
    session.continue_run()
    session.continue_run()  # redundant; must not drop _resume_payload
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    handoff = next(
        e for e in result_box[0].of_kind("handoff") if e.payload.get("source") == "intake"
    )
    assert handoff.payload["value"]["prior_reply"] == edited


def test_edit_rejects_multiple_fields() -> None:
    session = DebugSession()
    session.set_break("model_reply", enabled=True)
    held = threading.Event()

    def listener(event) -> None:
        if event.kind == "model_reply" and event.payload.get("agent") == "intake":
            held.set()

    runtime = RefundDeskRuntime(debug=session, listener=listener)

    def run() -> None:
        runtime.run("Please refund ORD-1001. The headphones arrived broken.")

    thread = threading.Thread(target=run)
    thread.start()
    assert held.wait(timeout=2.0)
    _wait_halted(session)
    try:
        session.edit(content="x", payload={"content": "y", "agent": "intake", "turn": 1})
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "only one" in str(exc)
    session.set_break("model_reply", enabled=False)
    session.continue_run()
    thread.join(timeout=2.0)
    assert not thread.is_alive()
