# smtc.ps1: what Windows tells every program about the media playing now (a6443, 17 Oct 2026). Run by media.py.
#
# Windows PowerShell 5.1 loads the WinRT class Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager
# (the system media session: what the volume flyout shows), so nothing is installed and nothing is elevated. Every
# half second it reads the sessions and, when anything changed, prints one JSON line on stdout:
#   {"ok":true,"apps":[...],"s":{app,title,artist,album,status,position,end,updated,shuffle,repeat,art,can:{...}}}
# s is the session it chose: Spotify's when there is one, else the one Windows calls current; none: "s":null.
# position and end are seconds; updated is when the app last said its position (unix seconds).
# The panel shows that static report, never a clock estimate. Art is written to AGORA_ART_DIR.
#
# It reads lines on stdin: play, pause, toggle, next, prev, shuffle on|off, repeat none|track|list. Each is sent to the
# chosen session (Try*Async: the app's own transport controls; no key is pressed, no window takes focus) and answered
# with {"did":"<line>","ok":true|false}. $env:AGORA_SMTC_DRY=1 answers without sending (tests).
# Off switch: stdin closing (its parent ended or said stop) ends it; so does $env:AGORA_SMTC_PARENT's process ending.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime]
$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStreamWithContentType, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Media.MediaPlaybackAutoRepeatMode, Windows.Media, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await($op, [Type]$type) {
  $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op))
  if (-not $t.Wait(4000)) { throw 'Windows did not answer in 4 s' }
  $t.Result
}
function Say($o) { [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress -Depth 4)); [Console]::Out.Flush() }

$out = [Console]::Out
$mgr = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
$stdin = New-Object IO.StreamReader([Console]::OpenStandardInput())
$pending = $stdin.ReadLineAsync()
$artDir = $env:AGORA_ART_DIR
$parent = 0; if ($env:AGORA_SMTC_PARENT) { $parent = [int]$env:AGORA_SMTC_PARENT }
$last = ''; $artKey = ''; $artPath = ''; $artWhy = ''; $beat = 0

function Pick() {
  $all = @($mgr.GetSessions())
  $s = $all | Where-Object { $_.SourceAppUserModelId -match 'spotify' } | Select-Object -First 1
  if (-not $s) { $s = $mgr.GetCurrentSession() }
  return @{ all = $all; s = $s }
}

function ArtOf($s, $props, $key) {
  if (-not $artDir) { $script:artWhy = 'no folder for art'; return '' }
  if (-not $props.Thumbnail) { $script:artWhy = 'the app gives no art'; return '' }
  if ($key -eq $script:artKey) { return $script:artPath }
  $script:artKey = $key; $script:artPath = ''; $script:artWhy = ''
  try {
    $st = Await ($props.Thumbnail.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
    # PowerShell 5.1 sees this stream as a bare __ComObject: no overload of AsStreamForRead or DataReader binds it and
    # its methods are not found. Reflection through the interface types casts it as COM does (QueryInterface)
    $n = [uint32][Windows.Storage.Streams.IRandomAccessStream].GetProperty('Size').GetValue($st)
    $dr = [Windows.Storage.Streams.DataReader].GetConstructor(@([Windows.Storage.Streams.IInputStream])).Invoke(@($st))
    $null = Await ($dr.LoadAsync($n)) ([uint32])
    $b = New-Object byte[] $n; $dr.ReadBytes($b); $dr.Dispose()     # disposing the reader closes the stream too
    if ($b.Length -lt 16) { return '' }
    $ext = '.jpg'; if ($b[0] -eq 0x89 -and $b[1] -eq 0x50) { $ext = '.png' }
    $sha = [Security.Cryptography.SHA1]::Create()
    $name = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($key))[0..7] | ForEach-Object { $_.ToString('x2') })
    $null = New-Item -ItemType Directory -Force -Path $artDir
    $p = Join-Path $artDir ($name + $ext)
    [IO.File]::WriteAllBytes($p, $b)
    $script:artPath = $p
  } catch { $script:artPath = ''; $script:artWhy = $_.Exception.Message }
  return $script:artPath
}

