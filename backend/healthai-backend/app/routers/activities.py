from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from ..db import SessionLocal
from ..models import User, Activity
from ..schemas import ActivityOut, ActivityCreate
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


def _to_out(a: Activity) -> ActivityOut:
    return ActivityOut(
        id=a.id, activity_date=a.activity_date,
        steps=a.steps, active_minutes=a.active_minutes,
        calories_out=a.calories_out, distance_km=a.distance_km,
        workout_type=a.workout_type, sleep_hours=a.sleep_hours,
        water_ml=a.water_ml, weight_kg=a.weight_kg,
    )


@router.get("/activities", response_model=list[ActivityOut])
def list_activities(
    from_: date = Query(None, alias="from"),
    to: date = Query(None),
    user_id: int | None = Query(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    target_user_id = user.id
    if user_id and user.plan in ("b2b",):
        target_user_id = user_id
    q = db.query(Activity).filter(Activity.user_id == target_user_id)
    if from_:
        q = q.filter(Activity.activity_date >= from_)
    if to:
        q = q.filter(Activity.activity_date <= to)
    return [_to_out(a) for a in q.order_by(Activity.activity_date.asc()).all()]


@router.post("/activities", response_model=ActivityOut, status_code=201)
def upsert_activity(
    payload: ActivityCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Create or update the activity entry for a given date."""
    existing = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date == payload.activity_date
    ).first()

    if existing:
        for field, val in payload.dict(exclude_unset=True).items():
            if field != "activity_date":
                setattr(existing, field, val)
        db.commit()
        db.refresh(existing)
        return _to_out(existing)
    else:
        a = Activity(user_id=user.id, **payload.dict())
        db.add(a)
        db.commit()
        db.refresh(a)
        return _to_out(a)


@router.delete("/activities/{activity_id}", status_code=204)
def delete_activity(
    activity_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    a = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.user_id == user.id
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Entrée introuvable.")
    db.delete(a)
    db.commit()
