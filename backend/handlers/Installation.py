from sqlalchemy import text


async def _update_repositories(repositories, github_installation_id, session, added):
    # ponytail: default_branch starts as 'main' (installation payloads don't carry it);
    # handle_push self-heals it from the first push payload. webhook_secret is the
    # deprecated per-repo column (see 003) -- the App uses a single app-level secret.
    add_query = text("""
        INSERT INTO repos (github_repo_id, owner, name, full_name, default_branch, webhook_secret, installation_id)
        VALUES (:github_repo_id, :owner, :name, :full_name, 'main', '',
                (SELECT id FROM installations WHERE github_installation_id = :gid))
        ON CONFLICT (github_repo_id) DO UPDATE SET
            owner = EXCLUDED.owner,
            name = EXCLUDED.name,
            full_name = EXCLUDED.full_name,
            installation_id = EXCLUDED.installation_id,
            removed_at = NULL,
            updated_at = NOW()
    """)
    remove_query = text("""
        UPDATE repos SET removed_at = NOW(), updated_at = NOW()
        WHERE github_repo_id = :github_repo_id AND removed_at IS NULL
    """)
    for repo in repositories:
        if added:
            owner, _, name = repo["full_name"].partition("/")
            await session.execute(add_query, {
                "github_repo_id": repo["id"],
                "owner": owner,
                "name": repo.get("name") or name,
                "full_name": repo["full_name"],
                "gid": github_installation_id,
            })
        else:
            await session.execute(remove_query, {"github_repo_id": repo["id"]})


async def handle_installation(payload, session):
    installation = payload["installation"]
    gid = installation["id"]
    action = payload["action"]
    if action == "created":
        await session.execute(text("""
            INSERT INTO installations (github_installation_id, account_login, account_type)
            VALUES (:gid, :login, :account_type)
            ON CONFLICT (github_installation_id) DO UPDATE SET
                account_login = EXCLUDED.account_login,
                account_type = EXCLUDED.account_type,
                suspended_at = NULL,
                deleted_at = NULL
        """), {"gid": gid, "login": installation["account"]["login"], "account_type": installation["account"]["type"]})
        await _update_repositories(payload.get("repositories", []), gid, session, True)
    elif action == "deleted":
        await session.execute(text("UPDATE installations SET deleted_at=NOW() WHERE github_installation_id=:gid"), {"gid": gid})
        await _update_repositories(payload.get("repositories", []), gid, session, False)
    elif action == "suspend":
        await session.execute(text("UPDATE installations SET suspended_at=NOW() WHERE github_installation_id=:gid"), {"gid": gid})
    elif action == "unsuspend":
        await session.execute(text("UPDATE installations SET suspended_at=NULL WHERE github_installation_id=:gid"), {"gid": gid})
    await session.commit()


async def handle_installation_repositories(payload, session):
    gid = payload["installation"]["id"]
    await _update_repositories(payload.get("repositories_added", []), gid, session, True)
    await _update_repositories(payload.get("repositories_removed", []), gid, session, False)
    await session.commit()
