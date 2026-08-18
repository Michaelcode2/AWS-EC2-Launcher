#define AppName "EC2 Desktop Manager"
#define AppVersion "0.1.0"
#define AppPublisher "EC2 Desktop Manager"
#define AppExeName "Ec2DesktopManager.exe"

[Setup]
AppId={{8C3E0E7A-6B1A-4F2D-9C44-A1B2C3D4E5F6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\EC2 Desktop Manager
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=EC2DesktopManager-{#AppVersion}
SetupIconFile=..\assets\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\nuitka\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\example-profile.toml"; DestDir: "{app}\config"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function AwsCliFound: Boolean;
begin
  Result := FileExists(ExpandConstant('{pf}\Amazon\AWSCLIV2\aws.exe')) or
            FileExists(ExpandConstant('{pf32}\Amazon\AWSCLIV2\aws.exe')) or
            (FileSearch('aws.exe', GetEnv('PATH')) <> '');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{localappdata}\Ec2DesktopManager\config');
    ForceDirectories(ConfigDir);
    if not FileExists(ConfigDir + '\example-profile.toml') then
      FileCopy(ExpandConstant('{app}\config\example-profile.toml'), ConfigDir + '\example-profile.toml', False);
    if not AwsCliFound then
      MsgBox('AWS CLI v2 was not detected. Install AWS CLI v2 before signing in with IAM Identity Center.', mbInformation, MB_OK);
  end;
end;
