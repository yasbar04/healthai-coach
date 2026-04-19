from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User
from ..schemas import SubscribeRequest, SubscribeResponse
from ..security import decode_token

router = APIRouter()

VALID_PLANS = {"freemium", "premium", "premium_plus", "b2b"}

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

@router.post("/subscribe", response_model=SubscribeResponse)
def subscribe(payload: SubscribeRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    plan = payload.plan.strip()
    if plan not in VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"Plan invalide. Valeurs: {sorted(VALID_PLANS)}")
    user.plan = plan
    db.add(user)
    db.commit()
    return SubscribeResponse(status="ok", plan=plan)
