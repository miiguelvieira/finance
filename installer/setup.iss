; Inno Setup 6+ — Finance Gestão Financeira Pessoal
; Uso: ISCC setup.iss /DAppVersion=1.0.0

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppName=Finance — Gestão Financeira Pessoal
AppVersion={#AppVersion}
AppPublisher=Miguel Vieira
AppPublisherURL=https://github.com/miguel-vieira
DefaultDirName={autopf}\Finance
DefaultGroupName=Finance
OutputDir=installer\output
OutputBaseFilename=Finance-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\finance.exe
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\finance\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Finance"; Filename: "{app}\finance.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{commondesktop}\Finance"; Filename: "{app}\finance.exe"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Run]
Filename: "{app}\finance.exe"; Description: "Iniciar Finance"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
