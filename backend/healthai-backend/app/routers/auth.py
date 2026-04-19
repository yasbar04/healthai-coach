from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import User
from ..schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from ..security import verify_password, create_access_token, hash_password

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides.")
    token = create_access_token(str(user.id))
    return LoginResponse(access_token=token)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email déjà utilisé.")
    VALID_PLANS = {"freemium", "premium", "premium_plus", "b2b"}
    plan = payload.plan.lower().replace(" ", "_").replace("+", "_plus")
    if plan not in VALID_PLANS:
        plan = "freemium"
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        plan=plan,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return RegisterResponse(access_token=token, plan=user.plan)
