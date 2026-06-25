from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from database import get_db
from handlers.PullRequests import handle_pull_request
import json, hmac, hashlib, os

load_dotenv()
secret = os.getenv("WEBHOOK_SECRET")

app = FastAPI()

@app.get("/health")

async def root():
    return {"status": "ok"}

def handlePush(payload):
    body = payload["repository"]["full_name"], payload["head_commit"]["id"]
    print(body)

def handlePullRequest(payload):
    body = payload["number"], payload["action"], payload["pull_request"]["user"]["login"]
    print(body)

def handleWorkflowRun(payload):
    body = payload["workflow_run"]["name"], payload["workflow_run"]["status"], payload["workflow_run"]["conclusion"], payload["repository"]["full_name"]
    print(body)

def handlePullRequestReview(payload):
    body = payload["review"]["state"], payload["review"]["user"]["login"], payload["pull_request"]["number"], payload["repository"]["full_name"]
    print(body)

@app.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    header = request.headers.get("X-Hub-Signature-256")
    rawBody = await request.body()
    mySignature = hmac.new(key = secret.encode("utf-8"), msg = rawBody, digestmod = hashlib.sha256).hexdigest()
    githubSignature = header.replace("sha256=", "")
    if not hmac.compare_digest(mySignature, githubSignature):
        raise HTTPException(status_code = 403, detail = "forbidden")
    
    payload = json.loads(rawBody)

    githubEventHeader = request.headers.get("X-GitHub-Event")
    if githubEventHeader == "push":
        handlePush(payload)
    elif githubEventHeader == "pull_request":
        await handle_pull_request(payload, session)
    elif githubEventHeader == "workflow_run":
        handleWorkflowRun(payload)
    elif githubEventHeader == "pull_request_review":
        handlePullRequestReview(payload)
    else:
        print("unhandled event: " + githubEventHeader)

    print(payload)
    return{"status": "received"}