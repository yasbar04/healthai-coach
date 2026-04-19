from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .settings import settings
from .db import Base, engine
from .seed import seed_if_empty, seed_bdd_if_empty, seed_exercises_cache, seed_food_catalog, seed_fitness_update
from .etl_scheduler import etl_scheduler, setup_etl_jobs

from .routers import auth, users, billing, activities, nutrition, analytics, quality, ai, biometrics, consultations, tenant, bdd, exercises_ext

# Create tables
Base.metadata.create_all(bind=engine)

# ── Safe migrations for SQLite (add new columns if missing) ──────────────────
_NEW_COLUMNS = [
    "ALTER TABLE activities ADD COLUMN workout_type TEXT",
    "ALTER TABLE activities ADD COLUMN sleep_hours REAL",
    "ALTER TABLE activities ADD COLUMN water_ml INTEGER",
    "ALTER TABLE activities ADD COLUMN weight_kg REAL",
    "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'",
]
with engine.connect() as _conn:
    for _stmt in _NEW_COLUMNS:
        try:
            _conn.execute(text(_stmt))
            _conn.commit()
        except Exception:
            pass  # column already exists

app = FastAPI(title="HealthAI Coach API", version="1.0.0")

# CORS must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
def root():
    return {"status": "HealthAI API running"}


@app.on_event("shutdown")
def shutdown_event():
    """Arrêter le scheduler à l'arrêt"""
    etl_scheduler.stop()
