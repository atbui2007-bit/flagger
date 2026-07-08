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


if __name__ == "__main__":
    asyncio.run(test_risk_recompute())
