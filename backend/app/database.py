from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATA_DIR, DATABASE_URL

Base = declarative_base()

DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record):
    # SQLite ignores ON DELETE CASCADE unless foreign keys are switched on per connection
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db)):
    """Returns the creator making the request."""
    # shortcut: one default creator and no login (allowed by the brief), swap this dependency for real auth when multi-user is needed
    from app.models import User

    user = db.query(User).first()
    if not user:
        user = User(email="demo@scaler.ai", name="Demo Creator")
        db.add(user)
        db.commit()
    return user
