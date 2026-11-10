"""World-only intentional chat context (a7063). Prints scoped patches; never applies live."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def before(name):
    return (HERE / f"before-{name}.lens").read_text(encoding="utf-8")


CLEAR = 'topic="" reply_to="" quote="" reply_in="" reply_thread="" reply_kind=""'
PENDING = '(($draft.topic or "") != "" or ($draft.reply_to or "") != "" or ($draft.reply_thread or "") != "")'

TOPIC = '''    topic : column
      only when held = "" and ($draft.reply_to or "") = "" and ($draft.reply_thread or "") = ""
      chip : row
        role answering
        only when ($draft.topic or "") != ""
        label : text "About $draft.topic"
          role aboutname
          share 1
          clamp 1
        lifetime : text "next message only"
          role meta
        remove : text "×"
          role tool
          tip "Remove context" "Send without the attached item"
          on click do prop $draft topic=""
      offer : row
        role tagline
        only when ($draft.topic or "") = "" and vopen != "" and vopen != "a5080"
        attach : text "Attach open item"
          role tool
          tip "Attach open item" "Include this named item with your next message only"
          on click do prop $draft topic=$(vopen)
        name : text "$(vopen)"
          role aboutname
          clamp 1
'''

NATIVE_TOPIC = '''  topic : column
    only when ($draft.reply_to or "") = "" and ($draft.reply_thread or "") = ""
    chip : row
      only when ($draft.topic or "") != ""
      label : text "About $draft.topic"
        role recipient
        share 1
        clamp 1
      lifetime : text "next message only"
        role meta
      remove : text "×"
        role tool
        tip "Remove context" "Send without the attached item"
        on click do prop $draft topic=""
'''

NATIVE_REPLY = '''  answering : row
    only when ($draft.reply_to or "") != "" or ($draft.reply_thread or "") != ""
    label : text "Answering: $draft.quote"
      role meta
      share 1
      clamp 1
    place : text "in $draft.reply_in"
      role meta
    remove : text "×"
      role tool
      on click do prop $draft reply_to="" quote="" reply_in="" reply_thread="" reply_kind=""
'''


def patches():
    hud = before("jeff-chat")
    tail = hud[hud.index("abouting : column\n"):]
    changes = [
        ("jeff-chat", '''  about : column
    of prop:role=home-view,prop:actor=$me as v
    each abouting
''', ""),
        ("jeff-chat", '''    let about = vopen when vopen != "" and vopen != "a5080" and vopen != ($draft.unabout or "")
    let about = "" otherwise
''', '''    let about = ($draft.topic or "")
'''),
        ("jeff-chat", "    answering : row\n", TOPIC + "    answering : row\n"),
        ("jeff-chat", tail, ""),
    ]
    # A successful message consumes its topic/reply intent. A refused append
    # stops its semicolon batch, leaving the pending intent available to retry.
    for line in hud.splitlines(True):
        if line.startswith("      on edit when elsewhere = \"no\""):
            cond, command = line.rstrip("\n").split(" do append ", 1)
            changes.append(("jeff-chat", line,
                            cond + " and " + PENDING + " do append " + command + f"; read $draft; do prop $draft {CLEAR}\n" +
                            cond + " and not " + PENDING + " do append " + command + "\n"))
        elif line.startswith("      on edit when elsewhere = \"yes\"") or line.startswith('      on edit when ($draft.reply_thread'):
            changes.append(("jeff-chat", line, line[:line.index("; read $draft")] + f"; read $draft; do prop $draft {CLEAR}\n"))
        elif line.startswith("          on edit when talk"):
            cond, command = line.rstrip("\n").split(" do ", 1)
            changes.append(("jeff-chat", line,
                            cond + " and " + PENDING + " do " + command + f"; read $draft; do prop $draft {CLEAR}\n" +
                            cond + " and not " + PENDING + " do " + command + "\n"))
        elif line.startswith("      on click when $s.what"):
            changes.append(("jeff-chat", line, line.rstrip("\n") + ' topic=""\n'))
    changes += [
        ("conversation", "  attachments : column\n", NATIVE_REPLY + NATIVE_TOPIC + "  attachments : column\n"),
        ("conversation",
         '    on edit do append a5080 line="$value" default_to="$draft.to" captures="$draft.context" context_from="$draft"\n',
         '    on edit when ($draft.reply_thread or "") != "" do comment $draft.reply_in id=$draft.reply_thread line="$value"; read $draft; do prop $draft ' + CLEAR + '\n'
         '    on edit when ($draft.reply_thread or "") = "" and ($draft.reply_to or "") != "" and ($draft.reply_in or "") != "" and $draft.reply_in != "a5080" do append $draft.reply_in line="$value" reply_to="$draft.reply_to"; read $draft; do prop $draft ' + CLEAR + '\n'
         '    on edit when ($draft.reply_thread or "") = "" and (($draft.reply_to or "") = "" or ($draft.reply_in or "") = "" or $draft.reply_in = "a5080") and ' + PENDING + ' do append a5080 line="$value" default_to="$draft.to" captures="$draft.context" context_from="$draft" reply_to="$draft.reply_to" about="$draft.topic"; read $draft; do prop $draft ' + CLEAR + '\n'
         '    on edit when not ' + PENDING + ' do append a5080 line="$value" default_to="$draft.to" captures="$draft.context" context_from="$draft"\n'),
    ]
    return changes


def apply(name, text):
    for target, old, new in patches():
        if target == name:
            if text.count(old) != 1:
                raise ValueError(f"{name}: expected one occurrence of {old[:80]!r}")
            text = text.replace(old, new, 1)
    return text


if __name__ == "__main__":
    print(json.dumps([{"lens": name, "old": old, "new": new}
                      for name, old, new in patches()], indent=2))
