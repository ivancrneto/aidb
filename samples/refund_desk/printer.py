from __future__ import annotations

import json
import sys
from typing import TextIO

from samples.refund_desk.events import Event


def print_event(event: Event, *, fmt: str, stream: TextIO | None = None) -> None:
    stream = stream or sys.stdout
    if fmt == "json":
        stream.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        return
    payload = event.payload
    if event.kind == "run_started":
        stream.write(f"[run] started run_id={event.run_id} order={payload['order_id']}\n")
        stream.write(f"  user: {payload['user_message']}\n")
        return
    if event.kind == "model_reply":
        stream.write(f"[model_reply] agent={payload['agent']} turn={payload['turn']}\n")
        stream.write(f"  {payload['content']}\n")
        return
    if event.kind == "handoff":
        stream.write(
            f"[handoff] kind={payload['kind']} from={payload['source']} to={payload['target']}\n"
        )
        stream.write(f"  {json.dumps(payload['value'], sort_keys=True)}\n")
        return
    if event.kind == "tool_result":
        stream.write(f"[tool_result] tool={payload['tool']} mocked={payload['mocked']}\n")
        stream.write(f"  {json.dumps(payload['value'], sort_keys=True)}\n")
        return
    if event.kind == "run_finished":
        stream.write(f"[run] finished run_id={event.run_id}\n")
        return
    stream.write(f"[{event.kind}] {payload}\n")
