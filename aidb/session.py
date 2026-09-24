from __future__ import annotations

import threading
from typing import Any, Literal, get_args

SessionState = Literal["running", "halted", "ended"]
BreakKind = Literal["model_reply", "handoff"]

_SUPPORTED_BREAKS: frozenset[str] = frozenset(get_args(BreakKind))


class SessionEnded(Exception):
    """Raised when a halted run is ended instead of continued."""


class DebugSession:
    """In-process halt / continue / end / break / edit control for a live run.

    Call ``gate_before_advance`` before emitting the next model reply or handoff.
    Call ``gate_after_event`` after emitting an event so break-on-reply or
    break-on-handoff can hold with the value available for inspect/edit. While
    halted, those calls block so the run cannot advance. After resume,
    ``gate_after_event`` returns the (possibly edited) payload for the next step.
    """

    def __init__(self) -> None:
        self._continue = threading.Event()
        self._continue.set()
        self._ended = threading.Event()
        self._lock = threading.Lock()
        self._breaks: set[BreakKind] = set()
        self._stop: dict[str, Any] | None = None
        self._resume_payload: dict[str, Any] | None = None

    @property
    def state(self) -> SessionState:
        if self._ended.is_set():
            return "ended"
        if not self._continue.is_set():
            return "halted"
        return "running"

    @property
    def stop(self) -> dict[str, Any] | None:
        """Stopped event snapshot for inspect, or None when not at a break stop."""
        with self._lock:
            if self._stop is None:
                return None
            return {
                "kind": self._stop["kind"],
                "run_id": self._stop["run_id"],
                "payload": dict(self._stop["payload"]),
            }

    @property
    def breaks(self) -> list[BreakKind]:
        with self._lock:
            return sorted(self._breaks)

    def set_break(self, kind: BreakKind | str, *, enabled: bool = True) -> None:
        normalized = str(kind or "").strip().lower()
        if normalized not in _SUPPORTED_BREAKS:
            raise ValueError(f"unsupported break kind: {kind}")
        break_kind: BreakKind = normalized  # type: ignore[assignment]
        with self._lock:
            if enabled:
                self._breaks.add(break_kind)
            else:
                self._breaks.discard(break_kind)

    def halt(self) -> None:
        with self._lock:
            if self._ended.is_set():
                return
            self._continue.clear()

    def continue_run(self) -> None:
        with self._lock:
            if self._ended.is_set():
                return
            # Snapshot only when there is an active stop. A redundant continue
            # must not clobber a pending _resume_payload still awaiting
            # gate_after_event.
            if self._stop is not None:
                self._resume_payload = dict(self._stop["payload"])
                self._stop = None
            self._continue.set()

    def end(self) -> None:
        with self._lock:
            self._ended.set()
            self._stop = None
            self._resume_payload = None
            self._continue.set()

    def edit(
        self,
        *,
        content: str | None = None,
        value: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Update the stopped payload while halted at a break. Resume still required."""
        with self._lock:
            if self._ended.is_set():
                raise ValueError("session ended")
            if self._stop is None or self._continue.is_set():
                raise ValueError("edit requires a halted break stop")
            kind = self._stop["kind"]
            provided = [
                name
                for name, val in (
                    ("payload", payload),
                    ("content", content),
                    ("value", value),
                )
                if val is not None
            ]
            if len(provided) > 1:
                raise ValueError(
                    f"edit accepts only one of content, value, payload (got {provided})"
                )
            if payload is not None:
                if not isinstance(payload, dict):
                    raise ValueError("payload must be an object")
                self._validate_payload_shape(kind, payload)
                self._stop["payload"] = dict(payload)
                return
            current = dict(self._stop["payload"])
            if content is not None:
                if kind != "model_reply":
                    raise ValueError("content edit only applies to model_reply stops")
                current["content"] = str(content)
                self._stop["payload"] = current
                return
            if value is not None:
                if kind != "handoff":
                    raise ValueError("value edit only applies to handoff stops")
                if not isinstance(value, dict):
                    raise ValueError("value must be an object")
                current["value"] = dict(value)
                self._stop["payload"] = current
                return
            raise ValueError("edit requires content, value, or payload")

    @staticmethod
    def _validate_payload_shape(kind: str, payload: dict[str, Any]) -> None:
        if kind == "model_reply":
            if not isinstance(payload.get("content"), str):
                raise ValueError("model_reply payload must include string 'content'")
            return
        if kind == "handoff":
            if not isinstance(payload.get("target"), str) or not payload.get("target"):
                raise ValueError("handoff payload must include non-empty string 'target'")
            if not isinstance(payload.get("value"), dict):
                raise ValueError("handoff payload must include object 'value'")
            return

    def gate_before_advance(self) -> None:
        """Block while halted. Raise SessionEnded if the session was ended."""
        self._continue.wait()
        if self._ended.is_set():
            raise SessionEnded("debug session ended")

    def gate_after_event(
        self,
        kind: BreakKind | str,
        *,
        run_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """If a break is armed for ``kind``, hold after the event for inspect/edit.

        Returns the payload the next step should consume (original or edited).
        The control plane only exposes it over localhost with a shared token.
        """
        normalized = str(kind or "").strip().lower()
        with self._lock:
            if self._ended.is_set():
                return dict(payload)
            if normalized not in self._breaks:
                return dict(payload)
            self._stop = {
                "kind": normalized,
                "run_id": run_id,
                "payload": dict(payload),
            }
            self._continue.clear()
        self._continue.wait()
        if self._ended.is_set():
            raise SessionEnded("debug session ended")
        with self._lock:
            # continue_run always snapshots into _resume_payload before waking us.
            effective = (
                dict(self._resume_payload)
                if self._resume_payload is not None
                else dict(payload)
            )
            self._resume_payload = None
            self._stop = None
        return effective
