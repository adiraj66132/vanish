"""Paths, persisted settings and logging shared by the CLI and desktop shell."""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

APP_NAME = "VanishCam"
__version__ = "2.0.0"

_DEFAULTS = {
    "mode": None,
    "camera": None,
    "width": None,
    "height": None,
    "fps": 30.0,
    "mirror": True,
    "virtual_camera": "auto",
    "virtual_backend": None,
    "virtual_device": None,
    "goku_delay": 3.0,
    "fullscreen": False,
    "gesture_debug": False,
}


def _base(env_name: str, fallback: Path, xdg_name: str | None = None) -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get(env_name, fallback))
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get(xdg_name or env_name, fallback))


def data_dir() -> Path:
    """Writable home for downloaded models and other app data."""
    return _base("LOCALAPPDATA", Path.home() / ".local" / "share",
                 "XDG_DATA_HOME") / APP_NAME


def config_dir() -> Path:
    return _base("APPDATA", Path.home() / ".config", "XDG_CONFIG_HOME") / APP_NAME


def log_dir() -> Path:
    return data_dir() / "logs"


def settings_path() -> Path:
    return config_dir() / "settings.json"


def model_dir() -> Path:
    return data_dir() / "models"


def model_path(name: str) -> Path:
    """Bundled models win; downloaded ones live in the user data directory."""
    bundled = getattr(sys, "_MEIPASS", None)
    roots = [Path(bundled)] if bundled else [Path(__file__).resolve().parent]
    for root in roots:
        for candidate in (root / "models" / name, root / name):
            if candidate.is_file():
                return candidate
    return model_dir() / name


@dataclass
class AppConfig:
    mode: str | None = None
    camera: int | None = None
    width: int | None = None
    height: int | None = None
    fps: float = 30.0
    mirror: bool = True
    virtual_camera: str = "auto"  # auto | on | off
    virtual_backend: str | None = None
    virtual_device: str | None = None
    goku_delay: float = 3.0
    fullscreen: bool = False
    gesture_debug: bool = False

    def to_args(self) -> argparse.Namespace:
        return argparse.Namespace(
            mode=self.mode,
            camera=self.camera,
            width=self.width,
            height=self.height,
            fps=self.fps,
            fullscreen=self.fullscreen,
            no_mirror=not self.mirror,
            gesture_debug=self.gesture_debug,
            virtual_camera={"on": True, "off": False, "auto": None}[self.virtual_camera],
            virtual_backend=self.virtual_backend,
            virtual_device=self.virtual_device,
            goku_delay=self.goku_delay,
            self_test=False,
        )

    @classmethod
    def load(cls) -> "AppConfig":
        try:
            raw = json.loads(settings_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        allowed = {field.name for field in fields(cls)}
        values = {key: value for key, value in raw.items() if key in allowed}
        for key, default in _DEFAULTS.items():
            if key not in values or not _valid(key, values[key]):
                values[key] = default
        return cls(**values)

    def save(self) -> None:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


_NULLABLE = {
    "mode": str, "camera": int, "width": int, "height": int,
    "virtual_backend": str, "virtual_device": str,
}


def _valid(key: str, value: object) -> bool:
    if key in _NULLABLE:
        if value is None:
            return True
        expected = _NULLABLE[key]
        if expected is int:
            return isinstance(value, int) and not isinstance(value, bool) and value >= 0
        return isinstance(value, str) and bool(value)
    if key in ("fps", "goku_delay"):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    if key in ("mirror", "fullscreen", "gesture_debug"):
        return isinstance(value, bool)
    if key == "virtual_camera":
        return value in ("auto", "on", "off")
    return False


class _LogWriter:
    """Send lost stdout/stderr (windowed builds) to the log file."""

    def __init__(self, level: int):
        self.level = level

    def write(self, text: str) -> None:
        text = text.strip()
        if text and not (text.isdigit() and "\r" not in text):
            logging.log(self.level, "%s", text)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False


def setup_logging() -> None:
    if getattr(logging, "_vanishcam_handler", None) is not None:
        return
    directory = log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        directory / "vanishcam.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging._vanishcam_handler = handler
    if sys.stdout is None:
        sys.stdout = _LogWriter(logging.INFO)
    if sys.stderr is None:
        sys.stderr = _LogWriter(logging.ERROR)
