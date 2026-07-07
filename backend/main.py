from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from database import get_db
from handlers.PullRequests import handle_pull_request
from handlers.WorkflowRun import handle_workflow_run
from handlers.PullRequestReview import handle_pull_request_review
from handlers.push import handle_push
from routers.activity import router as activity_router
from routers.timeline import router as timeline_router
from routers.prs import router as prs_router
import json, hmac, hashlib, os

load_dotenv()
secret = os.getenv("WEBHOOK_SECRET")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activity_router, prefix = "/activity")
app.include_router(timeline_router, prefix = "/repos")
app.include_router(prs_router, prefix = "/repos")

@app.get("/health")

async def root():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    header = request.headers.get("X-Hub-Signature-256")
    if not header:
        raise HTTPException(status_code = 401, detail = "missing signature")

    rawBody = await request.body()
    mySignature = hmac.new(key = secret.encode("utf-8"), msg = rawBody, digestmod = hashlib.sha256).hexdigest()
    githubSignature = header.replace("sha256=", "")
    if not hmac.compare_digest(mySignature, githubSignature):
        raise HTTPException(status_code = 403, detail = "forbidden")

    try:
        payload = json.loads(rawBody)
    except json.JSONDecodeError:
        raise HTTPException(status_code = 400, detail = "invalid JSON")

    githubEventHeader = request.headers.get("X-GitHub-Event")
    try:
        if githubEventHeader == "push":
            await handle_push(payload, session)
        elif githubEventHeader == "pull_request":
            await handle_pull_request(payload, session)
        elif githubEventHeader == "workflow_run":
            await handle_workflow_run(payload, session)
        elif githubEventHeader == "pull_request_review":
            await handle_pull_request_review(payload, session)
        else:
            print("unhandled event: " + str(githubEventHeader))
    except Exception as exc:
        print("handler failed for event " + str(githubEventHeader) + ": " + str(exc))
        raise HTTPException(status_code = 500, detail = "webhook handler failed")

    print(payload)
    return{"status": "received"}
