from __future__ import annotations

import threading
from typing import Literal

SessionState = Literal["running", "halted", "ended"]


class SessionEnded(Exception):
    """Raised when a halted run is ended instead of continued."""


class DebugSession:
    """In-process halt / continue / end control for a live run.

    Call ``gate_before_advance`` before emitting the next model reply or handoff.
    While halted, that call blocks so the run cannot advance.
    """

    def __init__(self) -> None:
        self._continue = threading.Event()
        self._continue.set()
        self._ended = threading.Event()
        self._lock = threading.Lock()

    @property
    def state(self) -> SessionState:
        if self._ended.is_set():
            return "ended"
        if not self._continue.is_set():
            return "halted"
        return "running"

    def halt(self) -> None:
        with self._lock:
            if self._ended.is_set():
                return
            self._continue.clear()

    def continue_run(self) -> None:
        with self._lock:
            if self._ended.is_set():
                return
            self._continue.set()

    def end(self) -> None:
        with self._lock:
            self._ended.set()
            self._continue.set()

    def gate_before_advance(self) -> None:
        """Block while halted. Raise SessionEnded if the session was ended."""
        self._continue.wait()
        if self._ended.is_set():
            raise SessionEnded("debug session ended")
