from handlers.push import _compare_commit_to_push_commit


def test_compare_commit_to_push_commit_maps_rest_shape():
    result = _compare_commit_to_push_commit({
        "sha": "abc123",
        "html_url": "https://github.com/owner/repo/commit/abc123",
        "author": {"login": "octocat"},
        "commit": {
            "message": "change",
            "author": {
                "name": "Mona Lisa",
                "email": "mona@example.com",
                "date": "2026-01-01T00:00:00Z",
            },
        },
    })

    assert result == {
        "id": "abc123",
        "message": "change",
        "timestamp": "2026-01-01T00:00:00Z",
        "url": "https://github.com/owner/repo/commit/abc123",
        "author": {
            "name": "Mona Lisa",
            "email": "mona@example.com",
            "login": "octocat",
        },
    }


def test_compare_commit_to_push_commit_handles_ghost_author():
    result = _compare_commit_to_push_commit({
        "sha": "def456",
        "html_url": "https://github.com/owner/repo/commit/def456",
        "author": None,
        "commit": {
            "message": "ghost change",
            "author": {
                "name": "Ghost",
                "email": "ghost@example.com",
                "date": "2026-01-02T00:00:00Z",
            },
        },
    })

    assert result["author"] == {
        "name": "Ghost",
        "email": "ghost@example.com",
        "login": None,
    }
