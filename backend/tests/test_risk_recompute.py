import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from risk_recompute import recompute_for_pull_request


class Row:
    def __init__(self, values):
        self._mapping = values


class Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self):
        self.updates = []

    async def execute(self, query, params):
        if str(query).lstrip().startswith("SELECT"):
            return Result([Row({
                "id": "commit-1", "additions": 10,
                "risk_sensitive_path": False, "risk_direct_to_main": False,
                "has_review": True, "ci_unclean": False,
            })])
        self.updates.append(params)
        return Result([])


async def test_risk_recompute():
    session = FakeSession()
    await recompute_for_pull_request("pr-1", session)
    update = session.updates[0]
    assert update["risk_no_review"] is False
    assert update["risk_level"] == "low"
    print(f"risk_no_review={update['risk_no_review']} risk_level={update['risk_level']} (was medium)")


from handlers.PullRequests import handle_pull_request


class PullRequestSession:
    """Routes handle_pull_request's queries: repo lookup, PR upsert,
    backfill, and the recompute SELECT/UPDATE cycle."""

    def __init__(self):
        self.executions = []
        self.commits = 0

    async def execute(self, query, params=None):
        sql = str(query)
        self.executions.append((sql, params))
        if "FROM repos" in sql:
            return _FetchoneResult((
                "repo-id", "installation-id", "main", "heuristic",
                "owner/repo", 777, None, None,
            ))
        if "INSERT INTO pull_requests" in sql:
            return _ScalarResult("pr-1")
        if sql.lstrip().startswith("SELECT") and "FROM commits c" in sql:
            return Result([Row({
                "id": "commit-1", "additions": 10,
                "risk_sensitive_path": False, "risk_direct_to_main": False,
                "has_review": False, "ci_unclean": False,
            })])
        return Result([])

    async def commit(self):
        self.commits += 1


class _FetchoneResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


def pr_payload(action):
    return {
        "action": action,
        "repository": {"full_name": "owner/repo"},
        "pull_request": {
            "number": 7,
            "title": "add feature",
            "html_url": "https://github.com/owner/repo/pull/7",
            "user": {"login": "octocat"},
            "state": "open",
            "head": {"ref": "feature-branch"},
            "merged_at": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "closed_at": None,
        },
    }


async def test_pr_opened_backfills_and_recomputes():
    session = PullRequestSession()
    await handle_pull_request(pr_payload("opened"), session)
    queries = [sql for sql, _ in session.executions]
    assert any("UPDATE commits SET pull_request_id" in q for q in queries)
    assert any("FROM commits c" in q for q in queries), "recompute did not run"
    recompute_updates = [p for q, p in session.executions if "risk_level" in q]
    assert recompute_updates and recompute_updates[0]["risk_no_review"] is True
    assert session.commits == 1


async def test_pr_synchronize_does_not_recompute():
    session = PullRequestSession()
    await handle_pull_request(pr_payload("synchronize"), session)
    queries = [sql for sql, _ in session.executions]
    assert not any("UPDATE commits SET pull_request_id" in q for q in queries)
    assert not any("FROM commits c" in q for q in queries)
    assert session.commits == 1


if __name__ == "__main__":
    asyncio.run(test_risk_recompute())
    asyncio.run(test_pr_opened_backfills_and_recomputes())
    asyncio.run(test_pr_synchronize_does_not_recompute())
