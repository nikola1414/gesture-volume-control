"""Pure hand-gesture maths: turns hand landmarks into a volume percentage.

This module deliberately imports nothing heavy (no OpenCV, no MediaPipe) so it can be
unit-tested anywhere. Landmarks are the ``[id, x, y]`` triples produced by
``handModule.handDetector.findPositioning`` (MediaPipe hand landmark ids).
"""

import math

WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5  # knuckle at the base of the index finger
INDEX_TIP = 8

# Pinch ratio = thumb-to-index distance divided by palm size, so the result does not
# depend on how far the hand is from the camera.
DEFAULT_CLOSED_RATIO = 0.15  # fingertips touching  -> 0 %
DEFAULT_OPEN_RATIO = 1.00    # fingers spread wide  -> 100 %


def _point(landmarks, landmark_id):
    """Returns (x, y) for a landmark id, or None if it is missing."""
    for lm_id, x, y in landmarks:
        if lm_id == landmark_id:
            return x, y
    return None


def pinch_ratio(landmarks):
    """Thumb-tip to index-tip distance relative to palm size, or None if not measurable."""
    thumb = _point(landmarks, THUMB_TIP)
    index = _point(landmarks, INDEX_TIP)
    wrist = _point(landmarks, WRIST)
    knuckle = _point(landmarks, INDEX_MCP)
    if None in (thumb, index, wrist, knuckle):
        return None

    palm = math.dist(wrist, knuckle)
    if palm == 0:
        return None
    return math.dist(thumb, index) / palm


def ratio_to_percent(ratio, closed=DEFAULT_CLOSED_RATIO, open_=DEFAULT_OPEN_RATIO):
    """Maps a pinch ratio linearly onto 0-100 and clamps it."""
    if open_ <= closed:
        raise ValueError("open_ must be greater than closed")
    fraction = (ratio - closed) / (open_ - closed)
    return 100.0 * min(1.0, max(0.0, fraction))


class Smoother:
    """Exponential moving average; removes jitter from the tracked landmarks."""

    def __init__(self, alpha=0.3):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = alpha
        self.value = None

    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

    def reset(self):
        self.value = None
