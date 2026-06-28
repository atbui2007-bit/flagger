import hmac, hashlib, json, requests

SECRET = "AustinBuiLikesBigBlackMen"
URL = "http://localhost:8000/webhook"

payload = {
    "action": "opened",
    "repository": {
        "full_name": "youruser/yourrepo"
    },
    "pull_request": {
        "number": 1,
        "title": "test pr",
        "html_url": "https://github.com/youruser/yourrepo/pull/1",
        "user": { "login": "youruser" },
        "state": "open",
        "merged_at": None,
        "closed_at": None,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
}

body = json.dumps(payload).encode("utf-8")

signature = "sha256=" + hmac.new(
    key=SECRET.encode("utf-8"),
    msg=body,
    digestmod=hashlib.sha256
).hexdigest()

headers = {
    "X-Hub-Signature-256": signature,
    "X-GitHub-Event": "pull_request",
    "Content-Type": "application/json"
}

response = requests.post(URL, data=body, headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())