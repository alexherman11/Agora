param(
    [string]$World = '',
    [int]$Port = 8790
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $World) { $World = Join-Path $projectRoot 'worlds\dev' }
Push-Location -LiteralPath $projectRoot
try {
    & uv run agora3 --world $World serve --port $Port
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
