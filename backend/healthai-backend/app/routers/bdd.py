"""
Router BDD HealthAI — expose les tables du schéma métier (BDD HealthAI.sql)
Endpoints : Utilisateurs, HealthData, Nutrition, DailyData, WeeklyData, B2B, Abonnements, Aliments
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..db import SessionLocal
from ..models import (
    User, Utilisateur, HealthData, HealthNutrition,
    DailyData, WeeklyData, B2BCompany, Abonnement, Aliment
)
from ..security import decode_token

router = APIRouter(prefix="/bdd", tags=["bdd"])


# ── Auth helper ─────────────────────────────────────────────────────────────

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


def current_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs.")
    return user


# ── Utilisateurs ─────────────────────────────────────────────────────────────

@router.get("/utilisateurs/filter-options")
def utilisateurs_filter_options(_: User = Depends(current_admin), db: Session = Depends(get_db)):
    """Retourne les valeurs distinctes pour les filtres dropdown."""
    from sqlalchemy import distinct
    diseases = [r[0] for r in db.query(distinct(HealthData.disease_type)).filter(HealthData.disease_type != None).order_by(HealthData.disease_type).all()]
    plans = [r[0] for r in db.query(distinct(Abonnement.name)).filter(Abonnement.name != None).order_by(Abonnement.name).all()]
    return {"diseases": diseases, "plans": plans}


@router.get("/utilisateurs")
def list_utilisateurs(
    limit: int = Query(20, le=200),
    offset: int = Query(0, ge=0),
    search: str = Query(None, description="Recherche nom ou email"),
    gender: str = Query(None),
    plan: str = Query(None, description="Plan abonnement: Freemium, Premium, Premium+, B2B"),
    disease: str = Query(None, description="Type de maladie"),
    _: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Utilisateur).options(
        joinedload(Utilisateur.company),
        joinedload(Utilisateur.health_data),
        joinedload(Utilisateur.nutrition_profile),
        joinedload(Utilisateur.daily_data),
        joinedload(Utilisateur.weekly_data),
        joinedload(Utilisateur.abonnements),
    )
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Utilisateur.name.ilike(like)) | (Utilisateur.email.ilike(like))
        )
    if gender:
        q = q.filter(Utilisateur.gender == gender)
    if disease:
        q = q.join(HealthData, Utilisateur.health_data_id == HealthData.id)\
             .filter(HealthData.disease_type.ilike(f"%{disease}%"))
    if plan:
        q = q.join(Abonnement, Abonnement.utilisateur_id == Utilisateur.id)\
             .filter(Abonnement.name.ilike(f"%{plan}%"))
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [_fmt_utilisateur(u, full=True) for u in items]
    }


@router.get("/utilisateurs/{uid}")
def get_utilisateur(uid: int, _: User = Depends(current_admin), db: Session = Depends(get_db)):
    u = db.query(Utilisateur).options(
        joinedload(Utilisateur.company),
        joinedload(Utilisateur.health_data),
        joinedload(Utilisateur.nutrition_profile),
        joinedload(Utilisateur.daily_data),
        joinedload(Utilisateur.weekly_data),
        joinedload(Utilisateur.abonnements),
    ).filter(Utilisateur.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return _fmt_utilisateur(u, full=True)


def _fmt_utilisateur(u: Utilisateur, full: bool = False) -> dict:
    base = {
        "id": u.id,
        "name": u.name,
        "age": u.age,
        "gender": u.gender,
        "email": u.email,
        "company": u.company.name_entreprise if u.company else None,
        "health_data": {
            "disease_type": u.health_data.disease_type,
            "severity": u.health_data.severity,
            "physical_activity_level": u.health_data.physical_activity_level,
            "cholesterol_mg_dl": u.health_data.cholesterol_mg_dl,
            "blood_pressure_mmhg": u.health_data.blood_pressure_mmhg,
            "glucose_mg_dl": u.health_data.glucose_mg_dl,
        } if u.health_data else None,
        "nutrition": {
            "diet_recommendation": u.nutrition_profile.diet_recommendation,
            "adherence_to_diet_plan": u.nutrition_profile.adherence_to_diet_plan,
            "preferred_cuisine": u.nutrition_profile.preferred_cuisine,
            "water_intake": u.nutrition_profile.water_intake,
            "dietary_restrictions": u.nutrition_profile.dietary_restrictions,
            "allergies": u.nutrition_profile.allergies,
        } if u.nutrition_profile else None,
        "daily": {
            "workout_type": u.daily_data.workout_type,
            "exercise_hours": u.daily_data.exercise_hours,
            "calories_burned": u.daily_data.calories_burned,
            "daily_caloric_intake": u.daily_data.daily_caloric_intake,
            "max_bpm": u.daily_data.max_bpm,
            "resting_bpm": u.daily_data.resting_bpm,
            "avg_bpm": u.daily_data.avg_bpm,
        } if u.daily_data else None,
        "weekly": {
            "weight": u.weekly_data.weight,
            "bmi": u.weekly_data.bmi,
            "fat_percentage": u.weekly_data.fat_percentage,
            "workout_frequency": u.weekly_data.workout_frequency,
        } if u.weekly_data else None,
    }
    if full:
        base["abonnements"] = [
            {"name": a.name, "price": a.price} for a in u.abonnements
        ]
    return base


# ── Health Data ──────────────────────────────────────────────────────────────

@router.get("/health-data")
def list_health_data(_: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(HealthData).limit(200).all()
    return {"items": [
        {
            "id": x.id,
            "experience_level": x.experience_level,
            "disease_type": x.disease_type,
            "severity": x.severity,
            "physical_activity_level": x.physical_activity_level,
            "cholesterol_mg_dl": x.cholesterol_mg_dl,
            "blood_pressure_mmhg": x.blood_pressure_mmhg,
            "glucose_mg_dl": x.glucose_mg_dl,
        } for x in items
    ]}


# ── Nutrition profiles ───────────────────────────────────────────────────────

@router.get("/nutrition-profiles")
def list_nutrition_profiles(
    diet: str = Query(None, description="Filtrer par Diet_Recommendation"),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    q = db.query(HealthNutrition)
    if diet:
        q = q.filter(HealthNutrition.diet_recommendation == diet)
    items = q.limit(200).all()
    return {"items": [
        {
            "id": x.id,
            "meal_context": x.meal_context,
            "adherence_to_diet_plan": x.adherence_to_diet_plan,
            "preferred_cuisine": x.preferred_cuisine,
            "water_intake": x.water_intake,
            "diet_recommendation": x.diet_recommendation,
            "dietary_restrictions": x.dietary_restrictions,
            "nutrient_imbalance_score": x.dietary_nutrient_imbalance_score,
            "allergies": x.allergies,
        } for x in items
    ]}


# ── Daily Data ───────────────────────────────────────────────────────────────

@router.get("/daily-data")
def list_daily_data(
    workout_type: str = Query(None),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    q = db.query(DailyData)
    if workout_type:
        q = q.filter(DailyData.workout_type == workout_type)
    items = q.limit(200).all()
    return {"items": [
        {
            "id": x.id,
            "workout_type": x.workout_type,
            "exercise_hours": x.exercise_hours,
            "calories_burned": x.calories_burned,
            "daily_caloric_intake": x.daily_caloric_intake,
            "max_bpm": x.max_bpm,
            "resting_bpm": x.resting_bpm,
            "avg_bpm": x.avg_bpm,
        } for x in items
    ]}


# ── Weekly Data ──────────────────────────────────────────────────────────────

@router.get("/weekly-data")
def list_weekly_data(_: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(WeeklyData).limit(200).all()
    return {"items": [
        {
            "id": x.id,
            "weight": x.weight,
            "bmi": x.bmi,
            "fat_percentage": x.fat_percentage,
            "workout_frequency": x.workout_frequency,
        } for x in items
    ]}


# ── B2B Companies ────────────────────────────────────────────────────────────

@router.get("/b2b-companies")
def list_b2b_companies(_: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(B2BCompany).all()
    return {"items": [
        {"id": x.id, "name": x.name_entreprise, "user_count": len(x.utilisateurs)}
        for x in items
    ]}


# ── Abonnements ──────────────────────────────────────────────────────────────

@router.get("/abonnements/stats")
def abonnements_stats(_: User = Depends(current_user), db: Session = Depends(get_db)):
    """Statistiques des abonnements par plan."""
    from sqlalchemy import func
    rows = db.query(
        Abonnement.name, Abonnement.price,
        func.count(Abonnement.id).label("total")
    ).group_by(Abonnement.name, Abonnement.price).all()
    return {"stats": [{"plan": r.name, "price": r.price, "total": r.total} for r in rows]}


@router.get("/abonnements")
def list_abonnements(_: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(Abonnement).limit(200).all()
    return {"items": [
        {"id": x.id, "utilisateur_id": x.utilisateur_id, "name": x.name, "price": x.price}
        for x in items
    ]}


# ── Aliments ─────────────────────────────────────────────────────────────────

@router.get("/aliments")
def list_aliments(
    search: str = Query(None, description="Recherche par nom"),
    max_sodium: int = Query(None, description="Sodium max (mg)"),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Aliment)
    if search:
        q = q.filter(Aliment.food_item.ilike(f"%{search}%"))
    if max_sodium is not None:
        q = q.filter(Aliment.sodium <= max_sodium)
    items = q.limit(200).all()
    return {"items": [
        {
            "id": x.id,
            "food_item": x.food_item,
            "calories": x.calories,
            "protein": x.protein,
            "carbohydrates": x.carbohydrates,
            "fat": x.fat,
            "fiber": x.fiber,
            "sugars": x.sugars,
            "sodium": x.sodium,
            "cholesterol": x.cholesterol,
        } for x in items
    ]}


# ── Analytics / Dashboard KPIs ───────────────────────────────────────────────

@router.get("/kpis")
def dashboard_kpis(_: User = Depends(current_user), db: Session = Depends(get_db)):
    """KPIs globaux du tableau de bord analytique (Section 9 du SQL)."""
    from sqlalchemy import func
    total_users = db.query(func.count(Utilisateur.id)).scalar()
    avg_bmi = db.query(func.avg(WeeklyData.bmi)).scalar()
    avg_cal = db.query(func.avg(DailyData.calories_burned)).scalar()
    avg_diet = db.query(func.avg(HealthNutrition.adherence_to_diet_plan)).scalar()
    avg_water = db.query(func.avg(HealthNutrition.water_intake)).scalar()
    avg_weight = db.query(func.avg(WeeklyData.weight)).scalar()

    # Distribution genre
    genders = db.query(Utilisateur.gender, func.count(Utilisateur.id)).group_by(Utilisateur.gender).all()
    # Types entraînement
    workouts = db.query(DailyData.workout_type, func.count(DailyData.id)).group_by(DailyData.workout_type).order_by(func.count(DailyData.id).desc()).limit(5).all()
    # Alertes risques santé
    alerts = db.query(func.count(HealthData.id)).filter(
        (HealthData.cholesterol_mg_dl > 240) |
        (HealthData.glucose_mg_dl > 180) |
        (HealthData.blood_pressure_mmhg > 140)
    ).scalar()

    return {
        "total_users": total_users,
        "avg_bmi": round(avg_bmi, 1) if avg_bmi else None,
        "avg_calories_burned": round(avg_cal) if avg_cal else None,
        "avg_diet_adherence": round(avg_diet, 1) if avg_diet else None,
        "avg_water_intake": round(avg_water, 1) if avg_water else None,
        "avg_weight": round(avg_weight, 1) if avg_weight else None,
        "health_risk_alerts": alerts,
        "gender_distribution": [{"gender": g, "count": c} for g, c in genders],
        "top_workouts": [{"type": w, "count": c} for w, c in workouts],
    }


# ── Alertes risques ──────────────────────────────────────────────────────────

@router.get("/alerts/health-risks")
def health_risk_alerts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    """Utilisateurs avec indicateurs biologiques critiques (Section 7 du SQL)."""
    items = db.query(Utilisateur).join(HealthData, Utilisateur.health_data_id == HealthData.id).filter(
        (HealthData.cholesterol_mg_dl > 240) |
        (HealthData.glucose_mg_dl > 180) |
        (HealthData.blood_pressure_mmhg > 140)
    ).all()
    return {"items": [
        {
            "name": u.name,
            "cholesterol": u.health_data.cholesterol_mg_dl,
            "glucose": u.health_data.glucose_mg_dl,
            "blood_pressure": u.health_data.blood_pressure_mmhg,
        } for u in items
    ]}


@router.get("/alerts/poor-diet-adherence")
def poor_diet_alerts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    """Utilisateurs avec adhérence au régime < 50% (Section 7 du SQL)."""
    items = db.query(Utilisateur).join(
        HealthNutrition, Utilisateur.nutrition_id == HealthNutrition.id
    ).filter(HealthNutrition.adherence_to_diet_plan < 50).all()
    return {"items": [
        {"name": u.name, "adherence": u.nutrition_profile.adherence_to_diet_plan}
        for u in items
    ]}
