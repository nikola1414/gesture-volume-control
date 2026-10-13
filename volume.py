"""System volume backends. Pick one with ``create_volume_controller``."""

import shutil
import subprocess
import sys


def _clamp_percent(percent):
    return int(round(min(100, max(0, percent))))


class NullVolume:
    """Does not touch the system volume. Used for dry runs and when no backend is available."""

    name = "dry run"

    def __init__(self):
        self.percent = None

    def set_percent(self, percent):
        self.percent = _clamp_percent(percent)


class WindowsVolume:
    """Windows Core Audio through the pycaw package."""

    name = "Windows"

    def __init__(self):
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        speakers = AudioUtilities.GetSpeakers()
        # Newer pycaw versions expose the endpoint directly; older ones need Activate().
        endpoint = getattr(speakers, "EndpointVolume", None)
        if endpoint is None:
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            endpoint = cast(interface, POINTER(IAudioEndpointVolume))
        self._endpoint = endpoint

    def set_percent(self, percent):
        self._endpoint.SetMasterVolumeLevelScalar(_clamp_percent(percent) / 100, None)


class MacVolume:
    name = "macOS"

    def set_percent(self, percent):
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {_clamp_percent(percent)}"],
            check=False,
        )


class LinuxVolume:
    """PulseAudio / PipeWire (pactl) with an ALSA (amixer) fallback."""

    name = "Linux"

    def __init__(self):
        if shutil.which("pactl"):
            self._command = lambda p: ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{p}%"]
        elif shutil.which("amixer"):
            self._command = lambda p: ["amixer", "-q", "set", "Master", f"{p}%"]
        else:
            raise RuntimeError("neither pactl nor amixer is installed")

    def set_percent(self, percent):
        subprocess.run(self._command(_clamp_percent(percent)), check=False)


def create_volume_controller(enabled=True):
    """Returns the backend for this OS, or a NullVolume if disabled or unavailable."""
    if not enabled:
        return NullVolume()
    try:
        if sys.platform == "win32":
            return WindowsVolume()
        if sys.platform == "darwin":
            return MacVolume()
        return LinuxVolume()
    except Exception as error:  # missing package, no audio device, ...
        print(f"System volume control unavailable ({error}); running as a dry run.")
        return NullVolume()
