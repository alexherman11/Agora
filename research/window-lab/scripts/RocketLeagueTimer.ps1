# Rocket League daily play-time limit.
# Counts the time RocketLeague.exe is running, gives a notice shortly before the
# limit, then closes the game and keeps it closed until the next day.
# If a match is in progress when time runs out, it waits for that match to end
# (read from the game's own Launch.log) before closing.
# The daily limit is weekday_minutes Monday to Friday and weekend_minutes on
# Saturday and Sunday, read from RocketLeagueTimer.settings.json next to this
# script (reread every check, so a change counts without a restart).
# -DryRun prints the limit for each day of the week and exits; it never watches
# or closes anything. -Clock pretends today is that date.
param(
    [double]$WeekdayMinutes     = 30,   # play time allowed Monday to Friday, if the settings file does not say
    [double]$WeekendMinutes     = 60,   # play time allowed Saturday and Sunday, if the settings file does not say
    [string]$SettingsFile       = (Join-Path $PSScriptRoot 'RocketLeagueTimer.settings.json'),
    [switch]$DryRun,
    [string]$Clock              = '',   # e.g. 2026-10-18: pretend it is that day (for -DryRun)
    [double]$WarnMinutes        = 7,    # give a notice when this much time is left
    [double]$MaxOvertimeMinutes = 10,   # longest it will wait for a match to finish
    [string]$ProcessName        = 'RocketLeague',
    [string]$GameLog            = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Rocket League\TAGame\Logs\Launch.log'),
    [string]$StateDir           = $PSScriptRoot,
    [int]$PollSeconds           = 5,    # check interval while the game is open
    [int]$IdlePollSeconds       = 30    # check interval while the game is closed
)

$ErrorActionPreference = 'Continue'

function Get-Now { if ($Clock) { [datetime]::Parse($Clock) } else { Get-Date } }

# Minutes allowed on the given day: the settings file wins, the params are the fallback.
function Get-LimitMinutes([datetime]$day) {
    $weekday = $WeekdayMinutes; $weekend = $WeekendMinutes
    if (Test-Path $SettingsFile) {
        try {
            $s = Get-Content $SettingsFile -Raw | ConvertFrom-Json
            if ($null -ne $s.weekday_minutes) { $weekday = [double]$s.weekday_minutes }
            if ($null -ne $s.weekend_minutes) { $weekend = [double]$s.weekend_minutes }
        } catch {}
    }
    if ($day.DayOfWeek -eq 'Saturday' -or $day.DayOfWeek -eq 'Sunday') { return $weekend }
    return $weekday
}

if ($DryRun) {
    $start = (Get-Now).Date
    for ($i = 0; $i -lt 7; $i++) {
        $d = $start.AddDays($i)
        "{0} {1,-9} limit {2} min" -f $d.ToString('yyyy-MM-dd'), $d.DayOfWeek, (Get-LimitMinutes $d)
    }
    exit 0
}

# Only one watcher per process name.
$created = $false
$mutex = New-Object System.Threading.Mutex($true, "Local\PlayTimer_$ProcessName", [ref]$created)
if (-not $created) { exit 0 }

$stateFile = Join-Path $StateDir "$ProcessName-usage.json"
$logFile   = Join-Path $StateDir "$ProcessName-timer.log"

function Write-Log([string]$msg) {
    Add-Content -Path $logFile -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg) -Encoding utf8
}

function Get-Today { (Get-Date).ToString('yyyy-MM-dd') }

function New-State { [pscustomobject]@{ date = (Get-Today); seconds = 0.0; warned = $false; closed = $false } }

function Read-State {
    if (-not (Test-Path $stateFile)) { return New-State }
    try {
        $s = Get-Content $stateFile -Raw | ConvertFrom-Json
        if ($s.date -ne (Get-Today)) { return New-State }
        return [pscustomobject]@{ date = $s.date; seconds = [double]$s.seconds; warned = [bool]$s.warned; closed = [bool]$s.closed }
    } catch { return New-State }
}

function Save-State($s) {
    $s | ConvertTo-Json | Set-Content -Path $stateFile -Encoding utf8
}

# Spoken + on-top popup, in a separate process so the watcher never blocks.
function Send-Notice([string]$msg) {
    Write-Log "NOTICE: $msg"
    $safe = $msg.Replace("'", "''")
    $cmd = "try { Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).SpeakAsync('$safe') | Out-Null } catch {}; " +
           "(New-Object -ComObject WScript.Shell).Popup('$safe', 20, 'Rocket League timer', 0x1030) | Out-Null"
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $cmd
}

# --- Match tracking from the game's log -------------------------------------
# "LoadMap: <ip:port>/<arena>" (or an offline arena) starts a match; "Match Ended"
# or loading the menu / free play ends it.
$script:logOffset = 0L
$script:logCarry  = ''
$script:inMatch   = $false

