from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from ..db import SessionLocal
from ..models import User, Activity, NutritionLog, Food
from ..schemas import SummaryOut, TrendOut, TrendPoint
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

def calories_in_for_day(db: Session, user_id: int, d: date) -> int:
    logs = db.query(NutritionLog).filter(NutritionLog.user_id==user_id, NutritionLog.log_date==d).all()
    total = 0.0
    for l in logs:
        food = db.query(Food).filter(Food.id==l.food_id).first()
        if food and food.calories_kcal is not None:
            total += float(food.calories_kcal) * (float(l.grams)/100.0)
    return int(round(total))

@router.get("/summary", response_model=SummaryOut)
def summary(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    acts = db.query(Activity).filter(Activity.user_id==user.id, Activity.activity_date>=from_, Activity.activity_date<=to).all()
    total_steps = sum([a.steps or 0 for a in acts])
    total_out = sum([a.calories_out or 0 for a in acts])
    days = set([a.activity_date.isoformat() for a in acts if a.activity_date])
    active_days = len(days)

    # calories in
    d = from_
    total_in = 0
    while d <= to:
        total_in += calories_in_for_day(db, user.id, d)
        d = d + timedelta(days=1)

    return SummaryOut(
        total_calories_in=total_in,
        total_calories_out=total_out,
        total_steps=total_steps,
        active_days=active_days
    )

@router.get("/trends/steps", response_model=TrendOut)
def trend_steps(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    pts = []
    d = from_
    while d <= to:
        a = db.query(Activity).filter(Activity.user_id==user.id, Activity.activity_date==d).first()
        pts.append(TrendPoint(date=d.isoformat(), value=float(a.steps or 0) if a else 0.0))
        d = d + timedelta(days=1)
    return TrendOut(points=pts)

@router.get("/trends/calories-in", response_model=TrendOut)
def trend_cal_in(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    pts = []
    d = from_
    while d <= to:
        pts.append(TrendPoint(date=d.isoformat(), value=float(calories_in_for_day(db, user.id, d))))
        d = d + timedelta(days=1)
    return TrendOut(points=pts)

@router.get("/trends/calories-out", response_model=TrendOut)
def trend_cal_out(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    pts = []
    d = from_
    while d <= to:
        a = db.query(Activity).filter(Activity.user_id==user.id, Activity.activity_date==d).first()
        pts.append(TrendPoint(date=d.isoformat(), value=float(a.calories_out or 0) if a else 0.0))
        d = d + timedelta(days=1)
    return TrendOut(points=pts)


@router.get("/today")
def today_snapshot(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Return today's activity entry + calories_in for the connected user."""
    from datetime import date as _date
    today = _date.today()
    a = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date == today
    ).first()
    cal_in = calories_in_for_day(db, user.id, today)
    return {
        "date": today.isoformat(),
        "has_entry": a is not None,
        "activity_id": a.id if a else None,
        "steps": a.steps if a else None,
        "active_minutes": a.active_minutes if a else None,
        "calories_out": a.calories_out if a else None,
        "distance_km": a.distance_km if a else None,
        "workout_type": a.workout_type if a else None,
        "sleep_hours": a.sleep_hours if a else None,
        "water_ml": a.water_ml if a else None,
        "weight_kg": a.weight_kg if a else None,
        "calories_in": cal_in,
    }
