"""Infinity gauntlet overlay, snap recognition and cosmic dust vanish."""

from __future__ import annotations

import cv2
import numpy as np


EFFECT_SECONDS = 2.6
BODY_SECONDS = 1.35


def hand_landmarks_from_result(result, width: int, height: int) -> list[np.ndarray]:
    hands = []
    for landmarks in result.hand_landmarks:
        points = np.asarray([(p.x * width, p.y * height) for p in landmarks], np.float32)
        if points.shape == (21, 2) and np.isfinite(points).all():
            hands.append(points)
    return hands


def upside_down_hands_from_result(result, width: int, height: int) -> list[np.ndarray]:
    """Map hands from a 180-degree-rotated frame back to the original space.

    Rotating by 180 degrees maps normalized (x, y) to (1 - x, 1 - y), so the
    landmarks stay valid for the gauntlet overlay and snap gate.
    """
    hands = []
    for landmarks in result.hand_landmarks:
        points = np.asarray(
            [((1 - p.x) * width, (1 - p.y) * height) for p in landmarks], np.float32
        )
        if points.shape == (21, 2) and np.isfinite(points).all():
            hands.append(points)
    return hands


class SnapGesture:
    """A deliberate thumb and middle finger pinch followed by a quick release."""

    def __init__(self):
        self.pinched_at: float | None = None
        self.pinched_points: np.ndarray | None = None
        self.armed = True
        self.release_at: float | None = None

    def update(self, hands: list[np.ndarray], now: float, frame_width: int) -> bool:
        pinched = False
        release_motion = False
        for points in hands:
            palm = max(np.linalg.norm(points[5] - points[17]),
                       np.linalg.norm(points[0] - points[9]))
            separation = np.linalg.norm(points[4] - points[12])
            if palm > frame_width * 0.012 and separation < palm * 0.28:
                pinched = True
                if self.pinched_at is None:
                    self.pinched_points = points.copy()
                break
            if (self.pinched_points is not None and palm > frame_width * 0.012
                    and separation > palm * 0.52):
                moved = np.linalg.norm((points[12] - points[0]) -
                                       (self.pinched_points[12] - self.pinched_points[0]))
                release_motion = moved > palm * 0.20
        if pinched:
            self.release_at = None
            if self.pinched_at is None:
                self.pinched_at = now
            return False
        if self.pinched_at is not None:
            duration = now - self.pinched_at
            self.pinched_at = None
            self.pinched_points = None
            if self.armed and 0.04 <= duration <= 0.55 and release_motion:
                self.armed = False
                self.release_at = now
                return True
        if not self.armed and self.release_at is not None and now - self.release_at >= 0.65:
            self.armed = True
            self.release_at = None
        return False


