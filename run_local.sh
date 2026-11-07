#!/usr/bin/env bash
# VanishCam launcher for Linux/macOS: creates a virtualenv when needed and
# starts the app from source (source runs have no online license check).
set -u
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv-local"
VENV_PY="$VENV_DIR/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "[Vanish Lab] Creating the local Python environment..."
  "$PYTHON" -m venv "$VENV_DIR" || exit 1
fi

if ! "$VENV_PY" -c "import cv2, mediapipe, numpy, pyvirtualcam" >/dev/null 2>&1; then
  echo "[Vanish Lab] Installing required packages. Internet is only needed this time..."
  "$VENV_PY" -m pip install --upgrade pip || exit 1
  "$VENV_PY" -m pip install -r requirements.txt || exit 1
fi

echo "[Vanish Lab] Starting the webcam..."
exec "$VENV_PY" vanish_cam.py "$@"
