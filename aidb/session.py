from __future__ import annotations

import threading
from typing import Any, Literal, get_args

SessionState = Literal["running", "halted", "ended"]
BreakKind = Literal["model_reply", "handoff"]

_SUPPORTED_BREAKS: frozenset[str] = frozenset(get_args(BreakKind))


class SessionEnded(Exception):
    """Raised when a halted run is ended instead of continued."""


class DebugSession:
    """In-process halt / continue / end / break control for a live run.

    Call ``gate_before_advance`` before emitting the next model reply or handoff.
    Call ``gate_after_event`` after emitting an event so break-on-reply or
    break-on-handoff can hold with the value available for inspect. While
    halted, those calls block so the run cannot advance.
    """

    def __init__(self) -> None:
        self._continue = threading.Event()
        self._continue.set()
        self._ended = threading.Event()
        self._lock = threading.Lock()
        self._breaks: set[BreakKind] = set()
        self._stop: dict[str, Any] | None = None

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
            self._stop = None
            self._continue.set()

    def end(self) -> None:
        with self._lock:
            self._ended.set()
            self._stop = None
            self._continue.set()

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
    ) -> None:
        """If a break is armed for ``kind``, hold after the event for inspect.

        Payload (model reply or handoff value) is retained in-process for inspect.
        The control plane only exposes it over localhost with a shared token.
        """
        normalized = str(kind or "").strip().lower()
        with self._lock:
            if self._ended.is_set():
                return
            if normalized not in self._breaks:
                return
            self._stop = {
                "kind": normalized,
                "run_id": run_id,
                "payload": dict(payload),
            }
            self._continue.clear()
        self._continue.wait()
        if self._ended.is_set():
            raise SessionEnded("debug session ended")
