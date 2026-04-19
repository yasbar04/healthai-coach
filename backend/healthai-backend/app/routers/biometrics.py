from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User, Biometrics
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

@router.get("/biometrics")
def biometrics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.plan != "premium_plus":
        raise HTTPException(status_code=403, detail="Fonction Premium+ requise.")
    items = db.query(Biometrics).filter(Biometrics.user_id==user.id).order_by(Biometrics.measured_at.desc()).limit(30).all()
    return {
        "items": [
            {
                "measured_at": x.measured_at.isoformat(),
                "heart_rate_bpm": x.heart_rate_bpm,
                "sleep_hours": x.sleep_hours,
                "weight_kg": x.weight_kg
            } for x in items
        ]
    }
