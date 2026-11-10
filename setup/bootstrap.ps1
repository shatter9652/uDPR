# BDSP PC rebuild - one-command project setup (started by setup.cmd in the repository root).
#
#   setup.cmd [-Dump <folder with exefs\ and romfs\>] [-Unity <...\2019.4.27f1\Editor\Unity.exe>] [-Wwise <Unity project with the
#             Launcher's Wwise integration>] [-Work <folder>] [-BatchMode] [-Build]
#   -Build: also build the standalone Windows game (Builds\win64_<time>\Dpr.exe); needs Unity's "Windows Build Support (IL2CPP)"
#           module and Visual Studio 2022 with "Desktop development with C++"
#
# What it does (each part is skipped when already done, so running it again resumes):
#   1. finds Unity 2019.4.27f1 (Unity Hub's install folders); if missing, opens Unity Hub on that exact version and stops;
#   2. asks for the game dump folder (exefs\main + romfs\Data of BDSP v1.3.0) unless -Dump is given;
#   3. downloads its own tools into SetupWork\bin, each checked against a pinned SHA-256: Python 3.13.12 (python.org's NuGet
#      package - no installer, nothing registered) + the Python packages in setup\requirements.lock, AssetRipper 1.3.14 (free);
#   4. Wwise: creates SetupWork\WwiseIntegration (an empty Unity project), shows the Audiokinetic Launcher steps and waits until
#      Wwise 2019.2.5 is integrated there (or uses -Wwise);
#   5. runs setup\setup.py: export -> ... -> verify (several hours; Unity windows open and close by themselves).
param(
    [string]$Dump,
    [string]$Unity,
    [string]$Wwise,
    [string]$Work,
    [switch]$BatchMode,
    [switch]$Build
)
$ErrorActionPreference = 'Stop'
# A PowerShell 7 parent can pass its module path to setup.cmd's Windows PowerShell process.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1')
$ProgressPreference = 'SilentlyContinue'          # Invoke-WebRequest is many times slower with the progress bar
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Project = Split-Path -Parent $PSScriptRoot
if (-not $Work) { $Work = Join-Path $Project 'SetupWork' }
$Bin = Join-Path $Work 'bin'
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
$logs = Join-Path $Work 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
try { Start-Transcript -LiteralPath (Join-Path $logs 'bootstrap.log') -Append | Out-Null } catch {}   # this window's text, for bug reports

$UnityVersion = '2019.4.27f1'
$UnityHubLink = 'unityhub://2019.4.27f1/23dc10685eb4'
$PythonUrl = 'https://www.nuget.org/api/v2/package/python/3.13.12'
$PythonSha = '389c0228afbb3530f6cd079f5cec44139b1441dd51c85ec704f7a63f1c9f3802'
$RipperUrl = 'https://github.com/AssetRipper/AssetRipper/releases/download/1.3.14/AssetRipper_win_x64.zip'
$RipperSha = '808cddf66dd0357ad6b36b97de3a2aef5e3552e63af3ee0610f9a03a0378101c'

# Paths go through -LiteralPath: dump folders are commonly named "... [0100000011D90000][v1.3.0]", and plain -Path reads [..]
# as a wildcard (Test-Path then says False for a folder that exists).

# Started by double-clicking setup.cmd (explorer.exe -> cmd.exe -> this): the window closes when we exit, so keep it open.
function Test-FromExplorer {
    try {
        $me = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
        $cmd = Get-CimInstance Win32_Process -Filter "ProcessId=$($me.ParentProcessId)"
        if (-not $cmd -or $cmd.Name -ne 'cmd.exe') { return $false }
        $top = Get-CimInstance Win32_Process -Filter "ProcessId=$($cmd.ParentProcessId)"
        return [bool]($top -and $top.Name -eq 'explorer.exe')
    } catch { return $false }
}
$FromExplorer = Test-FromExplorer

function Say($msg) { Write-Host ("[setup] " + $msg) }
function Hold { if ($FromExplorer) { Write-Host ''; Read-Host '[setup] Press Enter to close this window' | Out-Null } }
function Quit($code) { try { Stop-Transcript | Out-Null } catch {}; Hold; exit $code }
function Fail($msg) { Write-Host ("[setup] PROBLEM: " + $msg) -ForegroundColor Red; Quit 1 }
trap { Write-Host ("[setup] PROBLEM: " + $_) -ForegroundColor Red; Quit 1 }

function Get-Pinned($url, $sha, $dest) {
    if ((Test-Path -LiteralPath $dest) -and ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash -eq $sha.ToUpper())) { return }
    Say "downloading $url"
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    $got = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
    if ($got -ne $sha.ToUpper()) { Remove-Item -LiteralPath $dest; Fail "checksum mismatch for $url (got $got)" }
}

