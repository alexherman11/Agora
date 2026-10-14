param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$taskName = 'AgoraDeskListener-Codex-01a1172a'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$listenerPath = Join-Path $PSScriptRoot 'visual_event_listener.py'
$pythonPath = Join-Path $repoPath '.venv/Scripts/pythonw.exe'
if ($Uninstall) {
    & (Join-Path $repoPath '.venv/Scripts/python.exe') $listenerPath stop
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    return
}
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Pinned pythonw.exe is missing' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument ('"' + $listenerPath + '" supervise') -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Frontier Desk event listener for Alex: durable queue, app reconnect, no periodic model wakeups. Off switch: visual_event_listener.py stop.' -Force | Select-Object TaskName,State
