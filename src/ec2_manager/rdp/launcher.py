from __future__ import annotations

import socket
import subprocess
from collections.abc import Callable, Sequence

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.config.models import RdpConfig

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[bytes]]


def select_rdp_address(instance: Ec2Instance, rdp: RdpConfig) -> str | None:
    if rdp.use_elastic_ip:
        return instance.elastic_ip or rdp.elastic_ip or instance.public_ip
    return instance.public_ip or instance.elastic_ip or rdp.elastic_ip


def rdp_ready(address: str, *, port: int = 3389, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((address, port), timeout=timeout):
            return True
    except OSError:
        return False


def launch_rdp(
    address: str,
    *,
    runner: Runner | None = None,
) -> None:
    command = ["mstsc.exe", f"/v:{address}"]
    execute = runner or (
        lambda args: subprocess.run(list(args), check=False, capture_output=True)
    )
    execute(command)
