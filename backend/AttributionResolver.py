from dotenv import load_dotenv
import httpx, os, re

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

async def fetch_git_ai_note(sha, full_name):
    url = f"https://api.github.com/repos/{full_name}/git/notes/{sha}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()
    return None

def heuristic_resolver(commit_payload):
    known_bots = {"claude-ai[bot]": "Claude Code",
                   "devin-ai-integration[bot]": "devin"}
    
    known_authors = {"OpenAI Codex": "Codex",
                     "Aider": "Aider"}
    
    if commit_payload["author"]["login"] in known_bots:
        return {"agent_type": known_bots[commit_payload["author"]["login"]],
                "attribution_source": "heuristic",
                "attribution_confidence": "certain",
                "attribution_signal": "bot account login"}
    
    if "co-authored-by: " in commit_payload["message"].lower():
            match = re.search(r"Co-authored-by: (.+)", commit_payload["message"])
            if match:
                author = match.group(1)
                if author in known_authors:
                    return {"agent_type": known_authors[author],
                            "attribution_source": "heuristic",
                            "attribution_confidence": "likely",
                            "attribution_signal": "bot message"}
                
    return {"agent_type": "unknown",
            "attribution_source": "heuristic",
            "attribution_confidence": "suspected",
            "attribution_signal": "no match found"}

async def attribution_resolver(sha, full_name, commit_payload):
    note = await fetch_git_ai_note(sha, full_name)
    if note:
        return {"agent_type": note["agent"],
                "attribution_source": "git_ai_notes",
                "attribution_confidence": "certain",
                "attribution_signal": "git_ai_notes"}
    else:
        return heuristic_resolver(commit_payload)