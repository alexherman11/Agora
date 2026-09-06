"""Exercise the same local session bootstrap as the browser."""

from fastapi.testclient import TestClient as BaseClient


class TestClient(BaseClient):
    __test__ = False

    def __init__(self, app, **kwargs):
        super().__init__(app, base_url="http://localhost", **kwargs)

    def __enter__(self):
        super().__enter__()
        token = self.get("/session").json()["token"]
        self.headers["x-agora-session"] = token
        return self
