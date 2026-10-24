"""Every page the entry service shows, and the sign-in email.

Values are escaped by `render`; only fragments built here from escaped parts
are marked Safe.
"""

from __future__ import annotations

import time

from .render import Safe, esc, fill, join, tag

ASSET = "2"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def day(ts: int | None) -> str:
    if ts is None:
        return ""
    t = time.localtime(ts)
    return f"{t.tm_mday} {MONTHS[t.tm_mon - 1]} {t.tm_year}"


def when(ts: int) -> str:
    t = time.localtime(ts)
    hour = t.tm_hour % 12 or 12
    return f"{day(ts)}, {hour}:{t.tm_min:02d} {'am' if t.tm_hour < 12 else 'pm'}"


def first_name(account: dict) -> str:
    name = account.get("display_name") or account.get("suggested_name") or ""
    return name.split(" ")[0] if name else "neighbour"


def error_bits(message: str | None, field_id: str) -> dict:
    if not message:
        return {"error": "", "error_class": "", "error_attrs": Safe("")}
    return {"error": Safe(f'<p class="field-error" id="{field_id}-error">{esc(message)}</p>'),
            "error_class": " invalid",
            "error_attrs": Safe(f' aria-invalid="true" aria-describedby="{field_id}-error"')}


STATUS_LABEL = {"open": "Open", "frozen": "Frozen", "expired": "Expired", "full": "Used up",
                "missing": "Gone"}


