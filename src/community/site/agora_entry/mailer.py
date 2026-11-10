"""Sending sign-in email.

Test mode writes each message to `var/outbox/` (an .eml file plus one line in
outbox.jsonl) and sends nothing. Live mode speaks SMTP with STARTTLS to the
provider Alex chooses; every common provider (Postmark, Resend, Amazon SES,
Brevo, Mailgun) offers SMTP, so no provider SDK is needed.
"""

from __future__ import annotations

import json
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path


def build(sender: str, to: str, subject: str, text: str, html_body: str | None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = make_msgid(domain="agora-entry")
    msg["Auto-Submitted"] = "auto-generated"
    msg.set_content(text)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    return msg


class FileMailer:
    def __init__(self, outbox: Path, sender: str):
        self.outbox = Path(outbox)
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.sender = sender
        self._lock = threading.Lock()

    def send(self, to: str, subject: str, text: str, html_body: str | None = None,
             links: list[str] | None = None) -> None:
        msg = build(self.sender, to, subject, text, html_body)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        with self._lock:
            n = len(list(self.outbox.glob("*.eml")))
            (self.outbox / f"{stamp}-{n:04d}.eml").write_bytes(bytes(msg))
            with open(self.outbox / "outbox.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"at": int(time.time()), "to": to, "subject": subject,
                                     "text": text, "links": links or []}) + "\n")

    def recent(self, limit: int = 20) -> list[dict]:
        path = self.outbox / "outbox.jsonl"
        if not path.is_file():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in reversed(lines[-limit:])]


class SmtpMailer:
    def __init__(self, host: str, port: int, user: str, password: str, sender: str):
        self.host, self.port, self.user, self.password = host, port, user, password
        self.sender = sender

    def send(self, to: str, subject: str, text: str, html_body: str | None = None,
             links: list[str] | None = None) -> None:
        msg = build(self.sender, to, subject, text, html_body)
        context = ssl.create_default_context()
        if self.port == 465:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=20, context=context) as s:
                self._deliver(s, msg)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=20) as s:
                s.starttls(context=context)
                self._deliver(s, msg)

    def _deliver(self, s: smtplib.SMTP, msg: EmailMessage) -> None:
        if self.user:
            s.login(self.user, self.password)
        s.send_message(msg)
