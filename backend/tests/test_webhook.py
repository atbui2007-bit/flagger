import hashlib
import hmac
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
from database import get_db


TEST_SECRET = "test-webhook-secret"
PUSH_PAYLOAD = {
    "repository": {
        "id": 7,
        "full_name": "owner/repo",
        "default_branch": "main",
        "owner": {"login": "owner"},
    },
    "ref": "refs/heads/main",
    "commits": [],
}


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeSession:
    def __init__(self, row=None):
        self.row = row
        self.executions = []
        self.commits = 0

    async def execute(self, query, params=None):
        self.executions.append((str(query), params))
        return FakeResult(self.row)

    async def commit(self):
        self.commits += 1


def signed_headers(body, event="push"):
    digest = hmac.new(TEST_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return {
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": f"sha256={digest}",
        "Content-Type": "application/json",
    }


def request(body, session=None, event="push", headers=None):
    session = session or FakeSession()

    async def override_db():
        yield session

    main.app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(main.app) as client:
            return client.post(
                "/webhook",
                content=body,
                headers=headers if headers is not None else signed_headers(body, event),
            )
    finally:
        main.app.dependency_overrides.clear()


def push_body():
    return json.dumps(PUSH_PAYLOAD).encode()


def active_repo():
    return SimpleNamespace(
        id="repo-id",
        installation_id="installation-id",
        removed_at=None,
        full_name="owner/repo",
        suspended_at=None,
        deleted_at=None,
        github_installation_id=None,
    )


def test_missing_signature_returns_401():
    response = request(push_body(), headers={"X-GitHub-Event": "push"})
    assert response.status_code == 401


def test_wrong_signature_returns_403():
    headers = signed_headers(push_body())
    headers["X-Hub-Signature-256"] = "sha256=wrong"
    response = request(push_body(), headers=headers)
    assert response.status_code == 403


def test_invalid_json_with_valid_signature_returns_400():
    response = request(b"{not-json")
    assert response.status_code == 400


def test_push_for_unknown_repo_is_ignored():
    response = request(push_body(), FakeSession(row=None))
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_push_for_repo_without_installation_returns_409():
    repo = active_repo()
    repo.installation_id = None
    response = request(push_body(), FakeSession(repo))
    assert response.status_code == 409


def test_push_for_active_installation_dispatches(monkeypatch):
    calls = []

    async def fake_handle_push(payload, session):
        calls.append((payload, session))

    monkeypatch.setattr(main, "handle_push", fake_handle_push)
    session = FakeSession(active_repo())
    response = request(push_body(), session)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    assert calls == [(PUSH_PAYLOAD, session)]


def test_unhandled_event_is_received():
    body = json.dumps({"zen": "test"}).encode()
    response = request(body, event="ping")
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
