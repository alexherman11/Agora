param(
    [string]$Desk = 'C:\Projects\Agora\worlds\parallel-desk',
    [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$python = Join-Path $repo '.venv\Scripts\python.exe'
$launcher = Join-Path $Desk 'open_desk.py'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run uv sync --dev --locked in Agora4 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $Desk 'world\world.db'))) {
    throw 'Existing Desk history was not found. Supply -Desk with the retained Desk directory.'
}
if (-not (Test-Path -LiteralPath $launcher)) { throw 'The retained Desk launcher was not found.' }
$arguments = @($launcher)
if ($NoOpen) { $arguments += '--no-open' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Agora4 could not open. Inspect the Desk logs/service.log.' }
