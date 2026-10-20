param([switch]$Install, [switch]$Stop)
$ErrorActionPreference = 'Stop'
$taskName = 'AgoraHouseRecovery'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$labPath = Join-Path $repoPath 'research/text-desk-lab/notation'
$pythonPath = Join-Path $repoPath '.venv/Scripts/python.exe'
$controlPath = Join-Path $repoPath 'local/codex-residents/house-supervisor'
New-Item -ItemType Directory -Path $controlPath -Force | Out-Null
$stopPath = Join-Path $controlPath 'stop'
if ($Stop) {
    Set-Content -LiteralPath $stopPath -Value 'Recovery disabled by the operator.'
    return
}
if ($Install) {
    if (Test-Path -LiteralPath $stopPath) { Remove-Item -LiteralPath $stopPath }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $shellPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    $action = New-ScheduledTaskAction -Execute $shellPath -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"') -WorkingDirectory $repoPath
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
    $principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun:$false
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Recover the existing Agora house/door if absent; never wake models on a timer or restart a live service.' -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
    return
}
# One supervisor, including a manual launch alongside the scheduled task.
try { $lease = [IO.File]::Open((Join-Path $controlPath 'supervisor.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
catch [IO.IOException] { exit 0 }
$env:DESKD = 'http://127.0.0.1:8794'
$env:HOUSE_KEEPER = '1'
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
        # The existing keeper owns its children. If it disappears, adopt their presence; start only missing services.
        if ($keepers.Count -eq 0) {
            foreach ($service in @(
                @{Name='door'; Script='door.py'; Args='8794 --world frontier'; Present=$doors.Count},
                @{Name='house'; Script='house.py'; Args='frontier'; Present=$houses.Count}
            )) {
                if ($service.Present -gt 0) { continue }
                if ($lastStart.ContainsKey($service.Name) -and ((Get-Date) - $lastStart[$service.Name]).TotalSeconds -lt 60) { continue }
                if ($service.Name -eq 'house') {
                    try { $null = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8794/api/health' -TimeoutSec 5 }
                    catch { continue }
                }
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $scriptPath = Join-Path $labPath $service.Script
                $null = Start-Process -FilePath $pythonPath -ArgumentList ('"' + $scriptPath + '" ' + $service.Args) -WorkingDirectory $labPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $controlPath ($service.Name + '-' + $stamp + '.out')) -RedirectStandardError (Join-Path $controlPath ($service.Name + '-' + $stamp + '.err'))
                $lastStart[$service.Name] = Get-Date
            }
        }
        @{at=(Get-Date).ToUniversalTime().ToString('o'); pid=$PID; keeper=@($keepers.ProcessId); house=@($houses.ProcessId); door=@($doors.ProcessId)} |
            ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $controlPath 'status.json')
        Start-Sleep -Seconds 10
    }
} finally { $lease.Dispose() }
