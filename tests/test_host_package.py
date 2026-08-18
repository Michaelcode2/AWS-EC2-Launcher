from __future__ import annotations

import platform
from pathlib import Path

import ec2_manager


def test_package_dir_does_not_shadow_stdlib_platform() -> None:
    """Nuitka compiles main.py from this directory, so it is on sys.path."""
    pkg_dir = Path(ec2_manager.__file__).resolve().parent
    assert not (pkg_dir / "platform").exists()
    assert not (pkg_dir / "platform.py").exists()
    assert callable(platform.system)
    assert isinstance(platform.system(), str)
