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
# Notices are a small box at the top centre of the screen the game is on, shown
# for a few seconds over the game. It never takes the keyboard or the mouse
# (clicks go through it), so the game keeps playing. It shows over a borderless
# or windowed game; over exclusive full screen Windows cannot draw anything.
# -ShowNotice -Overlay 'words' -OverlayDetail 'more words' shows one notice the
# way the watcher does, and exits.
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
    [int]$IdlePollSeconds       = 30,   # check interval while the game is closed
    [double]$OverlaySeconds     = 6,    # how long a notice stays on the screen
    [string]$Overlay            = '',   # a notice's first line: this process draws it, then exits
    [string]$OverlayDetail      = '',   # its second, smaller line
    [switch]$ShowNotice,                # start one notice as the watcher does (its own hidden process), then exit
    [switch]$Quiet,                     # notices are not spoken
    [string]$OnlyOnDesktop      = ''    # for tests: draw only if this process is on the desktop of that name
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

# What each notice says: its first line (big) and its second (small).
$Notices = @{
    Warn      = '{0} minutes of Rocket League left', "Don't start another match after this one."
    UpInMatch = 'Rocket League time is up', 'The game closes when this match ends.'
    Up        = 'Rocket League time is up for today', 'The game is closing now.'
    MatchOver = 'Match over: time is up for today', 'The game is closing now.'
    Used      = 'No more Rocket League today', 'It will work again tomorrow.'
}
function Get-Notice([string]$key, $left = 0) { $t = $Notices[$key]; ($t[0] -f $left), $t[1] }

if ($DryRun) {
    $start = (Get-Now).Date
    for ($i = 0; $i -lt 7; $i++) {
        $d = $start.AddDays($i)
        $limit = Get-LimitMinutes $d
        "{0} {1,-9} limit {2} min" -f $d.ToString('yyyy-MM-dd'), $d.DayOfWeek, $limit
        $warn = Get-Notice Warn $WarnMinutes
        $up = Get-Notice UpInMatch
        $done = Get-Notice Up
        "    after {0} min: '{1}. {2}'" -f [math]::Max(0, $limit - $WarnMinutes), $warn[0], $warn[1]
        "    after {0} min, in a match: '{1}. {2}' (waits up to {3} min for it)" -f $limit, $up[0], $up[1], $MaxOvertimeMinutes
        "    after {0} min, not in a match: '{1}. {2}'" -f $limit, $done[0], $done[1]
    }
    exit 0
}

$stateFile = Join-Path $StateDir "$ProcessName-usage.json"
$logFile   = Join-Path $StateDir "$ProcessName-timer.log"

function Write-Log([string]$msg) {
    Add-Content -Path $logFile -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg) -Encoding utf8
}

