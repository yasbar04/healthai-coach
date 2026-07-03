import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from .settings import settings
from .db import Base, engine
from .seed import seed_if_empty, seed_bdd_if_empty, seed_exercises_cache, seed_food_catalog, seed_fitness_update
from .etl_scheduler import etl_scheduler, setup_etl_jobs

from .routers import auth, users, billing, activities, nutrition, analytics, quality, ai, biometrics, consultations, tenant, bdd, exercises_ext, social
from .routers import ml as ml_router

# Create tables
Base.metadata.create_all(bind=engine)

# ── Safe migrations for SQLite (add new columns if missing) ──────────────────
_NEW_COLUMNS = [
    "ALTER TABLE activities ADD COLUMN workout_type TEXT",
    "ALTER TABLE activities ADD COLUMN sleep_hours REAL",
    "ALTER TABLE activities ADD COLUMN water_ml INTEGER",
    "ALTER TABLE activities ADD COLUMN weight_kg REAL",
    "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'",
    "ALTER TABLE users ADD COLUMN display_name TEXT",
    "ALTER TABLE users ADD COLUMN avatar_url TEXT",
]
with engine.connect() as _conn:
    for _stmt in _NEW_COLUMNS:
        try:
            _conn.execute(text(_stmt))
            _conn.commit()
        except Exception:
            pass  # column already exists

# Rate limiter — 60 requests/minute by default per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="HealthAI Coach API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_UPLOADS_DIR = "uploads"
os.makedirs(_UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOADS_DIR), name="uploads")

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass

# Seed demo data
seed_if_empty()
seed_bdd_if_empty()
seed_exercises_cache()
seed_food_catalog()
seed_fitness_update()

# Setup ETL Scheduler
setup_etl_jobs()
etl_scheduler.start()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(activities.router, tags=["activities"])
app.include_router(nutrition.router, tags=["nutrition"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(quality.router, prefix="/quality", tags=["quality"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(biometrics.router, tags=["biometrics"])
app.include_router(consultations.router, tags=["consultations"])
app.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
app.include_router(bdd.router)
app.include_router(exercises_ext.router)
app.include_router(ml_router.router, tags=["ml"])
app.include_router(social.router)


@app.get("/")
def root():
    return {"status": "HealthAI API running"}


@app.on_event("shutdown")
def shutdown_event():
    """Arrêter le scheduler à l'arrêt"""
    etl_scheduler.stop()
