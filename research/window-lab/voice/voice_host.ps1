# voice_host.ps1 (a8901): Windows' own local speech, as a child of the home base. JSON lines on stdin, JSON lines on
# stdout. Recognition: System.Speech's installed en-US engine with a dictation grammar, from the default microphone
# (live use only, after Alex's Allow) or from a WAV file (tests). Voice: System.Speech's installed voices, to the
# default device (live use only) or into a WAV file (tests). Nothing here sends audio anywhere; no network route exists
# in System.Speech's local engine. Off switch: close stdin, or {"do":"quit"}; the child ends with its parent's pipe.
#
# in:  {"do":"listen","from":"mic"|"file","path":"<wav>","silence":4}   {"do":"stop"}
#      {"do":"say","id":"<id>","text":"...","to":"device"|"file","path":"<wav>"}   {"do":"hush"}   {"do":"quit"}
# out: {"ev":"ready",...}  {"ev":"hyp","text"}  {"ev":"final","text","conf"}  {"ev":"detected"}  {"ev":"stopped","why"}
#      {"ev":"speaking","id"}  {"ev":"spoke","id","cancelled"}  {"ev":"error","where","why"}
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$src = @"
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Speech.Recognition;
using System.Speech.Synthesis;

public static class AgoraVoice {
    static readonly object Out = new object();
    static SpeechRecognitionEngine rec;
    static SpeechSynthesizer syn;
    static string speakingId = null;
    static bool listening = false;
    static DateTime lastHeard = DateTime.UtcNow;
    static double silence = 4.0;
    static Timer silenceTimer;

