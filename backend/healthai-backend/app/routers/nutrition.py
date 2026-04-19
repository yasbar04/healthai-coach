from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from ..db import SessionLocal
from ..models import User, Food, NutritionLog
from ..schemas import FoodOut, NutritionLogOut
from ..security import decode_token

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

@router.get("/foods", response_model=list[FoodOut])
def list_foods(search: str | None = Query(None), meal_type: str | None = Query(None), limit: int = Query(100, ge=1, le=1000), user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Food)
    if search:
        q = q.filter(Food.name.ilike(f"%{search}%"))
    if meal_type:
        q = q.filter(Food.meal_type == meal_type)
    items = q.order_by(Food.name.asc()).limit(limit).all()
    return [FoodOut(
        id=f.id, name=f.name, category=f.category,
        calories_kcal=f.calories_kcal, protein_g=f.protein_g, carbs_g=f.carbs_g, fat_g=f.fat_g,
        fiber_g=f.fiber_g, sugars_g=f.sugars_g, sodium_mg=f.sodium_mg, cholesterol_mg=f.cholesterol_mg,
        meal_type=f.meal_type, water_intake_ml=f.water_intake_ml,
    ) for f in items]

@router.get("/nutrition-logs", response_model=list[NutritionLogOut])
def list_logs(
    from_: date = Query(None, alias="from"),
    to: date = Query(None),
    user_id: int | None = Query(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    target_user_id = user.id
    if user_id and user.plan in ("b2b",):
        target_user_id = user_id

    q = db.query(NutritionLog).filter(NutritionLog.user_id == target_user_id)
    if from_:
        q = q.filter(NutritionLog.log_date >= from_)
    if to:
        q = q.filter(NutritionLog.log_date <= to)

    logs = q.order_by(NutritionLog.log_date.asc()).all()
    out = []
    for l in logs:
        food = db.query(Food).filter(Food.id == l.food_id).first()
        total = None
        if food and food.calories_kcal is not None:
            # calories_kcal per 100g
            total = float(food.calories_kcal) * (float(l.grams) / 100.0)
        out.append(NutritionLogOut(
            id=l.id, log_date=l.log_date, grams=float(l.grams),
            food_id=l.food_id, food_name=(food.name if food else None),
            total_calories_kcal=total
        ))
    return out