function Read-State() {
  $p = Pick
  $apps = @($p.all | ForEach-Object { $_.SourceAppUserModelId })
  $s = $p.s
  if (-not $s) { return @{ ok = $true; apps = $apps; s = $null } }
  $props = Await ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
  $info = $s.GetPlaybackInfo(); $tl = $s.GetTimelineProperties(); $c = $info.Controls
  $key = "$($props.Title)|$($props.Artist)|$($props.AlbumTitle)"
  $rep = $null; if ($info.AutoRepeatMode -ne $null) { $rep = [string]$info.AutoRepeatMode }
  $shuf = $null; if ($info.IsShuffleActive -ne $null) { $shuf = [bool]$info.IsShuffleActive }
  $o = [ordered]@{
    app = $s.SourceAppUserModelId; title = $props.Title; artist = $props.Artist; album = $props.AlbumTitle
    status = [string]$info.PlaybackStatus
    position = [math]::Round(($tl.Position - $tl.StartTime).TotalSeconds, 1); end = [math]::Round(($tl.EndTime - $tl.StartTime).TotalSeconds, 1)
    updated = [math]::Round($tl.LastUpdatedTime.ToUnixTimeMilliseconds() / 1000.0, 1)
    shuffle = $shuf; repeat = $rep
    art = (ArtOf $s $props $key); artwhy = $script:artWhy
    can = [ordered]@{ play = $c.IsPlayEnabled; pause = $c.IsPauseEnabled; next = $c.IsNextEnabled; prev = $c.IsPreviousEnabled
                      shuffle = $c.IsShuffleEnabled; repeat = $c.IsRepeatEnabled }
  }
  return [ordered]@{ ok = $true; apps = $apps; s = $o }
}

function Do-Line($line) {
  $w = ($line.Trim() -split '\s+')
  $ok = $false
  try {
    $s = (Pick).s
    if (-not $s) { Say @{ did = $line; ok = $false; why = 'nothing is playing' }; return }
    if ($env:AGORA_SMTC_DRY -eq '1') { Say @{ did = $line; ok = $true; dry = $true }; return }
    switch ($w[0]) {
      'play'    { $ok = Await ($s.TryPlayAsync()) ([bool]) }
      'pause'   { $ok = Await ($s.TryPauseAsync()) ([bool]) }
      'toggle'  { $ok = Await ($s.TryTogglePlayPauseAsync()) ([bool]) }
      'next'    { $ok = Await ($s.TrySkipNextAsync()) ([bool]) }
      'prev'    { $ok = Await ($s.TrySkipPreviousAsync()) ([bool]) }
      'shuffle' { $ok = Await ($s.TryChangeShuffleActiveAsync(($w[1] -eq 'on'))) ([bool]) }
      'repeat'  {
        $m = @{ none = 'None'; track = 'Track'; list = 'List' }[$w[1]]
        if ($m) { $ok = Await ($s.TryChangeAutoRepeatModeAsync([Windows.Media.MediaPlaybackAutoRepeatMode]$m)) ([bool]) }
      }
      default   { Say @{ did = $line; ok = $false; why = 'not a word this knows' }; return }
    }
    Say @{ did = $line; ok = [bool]$ok }
  } catch { Say @{ did = $line; ok = $false; why = $_.Exception.Message } }
}

while ($true) {
  if ($pending.IsCompleted) {
    $line = $pending.Result
    if ($line -eq $null -or $line -eq 'stop') { break }
    if ($line.Trim()) { Do-Line $line }
    $script:last = ''                                     # say the state again at once after a press
    $pending = $stdin.ReadLineAsync()
    continue
  }
  if ($parent -and -not (Get-Process -Id $parent -ErrorAction SilentlyContinue)) { break }
  try { $st = Read-State } catch { $st = @{ ok = $false; why = $_.Exception.Message } }
  $j = ($st | ConvertTo-Json -Compress -Depth 4)
  $beat++
  if ($j -ne $last -or $beat -ge 20) { $out.WriteLine($j); $out.Flush(); $last = $j; $beat = 0 }
  Start-Sleep -Milliseconds 500
}
