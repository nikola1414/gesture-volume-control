"""Smoke test for the MediaPipe wrapper. Skipped where OpenCV or MediaPipe's legacy API is absent."""

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("cv2")
mp = pytest.importorskip("mediapipe")

if not hasattr(mp, "solutions"):
    pytest.skip("this MediaPipe build has no legacy `solutions` API", allow_module_level=True)

import handModule  # noqa: E402


def test_blank_frame_has_no_hands():
    detector = handModule.handDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    annotated = detector.findHands(frame)
    assert annotated.shape == frame.shape
    assert detector.findPositioning(annotated, draw=False) == []


def test_positioning_before_any_frame_is_empty():
    assert handModule.handDetector().findPositioning(np.zeros((10, 10, 3), dtype=np.uint8)) == []
