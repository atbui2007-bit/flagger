import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from handlers.Installation import handle_installation, handle_installation_repositories


class FakeSession:
    def __init__(self):
        self.executions = []
        self.commits = 0

    async def execute(self, query, params=None):
        self.executions.append((str(query), params))

    async def commit(self):
        self.commits += 1


def test_installation_created_upserts_installation_and_repos():
    session = FakeSession()
    payload = {
        "action": "created",
        "installation": {"id": 42, "account": {"login": "acme", "type": "Organization"}},
        "repositories": [{"id": 7, "name": "widgets", "full_name": "acme/widgets"}],
    }
    asyncio.run(handle_installation(payload, session))

    queries = [query for query, _ in session.executions]
    assert any("INSERT INTO installations" in query for query in queries)

    repo_query, repo_params = next(
        (query, params) for query, params in session.executions if "INSERT INTO repos" in query
    )
    assert "ON CONFLICT (github_repo_id)" in repo_query
    assert repo_params == {
        "github_repo_id": 7,
        "owner": "acme",
        "name": "widgets",
        "full_name": "acme/widgets",
        "gid": 42,
    }
    assert session.commits == 1


def test_repositories_removed_soft_deletes():
    session = FakeSession()
    payload = {
        "installation": {"id": 42},
        "repositories_added": [],
        "repositories_removed": [{"id": 7, "name": "widgets", "full_name": "acme/widgets"}],
    }
    asyncio.run(handle_installation_repositories(payload, session))

    query, params = session.executions[0]
    assert "SET removed_at = NOW()" in query
    assert params == {"github_repo_id": 7}
    assert session.commits == 1