    static string Q(string s) {
        if (s == null) return "null";
        var b = new StringBuilder("\"");
        foreach (char c in s) {
            if (c == '"') b.Append("\\\""); else if (c == '\\') b.Append("\\\\");
            else if (c < ' ') b.AppendFormat("\\u{0:x4}", (int)c); else b.Append(c);
        }
        return b.Append('"').ToString();
    }
    public static void Emit(string json) { lock (Out) { Console.Out.WriteLine(json); Console.Out.Flush(); } }
    static double Now() { return (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds; }

    public static void Start() {
        Console.OutputEncoding = new UTF8Encoding(false);
        string recName = "", voices = "";
        try {
            var info = SpeechRecognitionEngine.InstalledRecognizers();
            RecognizerInfo pick = null;
            foreach (var r in info) if (r.Culture.Name == "en-US") { pick = r; break; }
            if (pick == null) throw new Exception("no installed en-US recognizer");
            rec = new SpeechRecognitionEngine(pick);
            recName = pick.Name;
            rec.LoadGrammar(new DictationGrammar());
            rec.SpeechHypothesized += (s, e) => { lastHeard = DateTime.UtcNow; Emit("{\"ev\":\"hyp\",\"text\":" + Q(e.Result.Text) + ",\"at\":" + Now() + "}"); };
            rec.SpeechRecognized += (s, e) => { lastHeard = DateTime.UtcNow; Emit("{\"ev\":\"final\",\"text\":" + Q(e.Result.Text) + ",\"conf\":" + e.Result.Confidence + ",\"at\":" + Now() + "}"); };
            rec.SpeechDetected += (s, e) => { lastHeard = DateTime.UtcNow; Emit("{\"ev\":\"detected\",\"at\":" + Now() + "}"); };
            rec.RecognizeCompleted += (s, e) => {
                bool was = listening; listening = false;
                if (was) Emit("{\"ev\":\"stopped\",\"why\":" + Q(e.Error != null ? "error: " + e.Error.Message : (e.InputStreamEnded ? "end of file" : "stopped")) + ",\"at\":" + Now() + "}");
            };
        } catch (Exception x) { Emit("{\"ev\":\"error\",\"where\":\"recognizer\",\"why\":" + Q(x.Message) + "}"); }
        try {
            syn = new SpeechSynthesizer();
            var names = new StringBuilder();
            foreach (var v in syn.GetInstalledVoices()) { if (names.Length > 0) names.Append(","); names.Append(Q(v.VoiceInfo.Name)); }
            voices = names.ToString();
            syn.SpeakStarted += (s, e) => Emit("{\"ev\":\"speaking\",\"id\":" + Q(speakingId) + ",\"at\":" + Now() + "}");
            syn.SpeakCompleted += (s, e) => {
                string id = speakingId; speakingId = null;
                try { syn.SetOutputToNull(); } catch (Exception) { }
                Emit("{\"ev\":\"spoke\",\"id\":" + Q(id) + ",\"cancelled\":" + (e.Cancelled ? "true" : "false") + ",\"at\":" + Now() + "}");
            };
        } catch (Exception x) { Emit("{\"ev\":\"error\",\"where\":\"voice\",\"why\":" + Q(x.Message) + "}"); }
        Emit("{\"ev\":\"ready\",\"recognizer\":" + Q(recName) + ",\"voices\":[" + voices + "],\"at\":" + Now() + "}");
        silenceTimer = new Timer(_ => {
            if (listening && (DateTime.UtcNow - lastHeard).TotalSeconds >= silence) { try { rec.RecognizeAsyncCancel(); } catch (Exception) { } }
        }, null, 250, 250);
    }

    public static void Listen(string from, string path, double quiet) {
        if (rec == null) { Emit("{\"ev\":\"error\",\"where\":\"listen\",\"why\":\"no recognizer\"}"); return; }
        if (listening) return;
        try {
            if (from == "file") rec.SetInputToWaveFile(path); else rec.SetInputToDefaultAudioDevice();
            silence = quiet > 0 ? quiet : 4.0; lastHeard = DateTime.UtcNow; listening = true;
            rec.RecognizeAsync(RecognizeMode.Multiple);
            Emit("{\"ev\":\"listening\",\"from\":" + Q(from) + ",\"at\":" + Now() + "}");
        } catch (Exception x) { listening = false; Emit("{\"ev\":\"error\",\"where\":\"listen\",\"why\":" + Q(x.Message) + "}"); }
    }
    public static void Stop() { if (rec != null && listening) { try { rec.RecognizeAsyncCancel(); } catch (Exception) { } } }

    public static void Say(string id, string text, string to, string path) {
        if (syn == null) { Emit("{\"ev\":\"error\",\"where\":\"say\",\"why\":\"no voice\"}"); return; }
        try {
            syn.SpeakAsyncCancelAll();
            if (to == "file") syn.SetOutputToWaveFile(path); else syn.SetOutputToDefaultAudioDevice();
            speakingId = id;
            syn.SpeakAsync(text);
        } catch (Exception x) { speakingId = null; Emit("{\"ev\":\"error\",\"where\":\"say\",\"why\":" + Q(x.Message) + "}"); }
    }
    public static void Hush() { if (syn != null) { try { syn.SpeakAsyncCancelAll(); } catch (Exception) { } } }
}
"@
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Speech
[AgoraVoice]::Start()
while ($true) {
    $line = [Console]::In.ReadLine()
    if ($null -eq $line) { break }
    try { $c = $line | ConvertFrom-Json } catch { [AgoraVoice]::Emit('{"ev":"error","where":"command","why":"not JSON"}'); continue }
    switch ($c.do) {
        'listen' { [AgoraVoice]::Listen([string]$c.from, [string]$c.path, [double]$(if ($c.silence) { $c.silence } else { 4 })) }
        'stop'   { [AgoraVoice]::Stop() }
        'say'    { [AgoraVoice]::Say([string]$c.id, [string]$c.text, [string]$c.to, [string]$c.path) }
        'hush'   { [AgoraVoice]::Hush() }
        'quit'   { [AgoraVoice]::Stop(); [AgoraVoice]::Hush(); exit 0 }
        default  { [AgoraVoice]::Emit('{"ev":"error","where":"command","why":"unknown"}') }
    }
}
[AgoraVoice]::Stop(); [AgoraVoice]::Hush()
