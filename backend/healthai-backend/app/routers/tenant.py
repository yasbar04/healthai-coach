from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User
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

@router.get("/me")
def tenant_me(user: User = Depends(current_user)):
    # For demo: b2b users return custom branding
    if user.plan == "b2b":
        return {
            "mode": "b2b",
            "brand_name": "GymPartner (White Label)",
            "hero_title": "Bienvenue sur GymPartner Health",
            "hero_subtitle": "Votre coach santé marque blanche pour vos adhérents."
        }
    return {"mode": "b2c", "brand_name": "HealthAI Coach"}
