"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

Allowlisted, sanitized worker activity. Never publish tool input wholesale."""
import re


def redact(text):
    text = str(text)
    # Keep quoted values together, including escaped and doubled quote characters.
    value = r'''(?:"(?:\\.|`.|""|[^"\\`])*"|'(?:\\.|''|[^'\\])*'|[^\s;&|]+)'''
    text = re.sub(r'''(?i)(["']authorization\s*:\s*)[^"'\r\n]*''', r'\1[hidden]', text)
    text = re.sub(r'''(?i)\b(Bearer|Basic)\s+[^\s"']+''', r'\1 [hidden]', text)
    text = re.sub(r'(?i)(https?://)[^/\s:@]+:[^/\s@]+@', r'\1[hidden]@', text)
    text = re.sub(r'''(?im)(\bset\s+"?[\w.-]+=)[^&|\r\n]*''', r'\1[hidden]', text)
    # Named credentials in CLI flags, headers, JSON, and PowerShell parameters.
    # Do this BEFORE general assignments: cfg={"password": "value"} must not lose
    # its password key while leaving its value behind.
    secret = r'(?:[\w.-]*(?:token|password|passwd|secret|api[_-]?key|credential)[\w.-]*|authorization|key)'
    text = re.sub(r'''(?i)(["']?(?:--?)?''' + secret + r'''["']?\s*(?:[:=]\s*|\s+))''' + value,
                  r'\1[hidden]', text)
    text = re.sub(r'''(?i)((?:--user|--proxy-user|-u|-p)\s+)''' + value, r'\1[hidden]', text)
    # Hide every assigned environment value, including ordinary (non-secret) names.
    text = re.sub(r'''(?i)((?:\$env:|%env:)?[\w.-]+\s*=\s*)''' + value,
                  r'\1[hidden]', text)
    text = re.sub(r'''(?im)(\bset(?:x)?\s+["']?[\w.-]+\s+)''' + value,
                  r'\1[hidden]', text)
    text = re.sub(r'\b(?:sk-[\w-]{8,}|gh[pousr]_[\w]{8,}|github_pat_[\w_]+|eyJ[\w-]+\.[\w-]+\.[\w-]+)\b',
                  '[hidden]', text)
    return text


def record(label, text):
    detail = label + ': ' + redact(text)
    summary = ' '.join(detail.split())
    return dict(summary=summary if len(summary) <= 120 else summary[:119] + '…', detail=detail)


def codex(item):
    kind = item.get('type')
    if kind == 'commandExecution' and isinstance(item.get('command'), str):
        return record('ran', item['command'])
    if kind == 'fileChange':
        paths = [c['path'] for c in item.get('changes') or []
                 if isinstance(c, dict) and isinstance(c.get('path'), str)]
        if paths:
            return record('changed', ', '.join(paths))
    return None


def tool(event):
    """Claude native tools; Codex has already been reduced to a safe record."""
    if event.get('activity'):
        return event['activity']
    name, data = event.get('name'), event.get('input') or {}
    if name in ('Bash', 'shell', 'exec_command') and isinstance(data.get('command', data.get('cmd')), str):
        return record('ran', data.get('command', data.get('cmd')))
    if name in ('Read', 'Write', 'Edit', 'MultiEdit') and isinstance(data.get('file_path'), str):
        return record('read' if name == 'Read' else 'changed', data['file_path'])
    return None
