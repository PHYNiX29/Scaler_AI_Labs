from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, UPLOAD_DIR
from app.database import Base, SessionLocal, engine
from app.routes import form_routes, public_routes, response_routes, upload_routes
from app.utils.seeder import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and load sample data on first boot; a no-op once the database has forms
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Typeform Clone API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

app.include_router(form_routes.router)
app.include_router(response_routes.router)
app.include_router(public_routes.router)
app.include_router(upload_routes.router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "healthy"}
