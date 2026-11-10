# The control screen's helper (a5062): what Windows itself can say about a rectangle of the screen, asked by capture.py
# one JSON line at a time on stdin, answered one JSON line at a time on stdout. It reads; it never clicks, types or
# changes a window. It ends when its stdin closes (capture.py ended).
#
#   {"op":"tree","hwnd":N,"rect":[x,y,w,h]}  a Chromium window's page: its address, its rectangle, and every part the
#                                           painter drew (class r-<role>) that crosses the rectangle, with its words
#   {"op":"grab","rect":[x,y,w,h],"path":P,"max":2048,"ocr":true,"blt":false}
#                                           the screen's pixels there as a PNG at P (scaled to fit max), and the words
#                                           Windows' own text recognition finds in them
#   {"op":"ping"}
#
# Coordinates are physical screen pixels: the helper makes itself per-monitor DPI aware first, as capture.py is.
$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [Text.Encoding]::UTF8
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class CapDpi {
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr v);
  [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr h);
  [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr h, IntPtr dc);
  [DllImport("gdi32.dll")] static extern bool BitBlt(IntPtr d, int x, int y, int w, int h, IntPtr s, int sx, int sy, uint op);
  // SRCCOPY | CAPTUREBLT: layered windows too (the overlay's own picture); .NET's CopyFromScreen refuses the flag
  public static bool Blt(IntPtr dst, int x, int y, int w, int h) {
    IntPtr src = GetDC(IntPtr.Zero);
    try { return BitBlt(dst, 0, 0, w, h, src, x, y, 0x00CC0020u | 0x40000000u); } finally { ReleaseDC(IntPtr.Zero, src); }
  }
}
"@
[void][CapDpi]::SetProcessDpiAwarenessContext([IntPtr](-4))
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, WindowsBase, System.Drawing, System.Runtime.WindowsRuntime
$A = [System.Windows.Automation.AutomationElement]

# --- Windows' own text recognition (Windows.Media.Ocr), if this Windows has it -------------------------------------
$ocr = $null
try {
  $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
  $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
  $ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
} catch { $ocr = $null }
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); [void]$task.Wait(-1); $task.Result }

function Recognise([string]$path) {
  if (-not $ocr) { return $null }
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  try {
    $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $res = Await ($ocr.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
    return @($res.Lines | ForEach-Object { $_.Text })
  } finally { $stream.Dispose() }
}

function Grab($q) {
  $x, $y, $w, $h = [int]$q.rect[0], [int]$q.rect[1], [int]$q.rect[2], [int]$q.rect[3]
  $bmp = New-Object System.Drawing.Bitmap $w, $h
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  if ($q.blt) { $dc = $g.GetHdc(); [void][CapDpi]::Blt($dc, $x, $y, $w, $h); $g.ReleaseHdc($dc) }
  else { $g.CopyFromScreen($x, $y, 0, 0, (New-Object System.Drawing.Size $w, $h), [System.Drawing.CopyPixelOperation]::SourceCopy) }
  $g.Dispose()
  $max = if ($q.max) { [int]$q.max } else { 2048 }
  $words = $null
  $full = [IO.Path]::ChangeExtension($q.path, ".full.png")
  $scale = [Math]::Min(1.0, $max / [double][Math]::Max($w, $h))
  try {
    if ($scale -lt 1.0) {
      $bmp.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)          # recognised at full size, kept scaled
      if ($q.ocr) { $words = Recognise $full }
      $sw, $sh = [int][Math]::Max(1, [Math]::Round($w * $scale)), [int][Math]::Max(1, [Math]::Round($h * $scale))
      $small = New-Object System.Drawing.Bitmap $sw, $sh
      $g = [System.Drawing.Graphics]::FromImage($small)
      $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
      $g.DrawImage($bmp, 0, 0, $sw, $sh); $g.Dispose()
      $small.Save($q.path, [System.Drawing.Imaging.ImageFormat]::Png); $small.Dispose()
      $w, $h = $sw, $sh
    } else {
      $bmp.Save($q.path, [System.Drawing.Imaging.ImageFormat]::Png)
      if ($q.ocr) { $words = Recognise $q.path }
    }
    # Codex c5124: a sent image is at most 2 MiB of PNG; a busy screen's photograph shrinks until it is
    $limit = if ($q.maxbytes) { [long]$q.maxbytes } else { [long]0 }
    while ($limit -gt 0 -and (Get-Item $q.path).Length -gt $limit -and $w -gt 64) {
      $sw, $sh = [int]($w * 0.8), [int]($h * 0.8)
      $src = [System.Drawing.Image]::FromFile($q.path)
      $small = New-Object System.Drawing.Bitmap $sw, $sh
      $g = [System.Drawing.Graphics]::FromImage($small)
      $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
      $g.DrawImage($src, 0, 0, $sw, $sh); $g.Dispose(); $src.Dispose()
      $small.Save($q.path, [System.Drawing.Imaging.ImageFormat]::Png); $small.Dispose()
      $w, $h = $sw, $sh
    }
  } finally { $bmp.Dispose(); if (Test-Path $full) { Remove-Item $full -Force } }
  @{ ok = $true; w = $w; h = $h; ocr = [bool]$ocr; text = $words; bytes = (Get-Item $q.path).Length }
}

function Crosses($r, $sx, $sy, $sw, $sh) {
  -not ($r.IsEmpty -or $r.Right -le $sx -or $r.Left -ge $sx + $sw -or $r.Bottom -le $sy -or $r.Top -ge $sy + $sh)
}
function Words($e, [int]$depth = 0) {      # the words of a part: its own name, else its leaves' names, in order
  $kids = $e.CachedChildren
  if ($kids.Count -eq 0) { return $e.Cached.Name }
  $own = $e.Cached.Name
  $ct = $e.Cached.ControlType
  if ($own -and $ct -ne [System.Windows.Automation.ControlType]::Group -and $ct -ne [System.Windows.Automation.ControlType]::Document) { return $own }
  if ($depth -gt 3) { return "" }          # a frame's words are its parts' words; a deep frame is matched by its parts
  (@($kids | ForEach-Object { Words $_ ($depth + 1) }) | Where-Object { $_ }) -join " "
}

