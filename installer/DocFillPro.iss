#define MyAppName "DOCFILL PRO"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "DOCFILL PRO"
#define MyAppExeName "DOCFILL PRO.exe"

[Setup]
AppId={{8F96A00B-5A20-4C29-8F1E-6F12B4B8C201}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\DocFillPro
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=DOCFILL_PRO_SETUP
SetupIconFile=..\assets\icons\docfill.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
DesktopShortcutDescription=Create a desktop shortcut
ShortcutsGroup=Shortcuts:
OpenApp=Open DOCFILL PRO

[CustomMessages.brazilianportuguese]
DesktopShortcutDescription=Criar atalho na Area de Trabalho
ShortcutsGroup=Atalhos:
OpenApp=Abrir DOCFILL PRO

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcutDescription}"; GroupDescription: "{cm:ShortcutsGroup}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\mappings.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\template_semantic_mappings.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\template_profiles.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\history.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\user_session.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\DocFill Pro.lnk"
Type: files; Name: "{autodesktop}\DOCFILL PRO.lnk"
Type: files; Name: "{group}\DocFill Pro.lnk"
Type: files; Name: "{group}\DOCFILL PRO.lnk"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:OpenApp}"; Flags: nowait postinstall skipifsilent
