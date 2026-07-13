import base64
import json
import re

from github_client import github_request
from log_config import get_logger

logger = get_logger(__name__)

async def fetch_git_ai_note(sha, full_name, token=None):
    response = await github_request("GET", f"/repos/{full_name}/git/ref/notes/ai", token=token)
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        logger.warning("failed to fetch git-ai notes ref", extra={"repo": full_name, "status": response.status_code})
        return None
    notes_commit_sha = response.json().get("object", {}).get("sha")
    if not notes_commit_sha:
        logger.warning("git-ai notes ref missing commit sha", extra={"repo": full_name})
        return None

    response = await github_request("GET", f"/repos/{full_name}/git/commits/{notes_commit_sha}", token=token)
    tree_sha = response.json().get("tree", {}).get("sha") if response.status_code == 200 else None
    if not tree_sha:
        logger.warning("git-ai notes commit missing tree sha", extra={"repo": full_name})
        return None

    response = await github_request("GET", f"/repos/{full_name}/git/trees/{tree_sha}?recursive=1", token=token)
    entries = response.json().get("tree", []) if response.status_code == 200 else []
    entry = next((item for item in entries if item.get("path", "").replace("/", "") == sha), None)
    if not entry or not entry.get("sha"):
        return None

    response = await github_request("GET", f"/repos/{full_name}/git/blobs/{entry['sha']}", token=token)
    try:
        if response.status_code != 200:
            raise ValueError("blob request failed")
        note = json.loads(base64.b64decode(response.json()["content"]).decode("utf-8"))
        if not isinstance(note, dict) or not note:
            raise ValueError("invalid note")
        return note
    except (KeyError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("invalid git-ai note blob", extra={"repo": full_name, "sha": sha})
        return None

def heuristic_resolver(commit_payload):
    known_bots = {"claude-ai[bot]": "Claude Code",
                   "devin-ai-integration[bot]": "devin"}
    
    known_authors = {"OpenAI Codex": "Codex",
                     "Aider": "Aider",
                     "Claude": "Claude Code"}
    
    if commit_payload["author"].get("login") in known_bots:
        return {"agent_type": known_bots[commit_payload["author"]["login"]],
                "attribution_source": "heuristic",
                "attribution_confidence": "certain",
                "attribution_signal": "bot account login",
                "git_ai_model": None}
    
    for match in re.finditer(r"co-authored-by:\s*(.+)", commit_payload["message"], re.IGNORECASE):
        author = match.group(1).strip()
        for name, agent in known_authors.items():
            if author.startswith(name):
                return {"agent_type": agent,
                        "attribution_source": "heuristic",
                        "attribution_confidence": "likely",
                        "attribution_signal": "bot message",
                        "git_ai_model": None}
                
    return {"agent_type": "unknown",
            "attribution_source": "heuristic",
            "attribution_confidence": "suspected",
            "attribution_signal": "no match found",
            "git_ai_model": None}

async def attribution_resolver(sha, full_name, commit_payload, token=None):
    note = await fetch_git_ai_note(sha, full_name, token)
    if note:
        return {"agent_type": note.get("agent") or "unknown",
                "attribution_source": "git_ai_notes",
                "attribution_confidence": "certain",
                "attribution_signal": "git_ai_notes",
                "git_ai_model": note.get("model")}
    else:
        return heuristic_resolver(commit_payload)