function Tree($q) {
  $win = $A::FromHandle([IntPtr][long]$q.hwnd)
  # Chromium makes its page's accessibility tree only when something asks inside the page: asking what is at a point
  # in it wakes it (ran 14 Oct: a searched-only window gave no page at all, 40 asks in 20 s; after one point, at once)
  $wr = $win.Current.BoundingRectangle
  if (-not $wr.IsEmpty) {
    try { [void]$A::FromPoint((New-Object System.Windows.Point(($wr.X + $wr.Width / 2), ($wr.Y + $wr.Height * 0.6)))) } catch { }
  }
  $isDoc = New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
  $docs = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $isDoc)
  if ($docs.Count -eq 0) {   # Chromium builds its tree on the first ask: ask once more
    Start-Sleep -Milliseconds 150
    $docs = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $isDoc)
  }
  # a window may hold more than one page (a browser's own dialog, a frame): a lens page first, else the largest
  $doc, $url, $best = $null, $null, -1
  foreach ($d in $docs) {
    $u = $null
    try { $u = $d.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { }
    $b = $d.Current.BoundingRectangle
    $score = $(if ($u -and $u -match "/lens\.html") { 1e12 } else { 0 }) + $(if ($b.IsEmpty) { 0 } else { $b.Width * $b.Height })
    if ($score -gt $best) { $doc, $url, $best = $d, $u, $score }
  }
  if (-not $doc) { return @{ ok = $true; url = $null } }
  $dr = $doc.Current.BoundingRectangle
  $out = @{ ok = $true; url = $url; doc = @([int]$dr.X, [int]$dr.Y, [int]$dr.Width, [int]$dr.Height); parts = @() }
  if (-not $q.rect) { return $out }
  $sx, $sy, $sw, $sh = [double]$q.rect[0], [double]$q.rect[1], [double]$q.rect[2], [double]$q.rect[3]
  $req = New-Object System.Windows.Automation.CacheRequest
  foreach ($p in @($A::NameProperty, $A::ClassNameProperty, $A::BoundingRectangleProperty, $A::ControlTypeProperty, $A::IsOffscreenProperty, $A::AutomationIdProperty)) { $req.Add($p) }
  $req.TreeScope = [System.Windows.Automation.TreeScope]::Subtree
  $req.TreeFilter = [System.Windows.Automation.Automation]::RawViewCondition
  $root = $doc.GetUpdatedCache($req)
  $parts = New-Object System.Collections.ArrayList
  $n = 0
  $walk = {
    param($e, $depth, $up)
    $script:n++
    $r = $e.Cached.BoundingRectangle
    $cls = $e.Cached.ClassName
    $roles = @(); if ($cls) { $roles = @($cls.Split(" ") | Where-Object { $_.StartsWith("r-") } | ForEach-Object { $_.Substring(2) }) }
    $here = $up
    $aid = $e.Cached.AutomationId     # the painter's id="part:<scene key>" (Codex, m5110), where the page gives one
    if (-not ($aid -and $aid.StartsWith("part:"))) { $aid = $null }
    if (($roles.Count -or $aid) -and (Crosses $r $sx $sy $sw $sh)) {
      $here = $parts.Count
      [void]$parts.Add(@{ roles = $roles; aid = $aid; words = (Words $e); rect = @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height); depth = $depth; up = $up })
    }
    foreach ($k in $e.CachedChildren) {      # a part scrolled out of its frame is offscreen, though its box may lie here
      if ($k.Cached.IsOffscreen) { continue }
      $kr = $k.Cached.BoundingRectangle
      if ($kr.IsEmpty -or (Crosses $kr $sx $sy $sw $sh)) { & $walk $k ($depth + 1) $here }
    }
  }
  & $walk $root 0 -1
  $out.parts = @($parts)
  $out.seen = $script:n
  $out
}

while ($true) {
  $line = [Console]::In.ReadLine()
  if ($null -eq $line) { break }
  if (-not $line.Trim()) { continue }
  try {
    $q = $line | ConvertFrom-Json
    $t0 = [Diagnostics.Stopwatch]::StartNew()
    switch ($q.op) {
      "tree" { $r = Tree $q }
      "grab" { $r = Grab $q }
      "at" {   # what is at one point, and the parts it is in (a probe)
        $e = $A::FromPoint((New-Object System.Windows.Point([double]$q.x, [double]$q.y)))
        $chain = @(); $w = [System.Windows.Automation.TreeWalker]::RawViewWalker
        while ($e -and $chain.Count -lt 8) { $c = $e.Current; $chain += @{ type = $c.ControlType.ProgrammaticName; name = $c.Name; cls = $c.ClassName; aid = $c.AutomationId }; $e = $w.GetParent($e) }
        $r = @{ ok = $true; chain = $chain }
      }
      "ping" { $r = @{ ok = $true; ocr = [bool]$ocr; lang = $(if ($ocr) { $ocr.RecognizerLanguage.LanguageTag } else { $null }) } }
      default { $r = @{ ok = $false; error = "no such op: $($q.op)" } }
    }
    $r.ms = $t0.ElapsedMilliseconds
  } catch { $r = @{ ok = $false; error = "$($_.Exception.Message)" } }
  [Console]::Out.WriteLine(($r | ConvertTo-Json -Compress -Depth 8))
  [Console]::Out.Flush()
}