# The dump root under what the user picked: the folder itself, its parent when they picked exefs / romfs / romfs\Data, or a
# sub-folder up to two levels down (e.g. a dumper's <title id>\ folder).
function Test-DumpRoot($d) {
    (Test-Path -LiteralPath (Join-Path $d 'exefs\main') -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $d 'romfs\Data') -PathType Container)
}
function Find-DumpRoot($sel) {
    if (-not $sel -or -not (Test-Path -LiteralPath $sel -PathType Container)) { return $null }
    $sel = (Get-Item -LiteralPath $sel).FullName.TrimEnd('\')
    $cands = @($sel)
    $leaf = Split-Path -Leaf $sel
    $up = Split-Path -Parent $sel
    if ($up -and $leaf -in @('exefs', 'romfs')) { $cands += $up }
    if ($up -and $leaf -eq 'Data' -and (Split-Path -Leaf $up) -eq 'romfs') { $cands += (Split-Path -Parent $up) }
    $kids = @(Get-ChildItem -LiteralPath $sel -Directory -ErrorAction SilentlyContinue)
    $cands += $kids | ForEach-Object { $_.FullName }
    $cands += $kids | ForEach-Object { Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue } |
              ForEach-Object { $_.FullName }
    foreach ($c in $cands) { if ($c -and (Test-DumpRoot $c)) { return $c } }
    return $null
}
$Profiles = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'data\dump_profiles.json') -Raw | ConvertFrom-Json
$MainSizes = @($Profiles.PSObject.Properties | ForEach-Object { $_.Value.files.'exefs/main'.size })
function Get-DumpProblem($sel, $root) {
    if (-not $root) {
        $what = if (Test-Path -LiteralPath $sel -PathType Container) {
            $n = @(Get-ChildItem -LiteralPath $sel -Force -ErrorAction SilentlyContinue | Select-Object -First 12 | ForEach-Object { $_.Name })
            if ($n.Count) { 'it contains: ' + ($n -join ', ') } else { 'it is empty' }
        } else { 'that folder does not exist' }
        return "$sel is not a BDSP dump folder ($what). Pick the folder that has BOTH exefs\ (with the file main) and romfs\ (with Data\) in it."
    }
    $size = (Get-Item -LiteralPath (Join-Path $root 'exefs\main')).Length
    if ($size -notin $MainSizes) {
        return "$root\exefs\main is $size bytes - expected Brilliant Diamond or Shining Pearl v1.3.0. Dump the game with the v1.3.0 update applied (exefs and romfs from base game + update)."
    }
    return $null
}

# 1. Unity
if (-not $Unity) {
    $roots = @(Join-Path $env:ProgramFiles 'Unity\Hub\Editor')
    $secondary = Join-Path $env:APPDATA 'UnityHub\secondaryInstallPath.json'
    if (Test-Path -LiteralPath $secondary) {
        $raw = Get-Content -LiteralPath $secondary -Raw
        try { $p = [string]($raw | ConvertFrom-Json) } catch { $p = $raw.Trim().Trim('"') }   # a JSON string: "E:\\Unity" -> E:\Unity
        if ($p) { $roots += $p }
    }
    foreach ($r in $roots) {
        $c = Join-Path $r "$UnityVersion\Editor\Unity.exe"
        if (Test-Path -LiteralPath $c) { $Unity = $c; break }
    }
}
if (-not $Unity -or -not (Test-Path -LiteralPath $Unity)) {
    Say "Unity $UnityVersion is not installed. Opening Unity Hub on that version - install it (add 'Windows Build Support (IL2CPP)'"
    Say "only if you want to build a standalone game), then run setup.cmd again."
    Start-Process $UnityHubLink
    Quit 1
}
Say "Unity: $Unity"

# 2. the dump: -Dump, else the one saved by an earlier run, else ask; a folder that was picked (or saved) and is wrong -> ask again
$cfgPath = $env:BDSP_SETUP_CONFIG
if (-not $cfgPath) { $cfgPath = Join-Path $Project 'SetupWork\config.json' }
$canAsk = -not $Dump
if (-not $Dump -and (Test-Path -LiteralPath $cfgPath)) { $Dump = (Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json).dump }
$lastPick = $null
while ($true) {
    if (-not $Dump) {
        Add-Type -AssemblyName System.Windows.Forms
        $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
        $dlg.Description = 'Select your BDSP v1.3.0 dump: the folder that holds exefs and romfs'
        $dlg.ShowNewFolderButton = $false
        if ($lastPick) { $dlg.SelectedPath = $lastPick }
        $owner = New-Object System.Windows.Forms.Form -Property @{ TopMost = $true }   # else the dialog can open behind this window
        Say 'choose the dump folder in the dialog (it may be behind other windows)'
        $ok = $dlg.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK
        $owner.Dispose()
        if (-not $ok) { Fail 'no dump folder selected - run setup.cmd again to choose one' }
        $Dump = $dlg.SelectedPath
        $lastPick = $Dump
    }
    $root = Find-DumpRoot $Dump
    $problem = Get-DumpProblem $Dump $root
    if (-not $problem) { $Dump = $root; break }
    if (-not $canAsk) { Fail $problem }
    Write-Host ("[setup] PROBLEM: " + $problem) -ForegroundColor Red
    $Dump = $null
}
Say "dump: $Dump"

