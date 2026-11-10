"""Telling the kernel about a new member: `POST <kernel>/keep/account` (SEAM.md section 4).

Called once the welcome questions are answered, so the kernel gets the name
and answers with the account. If the kernel is away, nothing is lost: the
account waits, and the next visit to /home asks again. The kernel's join is
idempotent: asking twice for the same account returns the same person.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class KernelAway(Exception):
    """The kernel did not answer. Try again later."""


class KernelRefused(Exception):
    """The kernel answered no. `str(exc)` is written for the person."""


def keep_account(kernel_url: str, secret: str, account: str, name: str, invite: dict | None,
                 answers: dict) -> dict:
    body = json.dumps({"account": account, "name": name, "invite": invite, "answers": answers}).encode()
    req = urllib.request.Request(kernel_url.rstrip("/") + "/keep/account", body, method="POST",
                                 headers={"Content-Type": "application/json", "X-Kernel-Secret": secret})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read(100_000))
    except urllib.error.HTTPError as exc:
        try:
            said = json.loads(exc.read(100_000) or b"{}")
        except ValueError:
            said = {}
        if exc.code == 403 and said.get("refused"):
            raise KernelRefused(said["refused"]) from exc
        raise KernelAway(f"kernel said {exc.code}: {said.get('error', '')}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise KernelAway(str(exc)) from exc
