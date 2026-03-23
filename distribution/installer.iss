; ============================================================
;                   LyROI Installer Script
; ============================================================
; This installer:
;  - Downloads Miniforge automatically (if missing)
;  - Creates isolated conda environment
;  - Installs PyTorch (CPU or CUDA)
;  - Installs your PyPI package
;  - Creates shortcuts
;  - Removes environment on uninstall
; ============================================================

#define MyAppName "LyROI"
#define MyAppVersion "1.0"
#define GUIexec "lyroi_gui.exe"
#define PyPIpackage "lyroi"
#define MyEnvName "lyroi-app"
#define CondaDir "{localappdata}\Miniforge3"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=LyROI-setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Icons]
; Start Menu shortcut
Name: "{userprograms}\{#MyAppName}"; Filename: "{code:GetEnvPath}/Scripts/{#GUIexec}";
; Desktop shortcut
Name: "{userdesktop}\{#MyAppName}"; Filename: "{code:GetEnvPath}/Scripts/{#GUIexec}";
  

[Code]

var
  CpuRadio: TRadioButton;
  CudaRadio: TRadioButton;
  CudaLatestRadio: TRadioButton;

// ; ------------------------------------------------------------
// ; Returns full path to conda executable
// ; ------------------------------------------------------------
function GetCondaPath(Param: String): String;
begin
  Result := ExpandConstant('{#CondaDir}\Scripts\conda.exe');
end;

function GetEnvPath(Param: String): String;
begin
  Result := ExpandConstant('{app}\{#MyEnvName}')
end;

function GetPython(Param: String): String;
begin
  Result := GetEnvPath('') + '\python.exe'
end;

// ; ------------------------------------------------------------
// ; Check if Miniforge already exists
// ; ------------------------------------------------------------
function CondaInstalled(): Boolean;
begin
  Result := FileExists(GetCondaPath(''));
end;

// ; ------------------------------------------------------------
// ; Create hardware selection page
// ; ------------------------------------------------------------
procedure InitializeWizard;
var
  Page: TWizardPage;
begin
  Page := CreateCustomPage(wpSelectComponents,
    'Hardware Selection',
    'Select hardware acceleration');

  CpuRadio := TRadioButton.Create(Page.Surface);
  CpuRadio.Parent := Page.Surface;
  CpuRadio.Caption := 'CPU (no NVIDIA GPU available)';
  CpuRadio.Top := 16;
  CpuRadio.Left := 16;
  CpuRadio.Width := Page.SurfaceWidth - 32;
  CpuRadio.Checked := True;

  CudaRadio := TRadioButton.Create(Page.Surface);
  CudaRadio.Parent := Page.Surface;
  CudaRadio.Caption := 'CUDA 12.6 (NVIDIA GPU, recommended)';
  CudaRadio.Top := CpuRadio.Top + CpuRadio.Height + ScaleY(8);
  CudaRadio.Left := 16;
  CudaRadio.Width := Page.SurfaceWidth - 32;
  
  CudaLatestRadio := TRadioButton.Create(Page.Surface);
  CudaLatestRadio.Parent := Page.Surface;
  CudaLatestRadio.Caption := 'CUDA 13.0 (NVIDIA GPU, latest models)';
  CudaLatestRadio.Top := CudaRadio.Top + CudaRadio.Height + ScaleY(8);
  CudaLatestRadio.Left := 16;
  CudaLatestRadio.Width := Page.SurfaceWidth - 32;
  
end;

// ; ------------------------------------------------------------
// ; Update installer status text
// ; ------------------------------------------------------------
procedure UpdateStatus(Msg: String);
begin
  WizardForm.StatusLabel.Caption := Msg;
end;

// ; ------------------------------------------------------------
// ; Execute external process silently
// ; Fails installer if command returns non-zero
// ; ------------------------------------------------------------
procedure RunOrFail(FileName, Params: String);
var
  ResultCode: Integer;
  //Path: String;
begin
  //Path := GetEnv('PATH')
  //if not ExecAndLogOutput(
  //            'cmd.exe',
  //            '/C set "PATH=' + Path + '"' +
  //            ' && ' +
  //            FileName + ' ' + Params,
  //            '',
  //            SW_SHOW, ewWaitUntilTerminated, ResultCode, nil)
    if not ExecAndLogOutput(FileName, Params,
              '',
              SW_HIDE, ewWaitUntilTerminated, ResultCode, nil)
     or (ResultCode <> 0) then
  begin
    MsgBox('Installation failed during: ' + Params,
           mbCriticalError, MB_OK);
    RaiseException('Error during execution')
  end;
end;

// ; ------------------------------------------------------------
// ; Download Miniforge installer dynamically
// ; ------------------------------------------------------------
procedure DownloadMiniforge;
var
  Url: String;
  TargetFile: String;
begin
  Url :=
   'https://github.com/conda-forge/miniforge/releases/latest/download/' +
   'Miniforge3-Windows-x86_64.exe';

  TargetFile :='Miniforge3.exe';

  UpdateStatus('Downloading Miniforge...');

  DownloadTemporaryFile(Url, TargetFile, '', nil);
end;

// ; ------------------------------------------------------------
// ; Install Miniforge silently if not already installed
// ; ------------------------------------------------------------
procedure InstallMiniforge;
begin
  if not CondaInstalled() then
  begin
    DownloadMiniforge;

    UpdateStatus('Installing Miniforge...');

    RunOrFail(
      ExpandConstant('{tmp}\Miniforge3.exe'),
      '/S /D=' + ExpandConstant('{#CondaDir}')
    );
  end;
end;

// ; ------------------------------------------------------------
// ; Create isolated conda environment
// ; ------------------------------------------------------------
procedure CreateEnv;
begin
  UpdateStatus('Creating Python environment...');
  ForceDirectories(ExpandConstant('{app}'));
  //RunOrFail(
  //  GetCondaPath(''),
  //  'init'
  //);
  
  // RunOrFail('curl', 'https://conda.anaconda.org/conda-forge/win-64/repodata.json')  
  
  RunOrFail(
    GetCondaPath(''),
    'create -y -p ' +
    GetEnvPath('') +
    ' python=3.12 -c conda-forge'
  );
end;

// ; ------------------------------------------------------------
// ; Install correct PyTorch version
// ; ------------------------------------------------------------
procedure InstallTorch;
var
  TorchCmd: String;
begin
  UpdateStatus('Installing PyTorch...');

  if CudaRadio.Checked then
    TorchCmd :=
      '-m pip install torch --index-url https://download.pytorch.org/whl/cu126'
  else
    if CudaLatestRadio.Checked then
    TorchCmd :=
      '-m pip install torch --index-url https://download.pytorch.org/whl/cu130'
      else
        TorchCmd :=
          '-m pip install torch';

  RunOrFail(GetPython(''), TorchCmd);
end;

// ; ------------------------------------------------------------
// ; Install your PyPI package
// ; ------------------------------------------------------------
procedure InstallPackage;
begin
  UpdateStatus('Installing LyROI package...');
  RunOrFail(GetPython(''),
    '-m pip install {#PyPIpackage}'
  );
end;

// ; ------------------------------------------------------------
// ; Installation steps execution order
// ; ------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    try
      InstallMiniforge;
      CreateEnv;
      InstallTorch;
      InstallPackage;
      UpdateStatus('Installation completed.');
    except
      Abort;
    end;
  end;
end;

// ; ------------------------------------------------------------
// ; Remove conda environment during uninstall
// ; ------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    if FileExists(GetCondaPath('')) then
      Exec(GetCondaPath(''),
           'env remove  -p ' + GetEnvPath('') + ' -y',
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;