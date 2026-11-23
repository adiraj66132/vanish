"""Run the webcam pipeline on a worker thread and expose its latest state."""

from __future__ import annotations

import queue
import threading
from contextlib import ExitStack

from vanish_cam import run_camera


class CameraEngine:
    """The Qt shell polls :meth:`snapshot` on a timer; no Qt calls leave that thread."""

    def __init__(self, args, mode: str, license_session=None):
        self.args = args
        self.mode = mode
        self.license_session = license_session
        self._commands: queue.SimpleQueue[str] = queue.SimpleQueue()
        self._lock = threading.Lock()
        self._frame = None
        self._status = "Starting..."
        self._calibration = (False, 0)
        self._error = None
        self._finished = False
        self._thread = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="vanishcam-engine", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            with ExitStack() as resources:
                run_camera(
                    self.args, resources, self.mode, self.license_session,
                    on_frame=self._publish,
                    on_status=self._status_message,
                    on_calibration=self._calibration_message,
                    poll_command=self._poll_command,
                    on_fullscreen=lambda enabled: None,
                )
        except BaseException as error:  # surfaced to the UI thread via snapshot()
            with self._lock:
                self._error = error
        finally:
            with self._lock:
                self._finished = True

    def _publish(self, frame) -> None:
        with self._lock:
            self._frame = frame

    def _status_message(self, message: str) -> None:
        with self._lock:
            self._status = message

    def _calibration_message(self, active: bool, remaining: int) -> None:
        with self._lock:
            self._calibration = (bool(active), int(remaining))

    def calibration(self) -> tuple[bool, int]:
        """Return (is_calibrating, seconds_remaining) for the preview overlay."""
        with self._lock:
            return self._calibration

    def _poll_command(self):
        try:
            return self._commands.get_nowait()
        except queue.Empty:
            return None

    def command(self, name: str) -> None:
        if name in ("quit", "recapture", "reappear", "vanish", "fullscreen"):
            self._commands.put(name)

    def stop(self) -> None:
        self.command("quit")

    def join(self, timeout: float = 5.0) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def snapshot(self):
        """Return (frame, status, error, finished) for the UI timer."""
        with self._lock:
            return self._frame, self._status, self._error, self._finished
