from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
from auth import require_user
from database import get_db


USER_CLAIMS = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "user_metadata": {"user_name": "octocat", "provider_id": "12345"},
}
FACETS_ROW = SimpleNamespace(_mapping={"repositories": None, "contributors": None, "agents": None})


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def one(self):
        return self.rows[0]

    def scalar(self):
        return self.rows[0] if self.rows else None


class FakeSession:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executions = []

    async def execute(self, query, params=None):
        self.executions.append((str(query), params))
        return FakeResult(self.rows)

    async def commit(self):
        pass


def request(path, session, claims=USER_CLAIMS):
    async def override_db():
        yield session

    async def override_user():
        return claims

    main.app.dependency_overrides[get_db] = override_db
    main.app.dependency_overrides[require_user] = override_user
    try:
        with TestClient(main.app) as client:
            return client.get(path)
    finally:
        main.app.dependency_overrides.clear()


def assert_scoped(session):
    query, params = session.executions[-1]
    assert "installation_members" in query
    assert "im.supabase_user_id = :auth_user_id" in query
    assert params["auth_user_id"] == USER_CLAIMS["sub"]


def test_recent_is_scoped_to_user():
    session = FakeSession()
    response = request("/activity/recent", session)
    assert response.status_code == 200
    assert_scoped(session)


def test_facets_is_scoped_to_user():
    session = FakeSession(rows=[FACETS_ROW])
    response = request("/activity/facets", session)
    assert response.status_code == 200
    assert_scoped(session)


def test_agents_is_scoped_to_user():
    session = FakeSession()
    response = request("/activity/agents", session)
    assert response.status_code == 200
    assert_scoped(session)


def test_recent_unscoped_when_auth_disabled():
    session = FakeSession()
    response = request("/activity/recent", session, claims={"auth_disabled": True})
    assert response.status_code == 200
    query, params = session.executions[-1]
    assert "installation_members" not in query
    assert "auth_user_id" not in (params or {})


def test_timeline_unentitled_repo_is_404():
    session = FakeSession(rows=[])
    response = request("/repos/acme/widgets/timeline", session)
    assert response.status_code == 404
    query, params = session.executions[0]
    assert "installation_members" in query
    assert params["auth_user_id"] == USER_CLAIMS["sub"]


def test_activity_requires_bearer_token():
    with TestClient(main.app) as client:
        response = client.get("/activity/recent")
    assert response.status_code == 401
