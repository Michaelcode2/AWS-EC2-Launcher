from __future__ import annotations

import platform
from pathlib import Path

import ec2_manager
from ec2_manager.host import paths


def test_package_dir_does_not_shadow_stdlib_platform() -> None:
    """Nuitka compiles main.py from this directory, so it is on sys.path."""
    pkg_dir = Path(ec2_manager.__file__).resolve().parent
    assert not (pkg_dir / "platform").exists()
    assert not (pkg_dir / "platform.py").exists()
    assert callable(platform.system)
    assert isinstance(platform.system(), str)


def test_bundled_config_dir_source_tree() -> None:
    expected = Path(ec2_manager.__file__).resolve().parents[2] / "config"
    assert paths.bundled_config_dir() == expected
    assert (paths.bundled_config_dir() / "example-profile.toml").is_file()


def test_bundled_config_dir_compiled(monkeypatch, tmp_path: Path) -> None:
    binary = tmp_path / "Ec2DesktopManager"
    binary.write_text("", encoding="utf-8")
    (tmp_path / "config").mkdir()
    monkeypatch.setattr(paths.sys, "executable", str(binary))
    assert paths.bundled_config_dir(compiled=True) == tmp_path / "config"


def test_bundled_config_dir_source_override() -> None:
    assert paths.bundled_config_dir(compiled=False) == (
        Path(ec2_manager.__file__).resolve().parents[2] / "config"
    )


def test_ensure_user_config_seeds_example(tmp_path: Path, monkeypatch) -> None:
    data_home = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setattr(paths.sys, "platform", "linux")
    example = tmp_path / "example-profile.toml"
    example.write_text('name = "demo"\n', encoding="utf-8")

    config_dir = paths.ensure_user_config(example_source=example)

    assert config_dir == data_home / "Ec2DesktopManager" / "config"
    seeded = config_dir / "example-profile.toml"
    assert seeded.is_file()
    assert seeded.read_text(encoding="utf-8") == 'name = "demo"\n'


def test_ensure_user_config_keeps_existing_profile(tmp_path: Path, monkeypatch) -> None:
    data_home = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setattr(paths.sys, "platform", "linux")
    config_dir = data_home / "Ec2DesktopManager" / "config"
    config_dir.mkdir(parents=True)
    existing = config_dir / "customer.toml"
    existing.write_text('name = "keep-me"\n', encoding="utf-8")
    example = tmp_path / "example-profile.toml"
    example.write_text('name = "demo"\n', encoding="utf-8")

    paths.ensure_user_config(example_source=example)

    assert existing.read_text(encoding="utf-8") == 'name = "keep-me"\n'
    assert not (config_dir / "example-profile.toml").exists()


def test_ensure_user_config_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    data_home = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setattr(paths.sys, "platform", "linux")
    example = tmp_path / "example-profile.toml"
    example.write_text('name = "demo"\n', encoding="utf-8")

    first = paths.ensure_user_config(example_source=example)
    seeded = first / "example-profile.toml"
    seeded.write_text('name = "edited"\n', encoding="utf-8")
    paths.ensure_user_config(example_source=example)

    assert seeded.read_text(encoding="utf-8") == 'name = "edited"\n'
