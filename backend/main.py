from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from database import get_db
from handlers.PullRequests import handle_pull_request
from handlers.WorkflowRun import handle_workflow_run
from handlers.PullRequestReview import handle_pull_request_review
from handlers.push import handle_push
from handlers.Installation import handle_installation, handle_installation_repositories
from routers.activity import router as activity_router
from routers.timeline import router as timeline_router
from routers.prs import router as prs_router
from github_client import close_client
from log_config import configure_logging, get_logger
from auth import require_user
from sqlalchemy import text
from contextlib import asynccontextmanager
import json, hmac, hashlib, os

load_dotenv()
secret = os.getenv("WEBHOOK_SECRET")
if not secret:
    raise RuntimeError("WEBHOOK_SECRET is required")
configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_client()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activity_router, prefix = "/activity", dependencies=[Depends(require_user)])
app.include_router(timeline_router, prefix = "/repos", dependencies=[Depends(require_user)])
app.include_router(prs_router, prefix = "/repos", dependencies=[Depends(require_user)])

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
    repo_full_name = payload.get("repository", {}).get("full_name")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    logger.info("webhook received", extra={"event": githubEventHeader, "repo": repo_full_name, "delivery_id": delivery_id})
    logger.debug("webhook payload", extra={"payload": payload})
    try:
        if githubEventHeader == "installation":
            await handle_installation(payload, session)
        elif githubEventHeader == "installation_repositories":
            await handle_installation_repositories(payload, session)
        elif githubEventHeader in {"push", "pull_request", "workflow_run", "pull_request_review"}:
            guard_result = await session.execute(text("""
                SELECT r.id, r.installation_id, r.removed_at,
                       i.suspended_at, i.deleted_at
                FROM repos r
                LEFT JOIN installations i ON r.installation_id = i.id
                WHERE r.full_name = :full_name
            """), {"full_name": repo_full_name})
            guarded_repo = guard_result.fetchone()
            if not guarded_repo or guarded_repo.removed_at is not None:
                logger.info("webhook ignored for untracked repo", extra={"repo": repo_full_name, "event": githubEventHeader})
                return {"status": "ignored", "reason": "repo not tracked"}
            if guarded_repo.installation_id is None:
                raise HTTPException(status_code=409, detail="repository has no GitHub App installation")
            if guarded_repo.suspended_at is not None:
                raise HTTPException(status_code=409, detail="GitHub App installation is suspended")
            if guarded_repo.deleted_at is not None:
                raise HTTPException(status_code=409, detail="GitHub App installation is deleted")

            if githubEventHeader == "push":
                await handle_push(payload, session)
            elif githubEventHeader == "pull_request":
                await handle_pull_request(payload, session)
            elif githubEventHeader == "workflow_run":
                await handle_workflow_run(payload, session)
            else:
                await handle_pull_request_review(payload, session)
        else:
            logger.warning("unhandled webhook event", extra={"event": githubEventHeader})
    except HTTPException:
        raise
    except Exception:
        logger.exception("webhook handler failed", extra={"event": githubEventHeader, "repo": repo_full_name, "delivery_id": delivery_id})
        raise HTTPException(status_code = 500, detail = "webhook handler failed")

    return{"status": "received"}
