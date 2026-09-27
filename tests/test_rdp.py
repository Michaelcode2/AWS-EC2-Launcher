from __future__ import annotations

import pytest

from ec2_manager.config.models import RdpConfig
from ec2_manager.rdp.launcher import RdpClientError, launch_rdp, rdp_command, select_rdp_address
from tests.helpers import make_instance


def test_prefers_elastic_ip() -> None:
    instance = make_instance(elastic_ip="203.0.113.25", public_ip="198.51.100.9")
    address = select_rdp_address(instance, RdpConfig(use_elastic_ip=True))
    assert address == "203.0.113.25"


def test_profile_elastic_ip_fallback() -> None:
    instance = make_instance(elastic_ip=None, public_ip=None)
    address = select_rdp_address(
        instance, RdpConfig(use_elastic_ip=True, elastic_ip="203.0.113.80")
    )
    assert address == "203.0.113.80"


def test_rdp_command_windows() -> None:
    command = rdp_command("203.0.113.25", platform="win32")
    assert command == ["mstsc.exe", "/v:203.0.113.25"]
    assert "password" not in " ".join(command).lower()


def test_rdp_command_linux_prefers_xfreerdp() -> None:
    def which(name: str) -> str | None:
        return {
            "xfreerdp": "/usr/bin/xfreerdp",
            "xfreerdp3": "/usr/bin/xfreerdp3",
            "wlfreerdp": "/usr/bin/wlfreerdp",
        }.get(name)

    command = rdp_command("203.0.113.25", platform="linux", which=which)
    assert command == ["/usr/bin/xfreerdp", "/v:203.0.113.25"]
    assert "password" not in " ".join(command).lower()


def test_rdp_command_linux_falls_back_to_xfreerdp3() -> None:
    def which(name: str) -> str | None:
        return {
            "xfreerdp3": "/usr/bin/xfreerdp3",
            "wlfreerdp": "/usr/bin/wlfreerdp",
        }.get(name)

    command = rdp_command("203.0.113.25", platform="linux", which=which)
    assert command == ["/usr/bin/xfreerdp3", "/v:203.0.113.25"]


def test_rdp_command_linux_falls_back_to_wlfreerdp() -> None:
    def which(name: str) -> str | None:
        return {"wlfreerdp": "/usr/bin/wlfreerdp"}.get(name)

    command = rdp_command("203.0.113.25", platform="linux", which=which)
    assert command == ["/usr/bin/wlfreerdp", "/v:203.0.113.25"]


def test_rdp_command_linux_missing_client() -> None:
    with pytest.raises(RdpClientError) as excinfo:
        rdp_command("203.0.113.25", platform="linux", which=lambda _name: None)
    message = str(excinfo.value)
    assert "freerdp2-x11" in message
    assert "freerdp3-x11" in message


def test_launch_rdp_windows_does_not_pass_password() -> None:
    captured: list[list[str]] = []

    def runner(args: list[str]) -> object:
        captured.append(list(args))

        class Result:
            returncode = 0

        return Result()

    launch_rdp("203.0.113.25", runner=runner, platform="win32")
    assert captured == [["mstsc.exe", "/v:203.0.113.25"]]
    assert "password" not in " ".join(captured[0]).lower()


def test_launch_rdp_linux_uses_freerdp() -> None:
    captured: list[list[str]] = []

    def runner(args: list[str]) -> object:
        captured.append(list(args))

        class Result:
            returncode = 0

        return Result()

    launch_rdp(
        "203.0.113.25",
        runner=runner,
        platform="linux",
        which=lambda name: "/usr/bin/xfreerdp" if name == "xfreerdp" else None,
    )
    assert captured == [["/usr/bin/xfreerdp", "/v:203.0.113.25"]]
    assert "password" not in " ".join(captured[0]).lower()
