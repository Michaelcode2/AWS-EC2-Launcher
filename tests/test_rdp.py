from __future__ import annotations

from ec2_manager.config.models import RdpConfig
from ec2_manager.rdp.launcher import launch_rdp, select_rdp_address
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


def test_launch_rdp_does_not_pass_password() -> None:
    captured: list[list[str]] = []

    def runner(args):
        captured.append(list(args))

        class Result:
            returncode = 0

        return Result()

    launch_rdp("203.0.113.25", runner=runner)
    assert captured == [["mstsc.exe", "/v:203.0.113.25"]]
    joined = " ".join(captured[0]).lower()
    assert "password" not in joined
