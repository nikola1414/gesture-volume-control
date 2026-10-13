# Gesture Volume Control

[![CI](https://github.com/nikola1414/gesture-volume-control/actions/workflows/ci.yml/badge.svg)](https://github.com/nikola1414/gesture-volume-control/actions/workflows/ci.yml)

Change your computer's volume by pinching your thumb and index finger in front of a webcam. Hand landmarks come from MediaPipe, OpenCV handles the camera and the on-screen overlay, and the pinch distance is mapped to a 0-100 % system volume.

## How it works

1. `handModule.py` wraps MediaPipe Hands and returns the 21 landmarks of the detected hand.
2. `gesture.py` measures the distance between the thumb tip and the index fingertip and divides it by the palm size (wrist to index knuckle). Using a ratio means the result does not change when you move closer to or further from the camera.
3. The ratio is mapped linearly onto 0-100 % (clamped) and smoothed with an exponential moving average to remove jitter.
4. `volume.py` sends the value to the operating system, only when the whole-number percentage changes.

| Platform | Backend |
| --- | --- |
| Windows | Core Audio through [pycaw](https://github.com/AndreMiras/pycaw) |
| macOS | `osascript` |
| Linux | `pactl` (PulseAudio / PipeWire), falling back to `amixer` |

If a backend cannot start, the program falls back to a dry run that only shows the detected volume.

## Run it

Requires Python 3.12 and a webcam.

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Press `q` in the window to quit.

| Option | Meaning |
| --- | --- |
| `--dry-run` | Show the detected volume without changing the system volume |
| `--camera N` | Use camera number N (default 0) |
| `--closed R` | Pinch ratio that counts as 0 % (default 0.15) |
| `--open R` | Pinch ratio that counts as 100 % (default 1.0) |

If the range feels too short or too long for your hand, adjust `--closed` and `--open`.

## Tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

The gesture maths and the volume backends are covered by unit tests that need no camera: pinch ratio and scale independence, clamping, smoothing, platform selection, the exact OS commands, and both pycaw API shapes (with a fake module). A MediaPipe smoke test runs when OpenCV and MediaPipe are installed. GitHub Actions runs lint and tests on every push.

## Files

```text
main.py          camera loop, overlay and command-line options
handModule.py    MediaPipe hand detector wrapper
gesture.py       pinch ratio, mapping and smoothing (pure Python)
volume.py        system volume backends
tests/           pytest suite
```

`py-hand-tracker` (a separate repository) contains the standalone hand-tracking demo this project grew out of.
