from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, scan, tabung
from app.core.database import engine, Base
from app.core.config import settings

# Import all models so Base.metadata knows about them
from app.models import user, scan as scan_model, tabung as tabung_model, investment  # noqa: F401


async def _ensure_database_exists():
    """Connect to the default 'postgres' DB and create our DB if it doesn't exist."""
    # Parse the DB name from the URL  (e.g. "...localhost:5432/jimat")
    db_name = settings.DATABASE_URL.rsplit("/", 1)[-1]
    # Build a URL pointing at the default 'postgres' database
    server_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    # asyncpg needs a plain postgresql:// URL (no +asyncpg)
    server_url = server_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(server_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            # Can't use params in DDL, but db_name is from our own .env
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"[OK] Created database '{db_name}'")
        else:
            print(f"[OK] Database '{db_name}' already exists")
    finally:
        await conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-create database + tables on startup."""
    await _ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] All tables ready")
    yield


app = FastAPI(title="Jimat2go API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
app.include_router(scan.router,   prefix="/scan",   tags=["Scan"])
app.include_router(tabung.router, prefix="/tabung", tags=["Tabung"])

@app.get("/health")
def health():
    return {"status": "ok", "app": "Jimat2go"}