# --- The notice: a box over the game that never takes the keyboard or mouse ---
# A message box (what this script used before 17 Oct) becomes the active window,
# so the game loses the keyboard, and a game in exclusive full screen is
# minimised. This window is made so Windows never activates it: no-activate,
# tool window (not in Alt+Tab or the taskbar), topmost, layered and transparent
# to the mouse (clicks fall through to the game).
$overlaySource = @'
using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class RlTimerOverlay : Form {
    [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint flags);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int w, int h, uint flags);
    [DllImport("shcore.dll")] static extern int GetDpiForMonitor(IntPtr monitor, int type, out uint x, out uint y);
    [DllImport("shell32.dll")] static extern int SHQueryUserNotificationState(out int state);
    [DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);

    const int WS_EX_TOPMOST = 0x8, WS_EX_TRANSPARENT = 0x20, WS_EX_TOOLWINDOW = 0x80,
              WS_EX_LAYERED = 0x80000, WS_EX_NOACTIVATE = 0x8000000;
    const uint SWP_NOSIZE = 0x1, SWP_NOMOVE = 0x2, SWP_NOACTIVATE = 0x10, SWP_SHOWWINDOW = 0x40;

    string head, detail;
    float scale;
    Font headFont, detailFont;

    // What Windows says the screen is doing now, in words, for the log.
    public static string ScreenMode() {
        int s;
        try { if (SHQueryUserNotificationState(out s) != 0) return "unknown"; } catch { return "unknown"; }
        switch (s) {
            case 2: return "a full-screen program (borderless or windowed)";
            case 3: return "a game in exclusive full screen (nothing can be drawn over it)";
            case 4: return "presentation mode";
            case 5: return "the desktop";
            case 6: return "quiet time";
            case 1: return "locked or another user";
            default: return "state " + s;
        }
    }

    // Shows the notice on the monitor of `game` (or of the foreground window), at its top centre, for `seconds`.
    public static void Run(string head, string detail, IntPtr game, double seconds) {
        try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch { }
        IntPtr anchor = game != IntPtr.Zero ? game : GetForegroundWindow();
        Screen screen = anchor != IntPtr.Zero ? Screen.FromHandle(anchor) : Screen.PrimaryScreen;
        uint dpi = 96, dpiY;
        try { if (GetDpiForMonitor(MonitorFromWindow(anchor, 2), 0, out dpi, out dpiY) != 0) dpi = 96; } catch { dpi = 96; }
        RlTimerOverlay form = new RlTimerOverlay(head, detail, screen.Bounds, dpi / 96f);
        Timer done = new Timer();
        done.Interval = (int)Math.Max(1000, seconds * 1000);
        done.Tick += delegate { done.Stop(); form.Close(); };
        done.Start();
        Application.Run(form);
    }

    RlTimerOverlay(string head, string detail, Rectangle bounds, float scale) {
        this.head = head; this.detail = detail; this.scale = scale;
        Text = "Rocket League timer";
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        BackColor = Color.FromArgb(22, 24, 30);
        Opacity = 0.9;
        DoubleBuffered = true;
        headFont = new Font("Segoe UI Semibold", 22 * scale, GraphicsUnit.Pixel);
        detailFont = new Font("Segoe UI", 15 * scale, GraphicsUnit.Pixel);
        Size h = TextRenderer.MeasureText(head, headFont);
        Size d = String.IsNullOrEmpty(detail) ? Size.Empty : TextRenderer.MeasureText(detail, detailFont);
        int padX = (int)(22 * scale), padY = (int)(10 * scale);
        int w = Math.Max(h.Width, d.Width) + 2 * padX;
        int ht = h.Height + d.Height + 2 * padY;
        Bounds = new Rectangle(bounds.Left + (bounds.Width - w) / 2, bounds.Top + (int)(24 * scale), w, ht);
    }

    protected override bool ShowWithoutActivation { get { return true; } }

    protected override CreateParams CreateParams {
        get {
            CreateParams cp = base.CreateParams;
            cp.ExStyle |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT;
            return cp;
        }
    }

    protected override void WndProc(ref Message m) {
        if (m.Msg == 0x21) { m.Result = (IntPtr)3; return; }      // WM_MOUSEACTIVATE: MA_NOACTIVATE
        if (m.Msg == 0x84) { m.Result = (IntPtr)(-1); return; }   // WM_NCHITTEST: HTTRANSPARENT, the mouse goes through
        base.WndProc(ref m);
    }

    protected override void OnHandleCreated(EventArgs e) {
        base.OnHandleCreated(e);
        int round = 2;                                              // DWMWCP_ROUND (Windows 11; ignored elsewhere)
        try { DwmSetWindowAttribute(Handle, 33, ref round, 4); } catch { }
    }

    protected override void OnShown(EventArgs e) {
        base.OnShown(e);
        Topmost();
        Timer keep = new Timer();                                   // a game that puts itself on top is topped again
        keep.Interval = 1000;
        keep.Tick += delegate { Topmost(); };
        keep.Start();
    }

    void Topmost() {
        SetWindowPos(Handle, new IntPtr(-1), 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
    }

    protected override void OnPaint(PaintEventArgs e) {
        int padX = (int)(22 * scale), padY = (int)(10 * scale);
        using (SolidBrush accent = new SolidBrush(Color.FromArgb(255, 150, 60)))
            e.Graphics.FillRectangle(accent, 0, 0, Math.Max(3, (int)(4 * scale)), Height);
        Size h = TextRenderer.MeasureText(head, headFont);
        TextRenderer.DrawText(e.Graphics, head, headFont, new Point(padX, padY), Color.White);
        if (!String.IsNullOrEmpty(detail))
            TextRenderer.DrawText(e.Graphics, detail, detailFont, new Point(padX, padY + h.Height), Color.FromArgb(200, 204, 214));
    }
}
'@

