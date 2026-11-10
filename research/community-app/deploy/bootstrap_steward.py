"""Make (or find) the entry account of the first SITE_LEADERS address, as a leader, and print its account id, so a new
world's genesis can name that account as its steward. Prints nothing secret. Safe to run again.

    SITE_* settings in the environment (as the entry service has them), then:
    python research/community-app/deploy/bootstrap_steward.py

Claude, 5 Nov 2026, for the Seabright public host (research/community-app/board/PUBLIC-HOST.md).
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
sys.path.insert(0, str(SITE))

from agora_entry import config          # noqa: E402
from agora_entry.web import App          # noqa: E402


def main():
    cfg = config.from_env()
    email = sorted(cfg.leaders)[0] if cfg.leaders else None
    if not email:
        sys.exit("SITE_LEADERS is empty")
    svc = App(cfg).service
    have = svc.account_by_email(email)
    if have is None:
        with svc.store.connect() as conn:
            account_id = svc._create_account(conn, email, None, method="bootstrap")
            svc._grant(conn, account_id, "leader", "config")
        have = svc.account(account_id)
    print(have["id"])


if __name__ == "__main__":
    main()
