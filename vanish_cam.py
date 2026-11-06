"""Local webcam effects triggered by hand gestures."""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from contextlib import ExitStack
from pathlib import Path

if __name__ == "__main__" and not getattr(sys, "frozen", False):
    from mediapipe_log_filter import needs_filter, run_local_filtered
    if needs_filter(sys.argv[1:]):
        raise SystemExit(run_local_filtered(Path(__file__).resolve(), sys.argv[1:]))

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

try:
    from .goku_settings import choose_goku_delay
    from .itachi_effect import CROW_SHEET_PATH, SHARINGAN_PATH, EFFECT_SECONDS as ITACHI_SECONDS, ItachiCrowEffect, ItachiGestureGate, ItachiPoseRecognizer, load_crow_sprites, load_sharingan_art
    from .license_client import LicenseError, activate_license, load_config, show_license_error
    from .goku_effect import (
        GokuGestureGate, GokuPoseRecognizer, GokuTeleport, HOLD_SECONDS,
        TELEPORT_SECONDS,
    )
    from .particles_effect import PARTICLE_SECONDS, ParticleEffect
    from .infinity_effect import EFFECT_SECONDS as INFINITY_SECONDS, InfinityDust, SnapGesture, hand_landmarks_from_result, overlay_gauntlet
    from .naruto_effect import (
        EFFECT_SECONDS, LOG_PATH, joined_hands_from_landmarks, landed_log_anchor,
        load_log, overlay_log, render_substitution, substitution_anchor,
    )
    from .vanish_sound import SOUND_PATH, TELEPORT_SOUND_PATH, VanishSound
except ImportError:
    from goku_settings import choose_goku_delay
    from itachi_effect import CROW_SHEET_PATH, SHARINGAN_PATH, EFFECT_SECONDS as ITACHI_SECONDS, ItachiCrowEffect, ItachiGestureGate, ItachiPoseRecognizer, load_crow_sprites, load_sharingan_art
    from license_client import LicenseError, activate_license, load_config, show_license_error
    from goku_effect import (
        GokuGestureGate, GokuPoseRecognizer, GokuTeleport, HOLD_SECONDS,
        TELEPORT_SECONDS,
    )
    from particles_effect import PARTICLE_SECONDS, ParticleEffect
    from infinity_effect import EFFECT_SECONDS as INFINITY_SECONDS, InfinityDust, SnapGesture, hand_landmarks_from_result, overlay_gauntlet
    from naruto_effect import (
        EFFECT_SECONDS, LOG_PATH, joined_hands_from_landmarks, landed_log_anchor,
        load_log, overlay_log, render_substitution, substitution_anchor,
    )
    from vanish_sound import SOUND_PATH, TELEPORT_SOUND_PATH, VanishSound


APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "models"
WINDOW_NAME = "Webcam Preview"

SEGMENTER_MODEL = MODEL_DIR / "selfie_segmenter_landscape.tflite"
GESTURE_MODEL = MODEL_DIR / "gesture_recognizer.task"
HAND_MODEL = APP_DIR / "hand_landmarker.task"
FACE_MODEL = MODEL_DIR / "blaze_face_short_range.tflite"
ALL_MODES = ("normal", "naruto", "particles", "goku", "itachi", "infinity")
# Firestore licenses the app/device, not individual effects. Report a known
# value until the server rules are updated for newly added local modes.
LICENSE_REPORTED_MODES = frozenset(("normal", "naruto", "particles", "goku"))
EDITION_MODES = {
    "full": ALL_MODES,
    "naruto": ("naruto",),
    "goku": ("goku",),
    "normal_particles": ("normal", "particles"),
    "infinity": ("infinity",),
}


def edition_modes(edition_file: Path | None = None) -> tuple[str, ...]:
    """Limit a packaged EXE to the modes listed in its bundled edition file."""
    edition_file = edition_file or APP_DIR / "edition.txt"
    if not edition_file.is_file():
        if getattr(sys, "frozen", False):
            raise RuntimeError("Edition configuration was not found in the EXE.")
        return ALL_MODES
    edition = edition_file.read_text(encoding="utf-8").strip()
    if edition not in EDITION_MODES:
        raise RuntimeError(f"Unrecognized edition: {edition}")
    return EDITION_MODES[edition]

MODEL_URLS = {
    SEGMENTER_MODEL: (
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
        "selfie_segmenter_landscape/float16/latest/"
        "selfie_segmenter_landscape.tflite"
    ),
    GESTURE_MODEL: (
        "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
        "gesture_recognizer/float16/1/gesture_recognizer.task"
    ),
    FACE_MODEL: (
        "https://storage.googleapis.com/mediapipe-models/face_detector/"
        "blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
    ),
}

CALIBRATION_SECONDS = 4.0
BACKGROUND_SAMPLE_SECONDS = 0.55
VANISH_SECONDS = 3.6
GESTURE_INTERVAL_SECONDS = 0.14


@dataclass
class AppState:
    phase: str = "calibrating"
    calibration_started: float = 0.0
    vanish_started: float | None = None
    last_gesture_check: float = 0.0
    fullscreen: bool = False


def positive_fps(value: str) -> float:
    fps = float(value)
    if not np.isfinite(fps) or not 1 <= fps <= 120:
        raise argparse.ArgumentTypeError("FPS must be between 1 and 120.")
    return fps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Choose a webcam disappearance effect."
    )
    parser.add_argument(
        "--camera", type=int, default=None,
        help="Webcam index; if omitted, choose a webcam in the startup menu",
    )
    parser.add_argument(
        "--width", type=int, default=None,
        help="Requested camera width; by default use the highest supported common resolution",
    )
    parser.add_argument(
        "--height", type=int, default=None,
        help="Requested camera height; specify together with --width",
    )
    parser.add_argument(
        "--fullscreen", action="store_true", help="Start in fullscreen mode"
    )
    parser.add_argument(
        "--no-mirror", action="store_true", help="Do not mirror the webcam",
    )
    parser.add_argument("--fps", type=positive_fps, default=30.0, help="Maximum virtual output FPS (default: 30)")
    parser.add_argument(
        "--virtual-camera", action=argparse.BooleanOptionalAction, default=None,
        help="Require a virtual camera; enabled automatically when available. --no-virtual-camera disables it",
    )
    parser.add_argument(
        "--virtual-backend", choices=("obs", "unitycapture", "v4l2loopback"),
        help="Virtual camera driver to use",
    )
    parser.add_argument("--virtual-device", help="Name of the virtual camera device to use")
    parser.add_argument(
        "--mode", choices=edition_modes(),
        help="Skip the startup menu and launch the selected mode directly",
    )
    parser.add_argument(
        "--gesture-debug", action="store_true",
        help="Print recognition status in the terminal (without text in the video)",
    )
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if (args.width is None) != (args.height is None):
        parser.error("--width and --height must be specified together.")
    if args.width is not None and (args.width <= 0 or args.height <= 0):
        parser.error("--width and --height must be positive.")
    return args


