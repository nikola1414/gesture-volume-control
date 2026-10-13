import sys
import types

import pytest

import volume


class TestNullVolume:
    def test_records_a_clamped_integer(self):
        v = volume.NullVolume()
        v.set_percent(42.6)
        assert v.percent == 43
        v.set_percent(250)
        assert v.percent == 100
        v.set_percent(-5)
        assert v.percent == 0


class TestBackendSelection:
    def test_disabled_gives_a_dry_run(self):
        assert isinstance(volume.create_volume_controller(enabled=False), volume.NullVolume)

    def test_macos(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        assert isinstance(volume.create_volume_controller(), volume.MacVolume)

    def test_linux(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr(volume.shutil, "which", lambda name: "/usr/bin/" + name)
        assert isinstance(volume.create_volume_controller(), volume.LinuxVolume)

    def test_falls_back_to_a_dry_run_when_the_backend_cannot_start(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr(volume.shutil, "which", lambda name: None)
        assert isinstance(volume.create_volume_controller(), volume.NullVolume)
        assert "unavailable" in capsys.readouterr().out


class TestCommands:
    def record(self, monkeypatch):
        calls = []
        monkeypatch.setattr(volume.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
        return calls

    def test_macos_command(self, monkeypatch):
        calls = self.record(monkeypatch)
        volume.MacVolume().set_percent(37.4)
        assert calls == [["osascript", "-e", "set volume output volume 37"]]

    def test_linux_prefers_pactl(self, monkeypatch):
        calls = self.record(monkeypatch)
        monkeypatch.setattr(volume.shutil, "which", lambda name: "/bin/" + name)
        volume.LinuxVolume().set_percent(80)
        assert calls == [["pactl", "set-sink-volume", "@DEFAULT_SINK@", "80%"]]

    def test_linux_falls_back_to_amixer(self, monkeypatch):
        calls = self.record(monkeypatch)
        monkeypatch.setattr(volume.shutil, "which", lambda name: "/bin/amixer" if name == "amixer" else None)
        volume.LinuxVolume().set_percent(120)
        assert calls == [["amixer", "-q", "set", "Master", "100%"]]


class FakeEndpoint:
    def __init__(self):
        self.scalars = []

    def SetMasterVolumeLevelScalar(self, scalar, context):
        self.scalars.append(scalar)


def install_fake_pycaw(monkeypatch, device):
    comtypes = types.ModuleType("comtypes")
    comtypes.CLSCTX_ALL = 23
    pycaw_pkg = types.ModuleType("pycaw")
    pycaw = types.ModuleType("pycaw.pycaw")

    class IAudioEndpointVolume:
        _iid_ = "iid"

    class AudioUtilities:
        @staticmethod
        def GetSpeakers():
            return device

    pycaw.AudioUtilities = AudioUtilities
    pycaw.IAudioEndpointVolume = IAudioEndpointVolume
    monkeypatch.setitem(sys.modules, "comtypes", comtypes)
    monkeypatch.setitem(sys.modules, "pycaw", pycaw_pkg)
    monkeypatch.setitem(sys.modules, "pycaw.pycaw", pycaw)


class TestWindowsVolume:
    def test_uses_the_endpoint_exposed_by_newer_pycaw(self, monkeypatch):
        endpoint = FakeEndpoint()
        install_fake_pycaw(monkeypatch, types.SimpleNamespace(EndpointVolume=endpoint))
        volume.WindowsVolume().set_percent(25)
        assert endpoint.scalars == [0.25]

    def test_falls_back_to_activate_for_older_pycaw(self, monkeypatch):
        endpoint = FakeEndpoint()
        device = types.SimpleNamespace(Activate=lambda iid, ctx, params: "raw-interface")
        install_fake_pycaw(monkeypatch, device)
        # ctypes cannot wrap fake objects, so stub its helpers for this test.
        import ctypes

        monkeypatch.setattr(ctypes, "POINTER", lambda cls: cls)
        monkeypatch.setattr(ctypes, "cast", lambda interface, pointer_type: endpoint)
        volume.WindowsVolume().set_percent(100)
        assert endpoint.scalars == [1.0]

    def test_missing_pycaw_degrades_to_a_dry_run(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setitem(sys.modules, "pycaw", None)
        monkeypatch.setitem(sys.modules, "pycaw.pycaw", None)
        assert isinstance(volume.create_volume_controller(), volume.NullVolume)


@pytest.mark.parametrize("percent,expected", [(0, 0), (49.5, 50), (100, 100), (101, 100), (-1, 0)])
def test_clamping(percent, expected):
    assert volume._clamp_percent(percent) == expected
