from __future__ import annotations

import json
import socket
from typing import Any

_MAX_RESPONSE_BYTES = 64 * 1024


class ControlClientError(Exception):
    """Raised when the control server response cannot be used."""


def send_command(
    op: str,
    *,
    host: str = "127.0.0.1",
    port: int,
    timeout: float = 5.0,
) -> dict[str, Any]:
    payload = (json.dumps({"op": op}) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.sendall(payload)
        buffer = b""
        while b"\n" not in buffer:
            chunk = conn.recv(4096)
            if not chunk:
                raise ConnectionError("control server closed without a response")
            buffer += chunk
            if len(buffer) > _MAX_RESPONSE_BYTES:
                raise ControlClientError("control server response exceeded size limit")
        try:
            line = buffer.split(b"\n", 1)[0].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ControlClientError(
                f"control server returned invalid utf-8: {exc}"
            ) from exc
    try:
        response = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ControlClientError(f"control server returned invalid json: {exc}") from exc
    if not isinstance(response, dict):
        raise ControlClientError("control server returned a non-object response")
    return response
