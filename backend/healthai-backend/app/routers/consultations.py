from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User, Consultation
from ..security import decode_token

router = APIRouter()

class ConsultationReq(BaseModel):
    type: str = "nutrition"
    preferred_slot: str | None = None

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

@router.post("/consultations")
def create_consultation(payload: ConsultationReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.plan != "premium_plus":
        raise HTTPException(status_code=403, detail="Fonction Premium+ requise.")
    c = Consultation(user_id=user.id, type=payload.type, preferred_slot=payload.preferred_slot, status="requested")
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"status": "ok", "id": c.id, "consultation": {"type": c.type, "preferred_slot": c.preferred_slot, "status": c.status}}
