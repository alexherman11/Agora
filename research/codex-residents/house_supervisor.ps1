param([switch]$Install, [switch]$Stop)
$ErrorActionPreference = 'Stop'
$taskName = 'AgoraHouseRecovery'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$labPath = Join-Path $repoPath 'research/text-desk-lab/notation'
$pythonPath = Join-Path $repoPath '.venv/Scripts/python.exe'
$pythonwPath = Join-Path $repoPath '.venv/Scripts/pythonw.exe'
$launcherPath = Join-Path $repoPath 'research/window-lab/agora_start.py'
$launcherOff = Join-Path $repoPath 'research/window-lab/state/agora_start.off'
$controlPath = Join-Path $repoPath 'local/codex-residents/house-supervisor'
New-Item -ItemType Directory -Path $controlPath -Force | Out-Null
$stopPath = Join-Path $controlPath 'stop'
if ($Stop) {
    Set-Content -LiteralPath $stopPath -Value 'Recovery disabled by the operator.'
    return
}
if ($Install) {
    if (Test-Path -LiteralPath $stopPath) { Remove-Item -LiteralPath $stopPath }
    if (Test-Path -LiteralPath $launcherOff) { Remove-Item -LiteralPath $launcherOff }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $shellPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    $action = New-ScheduledTaskAction -Execute $shellPath -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"') -WorkingDirectory $repoPath
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
    $principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun:$false
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Start and recover the full Agora launcher at sign-in; preserve live Desk, HUD and worker sessions.' -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
    return
}
# One supervisor, including a manual launch alongside the scheduled task.
try { $lease = [IO.File]::Open((Join-Path $controlPath 'supervisor.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
catch [IO.IOException] { exit 0 }
$lastStart = @{}
function MatchingProcesses($processes, $scriptName, $arguments) {
    $full = [regex]::Escape((Join-Path $labPath $scriptName))
    $relative = [regex]::Escape($scriptName)
    # Relative commands are accepted only from the exact pinned project Python; full paths identify the checkout.
    @($processes | Where-Object {
        $_.Name -match '^pythonw?\.exe$' -and
        ($_.CommandLine -match ($full + '"?\s+' + $arguments + '(?:\s|$)') -or
         ($_.CommandLine -match [regex]::Escape($pythonPath) -and
          $_.CommandLine -match ('(?:^|\s)' + $relative + '\s+' + $arguments + '(?:\s|$)')))
    })
}
try {
    while (-not (Test-Path -LiteralPath $stopPath)) {
        $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'")
        $keepers = MatchingProcesses $processes 'keeper.py' 'frontier'
        $houses = MatchingProcesses $processes 'house.py' 'frontier'
        $doors = MatchingProcesses $processes 'door.py' '8794'
        $launchers = @($processes | Where-Object {
            $_.CommandLine -match ([regex]::Escape($launcherPath) + '(?:"|\s|$)')
        })
        # One service owner: the full launcher starts the keeper/HUD and adopts surviving services.
        # This watchdog never races it by starting a second door or house on cold startup.
        if ($launchers.Count -eq 0 -and -not (Test-Path -LiteralPath $launcherOff) -and
            (-not $lastStart.ContainsKey('launcher') -or ((Get-Date) - $lastStart['launcher']).TotalSeconds -ge 60)) {
            $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            $null = Start-Process -FilePath $pythonwPath -ArgumentList ('"' + $launcherPath + '"') -WorkingDirectory $repoPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $controlPath ('launcher-' + $stamp + '.out')) -RedirectStandardError (Join-Path $controlPath ('launcher-' + $stamp + '.err'))
            $lastStart['launcher'] = Get-Date
        }
        @{at=(Get-Date).ToUniversalTime().ToString('o'); pid=$PID; launcher=@($launchers.ProcessId); keeper=@($keepers.ProcessId); house=@($houses.ProcessId); door=@($doors.ProcessId)} |
            ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $controlPath 'status.json')
        Start-Sleep -Seconds 10
    }
} finally { $lease.Dispose() }
