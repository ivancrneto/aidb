from __future__ import annotations

import hmac
import json
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable

from aidb.session import DebugSession

_MAX_REQUEST_BYTES = 64 * 1024


@dataclass(frozen=True)
class BoundServer:
    host: str
    port: int
    token: str
    stop: Callable[[], None]


def _status_payload(session: DebugSession) -> dict:
    payload: dict = {
        "ok": True,
        "state": session.state,
        "breaks": session.breaks,
    }
    stop = session.stop
    if stop is not None:
        payload["stop"] = stop
    return payload


def handle_command(
    session: DebugSession,
    request: dict,
    *,
    token: str,
) -> dict:
    provided = request.get("token")
    if not isinstance(provided, str) or not hmac.compare_digest(provided, token):
        return {
            "ok": False,
            "error": "unauthorized: missing or invalid token",
            "state": session.state,
        }

    op = str(request.get("op") or "").strip().lower()
    if op == "halt":
        session.halt()
    elif op in {"continue", "cont"}:
        session.continue_run()
    elif op == "end":
        session.end()
    elif op in {"status", "inspect"}:
        return _status_payload(session)
    elif op == "break":
        on = str(request.get("on") or "").strip().lower()
        enabled = request.get("enabled", True)
        if isinstance(enabled, str):
            enabled = enabled.strip().lower() not in {"0", "false", "no", "off"}
        else:
            enabled = bool(enabled)
        try:
            session.set_break(on, enabled=enabled)
        except ValueError as exc:
            return {"ok": False, "error": str(exc), "state": session.state}
    else:
        return {"ok": False, "error": f"unknown op: {op}", "state": session.state}
    return _status_payload(session)


def start_control_server(
    session: DebugSession,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    token: str | None = None,
) -> BoundServer:
    """Serve JSON-line control commands on a localhost TCP port.

    Requires a shared ``token`` on every request so model-reply payloads returned
    by status/inspect are not readable by an unauthenticated local client.
    """
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("debug control server must bind to localhost only")

    control_token = token if token is not None else secrets.token_urlsafe(18)
    if not control_token:
        raise ValueError("control token must be non-empty")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(8)
    sock.settimeout(0.5)
    bound_host, bound_port = sock.getsockname()[:2]

    stop_flag = threading.Event()

    def serve() -> None:
        while not stop_flag.is_set():
            try:
                conn, _addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                # stop() sets the flag before closing the socket; other accept
                # failures should not permanently disable the control plane.
                if stop_flag.is_set():
                    break
                time.sleep(0.5)
                continue
            with conn:
                conn.settimeout(5.0)
                buffer = b""
                while not stop_flag.is_set():
                    try:
                        chunk = conn.recv(4096)
                    except socket.timeout:
                        break
                    except OSError:
                        break
                    if not chunk:
                        break
                    buffer += chunk
                    if len(buffer) > _MAX_REQUEST_BYTES:
                        response = {
                            "ok": False,
                            "error": "request exceeded size limit",
                            "state": session.state,
                        }
                        try:
                            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                        except OSError:
                            pass
                        break
                    while b"\n" in buffer:
                        raw, buffer = buffer.split(b"\n", 1)
                        try:
                            line = raw.decode("utf-8").strip()
                        except UnicodeDecodeError:
                            response = {
                                "ok": False,
                                "error": "invalid utf-8",
                                "state": session.state,
                            }
                            try:
                                conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                            except OSError:
                                break
                            continue
                        if not line:
                            continue
                        try:
                            request = json.loads(line)
                        except json.JSONDecodeError:
                            response = {
                                "ok": False,
                                "error": "invalid json",
                                "state": session.state,
                            }
                        else:
                            if not isinstance(request, dict):
                                response = {
                                    "ok": False,
                                    "error": "request must be an object",
                                    "state": session.state,
                                }
                            else:
                                response = handle_command(
                                    session, request, token=control_token
                                )
                        try:
                            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                        except OSError:
                            break

    thread = threading.Thread(target=serve, name="aidb-control-server", daemon=True)
    thread.start()

    def stop() -> None:
        stop_flag.set()
        try:
            sock.close()
        except OSError:
            pass
        thread.join(timeout=6.0)

    return BoundServer(
        host=bound_host,
        port=int(bound_port),
        token=control_token,
        stop=stop,
    )
