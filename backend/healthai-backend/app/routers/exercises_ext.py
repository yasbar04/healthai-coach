from __future__ import annotations

"""
Proxy vers ExerciseDB v2 (https://exercisedbv2.ascendapi.com/api/v1)
Cache à 2 niveaux :
  1. Mémoire (10 min) — pour les requêtes répétées
  2. SQLite  (persistant) — fallback si API rate-limitée ou hors-ligne
"""
import json
import time
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User, ExerciseCache
from ..security import decode_token

router = APIRouter(prefix="/exercises-ext", tags=["exercises-ext"])

EXERCISE_API_BASE = "https://exercisedbv2.ascendapi.com/api/v1"
TIMEOUT = 12.0
MEM_TTL = 600     # 10 min en mémoire
DB_TTL  = 86400   # 24h avant tentative de refresh depuis l'API

_mem_cache: dict[str, tuple[float, any]] = {}


# ── Auth / DB helpers ────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token manquant.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
    return user


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_key(path: str, params: dict | None) -> str:
    p = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    return f"{path}?{p}"


def _db_get(db: Session, key: str) -> any | None:
    row = db.query(ExerciseCache).filter(ExerciseCache.cache_key == key).first()
    if not row:
        return None
    return json.loads(row.payload)


def _db_set(db: Session, key: str, data: any):
    row = db.query(ExerciseCache).filter(ExerciseCache.cache_key == key).first()
    payload = json.dumps(data)
    if row:
        row.payload = payload
        row.created_at = datetime.utcnow()
    else:
        db.add(ExerciseCache(cache_key=key, payload=payload))
    db.commit()


def _db_is_fresh(db: Session, key: str) -> bool:
    """True si le cache DB a moins de DB_TTL secondes."""
    row = db.query(ExerciseCache).filter(ExerciseCache.cache_key == key).first()
    if not row:
        return False
    age = (datetime.utcnow() - row.created_at).total_seconds()
    return age < DB_TTL


# ── Main fetch ────────────────────────────────────────────────────────────────

async def _get(path: str, params: dict = None, db: Session = None):
    key = _cache_key(path, params)
    now = time.monotonic()

    # 1. Mémoire fraîche
    if key in _mem_cache:
        ts, data = _mem_cache[key]
        if now - ts < MEM_TTL:
            return data

    # 2. DB fraîche → pas besoin d'appeler l'API
    if db and _db_is_fresh(db, key):
        data = _db_get(db, key)
        if data:
            _mem_cache[key] = (now, data)
            return data

    # 3. Appel API
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{EXERCISE_API_BASE}{path}", params=params)
            resp.raise_for_status()
            data = resp.json()
            _mem_cache[key] = (now, data)
            if db:
                _db_set(db, key, data)
            return data

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        # Fallback : données en cache même périmées
        if db:
            stale = _db_get(db, key)
            if stale:
                return stale
        if status == 429:
            raise HTTPException(
                status_code=429,
                detail="Limite de requêtes ExerciseDB atteinte. Les données mises en cache sont indisponibles pour l'instant. Réessayez dans quelques minutes."
            )
        raise HTTPException(status_code=status, detail=f"ExerciseDB error {status}")

    except httpx.TimeoutException:
        if db:
            stale = _db_get(db, key)
            if stale:
                return stale
        raise HTTPException(status_code=504, detail="ExerciseDB ne répond pas (timeout).")

    except Exception as exc:
        if db:
            stale = _db_get(db, key)
            if stale:
                return stale
        raise HTTPException(status_code=502, detail=f"Erreur réseau : {str(exc)}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/exercises")
async def list_exercises(
    limit: int = Query(20, ge=1, le=100),
    cursor: str = Query(None),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    params = {"limit": limit}
    if cursor:
        params["nextCursor"] = cursor
    return await _get("/exercises", params, db)


@router.get("/exercises/search")
async def search_exercises(
    name: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return await _get("/exercises/search", {"name": name, "limit": limit}, db)


@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: str,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return await _get(f"/exercises/{exercise_id}", db=db)


@router.get("/bodyparts")
async def list_bodyparts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return await _get("/bodyparts", db=db)


@router.get("/equipments")
async def list_equipments(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return await _get("/equipments", db=db)


@router.get("/muscles")
async def list_muscles(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return await _get("/muscles", db=db)


