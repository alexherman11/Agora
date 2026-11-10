# popup.ps1 (7 Oct 2026, Claude for Alex): a note on the screen, above everything, that does not take the keyboard.
#
#   powershell -ExecutionPolicy Bypass -File popup.ps1 -Text "the editor is ready" [-Title "Agora"] [-Seconds 12]
#
# A borderless window marked topmost and shown without activating, in the top right corner; a click closes it.
# It shows over a game in Borderless or Windowed mode. Over exclusive Fullscreen nothing can draw but the game:
# set Rocket League's Display Mode to Borderless (Settings, Video) for this to be seen.
param([string]$Text = "hello", [string]$Title = "Agora", [int]$Seconds = 12)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Windows.Forms -TypeDefinition @'
using System;
using System.Windows.Forms;
public class QuietForm : Form {
    protected override bool ShowWithoutActivation { get { return true; } }
    protected override CreateParams CreateParams {
        get {
            CreateParams p = base.CreateParams;
            p.ExStyle |= 0x00000008;   // WS_EX_TOPMOST
            p.ExStyle |= 0x08000000;   // WS_EX_NOACTIVATE: never takes the keyboard from the game
            p.ExStyle |= 0x00000080;   // WS_EX_TOOLWINDOW: not in the taskbar or Alt+Tab
            return p;
        }
    }
}
'@

$form = New-Object QuietForm
$form.FormBorderStyle = 'None'
$form.StartPosition = 'Manual'
$form.BackColor = [System.Drawing.Color]::FromArgb(22, 30, 26)
$form.Opacity = 0.94
$form.Width = 460
$form.Padding = New-Object System.Windows.Forms.Padding(16)

$head = New-Object System.Windows.Forms.Label
$head.Text = $Title.ToUpper()
$head.ForeColor = [System.Drawing.Color]::FromArgb(230, 150, 70)
$head.Font = New-Object System.Drawing.Font('Consolas', 10, [System.Drawing.FontStyle]::Bold)
$head.AutoSize = $true
$head.Location = New-Object System.Drawing.Point(16, 12)

$body = New-Object System.Windows.Forms.Label
$body.Text = $Text
$body.ForeColor = [System.Drawing.Color]::FromArgb(232, 238, 228)
$body.Font = New-Object System.Drawing.Font('Consolas', 11)
$body.MaximumSize = New-Object System.Drawing.Size(428, 0)
$body.AutoSize = $true
$body.Location = New-Object System.Drawing.Point(16, 38)

$form.Controls.Add($head)
$form.Controls.Add($body)
$form.Height = $body.Bottom + 18
$area = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$form.Location = New-Object System.Drawing.Point(($area.Right - $form.Width - 24), ($area.Top + 24))

$close = { $form.Close() }
$form.Add_Click($close)
$head.Add_Click($close)
$body.Add_Click($close)
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = [Math]::Max(1, $Seconds) * 1000
$timer.Add_Tick({ $timer.Stop(); $form.Close() })
$timer.Start()
$form.TopMost = $true
[System.Windows.Forms.Application]::Run($form)
