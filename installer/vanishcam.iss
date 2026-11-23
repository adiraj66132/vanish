#include "version.iss"

[Setup]
AppName=VanishCam
AppVersion={#AppVersion}
AppPublisher=Vanish Lab
DefaultDirName={localappdata}\Programs\VanishCam
DefaultGroupName=VanishCam
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=VanishCamSetup
SetupMutex=VanishCamSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\VanishCam.exe
UninstallDisplayName=VanishCam
LicenseFile=..\LICENSE
DisableProgramGroupPage=yes

[Files]
Source: "..\dist\VanishCam\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Icons]
Name: "{group}\VanishCam"; Filename: "{app}\VanishCam.exe"
Name: "{group}\Uninstall VanishCam"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VanishCam"; Filename: "{app}\VanishCam.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VanishCam.exe"; Description: "Launch VanishCam"; Flags: nowait postinstall skipifsilent