# 3. tools
$py = Join-Path $Bin 'python\tools\python.exe'
if (-not (Test-Path -LiteralPath $py)) {
    $pkg = Join-Path $Bin 'python.3.13.12.zip'
    Get-Pinned $PythonUrl $PythonSha $pkg
    Expand-Archive -LiteralPath $pkg -DestinationPath (Join-Path $Bin 'python') -Force
}
$lock = Join-Path $PSScriptRoot 'requirements.lock'
$stamp = Join-Path $Bin 'python\requirements.installed'
if (-not (Test-Path -LiteralPath $stamp) -or
    ((Get-FileHash -LiteralPath $stamp).Hash -ne (Get-FileHash -LiteralPath $lock).Hash)) {
    Say 'installing the Python packages (setup\requirements.lock)'
    & $py -m pip install --disable-pip-version-check --no-warn-script-location -q -r $lock
    if ($LASTEXITCODE -ne 0) { Fail 'pip install failed' }
    Copy-Item -LiteralPath $lock -Destination $stamp -Force
}
$ripper = Join-Path $Bin 'AssetRipper\AssetRipper.GUI.Free.exe'
if (-not (Test-Path -LiteralPath $ripper)) {
    $zip = Join-Path $Bin 'AssetRipper_win_x64_1.3.14.zip'
    Get-Pinned $RipperUrl $RipperSha $zip
    Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $Bin 'AssetRipper') -Force
}
Say "tools ready: Python 3.13.12, AssetRipper 1.3.14"

# 4. Wwise
if (-not $Wwise) { $Wwise = Join-Path $Work 'WwiseIntegration' }
$wver = Join-Path $Wwise 'Assets\Wwise\Version.txt'
function Wwise-Ready { (Test-Path -LiteralPath $wver) -and ((Get-Content -LiteralPath $wver -Raw) -match '2019\.2\.5 Build 7349') }
if (-not (Wwise-Ready)) {
    if (-not (Test-Path -LiteralPath (Join-Path $Wwise 'ProjectSettings'))) {
        Say "creating an empty Unity project for the Wwise integration: $Wwise (a Unity window opens and closes)"
        for ($i = 0; $i -lt 3 -and -not (Test-Path -LiteralPath (Join-Path $Wwise 'ProjectSettings')); $i++) {
            # wait for Unity itself only: Start-Process -Wait would also wait for the C# compiler server (VBCSCompiler) Unity
            # leaves running for minutes after a compile
            $proc = Start-Process -FilePath $Unity -ArgumentList @('-quit', '-createProject', "`"$Wwise`"", '-logFile', "`"$(Join-Path $Work 'wwise_create_project.log')`"") -PassThru
            $proc.WaitForExit()
        }
        if (-not (Test-Path -LiteralPath (Join-Path $Wwise 'ProjectSettings'))) { Fail "Unity could not create $Wwise (see SetupWork\wwise_create_project.log)" }
    }
    Write-Host ''
    Say 'ONE MANUAL STEP - Wwise (free Audiokinetic account):'
    Say '  1. In the Audiokinetic Launcher, install Wwise 2019.2.5.7349: SDK (C++) with Microsoft > Windows (Visual Studio 2019).'
    Say "  2. Launcher > Unity > Browse for project > select:  $Wwise"
    Say '  3. Integrate Wwise into Project: version 2019.2.5.7349, platforms Windows + macOS (the Launcher requires macOS),'
    Say '     no "Unity Integration Extensions", no Addressables migration. If the Launcher reports a failure at its very'
    Say '     last step, that is fine - the setup only needs the files it copied.'
    Say 'Waiting for the integration to appear ... (Ctrl+C to stop; run setup.cmd again later to continue)'
    while (-not (Wwise-Ready)) { Start-Sleep -Seconds 5 }
}
Say "Wwise: $Wwise"

# 5. the setup proper
$argv = @('-I', (Join-Path $PSScriptRoot 'setup.py'), '--dump', $Dump, '--unity', $Unity, '--wwise', $Wwise, '--assetripper', $ripper,
          '--work', $Work)
if ($Build) { $argv += '--build' }
if ($BatchMode) {
    $cfg = if (Test-Path -LiteralPath $cfgPath) { Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json } else { New-Object psobject }
    $cfg | Add-Member -NotePropertyName unity_batchmode -NotePropertyValue $true -Force
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cfgPath) | Out-Null
    $cfg | ConvertTo-Json | Set-Content -LiteralPath $cfgPath -Encoding UTF8
}
Say 'running the setup (several hours; Unity windows open and close by themselves - do not close them)'
& $py @argv
if ($LASTEXITCODE -ne 0) { Fail "the setup stopped (exit $LASTEXITCODE) - see SetupWork\logs; run setup.cmd again to resume" }
Write-Host ''
Say 'DONE. Open this folder as a project in Unity Hub (Unity 2019.4.27f1), open Assets/Scenes/level0.unity and press Play.'
Quit 0
