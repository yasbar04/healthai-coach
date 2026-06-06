from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..db import SessionLocal
from ..models import User
from ..security import decode_token
from ..ml.predict import (
    predict_workout_type,
    predict_calories_burned,
    predict_diet_recommendation,
    get_metrics_report,
    models_trained,
)

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


class FitnessInput(BaseModel):
    age: float
    weight_kg: float
    height_m: float
    max_bpm: float
    avg_bpm: float
    resting_bpm: float
    session_duration_h: float
    fat_percentage: float
    water_intake_l: float
    workout_frequency: float
    experience_level: float
    bmi: float
    gender: Optional[str] = "Male"


class DietInput(BaseModel):
    age: float
    weight_kg: float
    height_cm: float
    bmi: float
    daily_caloric_intake: float
    weekly_exercise_hours: float
    adherence_to_diet_plan: float
    dietary_nutrient_imbalance_score: float
    gender: Optional[str] = "Male"
    disease_type: Optional[str] = "None"
    severity: Optional[str] = "Mild"
    physical_activity_level: Optional[str] = "Moderate"
    cholesterol: Optional[float] = None
    glucose: Optional[float] = None


@router.get("/ml/status")
def ml_status():
    trained = models_trained()
    return {
        "models_trained": trained,
        "message": "Modèles prêts." if trained else "Modèles non entraînés. POST /ml/train pour lancer l'entraînement.",
    }


@router.post("/ml/train")
def train_models(background_tasks: BackgroundTasks, user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux admins.")

    def _train():
        from ..ml.train import train_all
        train_all(verbose=False)

    background_tasks.add_task(_train)
    return {"message": "Entraînement lancé en arrière-plan. Consulter GET /ml/metrics une fois terminé."}


@router.get("/ml/metrics")
def ml_metrics(user: User = Depends(current_user)):
    report = get_metrics_report()
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@router.post("/ml/predict/workout-type")
def predict_workout(body: FitnessInput, user: User = Depends(current_user)):
    if not models_trained():
        raise HTTPException(status_code=503, detail="Modèles non encore entraînés.")
    try:
        return predict_workout_type(
            age=body.age, weight_kg=body.weight_kg, height_m=body.height_m,
            max_bpm=body.max_bpm, avg_bpm=body.avg_bpm, resting_bpm=body.resting_bpm,
            session_duration_h=body.session_duration_h, fat_percentage=body.fat_percentage,
            water_intake_l=body.water_intake_l, workout_frequency=body.workout_frequency,
            experience_level=body.experience_level, bmi=body.bmi, gender=body.gender,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/ml/predict/calories")
def predict_calories(body: FitnessInput, user: User = Depends(current_user)):
    if not models_trained():
        raise HTTPException(status_code=503, detail="Modèles non encore entraînés.")
    try:
        return predict_calories_burned(
            age=body.age, weight_kg=body.weight_kg, height_m=body.height_m,
            max_bpm=body.max_bpm, avg_bpm=body.avg_bpm, resting_bpm=body.resting_bpm,
            session_duration_h=body.session_duration_h, fat_percentage=body.fat_percentage,
            water_intake_l=body.water_intake_l, workout_frequency=body.workout_frequency,
            experience_level=body.experience_level, bmi=body.bmi, gender=body.gender,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/ml/predict/diet")
def predict_diet(body: DietInput, user: User = Depends(current_user)):
    if not models_trained():
        raise HTTPException(status_code=503, detail="Modèles non encore entraînés.")
    try:
        return predict_diet_recommendation(
            age=body.age, weight_kg=body.weight_kg, height_cm=body.height_cm,
            bmi=body.bmi, daily_caloric_intake=body.daily_caloric_intake,
            weekly_exercise_hours=body.weekly_exercise_hours,
            adherence_to_diet_plan=body.adherence_to_diet_plan,
            dietary_nutrient_imbalance_score=body.dietary_nutrient_imbalance_score,
            gender=body.gender, disease_type=body.disease_type,
            severity=body.severity, physical_activity_level=body.physical_activity_level,
            cholesterol=body.cholesterol, glucose=body.glucose,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
