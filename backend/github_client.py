import asyncio
import random

import httpx


_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url="https://api.github.com",
            timeout=15,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    return _client


async def github_request(method, path, token=None, **kwargs) -> httpx.Response:
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = None
    for attempt in range(3):
        try:
            response = await get_client().request(method, path, headers=headers, **kwargs)
            retryable = response.status_code >= 500 or response.status_code in (403, 429)
            if not retryable or attempt == 2:
                return response
            retry_after = response.headers.get("Retry-After")
        except httpx.TransportError:
            if attempt == 2:
                raise
            retry_after = None

        delay = float(retry_after) if retry_after else (2 ** attempt) + random.uniform(0, 0.25)
        await asyncio.sleep(delay)

    return response


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
