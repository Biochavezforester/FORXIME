; Inno Setup Script for FORXIME/2
; Optimized for Windows 10/11 - Professional Distribution

#define MyAppName "FORXIME"
#define MyAppVersion "2.0.2"
; Version updated to 2.0.2 (removed filters and chart limit)
#define MyAppPublisher "BioChavezForester"
#define MyAppURL "https://biochavezforester.com"
#define MyAppExeName "FORXIME_PORTABLE.vbs"
#define MyAppIcon "app\assets\icon.ico"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{E6C6F2A5-91B1-48C0-B77F-4B1C64D3F79E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright="Copyright (C) 2026 BioChavezForester"
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="FORXIME Installer"
DefaultDirName={autopf}\BioChavez\FORXIME
DisableDirPage=no
DisableProgramGroupPage=yes
; Fix 2: Full registration for uninstallation in Apps & Features
UninstallDisplayIcon={app}\{#MyAppIcon}
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=forxime_setup_v202
SetupIconFile=PORTABLE\{#MyAppIcon}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all files from the current PORTABLE directory
Source: "PORTABLE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Fix 1: Desktop shortcut directly on the Desktop, as a standalone app
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"; Tasks: desktopicon
; Start Menu Shortcut
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"

[Run]
; Option to run after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall skipifsilent