def choose_mode(available: tuple[str, ...] | None = None, check_license=None) -> str | None:
    """Simple keyboard/mouse menu shown before the clean camera feed."""
    available = available or edition_modes()
    display_modes = available
    title = "Choose an effect"
    selected = [None]
    compact = len(display_modes) > 6
    row_step = 94 if len(display_modes) > 5 else 115
    card_height = 80 if compact else row_step - 16 if len(display_modes) > 5 else 94
    rows = (len(display_modes) + 1) // 2 if compact else len(display_modes)
    window = np.zeros((120 + rows * row_step + 25, 700, 3), dtype=np.uint8)
    window[:] = (26, 29, 34)
    cv2.putText(window, "CHOOSE YOUR VANISH EFFECT", (68, 88),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (236, 239, 242), 2, cv2.LINE_AA)
    labels = {
        "normal": ("NORMAL VANISH", "V sign  /  dissolve"),
        "naruto": ("NARUTO VANISH", "Hands together  /  log and smoke"),
        "particles": ("PARTICLES", "V sign  /  windblown particles"),
        "goku": ("GOKU", "Two fingers to forehead  /  custom delay"),
        "itachi": ("ITACHI UCHIHA DISAPPEAR", "Hands at chest  /  crow swarm"),
        "infinity": ("INFINITY GAUNTLET", "Snap your fingers  /  cosmic dust"),
    }
    buttons = tuple(
        (mode, f"{index}  {labels[mode][0]}", labels[mode][1],
         (65 + ((index - 1) % 2) * 294 if compact else 65),
         120 + ((index - 1) // 2 if compact else index - 1) * row_step)
        for index, mode in enumerate(display_modes, 1)
    )
    for mode, heading, detail, left, top in buttons:
        disabled = mode not in available
        if disabled:
            heading = labels[mode][0]
            detail = "Coming soon"
        right = left + (277 if compact else 570)
        cv2.rectangle(window, (left, top), (right, top + card_height),
                      (35, 38, 43) if disabled else (48, 54, 62), -1, cv2.LINE_AA)
        cv2.rectangle(window, (left, top), (right, top + card_height),
                      (66, 71, 78) if disabled else (111, 142, 153), 2, cv2.LINE_AA)
        cv2.putText(window, heading, (left + 18, top + 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45 if compact else 0.77,
                    (115, 120, 128) if disabled else (240, 245, 247), 2, cv2.LINE_AA)
        cv2.putText(window, detail, (left + 18, top + 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.37 if compact else 0.53,
                    (135, 141, 150) if disabled else (179, 195, 201), 1, cv2.LINE_AA)

    def on_mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONUP:
            for mode, _, _, left, top in buttons:
                right = left + (277 if compact else 570)
                if mode in available and left <= x <= right and top <= y <= top + card_height:
                    selected[0] = mode

    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(title, on_mouse)
    try:
        while selected[0] is None:
            if check_license:
                check_license()
            cv2.imshow(title, window)
            key = cv2.waitKey(30) & 0xFF
            if ord("1") <= key < ord("1") + len(display_modes):
                candidate = display_modes[key - ord("1")]
                if candidate in available:
                    selected[0] = candidate
            elif key in (ord("q"), 27):
                return None
            if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                return None
        return selected[0]
    finally:
        cv2.destroyWindow(title)


def choose_camera(initial_index: int = 0, mirror: bool = True, check_license=None) -> int | None:
    """Preview camera indices 0-9 before opening the clean video output."""
    title = "Choose a webcam"
    selected = [max(0, min(9, initial_index))]
    confirmed = [False]
    opened_index = None
    capture = None
    preview_ready = False
    read_failures = 0

    def on_mouse(event, x, y, flags, userdata):
        if event != cv2.EVENT_LBUTTONUP or not 472 <= y <= 535:
            return
        if 70 <= x <= 165:
            selected[0] = max(0, selected[0] - 1)
        elif 180 <= x <= 275:
            selected[0] = min(9, selected[0] + 1)
        elif 445 <= x <= 710 and preview_ready:
            confirmed[0] = True

    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(title, on_mouse)
    try:
        while True:
            if check_license:
                check_license()
            if selected[0] != opened_index:
                if capture is not None:
                    capture.release()
                try:
                    capture = open_camera(selected[0], 640, 360)
                except RuntimeError:
                    capture = None
                opened_index = selected[0]
                preview_ready = False
                read_failures = 0

            window = np.full((560, 780, 3), (26, 29, 34), dtype=np.uint8)
            cv2.putText(window, "CHOOSE A WEBCAM", (70, 59),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.86, (236, 239, 242), 2, cv2.LINE_AA)
            cv2.putText(window, "0-9 or A/D: change  |  ENTER: confirm  |  R: retry", (70, 82),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.43, (179, 195, 201), 1, cv2.LINE_AA)
            cv2.rectangle(window, (69, 94), (711, 456), (111, 142, 153), 2)
            if capture is not None:
                ok, frame = capture.read()
                if ok:
                    if mirror:
                        frame = cv2.flip(frame, 1)
                    preview = fit_frame_to_box(frame, 640, 360)
                    window[95:455, 70:710] = preview
                    preview_ready = True
                    read_failures = 0
                else:
                    read_failures += 1
                    if read_failures >= 10:
                        capture.release()
                        capture = None
                        preview_ready = False
            if not preview_ready:
                message = ("Waiting for webcam signal..." if capture is not None
                           else "No signal from this webcam")
                cv2.putText(window, message, (125, 277),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.72, (179, 195, 201), 2, cv2.LINE_AA)

            for left, right, label in ((70, 165, "-"), (180, 275, "+")):
                cv2.rectangle(window, (left, 472), (right, 535), (48, 54, 62), -1)
                cv2.rectangle(window, (left, 472), (right, 535), (111, 142, 153), 2)
                cv2.putText(window, label, (left + 35, 516), cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (240, 245, 247), 2, cv2.LINE_AA)
            cv2.putText(window, f"CAM {selected[0]}", (302, 514),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.72, (240, 245, 247), 2, cv2.LINE_AA)
            button_color = (78, 132, 124) if preview_ready else (48, 54, 62)
            cv2.rectangle(window, (445, 472), (710, 535), button_color, -1)
            cv2.putText(window, "USE THIS WEBCAM", (464, 511),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.57, (240, 245, 247), 2, cv2.LINE_AA)
            if check_license:
                check_license()
            cv2.imshow(title, window)

            key = cv2.waitKey(30) & 0xFF
            if ord("0") <= key <= ord("9"):
                selected[0] = key - ord("0")
            elif key in (ord("a"), ord("A")):
                selected[0] = max(0, selected[0] - 1)
            elif key in (ord("d"), ord("D")):
                selected[0] = min(9, selected[0] + 1)
            elif key in (ord("r"), ord("R")):
                opened_index = None
            elif key in (10, 13) and preview_ready:
                confirmed[0] = True
            elif key in (ord("q"), 27):
                return None
            if confirmed[0] and preview_ready:
                return selected[0]
            if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                return None
    finally:
        if capture is not None:
            capture.release()
        cv2.destroyWindow(title)


def open_virtual_camera(args: argparse.Namespace, width: int, height: int):
    if args.virtual_camera is False:
        return None
    try:
        import pyvirtualcam

        camera = pyvirtualcam.Camera(
            width=width, height=height, fps=args.fps,
            fmt=pyvirtualcam.PixelFormat.BGR,
            backend=args.virtual_backend, device=args.virtual_device,
        )
    except (ImportError, RuntimeError, OSError, ValueError) as error:
        message = (
            "Virtual camera unavailable. Install OBS Studio (with the OBS Virtual "
            "Camera driver) or Unity Capture. If using OBS Virtual Camera, stop "
            "'Start Virtual Camera' in OBS. Launch through RUN_LOCAL.bat to "
            "install pyvirtualcam. "
            f"Details: {error}"
        )
        if args.virtual_camera is True or args.virtual_backend or args.virtual_device:
            raise RuntimeError(message) from error
        print(f"[Webcam] {message}\n[Webcam] Continuing with the local preview.")
        return None
    print(f"[Webcam] Virtual output active: {camera.device} ({width}x{height}, up to {args.fps:g} FPS)")
    return camera


def send_virtual_frame(camera, frame: np.ndarray) -> None:
    if frame.shape[:2] != (camera.height, camera.width):
        frame = cv2.resize(frame, (camera.width, camera.height), interpolation=cv2.INTER_LINEAR)
    camera.send(np.ascontiguousarray(frame))


def download_models(mode: str = "normal") -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for destination, url in MODEL_URLS.items():
        if mode in ("naruto", "goku", "itachi", "infinity") and destination == GESTURE_MODEL:
            continue
        if mode != "goku" and destination == FACE_MODEL:
            continue
        if destination.exists() and destination.stat().st_size > 100_000:
            continue

        temporary = destination.with_suffix(destination.suffix + ".part")
        print(f"[Vanish Lab] Downloading {destination.name}...")
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "Vanish-Lab/1.0"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                total = int(response.headers.get("Content-Length", 0))
                received = 0
                with temporary.open("wb") as output:
                    while chunk := response.read(1024 * 256):
                        output.write(chunk)
                        received += len(chunk)
                        if total:
                            percent = int(received * 100 / total)
                            print(f"\r  {percent:3d}%", end="", flush=True)
            print()
            os.replace(temporary, destination)
        except (OSError, urllib.error.URLError) as error:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(
                "Could not download the MediaPipe models. "
                "Check your internet connection and try again."
            ) from error


CAMERA_RESOLUTIONS = tuple(sorted((
    (4096, 2160), (3840, 2160), (3840, 2880), (3264, 2448),
    (2592, 1944), (2560, 1440), (2304, 1296), (2048, 1536),
    (1920, 1200), (1920, 1080), (1600, 1200), (1280, 960),
    (1280, 720), (1024, 768), (960, 540), (800, 600), (640, 480),
), key=lambda size: size[0] * size[1], reverse=True))


def fit_frame_to_box(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize a frame without changing its aspect ratio and center it in a dark box."""
    frame_height, frame_width = frame.shape[:2]
    scale = min(width / frame_width, height / frame_height)
    resized_width = max(1, round(frame_width * scale))
    resized_height = max(1, round(frame_height * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(frame, (resized_width, resized_height), interpolation=interpolation)
    output = np.full((height, width, 3), (18, 20, 24), dtype=np.uint8)
    left = (width - resized_width) // 2
    top = (height - resized_height) // 2
    output[top:top + resized_height, left:left + resized_width] = resized
    return output


def open_camera(index: int, width: int | None = None,
                height: int | None = None) -> cv2.VideoCapture:
    if platform.system() == "Windows":
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(index)
    else:
        capture = cv2.VideoCapture(index)

    if not capture.isOpened():
        raise RuntimeError(
            f"Webcam {index} is unavailable. Close other apps or try --camera 1."
        )

    if width is None and height is None:
        for requested_width, requested_height in CAMERA_RESOLUTIONS:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, requested_width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, requested_height)
            for _ in range(3):
                ok, frame = capture.read()
                if (ok and frame is not None
                        and frame.shape[1::-1] == (requested_width, requested_height)):
                    print(
                        "[Webcam] Using highest detected common resolution: "
                        f"{requested_width}x{requested_height}."
                    )
                    break
            else:
                continue
            break
    else:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def create_tasks(mode: str = "normal") -> tuple[
    vision.ImageSegmenter,
    MultiViewGestureRecognizer | MultiViewHandLandmarker | GokuPoseRecognizer | ItachiPoseRecognizer,
]:
    segmenter_options = vision.ImageSegmenterOptions(
        base_options=python.BaseOptions(model_asset_path=str(SEGMENTER_MODEL)),
        running_mode=vision.RunningMode.VIDEO,
        output_confidence_masks=True,
        output_category_mask=False,
    )
    if mode == "goku":
        if not HAND_MODEL.is_file() or not FACE_MODEL.is_file():
            raise RuntimeError("Hand or face models are missing for Goku mode.")
        hand_options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(HAND_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.45,
        )
        face_options = vision.FaceDetectorOptions(
            base_options=python.BaseOptions(model_asset_path=str(FACE_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            min_detection_confidence=0.5,
        )
        segmenter = vision.ImageSegmenter.create_from_options(segmenter_options)
        try:
            hands = vision.HandLandmarker.create_from_options(hand_options)
            try:
                fallback_hands = vision.HandLandmarker.create_from_options(
                    replace(hand_options, running_mode=vision.RunningMode.IMAGE)
                )
                try:
                    face = vision.FaceDetector.create_from_options(face_options)
                except Exception:
                    fallback_hands.close()
                    raise
            except Exception:
                hands.close()
                raise
        except Exception:
            segmenter.close()
            raise
        return segmenter, GokuPoseRecognizer(hands, face, fallback_hands)
    if mode in ("naruto", "itachi", "infinity"):
        if not HAND_MODEL.is_file():
            raise RuntimeError(f"Hand model not found: {HAND_MODEL}")
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(HAND_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.45,
        )
        task_class = vision.HandLandmarker
        wrapper_class = MultiViewHandLandmarker
    else:
        classifier_options = mp.tasks.components.processors.ClassifierOptions(
            score_threshold=0.55,
            category_allowlist=["Victory"],
        )
        options = vision.GestureRecognizerOptions(
            base_options=python.BaseOptions(model_asset_path=str(GESTURE_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.5,
            canned_gesture_classifier_options=classifier_options,
        )
        task_class = vision.GestureRecognizer
        wrapper_class = MultiViewGestureRecognizer

    segmenter = vision.ImageSegmenter.create_from_options(segmenter_options)
    try:
        primary = task_class.create_from_options(options)
        try:
            alternate = task_class.create_from_options(
                replace(options, running_mode=vision.RunningMode.IMAGE)
            )
        except Exception:
            primary.close()
            raise
    except Exception:
        segmenter.close()
        raise
    if mode == "itachi":
        return segmenter, ItachiPoseRecognizer(primary, alternate)
    if mode == "infinity":
        return segmenter, MultiViewHandLandmarker(primary, alternate)
    return segmenter, wrapper_class(primary, alternate)


def smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    values = np.clip((values - edge0) / max(edge1 - edge0, 1e-6), 0.0, 1.0)
    return values * values * (3.0 - 2.0 * values)


def ease_in_out_cubic(value: float) -> float:
    if value < 0.5:
        return 4.0 * value * value * value
    return 1.0 - ((-2.0 * value + 2.0) ** 3) / 2.0


def make_dissolve_fields(height: int, width: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7391)
    y, x = np.mgrid[0:height, 0:width]
    y_normal = y.astype(np.float32) / max(height - 1, 1)
    x_normal = x.astype(np.float32) / max(width - 1, 1)
    low_noise = rng.random((max(2, height // 10), max(2, width // 10)), dtype=np.float32)
    low_noise = cv2.resize(low_noise, (width, height), interpolation=cv2.INTER_CUBIC)
    fine_noise = rng.random((height, width), dtype=np.float32)
    field = (
        (1.0 - y_normal) * 0.72
        + low_noise * 0.17
        + fine_noise * 0.08
        + np.sin(x_normal * 18.0) * 0.025
    )
    return np.clip(field, 0.0, 1.0), fine_noise


def person_mask(
    segmenter: vision.ImageSegmenter,
    image: mp.Image,
    timestamp_ms: int,
    width: int,
    height: int,
) -> np.ndarray:
    result = segmenter.segment_for_video(image, timestamp_ms)
    if not result.confidence_masks:
        return np.zeros((height, width), dtype=np.float32)
    raw = np.squeeze(result.confidence_masks[0].numpy_view()).astype(np.float32)
    resized = cv2.resize(raw, (width, height), interpolation=cv2.INTER_LINEAR)
    resized = cv2.GaussianBlur(resized, (0, 0), sigmaX=2.2, sigmaY=2.2)
    return np.clip((resized - 0.12) / 0.68, 0.0, 1.0)


def alpha_composite(person: np.ndarray, background: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    alpha_3 = alpha[:, :, None]
    return (
        person.astype(np.float32) * alpha_3
        + background.astype(np.float32) * (1.0 - alpha_3)
    ).astype(np.uint8)


def apply_dissolve(
    frame: np.ndarray,
    background: np.ndarray,
    mask: np.ndarray,
    progress: float,
    field: np.ndarray,
    sparkle_noise: np.ndarray,
) -> np.ndarray:
    if progress <= 0.002:
        return alpha_composite(frame, background, mask)
    if progress >= 0.999:
        return background.copy()

    points = cv2.findNonZero((mask > 0.01).astype(np.uint8))
    if points is None:
        return background.copy()
    x, y, width, height = cv2.boundingRect(points)
    left, top = max(0, x - 18), max(0, y - 18)
    right = min(mask.shape[1], x + width + 18)
    bottom = min(mask.shape[0], y + height + 18)
    area = np.s_[top:bottom, left:right]
    mask = mask[area]
    field = field[area]
    sparkle_noise = sparkle_noise[area]
    eased = ease_in_out_cubic(progress)
    survival = smoothstep(eased - 0.055, eased + 0.055, field)
    alpha = mask * survival
    output = alpha_composite(frame[area], background[area], alpha)
    edge = (
        (np.abs(field - eased) < 0.018)
        & (mask > 0.48)
        & (sparkle_noise > 0.54)
    ).astype(np.float32)
    glow = cv2.GaussianBlur(edge, (0, 0), sigmaX=5.0, sigmaY=5.0)
    glow = np.clip(glow * 5.0 + edge, 0.0, 1.0)[:, :, None]
    cyan = np.full_like(output, (255, 228, 92), dtype=np.uint8)
    result = np.clip(
        output.astype(np.float32) * (1.0 - glow * 0.8)
        + cyan.astype(np.float32) * glow * 0.8,
        0,
        255,
    ).astype(np.uint8)
    canvas = background.copy()
    canvas[area] = result
    return canvas


def victory_landmark_score(points: np.ndarray) -> float:
    """Recognize extended index and middle fingers by 3D distance, not orientation."""
    if points.shape != (21, 3) or not np.isfinite(points).all():
        return 0.0

    straightness = []
    extended = []
    folded = []
    lengths = []
# MCP, PIP, DIP and fingertip landmarks for the index, middle, ring and little fingers.
    for index, base in enumerate((5, 9, 13, 17)):
        finger = points[base : base + 4]
        length = float(np.linalg.norm(np.diff(finger, axis=0), axis=1).sum())
        if length < 1e-6:
            if index < 2:
                return 0.0
            straightness.append(0.0)
            lengths.append(0.0)
            extended.append(False)
            folded.append(True)
            continue
        ratio = float(np.linalg.norm(finger[3] - finger[0])) / length
        tip_distance = float(np.linalg.norm(finger[3] - points[0]))
        joint_distance = float(np.linalg.norm(finger[1] - points[0]))
        straightness.append(ratio)
        lengths.append(length)
        extended.append(ratio >= 0.82 and tip_distance > joint_distance * 1.10)
        folded.append(ratio < 0.78 or tip_distance <= joint_distance * 1.05)

    # From the side, folded fingers can look straight but very short.
    # Do not require clearly visible joints for the ring and little fingers.
    reference_length = min(lengths[:2])
    for index, base in ((2, 13), (3, 17)):
        reach = float(np.linalg.norm(points[base + 3] - points[base]))
        folded[index] = folded[index] or reach < reference_length * 0.65
    if not (extended[0] and extended[1] and folded[2] and folded[3]):
        return 0.0
    # The two fingertips must be apart; the thumb may be hidden.
    separation = float(np.linalg.norm(points[8] - points[12]))
    if separation < min(lengths[:2]) * 0.20:
        return 0.0
    # Measure the geometry of the extended fingers rather than classifier confidence.
    return float(np.clip(min(straightness[:2]), 0.0, 1.0))


def classify_gesture_result(
    result: vision.GestureRecognizerResult,
    image: mp.Image,
) -> tuple[str, float]:
    # Landmarks are returned even when the classifier does not recognize
    # "Victory" (for example, when the back of the hand faces the webcam).
    for landmarks in result.hand_world_landmarks:
        points = np.array([(point.x, point.y, point.z) for point in landmarks])
        score = victory_landmark_score(points)
        if score:
            return "Victory", score
    # Always check the visible geometry too: estimated depth can be inaccurate
    # when the palm and folded fingers are hidden.
    for landmarks in result.hand_landmarks:
        points = np.array([(point.x * image.width, point.y * image.height, 0.0)
                           for point in landmarks])
        score = victory_landmark_score(points)
        if score:
            return "Victory", score
    for categories in result.gestures:
        for category in categories:
            if category.category_name == "Victory" and category.score >= 0.62:
                return "Victory", float(category.score)
    if result.hand_landmarks or result.hand_world_landmarks:
        return "Hand_Detected", 0.0
    return "No_Hand", 0.0


class MultiViewGestureRecognizer:
    """Retry detection on rotated frames without changing the tracking state."""

    def __init__(self, primary, alternate):
        self.primary = primary
        self.alternate = alternate
        self.preferred_rotation: int | None = None
        self.preferred_crop: str | None = None
        self.next_retry_ms = 0
        self.retry_cursor = 0

    def recognize_gesture(self, image: mp.Image, timestamp_ms: int) -> tuple[str, float]:
        result = self.primary.recognize_for_video(image, timestamp_ms)
        best = classify_gesture_result(result, image)
        if best[0] == "Victory":
            self.preferred_rotation = None
            self.preferred_crop = None
            return best
        if timestamp_ms < self.next_retry_ms:
            return best

        # IMAGE forces a fresh detection while the VIDEO model stays on the
        # original frame. This avoids inconsistent timestamps across rotations.
        rgb = image.numpy_view()
        height, width = rgb.shape[:2]
        # A side-facing palm is often too small in the full frame. The two lower
        # crops overlap and cover both hands, including in mirrored images.
        crops = {
            "full": rgb,
            "lower_left": rgb[int(height * 0.28):, :int(width * 0.78)],
            "lower_right": rgb[int(height * 0.28):, int(width * 0.22):],
        }
        views = [("full", rotation) for rotation in (0, 1, 3, 2)]
        views += [(crop, rotation) for crop in ("lower_left", "lower_right")
                  for rotation in (0, 1, 3)]
        preferred = (self.preferred_crop, self.preferred_rotation)
        selected = []
        if preferred in views:
            selected.append(preferred)
        # Spread the expensive IMAGE attempts over successive video frames.
        while len(selected) < 3:
            view = views[self.retry_cursor % len(views)]
            self.retry_cursor += 1
            if view not in selected:
                selected.append(view)
        for crop, rotation in selected:
            rotated = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=np.ascontiguousarray(np.rot90(crops[crop], rotation)),
            )
            result = self.alternate.recognize(rotated)
            candidate = classify_gesture_result(result, rotated)
            if candidate[0] == "Victory":
                self.preferred_rotation = rotation
                self.preferred_crop = crop
                self.next_retry_ms = timestamp_ms + int(GESTURE_INTERVAL_SECONDS * 1000)
                return candidate
            if candidate[0] == "Hand_Detected":
                best = candidate
        self.preferred_rotation = None
        self.preferred_crop = None
        self.next_retry_ms = timestamp_ms + int(GESTURE_INTERVAL_SECONDS * 1000)
        return best

    def close(self) -> None:
        try:
            self.primary.close()
        finally:
            self.alternate.close()


class MultiViewHandLandmarker:
    """Track two hands in video and retry difficult views with the hand model."""

    def __init__(self, primary, alternate):
        self.primary = primary
        self.alternate = alternate
        self.preferred_view: tuple[str, int] | None = None
        self.next_retry_ms = 0
        self.last_hand_count = 0
        self.retry_cursor = 0

    def recognize_joined_hands(self, image: mp.Image, timestamp_ms: int) -> bool:
        result = self.primary.detect_for_video(image, timestamp_ms)
        self.last_hand_count = len(result.hand_landmarks)
        if joined_hands_from_landmarks(result.hand_landmarks, image.width, image.height):
            self.preferred_view = None
            return True
        if timestamp_ms < self.next_retry_ms:
            return False

        rgb = image.numpy_view()
        height, width = rgb.shape[:2]
        views = {
            "full": rgb,
            "center": rgb[int(height * 0.18):, int(width * 0.12):int(width * 0.88)],
            "lower_left": rgb[int(height * 0.22):, :int(width * 0.78)],
            "lower_right": rgb[int(height * 0.22):, int(width * 0.22):],
        }
        attempts = [("full", rotation) for rotation in (1, 3, 2)]
        attempts += [("center", rotation) for rotation in (0, 1, 3)]
        attempts += [("lower_left", 0), ("lower_right", 0)]
        selected = []
        if self.preferred_view in attempts:
            selected.append(self.preferred_view)
        while len(selected) < 2:
            view = attempts[self.retry_cursor % len(attempts)]
            self.retry_cursor += 1
            if view not in selected:
                selected.append(view)
        for crop, rotation in selected:
            rotated = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=np.ascontiguousarray(np.rot90(views[crop], rotation)),
            )
            result = self.alternate.detect(rotated)
            self.last_hand_count = max(self.last_hand_count, len(result.hand_landmarks))
            if joined_hands_from_landmarks(result.hand_landmarks, rotated.width, rotated.height):
                self.preferred_view = (crop, rotation)
                self.next_retry_ms = timestamp_ms + 90
                return True
        self.preferred_view = None
        self.next_retry_ms = timestamp_ms + 80
        return False

    def close(self) -> None:
        try:
            self.primary.close()
        finally:
            self.alternate.close()


def recognize_gesture(
    recognizer: MultiViewGestureRecognizer,
    image: mp.Image,
    timestamp_ms: int,
) -> tuple[str, float]:
    if isinstance(recognizer, MultiViewGestureRecognizer):
        return recognizer.recognize_gesture(image, timestamp_ms)
    return classify_gesture_result(recognizer.recognize_for_video(image, timestamp_ms), image)


def start_vanish_on_gesture(state: AppState, name: str, score: float, now: float) -> bool:
    """Start the dissolve when a reliable V sign is first recognized."""
    if state.phase == "ready" and name == "Victory" and score >= 0.62:
        state.phase = "vanishing"
        state.vanish_started = now
        return True
    return False


def start_naruto_on_join(state: AppState, joined: bool, now: float) -> bool:
    if state.phase == "ready" and joined:
        state.phase = "naruto_vanishing"
        state.vanish_started = now
        return True
    return False


def set_fullscreen(enabled: bool) -> None:
    mode = cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, mode)


def self_test() -> int:
    """Check bundled resources and model initialization without opening a webcam."""
    load_config()
    modes = edition_modes()
    required = [SEGMENTER_MODEL]
    if any(mode in modes for mode in ("normal", "particles")):
        required.append(GESTURE_MODEL)
    if any(mode in modes for mode in ("naruto", "goku", "itachi", "infinity")):
        required.append(HAND_MODEL)
    if "goku" in modes:
        required.extend((FACE_MODEL, TELEPORT_SOUND_PATH))
    if "itachi" in modes:
        required.extend((CROW_SHEET_PATH, SHARINGAN_PATH))
    if "naruto" in modes:
        required.extend((LOG_PATH, SOUND_PATH))
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing resources: {', '.join(missing)}")
    if "naruto" in modes:
        load_log()
    if "itachi" in modes:
        load_crow_sprites()
        load_sharingan_art()
    for sound_path in (SOUND_PATH, TELEPORT_SOUND_PATH):
        if sound_path not in required:
            continue
        sound = VanishSound(sound_path)
        sound.close()
    for mode in modes:
        segmenter, recognizer = create_tasks(mode)
        try:
            recognizer.close()
        finally:
            segmenter.close()
    print("[Webcam] Self-test complete: models, assets and audio are available.")
    return 0


def run(license_session=None) -> int:
    args = parse_args()
    if getattr(args, "self_test", False):
        return self_test()
    available = edition_modes()
    check = license_session.ensure_valid if license_session is not None else None
    mode = args.mode or (available[0] if len(available) == 1 else (
        choose_mode(available, check_license=check) if check else choose_mode(available)))
    if mode is None:
        return 0
    if license_session is not None:
        license_session.backend.mode = mode if mode in LICENSE_REPORTED_MODES else "full"
    if args.camera is None:
        args.camera = (choose_camera(mirror=not args.no_mirror, check_license=check)
                       if check else choose_camera(mirror=not args.no_mirror))
        if args.camera is None:
            return 0
    if mode == "goku":
        args.goku_delay = choose_goku_delay(check_license=check) if check else choose_goku_delay()
        if args.goku_delay is None:
            return 0
    with ExitStack() as resources:
        if check:
            check()
            return run_camera(args, resources, mode, license_session)
        return run_camera(args, resources, mode)


def run_camera(args: argparse.Namespace, resources: ExitStack, mode: str, license_session=None) -> int:
    download_models(mode)
    capture = open_camera(args.camera, args.width, args.height)
    resources.callback(capture.release)
    capture.set(cv2.CAP_PROP_FPS, args.fps)
    segmenter, recognizer = create_tasks(mode)
    resources.callback(segmenter.close)
    resources.callback(recognizer.close)
    log_sprite = load_log() if mode == "naruto" else None
    sound_path = {"naruto": SOUND_PATH, "goku": TELEPORT_SOUND_PATH}.get(mode)
    vanish_sound = VanishSound(sound_path) if sound_path is not None else None
    if vanish_sound is not None:
        resources.callback(vanish_sound.close)
    resources.callback(cv2.destroyAllWindows)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    capture_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    capture_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if not isinstance(capture_width, (int, float)) or capture_width <= 0:
        capture_width = args.width or 960
    if not isinstance(capture_height, (int, float)) or capture_height <= 0:
        capture_height = args.height or 540
    window_scale = min(1280 / capture_width, 720 / capture_height, 1.0)
    cv2.resizeWindow(WINDOW_NAME, round(capture_width * window_scale),
                     round(capture_height * window_scale))

    state = AppState(
        calibration_started=time.perf_counter(), fullscreen=args.fullscreen
    )
    if state.fullscreen:
        set_fullscreen(True)

    background: np.ndarray | None = None
    background_samples: list[np.ndarray] = []
    last_mask: np.ndarray | None = None
    last_mask_at = float("-inf")
    dissolve_field: np.ndarray | None = None
    sparkle_noise: np.ndarray | None = None
    log_anchor: tuple[int, int, int] | None = None
    log_cache: dict[int, np.ndarray] = {}
    vanished_frame: np.ndarray | None = None
    particle_effect: ParticleEffect | None = None
    infinity_effect: InfinityDust | None = None
    infinity_gate = SnapGesture() if mode == "infinity" else None
    infinity_hands = []
    itachi_effect: ItachiCrowEffect | None = None
    itachi_gate = ItachiGestureGate() if mode == "itachi" else None
    goku_effect: GokuTeleport | None = None
    goku_delay = getattr(args,"goku_delay",HOLD_SECONDS)
    goku_gate = GokuGestureGate(hold_seconds=goku_delay) if mode == "goku" else None
    goku_countdown_remaining: float | None = None
    virtual_camera = None
    virtual_camera_initialized = False
    calibration_remaining = None
    last_gesture_report = 0.0
    started = time.perf_counter()
    print("[Webcam] Step out of frame for 4 seconds while I capture the background.")
    if mode == "goku":
        print(f"[Webcam] Goku: hold two joined fingers to your forehead for {goku_delay:g} seconds to disappear or reappear. "
              "Release the pose before repeating the gesture.")
        print("[Webcam] Controls: SPACE recapture background, F fullscreen, Q quit.")
    else:
        print("[Webcam] Window controls: SPACE recapture background, "
              "R reappear, V vanish, F fullscreen, Q quit.")
        if mode == "itachi":
            print("[Itachi] Touch both hands together in front of the center of your chest. "
                  "Release the gesture, then repeat it to reappear.")
        elif mode == "infinity":
            print("[Infinity] Show one hand to wear the gauntlet. Bring your thumb and middle finger together, then quickly snap them apart to vanish in cosmic dust.")

    try:
        while True:
            if license_session is not None:
                license_session.ensure_valid()
            ok, camera_frame = capture.read()
            if not ok:
                raise RuntimeError("The webcam stopped returning images.")

            if not args.no_mirror:
                camera_frame = cv2.flip(camera_frame, 1)

            height, width = camera_frame.shape[:2]
            if not virtual_camera_initialized:
                virtual_camera = open_virtual_camera(args, width, height)
                virtual_camera_initialized = True
                if virtual_camera is not None:
                    resources.callback(virtual_camera.close)
            if mode == "normal" and (dissolve_field is None or dissolve_field.shape != (height, width)):
                dissolve_field, sparkle_noise = make_dissolve_fields(height, width)
            now = time.perf_counter()

            elapsed_ms = int((now - started) * 1000)
            mp_image = None

            if (mode == "itachi" and background is not None
                    and state.phase in ("ready", "vanished")
                    and now - state.last_gesture_check >= 0.09):
                state.last_gesture_check = now
                rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                last_mask, last_mask_at = mask, now
                touching = recognizer.recognize_pose(mp_image, elapsed_ms, mask)
                if args.gesture_debug and now - last_gesture_report >= 1.0:
                    print(f"[Itachi] hands={recognizer.last_hand_count}, chest pose={touching}")
                    last_gesture_report = now
                if itachi_gate.update(touching, now):
                    try:
                        itachi_effect = ItachiCrowEffect(camera_frame, mask)
                    except ValueError:
                        itachi_gate.reset()
                    else:
                        appearing = state.phase == "vanished"
                        state.phase = "itachi_appearing" if appearing else "itachi_disappearing"
                        state.vanish_started = now
                        vanished_frame = None
                        print("[Itachi] Crows are reforming." if appearing
                              else "[Itachi] Dispersing into crows.")

            if (mode == "goku" and background is not None
                    and state.phase in ("ready", "vanished")
                    and now - state.last_gesture_check >= 0.10):
                state.last_gesture_check = now
                rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                pose = recognizer.recognize_pose(mp_image, elapsed_ms)
                if args.gesture_debug and now - last_gesture_report >= 1.0:
                    held = 0.0 if goku_gate.hold_started is None else now - goku_gate.hold_started
                    print(f"[Goku] faces={recognizer.last_face_count}, "
                          f"hands={recognizer.last_hand_count}, pose={pose}, "
                          f"held={held:.2f}/{goku_gate.hold_seconds:g} s")
                    last_gesture_report = now
                if goku_gate.update(pose, now):
                    action = "Reappearing" if state.phase == "vanished" else "Disappearing"
                    print(f"[Goku] {action}!")
                    goku_countdown_remaining = None
                    mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                    goku_effect = GokuTeleport(camera_frame, background, mask)
                    appearing = state.phase == "vanished"
                    state.phase = "goku_appearing" if appearing else "goku_vanishing"
                    state.vanish_started = time.perf_counter()
                    vanish_sound.play()
                elif pose and goku_gate.armed and goku_gate.hold_started is not None:
                    left = goku_gate.hold_seconds - (now - goku_gate.hold_started)
                    remaining = (max(.1,float(np.ceil(left*10)/10)) if goku_gate.hold_seconds < 1
                                 else max(1,int(np.ceil(left))))
                    if remaining != goku_countdown_remaining:
                        action = "Reappearing" if state.phase == "vanished" else "Disappearing"
                        print(f"[Goku] {action} in {remaining:g}...")
                        goku_countdown_remaining = remaining
                elif goku_gate.hold_started is None:
                    goku_countdown_remaining = None

            if (mode == "infinity" and background is not None
                    and state.phase in ("ready", "infinity_countdown")
                    and now - state.last_gesture_check >= 0.08):
                state.last_gesture_check = now
                rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = recognizer.primary.detect_for_video(mp_image, elapsed_ms)
                infinity_hands = hand_landmarks_from_result(result, width, height)
                snapped = (infinity_gate.update(infinity_hands, now, width)
                           if state.phase == "ready" else False)
                if args.gesture_debug and now - last_gesture_report >= 1.0:
                    print(f"[Infinity] hands={len(infinity_hands)}, snap={snapped}")
                    last_gesture_report = now
                if snapped:
                    state.phase = "infinity_countdown"
                    state.vanish_started = now
                    print("[Infinity] Snap detected. Disappearing in 3 seconds...")

            if state.phase == "calibrating":
                elapsed = now - state.calibration_started
                remaining = max(0, int(np.ceil(CALIBRATION_SECONDS - elapsed)))
                if remaining != calibration_remaining:
                    print(f"[Webcam] Capturing background: {remaining} seconds.")
                    calibration_remaining = remaining
                if elapsed >= CALIBRATION_SECONDS - BACKGROUND_SAMPLE_SECONDS:
                    background_samples.append(camera_frame.copy())
                if elapsed >= CALIBRATION_SECONDS:
                    if background_samples:
                        stack = np.stack(background_samples[-18:], axis=0)
                        background = np.median(stack, axis=0).astype(np.uint8)
                    else:
                        background = camera_frame.copy()
                    background_samples.clear()
                    state.phase = "ready"
                    print("[Webcam] Background captured. You can step back into frame.")
                display = camera_frame

            elif background is None:
                state.phase = "calibrating"
                state.calibration_started = now
                display = camera_frame

            elif mode == "goku" and state.phase in ("goku_vanishing", "goku_appearing"):
                appearing = state.phase == "goku_appearing"
                age = time.perf_counter() - state.vanish_started
                display = goku_effect.render(background, age, appearing)
                if age >= TELEPORT_SECONDS:
                    state.phase = "ready" if appearing else "vanished"
                    vanished_frame = None if appearing else background.copy()

            elif mode == "itachi" and state.phase in ("itachi_disappearing", "itachi_appearing"):
                appearing = state.phase == "itachi_appearing"
                age = max(0.0, time.perf_counter() - state.vanish_started)
                display = itachi_effect.render(background, age, appearing)
                if age >= ITACHI_SECONDS:
                    state.phase = "ready" if appearing else "vanished"
                    vanished_frame = None if appearing else display
                    itachi_effect = None

            elif mode == "infinity" and state.phase == "infinity_countdown":
                age = max(0.0, time.perf_counter() - state.vanish_started)
                display = overlay_gauntlet(camera_frame, infinity_hands)
                if age >= 3.0:
                    if mp_image is None:
                        rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                    infinity_effect = InfinityDust(camera_frame, mask)
                    state.phase = "infinity_vanishing"
                    state.vanish_started = time.perf_counter()
                    display = infinity_effect.render(background, 0.0)
                    print("[Infinity] Cosmic dust!")

            elif mode == "infinity" and state.phase == "infinity_vanishing":
                age = max(0.0, time.perf_counter() - state.vanish_started)
                display = infinity_effect.render(background, age)
                if age >= INFINITY_SECONDS:
                    state.phase = "vanished"
                    vanished_frame = background.copy()

            elif state.phase == "vanished":
                if vanished_frame is None:
                    vanished_frame = background.copy()
                    if mode == "naruto" and log_anchor is not None:
                        overlay_log(vanished_frame, log_sprite, landed_log_anchor(log_anchor, height),
                                    cache=log_cache)
                display = vanished_frame

            else:
                mask = last_mask
                if (
                    state.phase == "ready"
                    and mode not in ("goku", "itachi", "infinity")
                    and now - state.last_gesture_check >=
                    (0.08 if mode == "naruto" else GESTURE_INTERVAL_SECONDS)
                ):
                    state.last_gesture_check = now
                    rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    if mode != "naruto":
                        name, score = recognize_gesture(recognizer, mp_image, elapsed_ms)
                        if args.gesture_debug and now - last_gesture_report >= 1.0:
                            print(
                                f"[Gesture] {name}, score={score:.2f}, "
                                f"ritaglio={recognizer.preferred_crop or 'full'}, "
                                f"rotazione={recognizer.preferred_rotation or 0}"
                            )
                            last_gesture_report = now
                        start_vanish_on_gesture(state, name, score, now)
                    else:
                        joined = recognizer.recognize_joined_hands(mp_image, elapsed_ms)
                        if args.gesture_debug and now - last_gesture_report >= 1.0:
                            print(f"[Hands] detected={recognizer.last_hand_count}, "
                                  f"joined={joined}, view={recognizer.preferred_view or 'full'}")
                            last_gesture_report = now
                        if start_naruto_on_join(state, joined, time.perf_counter()):
                            vanish_sound.play()

                if state.phase in ("vanishing", "naruto_vanishing"):
                    # Normal tracks the silhouette at 20 Hz. Particles captures
                    # it once; Naruto needs it only while the person is visible.
                    needs_mask = (
                        (mode == "normal" and (mask is None or now - last_mask_at >= 0.05))
                        or (mode == "particles" and particle_effect is None)
                        or (mode == "naruto" and (log_anchor is None or now - state.vanish_started < 0.13))
                    )
                    if needs_mask:
                        if mp_image is None:
                            rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                        mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                        last_mask = mask
                        last_mask_at = now
                    if mode == "naruto" and log_anchor is None:
                        log_anchor = substitution_anchor(mask)

                if mode == "naruto" and state.phase == "naruto_vanishing":
                    age = max(0.04, time.perf_counter() - state.vanish_started)
                    display = render_substitution(
                        camera_frame, background, mask, log_sprite, log_anchor, age, log_cache
                    )
                    if age >= EFFECT_SECONDS:
                        state.phase = "vanished"
                        vanished_frame = display
                elif mode == "particles" and state.phase == "vanishing":
                    if particle_effect is None:
                        particle_effect = ParticleEffect(camera_frame, mask)
                    age = time.perf_counter() - state.vanish_started
                    display = particle_effect.render(background, age)
                    if age >= PARTICLE_SECONDS:
                        state.phase = "vanished"
                        vanished_frame = display
                elif state.phase == "ready":
                    display = camera_frame
                    if mode == "infinity" and infinity_hands:
                        display = overlay_gauntlet(display, infinity_hands)
                else:
                    progress = 0.0
                    if state.phase == "vanishing" and state.vanish_started is not None:
                        progress = min(
                            1.0, (time.perf_counter() - state.vanish_started) / VANISH_SECONDS
                        )
                        if progress >= 1.0:
                            state.phase = "vanished"
                    display = apply_dissolve(
                        camera_frame, background, mask, progress, dissolve_field, sparkle_noise
                    )
                    if state.phase == "vanished":
                        vanished_frame = display

            if license_session is not None:
                license_session.ensure_valid()
            if virtual_camera is not None:
                send_virtual_frame(virtual_camera, display)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord(" "):
                state.phase = "calibrating"
                state.calibration_started = now
                state.vanish_started = None
                log_anchor = None
                last_mask = None
                last_mask_at = float("-inf")
                vanished_frame = None
                particle_effect = None
                infinity_effect = None
                infinity_hands = []
                if infinity_gate is not None:
                    infinity_gate.armed = True
                itachi_effect = None
                if itachi_gate is not None:
                    itachi_gate.reset()
                goku_effect = None
                if goku_gate is not None:
                    goku_gate.reset()
                    goku_countdown_remaining = None
                background_samples.clear()
                calibration_remaining = None
                print("[Webcam] Step out of frame for 4 seconds while I capture the new background.")
            elif key == ord("r"):
                if background is not None and mode == "itachi" and state.phase == "vanished":
                    rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                    try:
                        itachi_effect = ItachiCrowEffect(camera_frame, mask)
                    except ValueError:
                        print("[Itachi] Step back into frame before reappearing.")
                    else:
                        state.phase = "itachi_appearing"
                        state.vanish_started = time.perf_counter()
                        vanished_frame = None
                elif background is not None and mode not in ("goku", "itachi"):
                    state.phase = "ready"
                    state.vanish_started = None
                    vanished_frame = None
                    log_anchor = None
                    last_mask = None
                    last_mask_at = float("-inf")
                    particle_effect = None
            elif key == ord("v") and background is not None and mode == "itachi" and state.phase == "ready":
                rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                mask = person_mask(segmenter, mp_image, elapsed_ms, width, height)
                try:
                    itachi_effect = ItachiCrowEffect(camera_frame, mask)
                except ValueError:
                    print("[Itachi] No person detected.")
                else:
                    state.phase = "itachi_disappearing"
                    state.vanish_started = time.perf_counter()
            elif key == ord("v") and background is not None and mode not in ("goku", "itachi", "infinity"):
                state.phase = "naruto_vanishing" if mode == "naruto" else "vanishing"
                state.vanish_started = time.perf_counter()
                if mode == "naruto":
                    vanish_sound.play()
                    log_anchor = None
                vanished_frame = None
                particle_effect = None
            elif key == ord("f"):
                state.fullscreen = not state.fullscreen
                set_fullscreen(state.fullscreen)
            if virtual_camera is not None:
                virtual_camera.sleep_until_next_frame()
    finally:
        resources.close()

    return 0


def main() -> int:
    try:
        if any(flag in sys.argv[1:] for flag in ("--self-test", "--help", "-h")):
            return run()  # Model/resource checks only; never opens a camera.
        if not getattr(sys, "frozen", False):
            print("[Webcam] Running locally from Python: no online license check.")
            return run()
        session = activate_license()
        if session is None:
            return 0
        with session:
            return run(session)
    except LicenseError as error:
        print(f"[License] {error}", file=sys.stderr)
        show_license_error(error)
        return 1
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f"\n[Vanish Lab] ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