function Get-DesktopName {
    $src = '[DllImport("user32.dll")] public static extern IntPtr GetThreadDesktop(int id);' +
           '[DllImport("kernel32.dll")] public static extern int GetCurrentThreadId();' +
           '[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool GetUserObjectInformation(IntPtr h, int i, System.Text.StringBuilder b, int n, out int need);'
    $t = Add-Type -Namespace RlTimer -Name Desk -MemberDefinition $src -PassThru
    $b = New-Object System.Text.StringBuilder 256
    $need = 0
    [void]$t::GetUserObjectInformation($t::GetThreadDesktop($t::GetCurrentThreadId()), 2, $b, 512, [ref]$need)
    $b.ToString()
}

# Draws one notice in this process (the watcher starts a process for each, so it never waits on one).
function Show-Overlay([string]$headline, [string]$detail) {
    if ($OnlyOnDesktop -and (Get-DesktopName) -ne $OnlyOnDesktop) {
        Write-Log "Notice not drawn: this process is not on the desktop $OnlyOnDesktop."
        return
    }
    Add-Type -AssemblyName System.Windows.Forms, System.Drawing
    Add-Type -TypeDefinition $overlaySource -ReferencedAssemblies System.Windows.Forms, System.Drawing
    $game = @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero })
    $hwnd = if ($game.Count) { $game[0].MainWindowHandle } else { [IntPtr]::Zero }
    Write-Log ("Notice shown over {0}; the screen shows {1}." -f $(if ($game.Count) { 'the game' } else { 'whatever is in front' }), [RlTimerOverlay]::ScreenMode())
    $voice = $null
    if (-not $Quiet) {
        try {
            Add-Type -AssemblyName System.Speech
            $voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $spoken = $voice.SpeakAsync(("$headline. $detail").Trim(' ', '.'))
        } catch { $voice = $null }
    }
    [RlTimerOverlay]::Run($headline, $detail, $hwnd, $OverlaySeconds)
    if ($voice) {
        $until = (Get-Date).AddSeconds(15)
        while (-not $spoken.IsCompleted -and (Get-Date) -lt $until) { Start-Sleep -Milliseconds 200 }
    }
}

function Quote-Arg([string]$s) { '"' + $s.Replace('"', "'") + '"' }

# Starts the notice in a separate hidden process, so the watcher never blocks.
function Send-Notice([string]$headline, [string]$detail) {
    Write-Log "NOTICE: $headline. $detail"
    $argv = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', (Quote-Arg $PSCommandPath),
              '-ProcessName', (Quote-Arg $ProcessName), '-StateDir', (Quote-Arg $StateDir),
              '-OverlaySeconds', $OverlaySeconds, '-Overlay', (Quote-Arg $headline), '-OverlayDetail', (Quote-Arg $detail))
    if ($Quiet) { $argv += '-Quiet' }
    if ($OnlyOnDesktop) { $argv += @('-OnlyOnDesktop', (Quote-Arg $OnlyOnDesktop)) }
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList $argv
}

if ($ShowNotice) { Send-Notice $Overlay $OverlayDetail; exit 0 }
if ($Overlay) { Show-Overlay $Overlay $OverlayDetail; exit 0 }

# Only one watcher per process name.
$created = $false
$mutex = New-Object System.Threading.Mutex($true, "Local\PlayTimer_$ProcessName", [ref]$created)
if (-not $created) { exit 0 }

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
    $n = Get-Notice $notice
    Send-Notice $n[0] $n[1]
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
            $n = Get-Notice Used
            Send-Notice $n[0] $n[1]
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
        $n = Get-Notice Warn $left
        Send-Notice $n[0] $n[1]
        $state.warned = $true
    }

    if ($state.seconds -ge $limitSeconds) {
        if (-not $overtimeStart) {
            if ($script:inMatch) {
                $overtimeStart = $now
                $n = Get-Notice UpInMatch
                Send-Notice $n[0] $n[1]
                Write-Log 'Limit reached mid-match, waiting for the match to end.'
            } else {
                Close-Game $running Up
            }
        } elseif (-not $script:inMatch) {
            Close-Game $running MatchOver
        } elseif (($now - $overtimeStart).TotalMinutes -ge $MaxOvertimeMinutes) {
            Write-Log 'Overtime cap reached.'
            Close-Game $running Up
        }
    }

    Save-State $state
}
