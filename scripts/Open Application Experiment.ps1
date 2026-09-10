param(
    [string]$Python = '',
    [int]$Port = 8872,
    [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$demoWorld = Join-Path $repo 'worlds\application-demo'
if ($Port -eq 8870 -or $Port -lt 1024 -or $Port -gt 65535) {
    throw 'Choose a separate local port (1024-65535); 8870 belongs to the active Desk.'
}
if (-not $Python) {
    foreach ($candidate in @((Join-Path $repo '.venv\Scripts\python.exe'), 'C:\Projects\Agora3\.venv\Scripts\python.exe')) {
        if (Test-Path -LiteralPath $candidate) { $Python = $candidate; break }
    }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) {
    throw 'Install this repository dependencies, then supply -Python with that environment executable.'
}
$readyPath = Join-Path $demoWorld 'application-ready.json'
$keepPath = Join-Path $demoWorld 'keep.json'
$baseUrl = "http://127.0.0.1:$Port"
function Test-Demo {
    try {
        $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
        if ($ready.world -ne $demoWorld -or $ready.port -ne $Port) { return $false }
        $keep = Get-Content -LiteralPath $keepPath -Raw | ConvertFrom-Json
        $response = Invoke-RestMethod -Uri "$baseUrl/api/rpc" -Method Post -ContentType 'application/json' -Headers @{Authorization = "Bearer $($keep.operator)"} -Body '{"method":"application.list","args":{}}' -TimeoutSec 2
        return ($null -ne $response.result.applications -and -not $response.error)
    } catch { return $false }
}
if (-not (Test-Demo)) {
    $probe = [Net.Sockets.TcpClient]::new()
    try { $probe.Connect('127.0.0.1', $Port); $occupied = $true } catch { $occupied = $false } finally { $probe.Dispose() }
    if ($occupied) { throw "Port $Port is already occupied by another or unavailable instance. Nothing was stopped." }
    New-Item -ItemType Directory -Path $demoWorld -Force | Out-Null
    $savedPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = Join-Path $repo 'src'
        $process = Start-Process -FilePath $Python -ArgumentList @('scripts/application_demo.py', '--world', 'worlds/application-demo', '--port', "$Port", '--serve') -WorkingDirectory $repo -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $demoWorld 'server.stdout.log') -RedirectStandardError (Join-Path $demoWorld 'server.stderr.log')
    } finally { $env:PYTHONPATH = $savedPythonPath }
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not (Test-Demo)) {
        if ($process.HasExited -or [DateTime]::UtcNow -gt $deadline) {
            throw "The isolated demo did not become ready. Inspect $demoWorld\server.stderr.log. No other instance was stopped."
        }
        Start-Sleep -Milliseconds 300
    }
}
Write-Output "Application experiment ready on port $Port. World: $demoWorld"
if (-not $NoOpen) {
    $keep = Get-Content -LiteralPath $keepPath -Raw | ConvertFrom-Json
    Start-Process "$baseUrl/#$($keep.operator)"
}