function Update-MatchState {
    if (-not (Test-Path $GameLog)) { $script:inMatch = $false; return }
    try {
        $fs = New-Object System.IO.FileStream($GameLog, 'Open', 'Read', ([System.IO.FileShare]'ReadWrite, Delete'))
    } catch { return }
    try {
        if ($fs.Length -lt $script:logOffset) {
            # New log file (game restarted).
            $script:logOffset = 0L; $script:logCarry = ''; $script:inMatch = $false
        }
        if ($fs.Length -eq $script:logOffset) { return }
        $fs.Position = $script:logOffset
        $buf  = New-Object byte[] ($fs.Length - $script:logOffset)
        $read = $fs.Read($buf, 0, $buf.Length)
        $script:logOffset += $read
        $text = $script:logCarry + [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
    } finally { $fs.Dispose() }

    $parts = $text -split "`n"
    $script:logCarry = $parts[-1]     # possibly incomplete last line
    for ($i = 0; $i -lt $parts.Length - 1; $i++) {
        $line = $parts[$i]
        if ($line -match 'Log: LoadMap: (\S+)') {
            $map = $Matches[1]
            $now = -not ($map -match '^MENU_|GameTags=Freeplay|^JoinGameTransition')
            if ($now -and -not $script:inMatch) { Write-Log "Match started: $($map.Split('?')[0])" }
            $script:inMatch = $now
        } elseif ($line -match 'ScriptLog: Match Ended' -or $line -match 'Log: Log file closed') {
            if ($script:inMatch) { Write-Log 'Match ended.' }
            $script:inMatch = $false
        }
    }
}

# -----------------------------------------------------------------------------
$state         = Read-State
$lastTick      = Get-Date
$lastBlocked   = [datetime]::MinValue
$overtimeStart = $null
Write-Log "Watcher started. Limit today $(Get-LimitMinutes (Get-Date)) min, used today: $([math]::Round($state.seconds / 60, 1)) min."

function Close-Game($procs, [string]$notice) {
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    $state.closed = $true
    $script:overtimeStart = $null
    $script:lastBlocked = Get-Date
    Send-Notice $notice
    Write-Log 'Game closed.'
}

$wasRunning = $false
while ($true) {
    if ($wasRunning) { Start-Sleep -Seconds $PollSeconds } else { Start-Sleep -Seconds $IdlePollSeconds }
    $now     = Get-Date
    $elapsed = ($now - $lastTick).TotalSeconds
    $lastTick = $now

    if ($state.date -ne (Get-Today)) {
        $state = New-State
        $overtimeStart = $null
        Save-State $state
        Write-Log 'New day, counter reset.'
    }

    $running = @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue)
    if ($running.Count -eq 0) {
        if ($overtimeStart) {
            # Quit by themselves while finishing the last match.
            $overtimeStart = $null; $state.closed = $true; Save-State $state
        }
        $wasRunning = $false
        continue
    }

    Update-MatchState

    if ($state.closed) {
        # Limit already used up today: close it straight away.
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        if (($now - $lastBlocked).TotalSeconds -gt 60) {
            Send-Notice "Rocket League time is used up for today. It will work again tomorrow."
            $lastBlocked = $now
        }
        $wasRunning = $false
        continue
    }

    # Only count time since the last check if the game was already open then.
    # Ignore gaps from sleep/hibernate: never count more than a few polls at once.
    if ($wasRunning) { $state.seconds += [math]::Min($elapsed, $PollSeconds * 3) }
    $wasRunning = $true

    $limitSeconds = (Get-LimitMinutes $now) * 60
    $warnAt       = [math]::Max(0, $limitSeconds - $WarnMinutes * 60)

    if (-not $state.warned -and $state.seconds -ge $warnAt -and $state.seconds -lt $limitSeconds) {
        $left = [math]::Ceiling(($limitSeconds - $state.seconds) / 60)
        Send-Notice "$left minutes of Rocket League left for today. Do not start another match after this one."
        $state.warned = $true
    }

    if ($state.seconds -ge $limitSeconds) {
        if (-not $overtimeStart) {
            if ($script:inMatch) {
                $overtimeStart = $now
                Send-Notice "Rocket League time is up. The game will close when this match ends."
                Write-Log 'Limit reached mid-match, waiting for the match to end.'
            } else {
                Close-Game $running "Rocket League time is up for today."
            }
        } elseif (-not $script:inMatch) {
            Close-Game $running "Match over. Rocket League time is up for today."
        } elseif (($now - $overtimeStart).TotalMinutes -ge $MaxOvertimeMinutes) {
            Write-Log 'Overtime cap reached.'
            Close-Game $running "Rocket League time is up for today."
        }
    }

    Save-State $state
}
