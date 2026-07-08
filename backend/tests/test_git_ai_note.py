import asyncio
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import AttributionResolver


class Response:
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body


async def test_git_ai_note():
    sha = "abcdef1234"
    note = {"agent": "Codex", "model": "gpt-5"}
    responses = [
        Response(200, {"object": {"sha": "notes-commit"}}),
        Response(200, {"tree": {"sha": "notes-tree"}}),
        Response(200, {"tree": [{"path": "ab/cdef1234", "sha": "blob-sha"}]}),
        Response(200, {"content": base64.b64encode(json.dumps(note).encode()).decode()}),
    ]

    async def fake_request(*args, **kwargs):
        return responses.pop(0)

    AttributionResolver.github_request = fake_request
    assert await AttributionResolver.fetch_git_ai_note(sha, "owner/repo", "token") == note
    assert not responses

    async def fake_404(*args, **kwargs):
        return Response(404)

    AttributionResolver.github_request = fake_404
    assert await AttributionResolver.fetch_git_ai_note(sha, "owner/repo", "token") is None
    print("parsed_note=", note, "ref_404=None", sep="")


if __name__ == "__main__":
    asyncio.run(test_git_ai_note())
