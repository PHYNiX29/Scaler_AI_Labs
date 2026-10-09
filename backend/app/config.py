import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Everything that must survive a restart (SQLite file + uploaded media) lives in DATA_DIR.
# In production this points at a mounted persistent volume (e.g. /data on Railway).
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'typeform.db'}"

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")]

ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
