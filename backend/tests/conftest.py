import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# main.py and database.py read these values during test collection.
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/flagger_test",
)
