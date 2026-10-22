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
#
# a9138: {"do":"device"} -> {"ev":"device","name":"<the microphone's name>","how":"..."} or {"ev":"device","name":"",
# "why":"..."}; a listen from the mic says the same first, and does not start when there is no input device. The name
# is READ ONLY: Windows' Core Audio property store of the endpoint (IMMDevice.OpenPropertyStore, STGM_READ), never
# Activate, so no audio stream is opened and no setting is changed. Which endpoint: SAPI's own audio-input choice when
# the user set one (HKCU\Software\Microsoft\Speech\AudioInput DefaultTokenId, an MMAudioIn token named by its endpoint
# id), otherwise Windows' default capture device for the console role, which is what SAPI's default input follows.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$src = @"
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;
using System.Speech.Recognition;
using System.Speech.Synthesis;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorCo { }
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    [PreserveSig] int EnumAudioEndpoints(int flow, int mask, out IntPtr devices);
    [PreserveSig] int GetDefaultAudioEndpoint(int flow, int role, out IMMDevice device);
    [PreserveSig] int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice device);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    [PreserveSig] int Activate(ref Guid iid, int ctx, IntPtr p, out IntPtr iface);
    [PreserveSig] int OpenPropertyStore(int access, out IPropertyStore store);
    [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
    [PreserveSig] int GetState(out int state);
}
[ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore {
    [PreserveSig] int GetCount(out int n);
    [PreserveSig] int GetAt(int i, out PropKey key);
    [PreserveSig] int GetValue(ref PropKey key, out PropVar value);
}
[StructLayout(LayoutKind.Sequential)] struct PropKey { public Guid fmt; public int pid; }
[StructLayout(LayoutKind.Sequential)] struct PropVar { public ushort vt; public ushort r1, r2, r3; public IntPtr p; public IntPtr p2; }

public static class AgoraMic {
    [DllImport("ole32.dll")] static extern int PropVariantClear(ref PropVar v);
    const int Capture = 1, ConsoleRole = 0, Read = 0, Active = 1;
    // PKEY_Device_FriendlyName, e.g. "Microphone (Wireless Controller)"
    static PropKey FriendlyName = new PropKey { fmt = new Guid("A45C254E-DF1C-4EFD-8020-67D146A850E0"), pid = 14 };

    // -> the endpoint's name, "" when there is none; how says which choice named it
    public static string Name(out string how) {
        how = "";
        var e = (IMMDeviceEnumerator)new MMDeviceEnumeratorCo();
        IMMDevice d = null;
        string sapi = SapiChoice();
        if (sapi != null && e.GetDevice(sapi, out d) == 0 && d != null) {
            int st; d.GetState(out st);
            if (st == Active) how = "speech settings' choice"; else d = null;
        }
        if (d == null) {
            if (e.GetDefaultAudioEndpoint(Capture, ConsoleRole, out d) != 0 || d == null) return "";   // E_NOTFOUND: none
            how = "Windows' default input";
        }
        IPropertyStore ps;
        if (d.OpenPropertyStore(Read, out ps) != 0 || ps == null) return "an input device with no name";
        PropVar v;
        string name = null;
        if (ps.GetValue(ref FriendlyName, out v) == 0) {
            if (v.vt == 31 && v.p != IntPtr.Zero) name = Marshal.PtrToStringUni(v.p);     // VT_LPWSTR
            PropVariantClear(ref v);
        }
        return string.IsNullOrEmpty(name) ? "an input device with no name" : name;
    }

    static string SapiChoice() {
        try {
            using (var k = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Speech\AudioInput")) {
                var t = k == null ? null : k.GetValue("DefaultTokenId") as string;
                if (t == null || t.IndexOf(@"\MMAudioIn\", StringComparison.OrdinalIgnoreCase) < 0) return null;
                return t.Substring(t.LastIndexOf('\\') + 1);
            }
        } catch (Exception) { return null; }
    }
}

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

    // a9138: the microphone's name, said as an event; "" when there is no input device
    public static string Device() {
        string name = "", how = "";
        try { name = AgoraMic.Name(out how); }
        catch (Exception x) { Emit("{\"ev\":\"device\",\"name\":null,\"why\":" + Q("its name could not be read: " + x.Message) + "}"); return null; }
        if (name == "") Emit("{\"ev\":\"device\",\"name\":\"\",\"why\":\"no input device\"}");
        else Emit("{\"ev\":\"device\",\"name\":" + Q(name) + ",\"how\":" + Q(how) + "}");
        return name;
    }

    public static void Listen(string from, string path, double quiet) {
        if (rec == null) { Emit("{\"ev\":\"error\",\"where\":\"listen\",\"why\":\"no recognizer\"}"); return; }
        if (listening) return;
        if (from != "file" && Device() == "") { Emit("{\"ev\":\"error\",\"where\":\"listen\",\"why\":\"no microphone\"}"); return; }
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
        'device' { [void][AgoraVoice]::Device() }
        'stop'   { [AgoraVoice]::Stop() }
        'say'    { [AgoraVoice]::Say([string]$c.id, [string]$c.text, [string]$c.to, [string]$c.path) }
        'hush'   { [AgoraVoice]::Hush() }
        'quit'   { [AgoraVoice]::Stop(); [AgoraVoice]::Hush(); exit 0 }
        default  { [AgoraVoice]::Emit('{"ev":"error","where":"command","why":"unknown"}') }
    }
}
[AgoraVoice]::Stop(); [AgoraVoice]::Hush()
