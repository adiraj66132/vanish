"""PyInstaller spec for the single-binary VanishCam desktop app (onedir)."""

from pathlib import Path
import platform

from PyInstaller.utils.hooks import collect_dynamic_libs


root = Path(SPECPATH).resolve()
is_windows = platform.system() == "Windows"
icon_file = root / "assets" / "vanish_icon.ico" if is_windows else None
version_file = root / "build" / "version_info.txt"

resources = [
    (root / "models" / "selfie_segmenter_landscape.tflite", "models"),
    (root / "models" / "gesture_recognizer.task", "models"),
    (root / "models" / "blaze_face_short_range.tflite", "models"),
    (root / "hand_landmarker.task", "."),
    (root / "assets" / "substitution_log.png", "assets"),
    (root / "assets" / "vanish.MP3", "assets"),
    (root / "assets" / "teleport.MP3", "assets"),
    (root / "assets" / "itachi_crow_sheet.png", "assets"),
    (root / "assets" / "sharingan.png", "assets"),
    (root / "license_config.json", "."),
]
missing = [str(path) for path, _ in resources if not path.is_file()]
if missing:
    raise SystemExit("Missing build resources:\n" + "\n".join(missing))

excludes = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D",
    "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtSerialPort", "PySide6.QtSql", "PySide6.QtTest",
    "PySide6.QtDesigner", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
]

analysis = Analysis(
    [str(root / "desktop.py")],
    pathex=[str(root)],
    binaries=collect_dynamic_libs("mediapipe"),
    datas=[(str(path), destination) for path, destination in resources],
    hiddenimports=["pygame.mixer", "mediapipe.tasks.c", "PySide6.QtNetwork"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
archive = PYZ(analysis.pure)
exe = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="VanishCam",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
    version=str(version_file) if is_windows and version_file.is_file() else None,
)
coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VanishCam",
)
