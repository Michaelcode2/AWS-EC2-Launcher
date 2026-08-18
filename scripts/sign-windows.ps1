$ErrorActionPreference = "Stop"
if (-not $env:SIGNING_CERT_PFX) {
    Write-Host "SIGNING_CERT_PFX is not set; skipping Authenticode signing."
    exit 0
}

$Pfx = Join-Path $env:TEMP "codesign.pfx"
[IO.File]::WriteAllBytes($Pfx, [Convert]::FromBase64String($env:SIGNING_CERT_PFX))

$Signtool = Get-ChildItem -Path "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $Signtool) {
    throw "signtool.exe was not found."
}

$Targets = Get-ChildItem -Path dist -Recurse -Include *.exe
foreach ($Target in $Targets) {
    & $Signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /f $Pfx /p $env:SIGNING_CERT_PASSWORD $Target.FullName
}
Remove-Item $Pfx -Force
Write-Host "Signed $($Targets.Count) executable(s)."
