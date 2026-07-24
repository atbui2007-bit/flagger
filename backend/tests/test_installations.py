from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
import routers.installations as installations_module
from auth import require_user
from database import get_db


USER_CLAIMS = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "user_metadata": {"user_name": "octocat", "provider_id": "12345"},
}
INSTALLATION = {"id": 777, "account": {"login": "octocat", "type": "User"}}


class FakeResult:
    def __init__(self, rows=None):
        self.rows = rows or []

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeSession:
    def __init__(self, rows=None):
        self.rows = rows
        self.executions = []
        self.commits = 0

    async def execute(self, query, params=None):
        self.executions.append((str(query), params))
        return FakeResult(self.rows)

    async def commit(self):
        self.commits += 1


def github_responses(user_id=12345, installations=None):
    """Return a fake github_request keyed on the requested path."""
    installations = installations if installations is not None else [INSTALLATION]

    async def fake_github_request(method, path, token=None, **kwargs):
        if path == "/user":
            return SimpleNamespace(status_code=200, json=lambda: {"id": user_id, "login": "octocat"})
        if path.startswith("/user/installations"):
            return SimpleNamespace(status_code=200, json=lambda: {"installations": installations})
        raise AssertionError(f"unexpected GitHub call: {path}")

    return fake_github_request


def identity_session(github_id="12345"):
    # _trusted_github_id reads auth.identities; FakeSession replays these rows for
    # every query, but only the identity lookup consumes fetchone().github_id.
    return FakeSession(rows=[SimpleNamespace(github_id=github_id)])


def request_claim(monkeypatch, session=None, claims=USER_CLAIMS, github=None, body=None):
    session = session or identity_session()
    monkeypatch.setattr(installations_module, "github_request", github or github_responses())

    async def override_db():
        yield session

    async def override_user():
        return claims

    main.app.dependency_overrides[get_db] = override_db
    main.app.dependency_overrides[require_user] = override_user
    try:
        with TestClient(main.app) as client:
            return client.post(
                "/installations/claim",
                json=body or {"installation_id": 777, "provider_token": "gho_test"},
            ), session
    finally:
        main.app.dependency_overrides.clear()


def test_claim_happy_path(monkeypatch):
    response, session = request_claim(monkeypatch)
    assert response.status_code == 200
    assert response.json() == {"status": "claimed", "installation_id": 777, "account_login": "octocat"}

    queries = [q for q, _ in session.executions]
    assert any("INSERT INTO installations" in q and "ON CONFLICT (github_installation_id)" in q for q in queries)
    member_calls = [(q, p) for q, p in session.executions if "INSERT INTO installation_members" in q]
    assert len(member_calls) == 1
    assert "ON CONFLICT (installation_id, supabase_user_id)" in member_calls[0][0]
    assert member_calls[0][1]["supabase_user_id"] == USER_CLAIMS["sub"]
    assert member_calls[0][1]["github_login"] == "octocat"
    assert session.commits == 1


def test_claim_installation_not_accessible(monkeypatch):
    response, session = request_claim(monkeypatch, github=github_responses(installations=[]))
    assert response.status_code == 403
    assert not any("INSERT" in q for q, _ in session.executions)
    assert session.commits == 0


def test_claim_github_identity_mismatch(monkeypatch):
    # Token's GitHub user (99999) != the id GoTrue recorded in auth.identities (12345).
    response, session = request_claim(monkeypatch, github=github_responses(user_id=99999))
    assert response.status_code == 403
    assert not any("INSERT" in q for q, _ in session.executions)
    assert session.commits == 0


def test_claim_ignores_user_metadata_provider_id(monkeypatch):
    # F3: a spoofed user_metadata.provider_id must not be trusted -- identity is
    # bound to auth.identities. Here metadata claims 99999 but the token and the
    # identities row both say 12345, so the claim must succeed.
    spoofed = {"sub": USER_CLAIMS["sub"], "user_metadata": {"user_name": "octocat", "provider_id": "99999"}}
    response, session = request_claim(monkeypatch, claims=spoofed)
    assert response.status_code == 200
    assert session.commits == 1


def test_claim_dead_provider_token(monkeypatch):
    async def unauthorized(method, path, token=None, **kwargs):
        return SimpleNamespace(status_code=401, json=lambda: {})

    response, session = request_claim(monkeypatch, github=unauthorized)
    assert response.status_code == 403
    assert session.executions == []


def test_claim_rejected_when_auth_disabled(monkeypatch):
    response, _ = request_claim(monkeypatch, claims={"auth_disabled": True})
    assert response.status_code == 400


def test_list_installations_scoped_to_user(monkeypatch):
    session = FakeSession(rows=[])

    async def override_db():
        yield session

    async def override_user():
        return USER_CLAIMS

    main.app.dependency_overrides[get_db] = override_db
    main.app.dependency_overrides[require_user] = override_user
    try:
        with TestClient(main.app) as client:
            response = client.get("/installations")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"data": []}
    query, params = session.executions[0]
    assert "im.supabase_user_id = :auth_user_id" in query
    assert "im.removed_at IS NULL" in query
    assert params["auth_user_id"] == USER_CLAIMS["sub"]


def test_installations_require_bearer_token():
    with TestClient(main.app) as client:
        response = client.get("/installations")
    assert response.status_code == 401


def test_claim_access_level_outside_collaborator_subset_is_member():
    assert installations_module._claim_access_level(
        "Organization",
        "acme",
        "octocat",
        [{"id": 1}, {"id": 2}],
        [{"id": 1, "permissions": {"admin": True}}],
    ) == "member"


def test_claim_access_level_full_coverage_non_admin_repo_is_member():
    assert installations_module._claim_access_level(
        "Organization",
        "acme",
        "octocat",
        [{"id": 1}, {"id": 2}],
        [
            {"id": 1, "permissions": {"admin": True}},
            {"id": 2, "permissions": {"push": True}},
        ],
    ) == "member"


def test_claim_access_level_full_coverage_all_admin_is_admin():
    assert installations_module._claim_access_level(
        "Organization",
        "acme",
        "octocat",
        [{"id": 1}, {"id": 2}],
        [
            {"id": 1, "permissions": {"admin": True}},
            {"id": 2, "permissions": {"admin": True}},
        ],
    ) == "admin"


def test_claim_access_level_empty_org_coverage_is_member():
    assert installations_module._claim_access_level(
        "Organization",
        "acme",
        "octocat",
        [],
        [],
    ) == "member"


def test_claim_access_level_matching_personal_account_is_admin():
    assert installations_module._claim_access_level(
        "User",
        "octocat",
        "octocat",
        [],
        [],
    ) == "admin"


def test_claim_access_level_non_matching_personal_account_is_member():
    assert installations_module._claim_access_level(
        "User",
        "other-user",
        "octocat",
        [{"id": 1}],
        [{"id": 1, "permissions": {"admin": True}}],
    ) == "member"
