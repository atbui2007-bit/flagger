import asyncio
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import jwt  # noqa: F401
except ModuleNotFoundError:
    sys.modules["jwt"] = types.SimpleNamespace(encode=lambda *args, **kwargs: "unused-in-test")

import github_app


class FakeResponse:
    status_code = 201
    text = ""

    def json(self):
        return {
            "token": "installation-token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }


async def test_installation_token_cache():
    calls = 0

    async def fake_github_request(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse()

    github_app._token_cache.clear()
    github_app._installation_locks.clear()
    github_app.github_request = fake_github_request
    github_app._make_app_jwt = lambda: "app-jwt"

    first = await github_app.get_installation_token(123)
    second = await github_app.get_installation_token(123)

    assert first == second == "installation-token"
    assert calls == 1
    print(f"first={first} second={second} mint_calls={calls}")


if __name__ == "__main__":
    asyncio.run(test_installation_token_cache())