def overlay_gauntlet(frame: np.ndarray, hands: list[np.ndarray]) -> np.ndarray:
    """Draw the gauntlet directly over the hand landmarks."""
    output = frame.copy()
    height, width = frame.shape[:2]
    scale = min(width, height) / 540.0
    for p in hands:
        palm = p[[0, 1, 2, 5, 9, 13, 17, 0]].astype(np.int32)
        layer = output.copy()
        cv2.fillPoly(layer, [palm], (20, 116, 220), cv2.LINE_AA)
        cv2.addWeighted(layer, 0.78, output, 0.22, 0, output)
        cv2.polylines(output, [palm], True, (52, 206, 255), max(1, round(2 * scale)), cv2.LINE_AA)
        for base in (1, 5, 9, 13, 17):
            ids = [base, base + 1, base + 2, base + 3]
            for a, b in zip(ids[:-1], ids[1:]):
                cv2.line(output, tuple(p[a].astype(int)), tuple(p[b].astype(int)),
                         (19, 111, 211), max(3, round(9 * scale)), cv2.LINE_AA)
                cv2.line(output, tuple(p[a].astype(int)), tuple(p[b].astype(int)),
                         (66, 195, 255), max(1, round(3 * scale)), cv2.LINE_AA)
                cv2.circle(output, tuple(p[b].astype(int)), max(2, round(3 * scale)),
                           (10, 70, 155), -1, cv2.LINE_AA)
        for idx, color in zip((0, 5, 9, 13, 17),
                              ((210, 40, 180), (40, 220, 80), (255, 140, 30),
                               (40, 80, 245), (190, 60, 245))):
            center = tuple(p[idx].astype(int))
            radius = max(3, round((np.linalg.norm(p[5] - p[17]) * 0.11)
                                  if idx else 5 * scale))
            cv2.circle(output, center, radius + max(1, round(2 * scale)),
                       (255, 221, 117), -1, cv2.LINE_AA)
            cv2.circle(output, center, radius, color, -1, cv2.LINE_AA)
            cv2.circle(output, (center[0] - radius // 3, center[1] - radius // 3),
                       max(1, radius // 4), (255, 255, 245), -1, cv2.LINE_AA)
    return output


class InfinityDust:
    """Captured silhouette scatters as glowing gold and violet cosmic ash."""

    def __init__(self, frame: np.ndarray, mask: np.ndarray, seed: int | None = None):
        self.rng = np.random.default_rng(seed)
        self.size = mask.shape
        occupied = cv2.findNonZero((mask > 0.04).astype(np.uint8))
        self.bounds = None
        if occupied is None:
            return
        x, y, bw, bh = cv2.boundingRect(occupied)
        self.bounds = (x, y, x + bw, y + bh)
        self.area = np.s_[y:y + bh, x:x + bw]
        self.person = frame[self.area].copy()
        self.mask = mask[self.area].copy()
        coords = np.argwhere(self.mask > 0.38)
        if not len(coords):
            self.bounds = None
            return
        count = min(3000, max(180, len(coords) // 48), len(coords))
        chosen = coords[self.rng.choice(len(coords), count, replace=False)]
        self.origins = chosen[:, ::-1].astype(np.float32) + (x, y)
        self.release = self.rng.uniform(0.0, BODY_SECONDS, count).astype(np.float32)
        angle = self.rng.uniform(-2.7, 2.7, count)
        speed = self.rng.uniform(70, 310, count) * frame.shape[1] / 960
        self.vx = np.cos(angle) * speed
        self.vy = np.sin(angle) * speed - self.rng.uniform(20, 120, count)
        self.colors = np.asarray([(42, 165, 255), (68, 72, 222), (18, 205, 247),
                                  (147, 72, 232), (232, 202, 112)], np.uint8)[
            self.rng.integers(0, 5, count)]
        self.radius = self.rng.choice((1, 2, 3), count, p=(.54, .36, .10))
        self.life = self.rng.uniform(.65, 1.25, count)

    def render(self, background: np.ndarray, age: float) -> np.ndarray:
        out = background.copy()
        if self.bounds is None or age >= EFFECT_SECONDS:
            return out
        x1, y1, x2, y2 = self.bounds
        progress = float(np.clip(age / BODY_SECONDS, 0, 1))
        yy, xx = np.mgrid[0:y2-y1, 0:x2-x1]
        radial = np.sqrt(((xx/(x2-x1+1e-6))-.5)**2 + ((yy/(y2-y1+1e-6))-.5)**2)
        front = np.clip(progress * 1.45 - radial * .38, 0, 1)
        alpha = self.mask * (1.0 - front)
        crop = out[self.area].astype(np.float32)
        crop[:] = self.person * alpha[..., None] + crop * (1 - alpha[..., None])
        edge = (front > .05) & (front < .95) & (self.mask > .25)
        crop[edge] = np.clip(crop[edge] + (18, 48, 82), 0, 255)
        out[self.area] = crop.astype(np.uint8)
        elapsed = age - self.release
        active = (elapsed >= 0) & (elapsed < self.life)
        idx = np.flatnonzero(active)
        if len(idx):
            t = elapsed[idx]
            x = np.rint(self.origins[idx, 0] + self.vx[idx] * t).astype(int)
            y = np.rint(self.origins[idx, 1] + self.vy[idx] * t + 30 * t * t).astype(int)
            good = (x >= 0) & (x < out.shape[1]) & (y >= 0) & (y < out.shape[0])
            for i, px, py in zip(idx[good], x[good], y[good]):
                r = int(self.radius[i])
                cv2.circle(out, (px, py), r + 2, (90, 100, 255), -1, cv2.LINE_AA)
                cv2.circle(out, (px, py), r, tuple(map(int, self.colors[i])), -1, cv2.LINE_AA)
        return out
