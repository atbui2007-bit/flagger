import pytest

from AttributionResolver import heuristic_resolver
from scoring import compute_risk


def test_bot_login_match_is_certain():
    result = heuristic_resolver(
        {"author": {"login": "claude-ai[bot]"}, "message": "generated change"}
    )
    assert result["agent_type"] == "Claude Code"
    assert result["attribution_confidence"] == "certain"


def test_coauthored_by_match_is_likely():
    result = heuristic_resolver(
        {"author": {"login": "developer"}, "message": "change\n\nCo-authored-by: OpenAI Codex"}
    )
    assert result["agent_type"] == "Codex"
    assert result["attribution_confidence"] == "likely"


def test_no_match_is_unknown_and_suspected():
    result = heuristic_resolver(
        {"author": {"name": "Developer"}, "message": "manual change"}
    )
    assert result["agent_type"] == "unknown"
    assert result["attribution_confidence"] == "suspected"


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ((False, False, False, False, False), "low"),
        ((True, False, False, False, False), "medium"),
        ((True, True, False, False, False), "high"),
        ((True, True, True, False, False), "critical"),
        ((True, True, True, True, True), "critical"),
    ],
)
def test_compute_risk_boundaries(flags, expected):
    assert compute_risk(*flags) == expected
