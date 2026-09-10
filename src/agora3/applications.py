"""Installed browser applications, subject-bound appearances, and portable releases.
Never execute application code on the host or expand a running view's grant implicitly.
"""

import copy
import secrets
import uuid

from agora3.application_data import request
from agora3.application_schema import BUNDLE, check_bundle
from agora3.packages import check_source, source_digest
from agora3.world import Refusal

VIEW = "agora.application-view"


class Applications:
    def __init__(self, gateway):
        self.gateway = gateway
        self.world, self.packages = gateway.world, gateway.packages

    def installed(self, package, *, enabled=True):
        obj = self.packages.installation(package)
        value = obj.get("facets", {}).get("agora.installation")
        if not value or (enabled and value.get("enabled") is False):
            raise Refusal("The application is not installed or has been disabled.")
        receipt = self.packages.receipt(value["build"])
        if "application" not in receipt["source"]["manifest"]:
            raise Refusal("This package does not provide a browser application.")
        return obj, receipt

    def view(self, view):
        obj = self.world.get(view)
        if VIEW not in obj["facets"]:
            raise Refusal("Not an application view.")
        return obj

    def rows(self):
        result = self.world.query([VIEW], 1000)
        if not result["complete"]:
            raise Refusal("Application view listing exceeds this prototype's 1000-view limit.")
        return result["items"]

    @staticmethod
    def public_view(obj):
        value = obj["facets"][VIEW]
        return {
            "id": obj["id"],
            "revision": obj["revision"],
            **{
                k: copy.deepcopy(value[k])
                for k in ("package", "subject", "build", "installation_revision", "open", "bounds")
            },
        }

    def list(self):
        apps = []
        for obj in self.world.query(["agora.installation"], 1000)["items"]:
            installation = obj["facets"]["agora.installation"]
            if installation.get("enabled") is False:
                continue
            receipt = self.packages.receipt(installation["build"])
            manifest = receipt["source"]["manifest"]
            if "application" in manifest:
                apps.append(
                    {
                        "package": installation["package"],
                        "name": manifest["name"],
                        "revision": obj["revision"],
                        "build": installation["build"],
                        "description": manifest.get("description", ""),
                        "contract": copy.deepcopy(manifest["application"]),
                    }
                )
        return {"applications": apps, "views": [self.public_view(obj) for obj in self.rows()]}

    def open(self, actor, package, subject=None, bounds=None):
        installation, receipt = self.installed(package)
        app = receipt["source"]["manifest"]["application"]
        changes = []
        if subject is None:
            subject = "document-" + uuid.uuid4().hex
            facets = copy.deepcopy(app["create"])
            changes.append({"id": subject, "expected_revision": 0, "facets": facets})
        else:
            target = self.world.get(subject)
            facets = target["facets"]
        if not set(app["accepts"]) <= set(facets):
            raise Refusal("This object does not support the application's accepted facets.")
        if subject.startswith("agora."):
            raise Refusal("Protected runtime objects cannot be application subjects.")
        view = "agora.view." + uuid.uuid4().hex
        active = sum(obj["facets"][VIEW]["open"] for obj in self.rows())
        if active >= 32:
            raise Refusal("Close a view first; this prototype supports 32 open views.")
        value = {
            "package": package,
            "subject": subject,
            "build": installation["facets"]["agora.installation"]["build"],
            "installation_revision": installation["revision"],
            "open": True,
            "lease": secrets.token_urlsafe(24),
            "state": {},
            "grant": {k: list(app[k]) for k in ("read_facets", "write_facets")},
            "bounds": self.bounds(
                bounds or {"x": 24 + active * 28, "y": 24 + active * 28, **app["size"]}
            ),
        }
        changes.append({"id": view, "expected_revision": 0, "facets": {VIEW: value}})
        self.gateway.commit(
            actor, changes, internal=True, guards={installation["id"]: installation["revision"]}
        )
        return self.public_view(self.view(view))

    @staticmethod
    def bounds(value):
        if not isinstance(value, dict) or set(value) != {"x", "y", "width", "height"}:
            raise Refusal("View bounds require x, y, width and height.")
        if any(type(n) not in (int, float) or not -10000 <= n <= 10000 for n in value.values()):
            raise Refusal("View bounds must be finite numbers between -10000 and 10000.")
        if not 220 <= value["width"] <= 1400 or not 180 <= value["height"] <= 1200:
            raise Refusal("View size must be 220–1400 by 180–1200 pixels.")
        return dict(value)

    def update(self, actor, obj, **patch):
        value = {**obj["facets"][VIEW], **patch}
        self.gateway.commit(
            actor,
            [{"id": obj["id"], "expected_revision": obj["revision"], "facets": {VIEW: value}}],
            internal=True,
        )
        return self.public_view(self.view(obj["id"]))

    def surface(self, view):
        obj = self.view(view)
        value = obj["facets"][VIEW]
        self.installed(value["package"])
        if not value["open"]:
            raise Refusal("The view is closed.")
        receipt = self.packages.receipt(value["build"])
        return {
            "html": self.packages.browser_html(value["build"]),
            "view": self.public_view(obj),
            "context": {
                "view": view,
                "subject": value["subject"],
                "lease": value["lease"],
                "package": value["package"],
                "grant": copy.deepcopy(value["grant"]),
                "name": receipt["source"]["manifest"]["name"],
            },
        }

    def refresh(self, actor, view):
        obj = self.view(view)
        value = obj["facets"][VIEW]
        installation, receipt = self.installed(value["package"])
        app = receipt["source"]["manifest"]["application"]
        if any(not set(app[k]) <= set(value["grant"][k]) for k in ("read_facets", "write_facets")):
            raise Refusal(
                "Update requests broader access. Open a new view to grant that access explicitly."
            )
        if not set(app["accepts"]) <= set(self.world.get(value["subject"])["facets"]):
            raise Refusal("Updated application no longer accepts this subject.")
        return self.update(
            actor,
            obj,
            build=installation["facets"]["agora.installation"]["build"],
            installation_revision=installation["revision"],
            lease=secrets.token_urlsafe(24),
            grant={k: list(app[k]) for k in ("read_facets", "write_facets")},
        )

    def uninstall(self, actor, package, expected_revision):
        installation, _ = self.installed(package)
        if installation["revision"] != expected_revision:
            raise Refusal("Application installation changed; inspect before uninstalling.")
        changes = [
            {
                "id": installation["id"],
                "expected_revision": expected_revision,
                "facets": {
                    "agora.installation": {
                        **installation["facets"]["agora.installation"],
                        "enabled": False,
                    }
                },
            }
        ]
        for obj in self.rows():
            value = obj["facets"][VIEW]
            if value["package"] == package and value["open"]:
                changes.append(
                    {
                        "id": obj["id"],
                        "expected_revision": obj["revision"],
                        "facets": {
                            VIEW: {**value, "open": False, "lease": secrets.token_urlsafe(24)}
                        },
                    }
                )
        self.gateway.commit(actor, changes, internal=True)
        return {"uninstalled": package, "content_preserved": True, "schemas_preserved": True}

    def export(self, package):
        _, receipt = self.installed(package, enabled=False)
        return {
            "format": BUNDLE,
            "source": copy.deepcopy(receipt["source"]),
            "sha256": receipt["digest"],
        }

    def import_bundle(self, actor, bundle, expected_revision=0):
        check_bundle(bundle)
        source = bundle["source"]
        check_source(source["files"], source["manifest"])
        if source_digest(source) != bundle["sha256"]:
            raise Refusal("Application source checksum does not match the bundle.")
        saved = self.packages.save(
            actor,
            id=source["id"],
            expected_revision=expected_revision,
            files=source["files"],
            manifest=source["manifest"],
        )
        revision = next(
            o["revision"] for o in saved["items"] if o["id"] == "agora.package." + source["id"]
        )
        built = self.packages.build(actor, id=source["id"], expected_revision=revision)
        self.packages.install(actor, **built["install_args"])
        return {
            "package": source["id"],
            "source_revision": revision,
            "build": built["build"],
            "installed": True,
        }

    def dispatch(self, actor, name, args):
        # The parent holds management authority. Child frames receive only request,
        # with a lease bound to one subject; declarations never grant global access.
        with self.gateway.lock:
            self.gateway.check_authority(actor)
            if name == "list":
                return self.list()
            if name == "open":
                return self.open(actor, **args)
            if name == "surface":
                return self.surface(**args)
            if name == "request":
                obj = self.view(args["view"])
                value = obj["facets"][VIEW]
                self.installed(value["package"])
                if not value["open"] or not secrets.compare_digest(value["lease"], args["lease"]):
                    raise Refusal("The application view was closed, refreshed or revoked.")
                return request(self.gateway, actor, obj, args["method"], args["args"])
            if name == "position":
                return self.update(
                    actor, self.view(args["view"]), bounds=self.bounds(args["bounds"])
                )
            if name == "close":
                return self.update(
                    actor, self.view(args["view"]), open=False, lease=secrets.token_urlsafe(24)
                )
            if name == "reopen":
                obj = self.view(args["view"])
                self.installed(obj["facets"][VIEW]["package"])
                if (
                    not obj["facets"][VIEW]["open"]
                    and sum(row["facets"][VIEW]["open"] for row in self.rows()) >= 32
                ):
                    raise Refusal("Close a view first; this prototype supports 32 open views.")
                return self.update(actor, obj, open=True, lease=secrets.token_urlsafe(24))
            if name == "refresh":
                return self.refresh(actor, **args)
            if name == "uninstall":
                return self.uninstall(actor, **args)
            if name == "export":
                return self.export(**args)
            if name == "import":
                return self.import_bundle(actor, **args)
            raise Refusal("Unknown application operation.")
