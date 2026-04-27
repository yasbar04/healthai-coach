from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from ..db import SessionLocal
from ..models import User, EtlRun, EtlError, Activity, NutritionLog, Food
from ..schemas import EtlRunOut, EtlErrorOut
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

@router.get("/etl-runs")
def etl_runs(
    user: User = Depends(current_user), 
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Récupérer l'historique des exécutions ETL"""
    query = db.query(EtlRun).order_by(EtlRun.started_at.desc())
    total = query.count()
    runs = query.limit(limit).offset(offset).all()
    items = [EtlRunOut(
        id=r.id, source_name=r.source_name, status=r.status,
        started_at=r.started_at, ended_at=r.ended_at,
        rows_in=r.rows_in, rows_out=r.rows_out, errors_count=r.errors_count
    ) for r in runs]
    return {"items": items, "total": total}

@router.get("/etl-runs/{run_id}/errors")
def run_errors(
    run_id: int, 
    user: User = Depends(current_user), 
    db: Session = Depends(get_db),
    limit: int = Query(100, le=500)
):
    """Récupérer les erreurs d'une exécution ETL"""
    query = db.query(EtlError).filter(EtlError.run_id==run_id).order_by(EtlError.created_at.desc())
    total = query.count()
    errs = query.limit(limit).all()
    items = [EtlErrorOut(
        id=e.id, severity=e.severity, row_reference=e.row_reference,
        message=e.message, created_at=e.created_at
    ) for e in errs]
    return {"items": items, "total": total}

@router.get("/data-quality-summary")
def data_quality_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Résumé qualitatif des données"""
    return {
        "summary": {
            "total_users": db.query(func.count(User.id)).scalar(),
            "total_activities": db.query(func.count(Activity.id)).scalar(),
            "total_nutrition_logs": db.query(func.count(NutritionLog.id)).scalar(),
            "total_foods": db.query(func.count(Food.id)).scalar(),
        },
        "data_completeness": {
            "activities_with_calories": db.query(func.count(Activity.id)).filter(Activity.calories_out.isnot(None)).scalar(),
            "activities_total": db.query(func.count(Activity.id)).scalar(),
        },
        "last_etl_run": db.query(EtlRun).order_by(EtlRun.started_at.desc()).first(),
        "recent_errors": db.query(EtlError).order_by(EtlError.created_at.desc()).limit(5).all(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/etl-stats")
def etl_stats(
    user: User = Depends(current_user), 
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30)
):
    """Statistiques ETL des N derniers jours"""
    since = datetime.utcnow() - timedelta(days=days)
    
    runs = db.query(EtlRun).filter(EtlRun.started_at >= since).all()
    
    success_count = sum(1 for r in runs if r.status == "success")
    failed_count = sum(1 for r in runs if r.status == "failed")
    total_rows_in = sum(r.rows_in for r in runs)
    total_rows_out = sum(r.rows_out for r in runs)
    total_errors = sum(r.errors_count for r in runs)
    
    return {
        "period_days": days,
        "total_runs": len(runs),
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": (success_count / len(runs) * 100) if runs else 0,
        "total_rows_processed": total_rows_in,
        "total_rows_loaded": total_rows_out,
        "total_errors": total_errors,
        "avg_processing_time": None,  # À implémenter
        "status": "healthy" if runs and (success_count / len(runs) * 100) > 95 else "warning"
    }

@router.get("/data-health-check")
def health_check(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Vérification complète de la santé des données"""
    return {
        "database_connected": True,
        "user_count": db.query(func.count(User.id)).scalar(),
        "recent_activity": db.query(Activity).order_by(Activity.activity_date.desc()).first() is not None,
        "tables_status": {
            "users": db.query(func.count(User.id)).scalar(),
            "activities": db.query(func.count(Activity.id)).scalar(),
            "foods": db.query(func.count(Food.id)).scalar(),
            "nutrition_logs": db.query(func.count(NutritionLog.id)).scalar(),
        },
        "last_check": datetime.utcnow().isoformat(),
        "status": "healthy"
    }

