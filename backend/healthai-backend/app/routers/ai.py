from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from ..db import SessionLocal
from ..models import User
from ..security import decode_token
from ..services.ai_service import ai_service

router = APIRouter()


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


class MealPlanRequest(BaseModel):
    goal: Optional[str] = "maintain"
    duration_days: Optional[int] = 7
    meals_per_day: Optional[int] = 3
    budget_level: Optional[str] = "medium"
    calorie_target: Optional[float] = None
    dietary_preferences: Optional[List[str]] = []
    allergies: Optional[List[str]] = []


class WorkoutRequest(BaseModel):
    goal: Optional[str] = "maintain"
    fitness_level: Optional[str] = "intermediate"
    available_minutes: Optional[int] = 45
    equipment: Optional[List[str]] = []
    restrictions: Optional[List[str]] = []
    preferred_categories: Optional[List[str]] = []


@router.post("/analyze-meal")
async def analyze_meal_photo(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    if user.plan not in ("premium", "premium_plus") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (JPEG, PNG, WebP).")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image trop volumineuse (max 10 MB).")

    user_profile = {
        "goal": getattr(user, "goal", "maintain") or "maintain",
        "weight_kg": getattr(user, "weight_kg", 70) or 70,
        "height_cm": getattr(user, "height_cm", 170) or 170,
        "age": getattr(user, "age", 30) or 30,
        "allergies": [],
        "activity_level": getattr(user, "activity_level", "moderate") or "moderate",
    }

    result = await ai_service.analyze_meal_photo(image_bytes, user_profile)
    return result


@router.post("/meal-plan")
async def generate_meal_plan(
    body: MealPlanRequest,
    user: User = Depends(current_user),
):
    if user.plan not in ("premium", "premium_plus") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")

    user_profile = {
        "goal": getattr(user, "goal", None) or body.goal,
        "weight_kg": getattr(user, "weight_kg", 70) or 70,
        "height_cm": getattr(user, "height_cm", 170) or 170,
        "age": getattr(user, "age", 30) or 30,
        "activity_level": getattr(user, "activity_level", "moderate") or "moderate",
        "allergies": body.allergies or [],
        "dietary_preferences": body.dietary_preferences or [],
    }

    request_params = {
        "duration_days": body.duration_days,
        "meals_per_day": body.meals_per_day,
        "budget_level": body.budget_level,
        "calorie_target": body.calorie_target,
    }

    try:
        result = await ai_service.generate_meal_plan(user_profile, request_params)
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/workout")
async def generate_workout(
    body: WorkoutRequest,
    user: User = Depends(current_user),
):
    if user.plan not in ("premium", "premium_plus") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")

    user_profile = {
        "user_id": user.id,
        "goal": getattr(user, "goal", None) or body.goal,
        "weight_kg": getattr(user, "weight_kg", 70) or 70,
        "age": getattr(user, "age", 30) or 30,
    }

    request_params = {
        "goal": body.goal,
        "fitness_level": body.fitness_level,
        "available_minutes": body.available_minutes,
        "equipment": body.equipment or [],
        "restrictions": body.restrictions or [],
    }

    result = await ai_service.generate_workout(user_profile, request_params)
    return result


@router.get("/recommendations")
def recommendations(user: User = Depends(current_user)):
    if user.plan not in ("premium", "premium_plus") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")
    return {
        "user_id": user.id,
        "summary": "Recommandations personnalisées.",
        "nutrition": [
            "Augmenter les fibres (fruits/légumes) et viser 25-30g/jour.",
            "Répartir les protéines sur 3 repas.",
        ],
        "activity": [
            "Objectif 8 000 pas/jour.",
            "2 séances de renforcement léger/semaine.",
        ],
    }


@router.get("/plans")
def plans(user: User = Depends(current_user)):
    if user.plan not in ("premium", "premium_plus") and user.role != "admin":
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")
    return {
        "nutrition_plan": {
            "goal": "Déficit léger",
            "meals": ["Petit-déj équilibré", "Déjeuner riche en protéines", "Dîner léger"],
        },
        "sport_plan": {
            "goal": "Remise en forme",
            "sessions": ["Cardio 30min", "Renforcement 20min", "Mobilité 10min"],
        },
    }
