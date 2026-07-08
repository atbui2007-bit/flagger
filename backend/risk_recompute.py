from sqlalchemy import text

from scoring import compute_risk


async def recompute_for_pull_request(pull_request_id, session):
    result = await session.execute(text("""
        SELECT c.id, c.additions, c.risk_sensitive_path, c.risk_direct_to_main,
               EXISTS (SELECT 1 FROM reviews r WHERE r.pull_request_id = :pull_request_id) AS has_review,
               EXISTS (
                   SELECT 1 FROM ci_runs ci
                   WHERE ci.pull_request_id = :pull_request_id
                     AND ci.conclusion IN ('failure', 'cancelled', 'timed_out', 'action_required')
               ) AS ci_unclean
        FROM commits c
        WHERE c.pull_request_id = :pull_request_id
    """), {"pull_request_id": pull_request_id})
    for row in result.fetchall():
        values = row._mapping
        no_review = not values["has_review"]
        ci_unclean = bool(values["ci_unclean"])
        large_unreviewed = (values["additions"] or 0) > 500 and no_review
        risk_level = compute_risk(
            no_review,
            ci_unclean,
            bool(values["risk_sensitive_path"]),
            large_unreviewed,
            bool(values["risk_direct_to_main"]),
        )
        await session.execute(text("""
            UPDATE commits SET
                risk_no_review = :risk_no_review,
                risk_ci_unclean = :risk_ci_unclean,
                risk_large_unreviewed = :risk_large_unreviewed,
                risk_level = :risk_level,
                altered_at = NOW()
            WHERE id = :id
        """), {
            "id": values["id"],
            "risk_no_review": no_review,
            "risk_ci_unclean": ci_unclean,
            "risk_large_unreviewed": large_unreviewed,
            "risk_level": risk_level,
        })
