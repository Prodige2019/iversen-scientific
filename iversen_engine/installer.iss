[Setup]
AppName=Iversen Scientific
AppVersion=1.0
DefaultDirName={autopf}\Iversen Scientific
DefaultGroupName=Iversen Scientific
OutputBaseFilename=IversenScientific-Setup
OutputDir=installer_output
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
Source: "dist\IversenScientific\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Iversen Scientific"; Filename: "{app}\IversenScientific.exe"
Name: "{autodesktop}\Iversen Scientific"; Filename: "{app}\IversenScientific.exe"

[Run]
Filename: "{app}\IversenScientific.exe"; Description: "Lancer Iversen Scientific"; Flags: nowait postinstall skipifsilent
