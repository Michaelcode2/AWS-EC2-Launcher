from __future__ import annotations

import shutil
import socket
import subprocess
import sys
from collections.abc import Callable, Sequence

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.config.models import RdpConfig

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[bytes]]
Which = Callable[[str], str | None]

_LINUX_RDP_CLIENTS = ("xfreerdp", "xfreerdp3", "wlfreerdp")


class RdpClientError(RuntimeError):
    """Raised when no platform Remote Desktop client is available."""


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


def rdp_command(
    address: str,
    *,
    platform: str | None = None,
    which: Which | None = None,
) -> list[str]:
    """Build the platform Remote Desktop launch command without a password."""
    current = sys.platform if platform is None else platform
    if current == "win32":
        return ["mstsc.exe", f"/v:{address}"]

    locate = which or shutil.which
    for name in _LINUX_RDP_CLIENTS:
        path = locate(name)
        if path:
            return [path, f"/v:{address}"]
    raise RdpClientError(
        "No FreeRDP client was found on PATH. "
        "Install freerdp2-x11 or freerdp3-x11, then try Connect RDP again."
    )


def launch_rdp(
    address: str,
    *,
    runner: Runner | None = None,
    platform: str | None = None,
    which: Which | None = None,
) -> None:
    command = rdp_command(address, platform=platform, which=which)
    execute = runner or (
        lambda args: subprocess.run(list(args), check=False, capture_output=True)
    )
    execute(command)
