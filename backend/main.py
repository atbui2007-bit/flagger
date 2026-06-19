from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.get("/health")

async def root():
    return {"status": "ok"}

@app.post("/webhook")

async def webhook(request: Request):
    payload = json.loads(await request.body())
    print(payload)
    return{"status": "received"}