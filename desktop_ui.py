"""Native Qt shell for VanishCam: launcher, camera preview and live effects window."""

from __future__ import annotations

import contextlib
import os
import queue
import sys
import threading

import cv2
import numpy as np
from PySide6.QtCore import QLoggingCategory, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from app_config import APP_NAME, __version__, setup_logging
from camera_engine import CameraEngine
from vanish_cam import CAMERA_RESOLUTIONS, open_camera

EFFECTS = (
    ("normal", "Normal Vanish", "V sign / dissolve"),
    ("naruto", "Naruto Vanish", "Hands together / log and smoke"),
    ("particles", "Particles", "V sign / windblown particles"),
    ("goku", "Goku", "Two fingers to forehead / custom delay"),
    ("itachi", "Itachi Uchiha", "Hands at chest / crow swarm"),
    ("infinity", "Infinity Gauntlet", "Snap your fingers / cosmic dust"),
)
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vanish_icon.ico")
WINDOW_TITLE = "Webcam Preview"  # OBS Window Capture setups depend on this exact name.


def _app_icon() -> QIcon:
    return QIcon(ICON_PATH) if os.path.isfile(ICON_PATH) else QIcon()


def _bgr_to_pixmap(frame: np.ndarray, label_size=None):
    if frame is None:
        return None
    frame = np.ascontiguousarray(frame)
    height, width = frame.shape[:2]
    image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888)
    return image if not image.isNull() else None


