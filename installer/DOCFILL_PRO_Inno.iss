#define MyAppName "DocFill Pro"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "DocFill Pro"
#define MyAppExeName "DOCFILL PRO.exe"

[Setup]
AppId={{8F96A00B-5A20-4C29-8F1E-6F12B4B8C201}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\DocFillPro
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=DOCFILL_PRO_Inno_Setup
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl,ChineseSimplified.isl"

[CustomMessages]
DesktopShortcutDescription=Create a desktop shortcut
ShortcutsGroup=Shortcuts:
OpenApp=Open DocFill Pro

[CustomMessages.brazilianportuguese]
DesktopShortcutDescription=Criar atalho na Área de Trabalho
ShortcutsGroup=Atalhos:
OpenApp=Abrir DocFill Pro

[CustomMessages.chinesesimplified]
DesktopShortcutDescription=创建桌面快捷方式
ShortcutsGroup=快捷方式:
OpenApp=打开 DocFill Pro

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcutDescription}"; GroupDescription: "{cm:ShortcutsGroup}"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\data\template_semantic_mappings.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\template_profiles.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\history.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion
Source: "..\data\user_session.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
Type: files; Name: "{autodesktop}\DOCFILL PRO.lnk"
Type: files; Name: "{group}\DOCFILL PRO.lnk"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:OpenApp}"; Flags: nowait postinstall skipifsilent
