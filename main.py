"""Control the system volume by pinching your thumb and index finger in front of a webcam."""

import argparse
import time

import cv2

import gesture
import handModule as hm
from volume import create_volume_controller

WINDOW = "Volume Controller"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0, help="camera index (default: 0)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the detected volume but do not change the system volume",
    )
    parser.add_argument(
        "--closed",
        type=float,
        default=gesture.DEFAULT_CLOSED_RATIO,
        help="pinch ratio that means 0%% (default: %(default)s)",
    )
    parser.add_argument(
        "--open",
        type=float,
        default=gesture.DEFAULT_OPEN_RATIO,
        dest="open_",
        help="pinch ratio that means 100%% (default: %(default)s)",
    )
    return parser.parse_args()


def draw_overlay(img, landmarks, percent, fps, backend_name):
    """Draws the pinch line, the volume bar, the percentage and the frame rate."""
    thumb = next(((x, y) for i, x, y in landmarks if i == gesture.THUMB_TIP), None)
    index = next(((x, y) for i, x, y in landmarks if i == gesture.INDEX_TIP), None)
    if thumb and index:
        cv2.line(img, thumb, index, (255, 0, 255), 3)
        cv2.circle(img, thumb, 12, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, index, 12, (255, 0, 255), cv2.FILLED)
        middle = ((thumb[0] + index[0]) // 2, (thumb[1] + index[1]) // 2)
        cv2.circle(img, middle, 8, (0, 255, 0) if percent > 0 else (0, 0, 255), cv2.FILLED)

    top, bottom = 150, 400
    filled = int(bottom - (bottom - top) * percent / 100)
    cv2.rectangle(img, (50, top), (85, bottom), (0, 255, 0), 3)
    cv2.rectangle(img, (50, filled), (85, bottom), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f"{int(percent)} %", (40, 440), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(img, f"FPS: {int(fps)}   Output: {backend_name}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)


def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {args.camera}.")

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, 1280, 720)

    detector = hm.handDetector(maxHands=1)
    volume = create_volume_controller(enabled=not args.dry_run)
    smoother = gesture.Smoother(alpha=0.3)
    percent, last_sent, previous_time = 0.0, None, time.time()

    while True:
        success, img = cap.read()
        if not success:
            print("Could not read a frame from the camera.")
            break

        img = detector.findHands(img)
        landmarks = detector.findPositioning(img, draw=False)

        ratio = gesture.pinch_ratio(landmarks)
        if ratio is None:
            smoother.reset()  # hand left the frame: start fresh when it returns
        else:
            percent = smoother.update(gesture.ratio_to_percent(ratio, args.closed, args.open_))
            if int(percent) != last_sent:  # only talk to the OS when the value changes
                volume.set_percent(percent)
                last_sent = int(percent)

        now = time.time()
        fps = 1 / max(now - previous_time, 1e-6)
        previous_time = now

        draw_overlay(img, landmarks, percent, fps, volume.name)
        cv2.imshow(WINDOW, img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
