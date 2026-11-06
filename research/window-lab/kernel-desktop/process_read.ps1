# Read-only metadata collector, launched hidden by the system module, never a worker.
# The general query deliberately excludes CommandLine, ExecutablePath and titles.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
try {
    $config = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $fields = 'Name,ProcessId,ParentProcessId,CreationDate,WorkingSetSize,PrivatePageCount,KernelModeTime,UserModeTime'
    $processes = @(Get-CimInstance -Query "SELECT $fields FROM Win32_Process" | ForEach-Object {
        @{
            name = $_.Name; pid = [int]$_.ProcessId; parent_pid = [int]$_.ParentProcessId
            born = if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().Ticks.ToString() } else { $null }
            working_set = $_.WorkingSetSize; private_bytes = $_.PrivatePageCount
            cpu_ticks = if ($null -ne $_.KernelModeTime -and $null -ne $_.UserModeTime) {
                [decimal]$_.KernelModeTime + [decimal]$_.UserModeTime
            } else { $null }
        }
    })
    $profiles = @()
    # Only browser processes matching an Agora-owned profile prefix are queried
    # for CommandLine. No general application/browser command-line dump.
    $clauses = @()
    foreach ($prefix in $config.prefixes) {
        foreach ($variant in @($prefix, $prefix.Replace('\', '/'))) {
            $escaped = $variant.Replace('\', '\\').Replace("'", "\'").Replace('[', '[[]').Replace('%', '[%]').Replace('_', '[_]')
            foreach ($separator in @('=', '="', ' ', ' "')) {
                $clauses += "CommandLine LIKE '%--user-data-dir$separator$escaped%'"
            }
        }
    }
    if ($clauses.Count) {
        $query = "SELECT ProcessId,CreationDate,CommandLine FROM Win32_Process WHERE (Name='chrome.exe' OR Name='msedge.exe') AND (" + ($clauses -join ' OR ') + ')'
        foreach ($browser in @(Get-CimInstance -Query $query)) {
            $match = [regex]::Match($browser.CommandLine, '(?:^|\s)(?:"--user-data-dir=([^"]+)"|--user-data-dir(?:=|\s+)(?:"([^"]+)"|([^\s"]+)))')
            if ($match.Success) {
                $folder = @($match.Groups[1].Value, $match.Groups[2].Value, $match.Groups[3].Value) |
                    Where-Object { $_ } | Select-Object -First 1
                if ([IO.Path]::IsPathRooted($folder)) {
                    $folder = [IO.Path]::GetFullPath($folder)
                    foreach ($prefix in $config.prefixes) {
                        if ($folder.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
                            $profiles += @{pid = [int]$browser.ProcessId; profile = $folder
                                born = if ($browser.CreationDate) { $browser.CreationDate.ToUniversalTime().Ticks.ToString() } else { $null }}
                            break
                        }
                    }
                }
            }
        }
    }
    @{processes = $processes; profiles = $profiles} | ConvertTo-Json -Depth 4 -Compress
} catch {
    # Never echo exception text: it can include query inputs or command lines.
    [Console]::Error.WriteLine('Process inventory unavailable.')
    exit 1
}