class CameraPreview:
    """Opens the selected webcam off the GUI thread and keeps the newest frame."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._frame = None
        self._error = None
        self.index = None

    def start(self, index: int) -> None:
        self.stop()
        self.index = index
        self._stop.clear()
        with self._lock:
            self._frame, self._error = None, None
        self._thread = threading.Thread(target=self._run, name="camera-preview", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=3)
        self._thread = None

    def _run(self) -> None:
        capture = None
        try:
            capture = open_camera(self.index, 640, 360)
            while not self._stop.is_set():
                ok, frame = capture.read()
                if not ok:
                    break
                with self._lock:
                    self._frame = cv2.flip(frame, 1)
        except Exception as error:
            with self._lock:
                self._error = error
        finally:
            if capture is not None:
                capture.release()

    def snapshot(self):
        with self._lock:
            return self._frame, self._error


class VideoWidget(QWidget):
    """Raster paint keeps OBS Window Capture working on Windows and Linux."""

    def __init__(self):
        super().__init__()
        self.frame = None
        self.calibration_text = ""
        self.setMinimumSize(320, 240)
        self.setAutoFillBackground(True)

    def set_calibration(self, text: str) -> None:
        """Show a persistent instruction while the background is captured."""
        if text != self.calibration_text:
            self.calibration_text = text
            self.update()

    def _draw_calibration_banner(self, painter: QPainter) -> None:
        font = painter.font()
        font.setPointSize(max(14, font.pointSize() + 8))
        font.setBold(True)
        painter.setFont(font)
        bounds = painter.fontMetrics().boundingRect(self.calibration_text)
        banner = bounds.adjusted(-20, -14, 20, 14)
        banner.moveCenter(self.rect().center())
        painter.setPen(Qt.white)
        painter.setBrush(QColor(0, 0, 0, 190))
        painter.drawRoundedRect(banner, 8, 8)
        painter.drawText(banner, Qt.AlignCenter, self.calibration_text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if self.frame is None:
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "Starting the webcam...")
            return
        image = _bgr_to_pixmap(self.frame)
        if image is None:
            return
        target = self.rect()
        scaled = image.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage((target.width() - scaled.width()) // 2,
                          (target.height() - scaled.height()) // 2, scaled)
        if self.calibration_text:
            self._draw_calibration_banner(painter)


class Launcher(QMainWindow):
    def __init__(self, config, on_start, available=None):
        super().__init__()
        from app_config import AppConfig
        self.config: AppConfig = config
        self._on_start = on_start
        self._preview = CameraPreview()
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.setWindowIcon(_app_icon())
        self.setMinimumWidth(620)

        central = QWidget()
        layout = QHBoxLayout(central)
        self.effects = QListWidget()
        available = available or [mode for mode, _, _ in EFFECTS]
        for mode, title, detail in EFFECTS:
            if mode in available:
                self.effects.addItem(f"{title}\n    {detail}")
            else:
                item = self.effects.addItem(f"{title}\n    Coming soon") or self.effects.item(
                    self.effects.count() - 1)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        self.effects.setCurrentRow(0)
        if config.mode in available:
            self.effects.setCurrentRow([mode for mode, _, _ in EFFECTS].index(config.mode))
        layout.addWidget(self.effects, 1)

        form = QVBoxLayout()
        self.camera_view = QLabel()
        self.camera_view.setFixedSize(320, 180)
        self.camera_view.setStyleSheet("background: black; color: white;")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setText("Camera preview")
        form.addWidget(self.camera_view, 0, Qt.AlignCenter)

        self.camera = QSpinBox()
        self.camera.setRange(0, 9)
        self.camera.setValue(config.camera or 0)
        form.addWidget(QLabel("Webcam index"))
        form.addWidget(self.camera)

        self.resolution = QComboBox()
        self.resolution.addItem("Auto (highest common)", None)
        for width, height in CAMERA_RESOLUTIONS:
            self.resolution.addItem(f"{width} x {height}", (width, height))
        chosen = (config.width, config.height)
        index = self.resolution.findData(chosen if None not in chosen else None)
        if index >= 0:
            self.resolution.setCurrentIndex(index)
        form.addWidget(QLabel("Resolution"))
        form.addWidget(self.resolution)

        self.fps = QDoubleSpinBox()
        self.fps.setRange(1, 120)
        self.fps.setValue(config.fps)
        form.addWidget(QLabel("Virtual camera FPS"))
        form.addWidget(self.fps)

        self.mirror = QCheckBox("Mirror the preview")
        self.mirror.setChecked(config.mirror)
        form.addWidget(self.mirror)

        self.virtual_camera = QComboBox()
        self.virtual_camera.addItems(("auto", "on", "off"))
        self.virtual_camera.setCurrentText(config.virtual_camera)
        form.addWidget(QLabel("Virtual camera"))
        form.addWidget(self.virtual_camera)

        self.backend = QComboBox()
        self.backend.addItem("Default", None)
        for item in ("obs", "unitycapture", "v4l2loopback"):
            self.backend.addItem(item, item)
        index = self.backend.findData(config.virtual_backend)
        if index >= 0:
            self.backend.setCurrentIndex(index)
        form.addWidget(QLabel("Virtual backend"))
        form.addWidget(self.backend)

        self.goku_delay = QDoubleSpinBox()
        self.goku_delay.setRange(0.1, 30)
        self.goku_delay.setSingleStep(0.1)
        self.goku_delay.setValue(config.goku_delay)
        form.addWidget(QLabel("Goku gesture hold (seconds)"))
        form.addWidget(self.goku_delay)

        self.fullscreen = QCheckBox("Start in fullscreen")
        self.fullscreen.setChecked(config.fullscreen)
        form.addWidget(self.fullscreen)

        self.gesture_debug = QCheckBox("Gesture diagnostics (log)")
        self.gesture_debug.setChecked(config.gesture_debug)
        form.addWidget(self.gesture_debug)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        form.addWidget(self.status)
        self.start = QPushButton("Start effect")
        self.start.clicked.connect(self._start)
        form.addWidget(self.start)
        form.addStretch(1)
        layout.addLayout(form)
        self.setCentralWidget(central)

        self._timer = QTimer(self)
        self._timer.setInterval(66)
        self._timer.timeout.connect(self._poll_preview)
        self._preview.start(self.camera.value())
        self._timer.start()
        self.camera.valueChanged.connect(self._preview.start)

    def _poll_preview(self):
        frame, error = self._preview.snapshot()
        if error is not None:
            self.camera_view.setText(f"No signal from camera {self._preview.index}")
            return
        image = _bgr_to_pixmap(frame)
        if image is not None:
            self.camera_view.setPixmap(
                QPixmap.fromImage(image).scaled(
                    self.camera_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def current_config(self):
        row = self.effects.currentRow()
        mode = EFFECTS[row][0] if row >= 0 else None
        size = self.resolution.currentData()
        self.config.mode = mode
        self.config.camera = self.camera.value()
        self.config.width, self.config.height = size if size else (None, None)
        self.config.fps = self.fps.value()
        self.config.mirror = self.mirror.isChecked()
        self.config.virtual_camera = self.virtual_camera.currentText()
        self.config.virtual_backend = self.backend.currentData()
        self.config.goku_delay = self.goku_delay.value()
        self.config.fullscreen = self.fullscreen.isChecked()
        self.config.gesture_debug = self.gesture_debug.isChecked()
        return self.config

    def _start(self):
        self.status.setText("")
        config = self.current_config()
        config.save()
        self._preview.stop()
        self._on_start(config)

    def closeEvent(self, event):
        self._preview.stop()
        super().closeEvent(event)


class PreviewWindow(QMainWindow):
    def __init__(self, engine: CameraEngine, on_close, mode: str | None = None):
        super().__init__()
        self.engine = engine
        self._on_close = on_close
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(_app_icon())
        self.video = VideoWidget()
        self.setCentralWidget(self.video)

        self.status = QLabel("Step out of frame - capturing background...")
        controls = QHBoxLayout()
        controls.addWidget(self.status, 1)
        buttons = {}
        for caption, command in (("Recapture", "recapture"), ("Reappear", "reappear"),
                                 ("Vanish", "vanish"), ("Fullscreen", "fullscreen"),
                                 ("Quit", "quit")):
            button = QPushButton(caption)
            button.clicked.connect(lambda _checked=False, name=command: self.engine.command(name))
            controls.addWidget(button)
            buttons[command] = button
        # Goku and Infinity use gestures to vanish; the button would do nothing.
        if mode in ("goku", "infinity"):
            buttons["vanish"].setEnabled(False)
            buttons["vanish"].setToolTip("This effect is triggered by its gesture.")
        bar = QWidget()
        bar.setLayout(controls)
        self.statusBar().addWidget(bar, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._poll)
        self._timer.start()
        self.engine.start()

    def keyPressEvent(self, event):
        command = {
            Qt.Key_Space: "recapture", Qt.Key_R: "reappear", Qt.Key_V: "vanish",
            Qt.Key_F: "fullscreen", Qt.Key_Q: "quit", Qt.Key_Escape: "quit",
        }.get(event.key())
        if command == "fullscreen":
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif command:
            self.engine.command(command)
        else:
            super().keyPressEvent(event)

    def _poll(self):
        frame, status, error, finished = self.engine.snapshot()
        if frame is not None:
            self.video.frame = frame
            self.video.update()
        if status:
            self.status.setText(status.split("] ", 1)[-1])
        calibrating, remaining = self.engine.calibration()
        if calibrating:
            self.video.set_calibration(
                f"STEP OUT OF FRAME - capturing background in {remaining}s")
        else:
            self.video.set_calibration("")
        if error is not None or finished:
            self._timer.stop()
            self.engine.join()
            self.close()
            if error is not None:
                QMessageBox.critical(self, APP_NAME, str(error))

    def closeEvent(self, event):
        self._timer.stop()
        self.engine.stop()
        self.engine.join()
        self._on_close()
        super().closeEvent(event)


class SingleInstance:
    def __init__(self, name: str):
        self.name = name
        self.server = QLocalServer()
        self.on_activate = None
        self.server.newConnection.connect(self._connected)

    def acquire(self) -> bool:
        probe = QLocalSocket()
        probe.connectToServer(self.name)
        connected = probe.waitForConnected(200)
        probe.disconnectFromServer()
        if connected:
            return False
        QLocalServer.removeServer(self.name)
        return self.server.listen(self.name)

    def _connected(self):
        while self.server.hasPendingConnections():
            connection = self.server.nextPendingConnection()
            connection.disconnectFromServer()
        if self.on_activate is not None:
            self.on_activate()


def _license_dialog(auth, config, fingerprint):
    """Qt equivalent of the Windows activation prompt."""
    from license_client import FirestoreLicense, LicenseError, normalize_email

    dialog = QDialog()
    dialog.setWindowTitle(f"{APP_NAME} - Activate License")
    dialog.setWindowIcon(_app_icon())
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Enter the email address associated with your license."))
    email = QLineEdit(auth.state.get("email", ""))
    layout.addWidget(email)
    status = QLabel("")
    status.setWordWrap(True)
    layout.addWidget(status)
    button = QPushButton("Activate and Start")
    layout.addWidget(button)
    result = {}
    events = queue.Queue()

    def activate():
        try:
            address = normalize_email(email.text())
        except LicenseError as error:
            status.setText(str(error))
            return
        button.setEnabled(False)
        email.setEnabled(False)
        status.setText("Checking license...")

        def work():
            backend = FirestoreLicense(config, auth, address, fingerprint)
            try:
                deadline = backend.acquire()
                auth.state["email"] = address
                auth.store.save(auth.state)
                events.put((backend, deadline, None))
            except Exception as error:
                events.put((backend, None, error))

        threading.Thread(target=work, daemon=True).start()

    def poll():
        try:
            backend, deadline, error = events.get_nowait()
        except queue.Empty:
            return
        if error:
            status.setText(str(error) if isinstance(error, LicenseError) else "Check failed. Try again.")
            button.setEnabled(True)
            email.setEnabled(True)
        else:
            result["session"] = (backend, deadline)
            dialog.accept()

    timer = QTimer(dialog)
    timer.setInterval(80)
    timer.timeout.connect(poll)
    timer.start()
    button.clicked.connect(activate)
    email.returnPressed.connect(activate)
    if dialog.exec() == QDialog.Accepted and "session" in result:
        return result["session"]
    return None


def run_desktop() -> int:
    setup_logging()
    # Qt 6 on Wayland warns when a hidden window's text input is disabled.
    # It is harmless noise from showing/hiding the launcher and preview.
    QLoggingCategory.setFilterRules(
        "qt.qpa.wayland.textinput.warning=false\n"
        + os.environ.get("QT_LOGGING_RULES", "")
    )
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(_app_icon())

    user = os.getuid() if hasattr(os, "getuid") else os.environ.get("USERNAME", "")
    single = SingleInstance(f"vanishcam-{user}")
    if not single.acquire():
        return 0

    from app_config import AppConfig
    from license_client import LicenseError, activate_license

    config = AppConfig.load()
    launcher = None
    session = None
    stack = contextlib.ExitStack()
    try:
        if getattr(sys, "frozen", False) and sys.platform == "win32":
            session = activate_license(dialog=_license_dialog)
            if session is None:
                return 0
            stack.enter_context(session)

        def start(chosen):
            launcher.hide()
            preview = PreviewWindow(CameraEngine(chosen.to_args(), chosen.mode, session),
                                    on_close=launcher.show, mode=chosen.mode)
            preview.showFullScreen() if chosen.fullscreen else preview.show()

        launcher = Launcher(config, start)
        single.on_activate = lambda: (launcher.show(), launcher.raise_(), launcher.activateWindow())
        launcher.show()
        return app.exec()
    except LicenseError as error:
        QMessageBox.critical(None, APP_NAME, str(error))
        return 1
    finally:
        stack.close()
