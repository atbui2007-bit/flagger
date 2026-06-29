from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv
from db.repos import get_repo
from AttributionResolver import attribution_resolver
from scoring import compute_risk
from datetime import datetime, timezone
import httpx, os

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

SENSITIVE_PATH_TOKENS = ["env", ".secret", "config", "credentials", "key", "token", "password"]


def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def fetch_commit_diff(sha, full_name):
    url = f"https://api.github.com/repos/{full_name}/commits/{sha}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()
    return None


async def handle_push(payload, session: AsyncSession):
    full_name = payload["repository"]["full_name"]
    default_branch = payload["repository"]["default_branch"]
    repo_id = await get_repo(full_name, session)

    branch = payload["ref"].replace("refs/heads/", "")
    merged_to_default = branch == default_branch
    risk_direct_to_main = branch == default_branch

    commit_insert = text("""
        INSERT INTO commits (
            id, repo_id, pull_request_id, sha, short_sha, message, url, branch,
            merged_to_default, agent_type, attribution_source, attribution_confidence,
            attribution_signal, author_login, author_avatar_url, git_ai_model,
            github_ai_summary_prompt, github_ai_approved_lines, github_ai_overridden_lines,
            additions, deletions, risk_level, risk_no_review, risk_ci_unclean,
            risk_sensitive_path, risk_large_unreviewed, risk_direct_to_main,
            pushed_at, arrived_at, altered_at
        )
        VALUES (
            gen_random_uuid(), :repo_id, :pull_request_id, :sha, :short_sha, :message, :url, :branch,
            :merged_to_default, :agent_type, :attribution_source, :attribution_confidence,
            :attribution_signal, :author_login, :author_avatar_url, :git_ai_model,
            :github_ai_summary_prompt, :github_ai_approved_lines, :github_ai_overridden_lines,
            :additions, :deletions, :risk_level, :risk_no_review, :risk_ci_unclean,
            :risk_sensitive_path, :risk_large_unreviewed, :risk_direct_to_main,
            :pushed_at, :arrived_at, :altered_at
        )
        RETURNING id
    """)

    file_change_insert = text("""
        INSERT INTO file_changes (
            id, commit_id, file_path, change_type, additions, deletions, ai_lines_ranges
        )
        VALUES (
            gen_random_uuid(), :commit_id, :file_path, :change_type, :additions, :deletions, :ai_lines_ranges
        )
    """)

    for commit in payload["commits"]:
        sha = commit["id"]

        attribution = await attribution_resolver(sha, full_name, commit)

        diff = await fetch_commit_diff(sha, full_name)
        files = diff["files"] if diff and diff.get("files") else []

        total_additions = sum(f["additions"] for f in files)
        total_deletions = sum(f["deletions"] for f in files)

        risk_no_review = True
        risk_ci_unclean = False
        risk_sensitive_path = any(
            token_str in f["filename"].lower()
            for f in files
            for token_str in SENSITIVE_PATH_TOKENS
        )
        risk_large_unreviewed = total_additions > 500

        risk_level = compute_risk(
            risk_no_review,
            risk_ci_unclean,
            risk_sensitive_path,
            risk_large_unreviewed,
            risk_direct_to_main,
        )

        author_login = commit["author"].get("login") or commit["author"]["name"]

        result = await session.execute(commit_insert, {
            "repo_id": repo_id,
            "pull_request_id": None,
            "sha": sha,
            "short_sha": sha[:7],
            "message": commit["message"],
            "url": commit["url"],
            "branch": branch,
            "merged_to_default": merged_to_default,
            "agent_type": attribution["agent_type"],
            "attribution_source": attribution["attribution_source"],
            "attribution_confidence": attribution["attribution_confidence"],
            "attribution_signal": attribution["attribution_signal"],
            "author_login": author_login,
            "author_avatar_url": None,
            "git_ai_model": None,
            "github_ai_summary_prompt": None,
            "github_ai_approved_lines": None,
            "github_ai_overridden_lines": None,
            "additions": total_additions,
            "deletions": total_deletions,
            "risk_level": risk_level,
            "risk_no_review": risk_no_review,
            "risk_ci_unclean": risk_ci_unclean,
            "risk_sensitive_path": risk_sensitive_path,
            "risk_large_unreviewed": risk_large_unreviewed,
            "risk_direct_to_main": risk_direct_to_main,
            "pushed_at": parse_dt(commit["timestamp"]),
            "arrived_at": datetime.now(timezone.utc),
            "altered_at": None,
        })
        commit_id = result.scalar()

        for f in files:
            await session.execute(file_change_insert, {
                "commit_id": commit_id,
                "file_path": f["filename"],
                "change_type": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "ai_lines_ranges": None,
            })

    await session.commit()