class Pages:
    def __init__(self, app):
        self.app = app

    @property
    def content(self) -> dict:
        return self.app.content

    # -- frame --------------------------------------------------------------
    def nav(self, req) -> Safe:
        if req.account and not req.account["onboarded_at"]:
            return Safe("")  # nothing to wander off to before the questions
        if req.account:
            links = []
            if "leader" in self.app.service.roles(req.account["id"]):
                links.append(tag("a", "Invites", href="/leader/invites"))
            links.append(tag("a", "You", href="/account"))
            return join(links)
        if req.path.startswith("/signin") or req.path.startswith("/join"):
            return Safe("")
        return tag("a", "Sign in", href="/signin", class_="nav-signin")

    def page(self, req, title: str, content, *, status: str = "200 OK", main_class: str = "narrow",
             body_class: str = "", description: str = "", head_extra: str = ""):
        from .web import Response
        c = self.content
        draft = ""
        if c.get("draft"):
            draft = tag("div", c.get("draft_banner", "Draft wording."), class_="draft-banner", role="note")
        html = fill("base.html", title=f"{title} · {c['community_name']}" if title else c["community_name"],
                    description=description or c["hero"]["lead"], asset=ASSET,
                    head_extra=Safe(head_extra), body_class=body_class, draft=draft,
                    community=c["community_name"], nav=self.nav(req), main_class=main_class,
                    content=content, footer=c.get("footer", ""))
        return Response(html, status)

    def message(self, req, heading: str, text: str, *, back: tuple[str, str] | None = None,
                status: str = "200 OK", extra=""):
        back_html = tag("a", back[1], href=back[0], class_="btn ghost") if back else Safe("")
        return self.page(req, heading, fill("message.html", heading=heading, text=text,
                                            extra=extra, back=back_html), status=status)

    def too_many(self, req):
        return self.message(req, "Slow down a little",
                            "That's a lot of tries in a short time. Wait a few minutes and try again.",
                            back=("/", "Front page"), status="429 Too Many Requests")

    # -- public ---------------------------------------------------------------
    def public(self, req):
        c = self.content
        if req.account:
            primary = tag("a", "Go to the place", href="/home", class_="btn primary")
            secondary = Safe("")
        else:
            public = self.app.service.public_invite()
            if public and public.open:
                primary = tag("a", "Join", href="/join/" + public.invite["code"], class_="btn primary")
            else:
                primary = tag("a", "How to join", href="#join", class_="btn primary")
            secondary = tag("a", "Sign in", href="/signin", class_="btn ghost")
        mission = join(tag("p", p) for p in c["mission"]["paragraphs"])
        icons = [_ICON_FEED, _ICON_MAP, _ICON_LINK]
        doing = join(Safe(f'<article class="card"><div class="card-icon" aria-hidden="true">{icons[i % 3]}</div>'
                          f'<h3>{esc(item["title"])}</h3><p>{esc(item["body"])}</p></article>')
                     for i, item in enumerate(c["doing"]["items"]))
        steps = join(Safe(f'<li><span class="step-n" aria-hidden="true">{i + 1}</span><div>'
                          f'<h3>{esc(s["title"])}</h3><p>{esc(s["body"])}</p></div></li>')
                     for i, s in enumerate(c["join"]["steps"]))
        body = fill("public.html", place=c.get("place", ""), hero_title=c["hero"]["title"],
                    hero_lead=c["hero"]["lead"], primary_action=primary, secondary_action=secondary,
                    mission_title=c["mission"]["title"], mission=mission,
                    doing_title=c["doing"]["title"], doing=doing, join_title=c["join"]["title"],
                    steps=steps, no_invite=c["join"]["no_invite"])
        return self.page(req, "", body, main_class="wide", body_class="public")

    def privacy(self, req):
        p = self.app.privacy
        sections = join(Safe(f'<h2>{esc(s["title"])}</h2>' + "".join(f"<p>{esc(b)}</p>" for b in s["body"]))
                        for s in p["sections"])
        body = Safe(f'<section class="panel prose"><h1>{esc(p["title"])}</h1>'
                    f'<p class="fine">{esc(p["updated"])}</p>{sections}</section>')
        return self.page(req, p["title"], body)

    # -- ways in ----------------------------------------------------------------
    def ways_in(self, req, invite_code: str = "", email: str = "", error: str | None = None,
                fine: str = "") -> Safe:
        google = Safe("")
        if self.app.google is not None:
            href = "/auth/google/start" + (f"?invite={invite_code}" if invite_code else "")
            label = "Continue with Google"
            note = Safe('<span class="stand-in">test stand-in</span>') if self.app.cfg.google_mode == "fake" else ""
            google = Safe(f'<a class="btn google" href="{esc(href)}">{_ICON_G}<span>{esc(label)}</span>{note}</a>'
                          '<div class="or" role="separator"><span>or</span></div>')
        return fill("ways_in.html", google=google, csrf=self.app.csrf_token(req), invite=invite_code,
                    email=email, fine=fine,
                    email_button_class="secondary" if self.app.google is not None else "primary",
                    **error_bits(error, "email"))

    def join(self, req, invite: dict, maker: dict | None):
        c = self.content
        who = (maker or {}).get("display_name")
        heading = f"{who} invited you to join" if who else "You're invited to join"
        body = Safe(
            f'<section class="panel">'
            f'<p class="kicker">{esc(heading)}</p>'
            f'<h1>{esc(c["community_name"])}</h1>'
            f'<p class="lead">{esc(c["hero"]["lead"])}</p>'
            f'{self.ways_in(req, invite_code=invite["code"], fine="New here? After this we ask your name and how you would like to help.")}'
            f'<p class="fine">Already a member? Either way signs you in.</p>'
            f'</section>')
        return self.page(req, "Join", body)

    def signin(self, req, invite_code: str | None = None, email: str = "", error: str | None = None):
        c = self.content
        body = Safe(
            f'<section class="panel">'
            f'<h1>Sign in</h1>'
            f'<p class="lead">Welcome back to {esc(c["community_name"])}.</p>'
            f'{self.ways_in(req, invite_code=invite_code or "", email=email, error=error)}'
            f'<p class="fine">New here? You join through an invite link from a neighbour. '
            f'<a href="/#join">How to join</a></p>'
            f'</section>')
        status = "400 Bad Request" if error else "200 OK"
        return self.page(req, "Sign in", body, status=status)

    def invite_closed(self, req, state):
        text = {
            "frozen": "This invite link has been paused by the group's leaders.",
            "expired": "This invite link has expired.",
            "full": "This invite link has been used as many times as it allows.",
            "missing": "We couldn't find this invite link. Check that it was copied whole.",
        }[state.status]
        return self.message(req, "This invite isn't open", text + " Ask whoever shared it for a new one. "
                            "Already a member? You can still sign in.", back=("/signin", "Sign in"),
                            status="410 Gone" if state.status != "missing" else "404 Not Found")

    def check(self, req, email: str, error: str | None = None):
        dev = ""
        if self.app.cfg.is_test:
            dev = Safe('<p class="dev-note">Test mode: no email is sent. '
                       '<a href="/dev/outbox">Open the test outbox</a></p>')
        body = fill("check.html", email=email, csrf=self.app.csrf_token(req),
                    minutes=self.app.cfg.link_minutes, dev=dev, **error_bits(error, "code"))
        return self.page(req, "Check your email", body, status="400 Bad Request" if error else "200 OK")

    def link_confirm(self, req, token: str, email: str):
        body = Safe(
            f'<section class="panel">'
            f'<h1>Sign in</h1>'
            f'<p class="lead">Signing in as <strong>{esc(email)}</strong>.</p>'
            f'<form method="post" action="/signin/link" class="stack">'
            f'<input type="hidden" name="csrf" value="{esc(self.app.csrf_token(req))}">'
            f'<input type="hidden" name="t" value="{esc(token)}">'
            f'<button class="btn primary" type="submit">Continue</button>'
            f'</form>'
            f'<p class="fine">Not you? Close this page. Nothing happens until you press Continue.</p>'
            f'</section>')
        return self.page(req, "Sign in", body)

    def refused(self, req, refused):
        back = ("/signin", "Back to sign in")
        return self.message(req, "We couldn't sign you in", refused.reason, back=back,
                            status="400 Bad Request")

    # -- questions --------------------------------------------------------
    def fields(self, values: dict, errors: dict) -> Safe:
        out = []
        for q in self.app.questions.questions:
            fid = "q_" + q.key
            err = errors.get(q.key)
            help_html = Safe(f'<p class="field-help" id="{fid}-help">{esc(q.help)}</p>') if q.help else Safe("")
            err_html = Safe(f'<p class="field-error" id="{fid}-error">{esc(err)}</p>') if err else Safe("")
            described = " ".join(x for x in (f"{fid}-help" if q.help else "", f"{fid}-error" if err else "") if x)
            aria = Safe(f' aria-describedby="{described}"' if described else "")
            if q.type == "text":
                value = values.get(q.key, "")
                req_attr = " required" if q.required else ""
                inv = ' aria-invalid="true"' if err else ""
                auto = ' autocomplete="name"' if q.key == "display_name" else ""
                out.append(Safe(
                    f'<div class="field"><label class="field-label" for="{fid}">{esc(q.label)}</label>{help_html}'
                    f'<input class="input{" invalid" if err else ""}" id="{fid}" name="{fid}" value="{esc(value)}" '
                    f'maxlength="{q.max}" placeholder="{esc(q.placeholder)}"{req_attr}{inv}{auto}{aria}>{err_html}</div>'))
            else:
                chosen = values.get(q.key) or ([] if q.type == "choices" else "")
                chosen = chosen if isinstance(chosen, list) else [chosen]
                kind = "checkbox" if q.type == "choices" else "radio"
                opts = join(Safe(
                    f'<label class="chip"><input type="{kind}" name="{fid}" value="{esc(o["value"])}"'
                    f'{" checked" if o["value"] in chosen else ""}><span>{esc(o["label"])}</span></label>')
                    for o in q.options)
                out.append(Safe(
                    f'<fieldset class="field"{aria}><legend class="field-label">{esc(q.label)}</legend>{help_html}'
                    f'<div class="chips">{opts}</div>{err_html}</fieldset>'))
        return join(out)

    def welcome(self, req, values: dict | None = None, errors: dict | None = None):
        account = req.account
        if values is None:
            # "prefill": "name" in questions.json takes the name Google gave, theirs to change.
            known = account.get("display_name") or account.get("suggested_name") or ""
            values = {q.key: known for q in self.app.questions.questions if q.prefill == "name"}
        body = Safe(
            f'<section class="panel">'
            f'<p class="kicker">You\'re nearly in</p>'
            f'<h1>Welcome</h1>'
            f'<p class="lead">{esc(self.app.questions.intro)}</p>'
            f'<form method="post" action="/welcome" class="stack questions" novalidate>'
            f'<input type="hidden" name="csrf" value="{esc(self.app.csrf_token(req))}">'
            f'{self.fields(values, errors or {})}'
            f'<button class="btn primary" type="submit">Done</button>'
            f'</form>'
            f'<p class="fine">We never ask where you live. Signed in as {esc(account["email"])}.</p>'
            f'</section>')
        return self.page(req, "Welcome", body, status="400 Bad Request" if errors else "200 OK")

    def home(self, req):
        account = req.account
        leader = "leader" in self.app.service.roles(account["id"])
        lead_card = ""
        if leader:
            lead_card = Safe('<a class="card link-card" href="/leader/invites"><h3>Invites</h3>'
                             '<p>Make links for each place you share, and QR codes for events.</p></a>')
        body = Safe(
            f'<section class="panel">'
            f'<p class="kicker">You\'re in</p>'
            f'<h1>Hi, {esc(first_name(account))}</h1>'
            f'<p class="lead">The feed will live here: announcements at the top, then what neighbours post. '
            f'It is being built now.</p>'
            f'</section>'
            f'<div class="cards two">{lead_card}'
            f'<a class="card link-card" href="/account"><h3>Your details</h3>'
            f'<p>Your name in chat, and how you\'d like to help.</p></a></div>')
        return self.page(req, "Home", body)

    def account(self, req, values: dict | None = None, errors: dict | None = None, saved: bool = False):
        account = req.account
        if values is None:
            values = self.app.service.answers(account["id"])
            values["display_name"] = account.get("display_name") or ""
        via = "Google or an emailed link" if account.get("google_sub") else "an emailed link"
        csrf = esc(self.app.csrf_token(req))
        note = Safe('<p class="saved" role="status">Saved.</p>') if saved else Safe("")
        body = Safe(
            f'<section class="panel">'
            f'<h1>Your details</h1>{note}'
            f'<form method="post" action="/account" class="stack questions" novalidate>'
            f'<input type="hidden" name="csrf" value="{csrf}">'
            f'{self.fields(values, errors or {})}'
            f'<button class="btn primary" type="submit">Save</button>'
            f'</form>'
            f'</section>'
            f'<section class="panel quiet">'
            f'<h2>Signing in</h2>'
            f'<p>{esc(account["email"])}. You sign in with {esc(via)}.</p>'
            f'<div class="row">'
            f'<form method="post" action="/signout"><input type="hidden" name="csrf" value="{csrf}">'
            f'<button class="btn ghost" type="submit">Sign out</button></form>'
            f'<form method="post" action="/signout"><input type="hidden" name="csrf" value="{csrf}">'
            f'<input type="hidden" name="everywhere" value="1">'
            f'<button class="btn ghost" type="submit">Sign out on every device</button></form>'
            f'</div></section>')
        return self.page(req, "Your details", body, status="400 Bad Request" if errors else "200 OK")

    # -- leaders -------------------------------------------------------------
    def leader_invites(self, req, error: str | None = None, form: dict | None = None):
        form = form or {}
        pick = lambda k, d="": (form.get(k) or [d])[0]  # noqa: E731
        kind = pick("kind", "link")
        public = self.app.service.public_invite()
        public_id = public.invite["id"] if public and public.invite else None
        rows = []
        for inv in self.app.service.invites():
            uses = f'{inv["uses"]} joined' + (f' of {inv["max_uses"]}' if inv["max_uses"] else "")
            flag = Safe(' <span class="chip-s public">On the site</span>') if inv["id"] == public_id else ""
            rows.append(Safe(
                f'<li><a class="invite-row" href="/leader/invites/{esc(inv["id"])}">'
                f'<div><strong>{esc(inv["channel"])}</strong>{flag}'
                f'<span class="sub">{"Event QR" if inv["kind"] == "event" else "Link"} · made by '
                f'{esc(inv["maker_name"] or inv["maker_email"] or "someone")} · until {esc(day(inv["expires_at"]))}</span></div>'
                f'<div class="right"><span class="chip-s {esc(inv["status"])}">{esc(STATUS_LABEL[inv["status"]])}</span>'
                f'<span class="sub">{esc(uses)}</span></div></a></li>'))
        listing = join(rows) if rows else Safe('<li class="empty">No invites yet. Make the first one above.</li>')
        expiry = join(Safe(f'<option value="{d}"{" selected" if str(d) == pick("expires_days", "1" if kind == "event" else "30") else ""}>'
                           f'{esc(_days_label(d))}</option>') for d in self.app.expiry_choices())
        err = Safe(f'<p class="field-error" role="alert">{esc(error)}</p>') if error else Safe("")
        body = Safe(
            f'<section class="panel">'
            f'<h1>Invites</h1>'
            f'<p class="lead">Make one link for each place you share it, so if one gets out of hand you can '
            f'freeze it alone.</p>'
            f'<form method="post" action="/leader/invites" class="stack" novalidate>'
            f'<input type="hidden" name="csrf" value="{esc(self.app.csrf_token(req))}">'
            f'<div class="field"><label class="field-label" for="channel">Where will you share it?</label>'
            f'<input class="input" id="channel" name="channel" maxlength="60" required '
            f'placeholder="Instagram, Nextdoor, 25 Oct meeting…" value="{esc(pick("channel"))}"></div>'
            f'<fieldset class="field"><legend class="field-label">Kind</legend><div class="chips">'
            f'<label class="chip"><input type="radio" name="kind" value="link"{" checked" if kind != "event" else ""}>'
            f'<span>Link to share</span></label>'
            f'<label class="chip"><input type="radio" name="kind" value="event"{" checked" if kind == "event" else ""}>'
            f'<span>QR code for an event</span></label></div></fieldset>'
            f'<div class="two-fields">'
            f'<div class="field"><label class="field-label" for="max_uses">Most people</label>'
            f'<input class="input" id="max_uses" name="max_uses" inputmode="numeric" placeholder="No limit" '
            f'value="{esc(pick("max_uses"))}"></div>'
            f'<div class="field"><label class="field-label" for="expires_days">Open for</label>'
            f'<select class="input" id="expires_days" name="expires_days">{expiry}</select></div>'
            f'</div>{err}'
            f'<button class="btn primary" type="submit">Make invite</button>'
            f'</form></section>'
            f'<section class="panel quiet"><h2>All invites</h2><ul class="invite-list">{listing}</ul></section>')
        return self.page(req, "Invites", body, status="400 Bad Request" if error else "200 OK")

    def leader_invite(self, req, state):
        inv = state.invite
        url = self.app.invite_url(inv)
        maker = self.app.service.account(inv["maker_id"]) or {}
        people = self.app.service.invite_people(inv["id"])
        csrf = esc(self.app.csrf_token(req))
        public = self.app.service.public_invite()
        is_public = bool(public and public.invite and public.invite["id"] == inv["id"])
        plist = join(Safe(f'<li><span>{esc(p["display_name"] or p["email"])}</span>'
                          f'<span class="sub">{esc(when(p["at"]))}</span></li>') for p in people) \
            if people else Safe('<li class="empty">Nobody yet.</li>')
        freeze = ("unfreeze", "Unfreeze this link", "ghost") if inv["frozen_at"] else \
            ("freeze", "Freeze this link", "danger")
        site_btn = ("unpublic", "Take off the public site", "ghost") if is_public else \
            ("public", "Put on the public site", "ghost")
        frozen_note = ""
        if inv["frozen_at"]:
            by = self.app.service.account(inv["frozen_by"] or "") or {}
            frozen_note = Safe(f'<p class="note warn">Frozen {esc(when(inv["frozen_at"]))} by '
                               f'{esc(by.get("display_name") or by.get("email") or "a leader")}. '
                               f'Nobody new can join through it.</p>')
        limit = f'{inv["uses"]} of {inv["max_uses"]}' if inv["max_uses"] else f'{inv["uses"]} (no limit)'
        body = Safe(
            f'<p class="crumb"><a href="/leader/invites">← All invites</a></p>'
            f'<section class="panel">'
            f'<p class="kicker">{"Event QR" if inv["kind"] == "event" else "Invite link"}</p>'
            f'<h1>{esc(inv["channel"])} <span class="chip-s {esc(state.status)}">{esc(STATUS_LABEL[state.status])}</span></h1>'
            f'{frozen_note}'
            f'<label class="field-label" for="link">Link</label>'
            f'<div class="copy-row"><input class="input mono" id="link" value="{esc(url)}" readonly>'
            f'<button class="btn ghost copy" type="button" data-copy="link" hidden>Copy</button></div>'
            f'<dl class="facts">'
            f'<div><dt>Made by</dt><dd>{esc(maker.get("display_name") or maker.get("email") or "")}</dd></div>'
            f'<div><dt>Made</dt><dd>{esc(day(inv["created_at"]))}</dd></div>'
            f'<div><dt>Open until</dt><dd>{esc(when(inv["expires_at"]))}</dd></div>'
            f'<div><dt>Joined</dt><dd>{esc(limit)}</dd></div>'
            f'</dl>'
            f'<div class="qr-preview">{self.app.qr_svg(inv)}</div>'
            f'<div class="row">'
            f'<a class="btn secondary" href="/leader/invites/{esc(inv["id"])}/qr">Printable QR code</a>'
            f'<form method="post" action="/leader/invites/{esc(inv["id"])}/{freeze[0]}">'
            f'<input type="hidden" name="csrf" value="{csrf}">'
            f'<button class="btn {freeze[2]}" type="submit">{esc(freeze[1])}</button></form>'
            f'<form method="post" action="/leader/invites/{esc(inv["id"])}/{site_btn[0]}">'
            f'<input type="hidden" name="csrf" value="{csrf}">'
            f'<button class="btn {site_btn[2]}" type="submit">{esc(site_btn[1])}</button></form>'
            f'</div></section>'
            f'<section class="panel quiet"><h2>Who came through it</h2><ul class="people">{plist}</ul></section>')
        return self.page(req, inv["channel"], body,
                         head_extra='<script src="/entry-static/copy.js" defer></script>')

    def invite_qr(self, req, state):
        from .web import Response
        inv, c = state.invite, self.content
        url = self.app.invite_url(inv)
        closed = "" if state.open else f'<p class="qr-closed">This invite is {esc(STATUS_LABEL[state.status].lower())}.</p>'
        html = (
            f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="color-scheme" content="light">'
            f'<title>QR · {esc(inv["channel"])}</title>'
            f'<link rel="stylesheet" href="/entry-static/site.css?v={ASSET}"></head>'
            f'<body class="print-qr"><main class="poster">'
            f'<p class="crumb no-print"><a href="/leader/invites/{esc(inv["id"])}">← Back</a> · '
            f'Use your browser\'s Print to print this page.</p>'
            f'<img class="poster-mark" src="/entry-static/icon.svg" alt="" width="56" height="56">'
            f'<h1>{esc(c["community_name"])}</h1>'
            f'<p class="poster-lead">Scan to join</p>'
            f'<div class="poster-qr">{self.app.qr_svg(inv)}</div>'
            f'<p class="poster-event">{esc(inv["channel"])}</p>'
            f'<p class="poster-url">{esc(url)}</p>{closed}'
            f'<p class="poster-fine">Open until {esc(when(inv["expires_at"]))}</p>'
            f'</main></body></html>')
        return Response(html)

    # -- test mode --------------------------------------------------------------
    def outbox(self, req, messages: list[dict]):
        items = []
        for m in messages:
            links = join(tag("a", "Open the link", href=link, class_="btn secondary") for link in m["links"])
            items.append(Safe(
                f'<li class="mail"><div class="mail-head"><strong>{esc(m["subject"])}</strong>'
                f'<span class="sub">to {esc(m["to"])} · {esc(when(m["at"]))}</span></div>'
                f'<pre>{esc(m["text"])}</pre>{links}</li>'))
        listing = join(items) if items else Safe('<li class="empty">Nothing sent yet.</li>')
        body = Safe(f'<section class="panel"><p class="kicker">Test mode</p><h1>Outbox</h1>'
                    f'<p class="lead">Email the site would have sent, newest first. Nothing leaves this computer.</p>'
                    f'<ul class="outbox">{listing}</ul></section>')
        return self.page(req, "Outbox", body)


