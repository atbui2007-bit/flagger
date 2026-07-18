import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

from github_client import github_request


_token_cache: dict[int, tuple[str, datetime]] = {}
_installation_locks: dict[int, asyncio.Lock] = {}
_locks_guard = asyncio.Lock()


async def repo_token(repo) -> str:
    if not (repo.github_installation_id and os.getenv("GITHUB_APP_ID")):
        raise RuntimeError(
            f"no installation token for repo {repo.id}: GitHub App not configured or repo unlinked"
        )
    return await get_installation_token(repo.github_installation_id)


def _private_key() -> str:
    key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    if key_path:
        return Path(key_path).read_text(encoding="utf-8")
    key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    if not key:
        raise RuntimeError("GITHUB_APP_PRIVATE_KEY_PATH or GITHUB_APP_PRIVATE_KEY is required")
    return key.replace("\\n", "\n")


def _make_app_jwt() -> str:
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise RuntimeError("GITHUB_APP_ID is required")
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"iat": now - timedelta(seconds=60), "exp": now + timedelta(seconds=540), "iss": app_id},
        _private_key(),
        algorithm="RS256",
    )


async def _get_lock(installation_id: int) -> asyncio.Lock:
    async with _locks_guard:
        return _installation_locks.setdefault(installation_id, asyncio.Lock())


def _cached_token(installation_id: int) -> str | None:
    cached = _token_cache.get(installation_id)
    if cached and cached[1] - datetime.now(timezone.utc) > timedelta(minutes=5):
        return cached[0]
    return None


async def get_installation_token(github_installation_id: int) -> str:
    token = _cached_token(github_installation_id)
    if token:
        return token

    lock = await _get_lock(github_installation_id)
    async with lock:
        token = _cached_token(github_installation_id)
        if token:
            return token

        response = await github_request(
            "POST",
            f"/app/installations/{github_installation_id}/access_tokens",
            token=_make_app_jwt(),
        )
        if response.status_code != 201:
            raise RuntimeError(
                f"GitHub installation token request failed for installation "
                f"{github_installation_id}: HTTP {response.status_code} {response.text}"
            )
        body = response.json()
        expires_at = datetime.fromisoformat(body["expires_at"].replace("Z", "+00:00"))
        _token_cache[github_installation_id] = (body["token"], expires_at)
        return body["token"]
