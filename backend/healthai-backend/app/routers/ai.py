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

@router.get("/recommendations")
def recommendations(user: User = Depends(current_user)):
    if user.plan not in ("premium", "premium_plus"):
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")
    # Stub IA: réponses fixes pour la soutenance
    return {
        "user_id": user.id,
        "summary": "Recommandations personnalisées (démo).",
        "nutrition": [
            "Augmenter les fibres (fruits/légumes) et viser 25-30g/jour.",
            "Répartir les protéines sur 3 repas."
        ],
        "activity": [
            "Objectif 8 000 pas/jour.",
            "2 séances de renforcement léger/semaine."
        ]
    }

@router.get("/plans")
def plans(user: User = Depends(current_user)):
    if user.plan not in ("premium", "premium_plus"):
        raise HTTPException(status_code=403, detail="Fonction Premium requise.")
    return {
        "nutrition_plan": {
            "goal": "Déficit léger (démo)",
            "meals": ["Petit-déj équilibré", "Déjeuner riche en protéines", "Dîner léger"]
        },
        "sport_plan": {
            "goal": "Remise en forme",
            "sessions": ["Cardio 30min", "Renforcement 20min", "Mobilité 10min"]
        }
    }
