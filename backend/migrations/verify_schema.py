"""Verify that the expected migrated schema is present in the target database."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import engine


EXPECTED_COLUMNS = {
    "installations": {
        "id": "uuid",
        "github_installation_id": "bigint",
        "account_login": "text",
        "account_type": "text",
        "installed_at": "timestamp with time zone",
        "suspended_at": "timestamp with time zone",
        "deleted_at": "timestamp with time zone",
    },
    "repos": {
        "removed_at": "timestamp with time zone",
        "installation_id": "uuid",
        "github_repo_id": "bigint",
        "created_at": "timestamp with time zone",
        "updated_at": "timestamp with time zone",
    },
    "file_changes": {
        "created_at": "timestamp with time zone",
        "updated_at": "timestamp with time zone",
    },
    "repo_members": {
        "id": "uuid",
        "repo_id": "uuid",
        "supabase_user_id": "uuid",
        "github_login": "text",
        "role": "text",
        "github_permission": "text",
        "access_checked_at": "timestamp with time zone",
        "access_expires_at": "timestamp with time zone",
        "created_at": "timestamp with time zone",
        "removed_at": "timestamp with time zone",
    },
}

INDEX_CHECKS = {
    "commits (pushed_at DESC, id DESC) index": (
        "commits",
        ('using btree', 'pushed_at desc', 'id desc'),
    ),
    "commits (author_login) btree index": (
        "commits",
        ('using btree', '(author_login)'),
    ),
    "commits LOWER(attribution_confidence) index": (
        "commits",
        ('using btree', 'lower(attribution_confidence)'),
    ),
    "commits (repo_id, branch) index": (
        "commits",
        ('using btree', '(repo_id, branch)'),
    ),
    "commits.message GIN trgm index": (
        "commits",
        ('using gin', 'message gin_trgm_ops'),
    ),
    "commits.sha GIN trgm index": (
        "commits",
        ('using gin', 'sha gin_trgm_ops'),
    ),
    "commits.author_login GIN trgm index": (
        "commits",
        ('using gin', 'author_login gin_trgm_ops'),
    ),
    "commits.agent_type GIN trgm index": (
        "commits",
        ('using gin', 'agent_type gin_trgm_ops'),
    ),
    "repos.full_name GIN trgm index": (
        "repos",
        ('using gin', 'full_name gin_trgm_ops'),
    ),
    "repo_members (supabase_user_id) index": (
        "repo_members",
        ('using btree', '(supabase_user_id)'),
    ),
}


def report(label, passed):
    print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return passed


async def main():
    results = []
    async with engine.connect() as connection:
        column_rows = (await connection.execute(text("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('installations', 'repos', 'file_changes', 'repo_members')
        """))).mappings().all()
        columns = {
            (row["table_name"], row["column_name"]): row
            for row in column_rows
        }

        for table, expected in EXPECTED_COLUMNS.items():
            for column, data_type in expected.items():
                row = columns.get((table, column))
                results.append(report(
                    f"{table}.{column} is {data_type}",
                    row is not None and row["data_type"] == data_type,
                ))

        webhook = columns.get(("repos", "webhook_secret"))
        results.append(report(
            "repos.webhook_secret default is empty string",
            webhook is not None
            and webhook["column_default"] is not None
            and webhook["column_default"].startswith("''"),
        ))

        index_rows = (await connection.execute(text("""
            SELECT tablename, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename IN ('commits', 'repos', 'repo_members')
        """))).mappings().all()
        indexes = [
            (row["tablename"], row["indexdef"].lower())
            for row in index_rows
        ]
        for label, (table, patterns) in INDEX_CHECKS.items():
            found = any(
                indexed_table == table
                and all(pattern in definition for pattern in patterns)
                for indexed_table, definition in indexes
            )
            results.append(report(label, found))

        extension = await connection.scalar(text("""
            SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
        """))
        results.append(report("pg_trgm extension installed", bool(extension)))

    await engine.dispose()
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