def _days_label(d: int) -> str:
    return {1: "1 day", 7: "1 week", 30: "30 days", 90: "90 days", 365: "1 year"}[d]


def signin_email(app, send: dict) -> tuple[str, str, str | None, list[str]]:
    """(subject, text, html, links) for one sign-in email."""
    name = app.content["community_name"]
    if send["kind"] == "link":
        url = f'{app.cfg.base_url}/signin/link?t={send["token"]}'
        code = send["code"]
        spaced = f"{code[:3]} {code[3:]}"
        verb = "join" if send["new"] else "sign in to"
        subject = f"Your link to {verb} {name}"
        text = (f"Hi,\n\nHere's your link to {verb} {name}:\n\n{url}\n\n"
                f"Or type this code on the sign-in page: {spaced}\n\n"
                f"The link and code work once, for the next {app.cfg.link_minutes} minutes. "
                f"If you didn't ask for this, ignore this email: nobody can sign in without it.\n")
        html = (f'<div style="font-family:system-ui,sans-serif;color:#1f2a30;max-width:480px;line-height:1.5">'
                f'<p>Hi,</p><p>Here\'s your link to {esc(verb)} {esc(name)}:</p>'
                f'<p><a href="{esc(url)}" style="display:inline-block;background:#1d6f6a;color:#fff;'
                f'padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:600">'
                f'{"Join" if send["new"] else "Sign in"}</a></p>'
                f'<p>Or type this code on the sign-in page:</p>'
                f'<p style="font-size:24px;letter-spacing:4px;font-weight:600">{esc(spaced)}</p>'
                f'<p style="color:#5f6b70;font-size:14px">The link and code work once, for the next '
                f'{app.cfg.link_minutes} minutes. If you didn\'t ask for this, ignore this email: nobody can '
                f'sign in without it.</p></div>')
        return subject, text, html, [url]
    if send["kind"] == "invite_closed":
        why = "the invite link you used has closed"
    else:
        why = "this address isn't a member yet, and joining is by invite"
    subject = f"About signing in to {name}"
    text = (f"Hi,\n\nSomeone, hopefully you, asked to sign in to {name} with this address, but {why}.\n\n"
            f"Ask a neighbour who's already in for an invite link, or come to the next meeting.\n\n"
            f"If you didn't ask, you can ignore this email.\n")
    return subject, text, None, []


_ICON_G = ""  # Google asks for its own button artwork; add it with the real keys.
_ICON_FEED = ('<svg viewBox="0 0 24 24" width="22" height="22"><path d="M5 5h14M5 10h14M5 15h9" fill="none" '
              'stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="18" cy="17" r="2.2" '
              'fill="currentColor"/></svg>')
_ICON_MAP = ('<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 21s-6-5.5-6-10.5a6 6 0 0 1 12 0C18 15.5 '
             '12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
             '<circle cx="12" cy="10.5" r="2.2" fill="currentColor"/></svg>')
_ICON_LINK = ('<svg viewBox="0 0 24 24" width="22" height="22"><circle cx="6.5" cy="12" r="2.5" fill="none" '
              'stroke="currentColor" stroke-width="1.8"/><circle cx="17.5" cy="6.5" r="2.5" fill="none" '
              'stroke="currentColor" stroke-width="1.8"/><circle cx="17.5" cy="17.5" r="2.5" fill="none" '
              'stroke="currentColor" stroke-width="1.8"/><path d="m8.8 10.8 6.4-3.2M8.8 13.2l6.4 3.2" '
              'stroke="currentColor" stroke-width="1.8"/></svg>')
