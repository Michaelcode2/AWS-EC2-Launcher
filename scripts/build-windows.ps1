$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VersionMatch = Select-String -Path "pyproject.toml" -Pattern '^\s*version = "([^"]+)"' | Select-Object -First 1
if (-not $VersionMatch) {
    throw "Could not read project version from pyproject.toml"
}
$Version = $VersionMatch.Matches[0].Groups[1].Value
Write-Host "Building EC2 Desktop Manager $Version"

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
New-Item -ItemType Directory -Path "dist\nuitka" -Force | Out-Null

python -m nuitka `
    --standalone `
    --assume-yes-for-downloads `
    --enable-plugin=pyside6 `
    --windows-console-mode=disable `
    --windows-icon-from-ico=assets\app.ico `
    --include-data-dir=config=config `
    --include-package-data=ec2_manager `
    --company-name="EC2 Desktop Manager" `
    --product-name="EC2 Desktop Manager" `
    --file-version=$Version `
    --product-version=$Version `
    --output-dir=dist\nuitka `
    --output-filename=Ec2DesktopManager.exe `
    src\ec2_manager\main.py

$Inno = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Inno) {
    throw "Inno Setup 6 is not installed. Install it or run this script on the Windows CI runner."
}

New-Item -ItemType Directory -Path "dist\installer" -Force | Out-Null
& $Inno "installer\ec2-manager.iss"
Write-Host "Installer written under dist\installer"
