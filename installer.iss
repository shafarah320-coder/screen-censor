#define MyAppName "Screen Censor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Screen Censor"
#define MyAppExeName "ScreenCensor.exe"

[Setup]
AppId={{7E1F2B73-89D1-4E8A-9B1B-8E5D1D52C440}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Screen Censor
DefaultGroupName=Screen Censor
OutputDir=output
OutputBaseFilename=ScreenCensor_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut tambahan:"

[Files]
Source: "dist\ScreenCensor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Screen Censor"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Screen Censor"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Jalankan Screen Censor"; Flags: postinstall nowait skipifsilent
