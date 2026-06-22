from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import json, hmac, hashlib, os

load_dotenv()
secret = os.getenv("WEBHOOK_SECRET")

app = FastAPI()

@app.get("/health")

async def root():
    return {"status": "ok"}

@app.post("/webhook")

async def webhook(request: Request):
    header = request.headers.get("X-Hub-Signature-256")
    rawBody = await request.body()
    mySignature = hmac.new(key = secret.encode("utf-8"), msg = rawBody, digestmod = hashlib.sha256).hexdigest()
    githubSignature = header.replace("sha256=", "")
    if not hmac.compare_digest(mySignature, githubSignature):
        raise HTTPException(status_code = 403, detail = "forbidden")
    
    payload = json.loads(rawBody)
    print(payload)
    return{"status": "received"}