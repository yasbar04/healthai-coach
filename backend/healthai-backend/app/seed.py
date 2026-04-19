from datetime import datetime, date, timedelta
import csv
import json
import os
import math
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import (
    User, Activity, Food, NutritionLog, Biometrics, EtlRun, EtlError,
    B2BCompany, HealthData, HealthNutrition, DailyData, WeeklyData,
    Utilisateur, Abonnement, Aliment, ExerciseCache,
)
from .security import hash_password

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_DIET_CSV = os.path.join(_DATA_DIR, "diet_recommendations.csv")
_FOOD_CSV = os.path.join(_DATA_DIR, "daily_food_nutrition.csv")
_FITNESS_CSV = os.path.join(_DATA_DIR, "fitness_tracker.csv")

DEMO_PW = "Demo123!"

def seed_if_empty():
    db: Session = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        users = [
            User(email="admin@demo.fr", password_hash=hash_password(DEMO_PW), plan="b2b", role="admin"),
            User(email="user@demo.fr", password_hash=hash_password(DEMO_PW), plan="freemium", role="user"),
            User(email="premium@demo.fr", password_hash=hash_password(DEMO_PW), plan="premium", role="user"),
            User(email="plus@demo.fr", password_hash=hash_password(DEMO_PW), plan="premium_plus", role="user"),
            User(email="b2b@demo.fr", password_hash=hash_password(DEMO_PW), plan="b2b", role="user"),
        ]
        db.add_all(users)
        db.flush()

        # Foods
        foods = [
            Food(name="Pomme", calories_kcal=52, protein_g=0.3, carbs_g=14, fat_g=0.2),
            Food(name="Pâtes complètes cuites", calories_kcal=124, protein_g=5, carbs_g=26, fat_g=1.1),
            Food(name="Poulet (blanc)", calories_kcal=165, protein_g=31, carbs_g=0, fat_g=3.6),
        ]
        db.add_all(foods)
        db.flush()

        # Activities (7 days) for user 1 (index 1 is user@demo.fr)
        u1 = users[1]
        for i in range(7):
            d = date.today() - timedelta(days=6-i)
            db.add(Activity(
                user_id=u1.id, activity_date=d,
                steps=7000 + i*500, active_minutes=40 + i*3, calories_out=250 + i*15, distance_km=4.5 + i*0.2
            ))

        # Nutrition logs for user 1
        for i in range(7):
            d = date.today() - timedelta(days=6-i)
            db.add(NutritionLog(user_id=u1.id, food_id=foods[0].id, log_date=d, grams=150))
            db.add(NutritionLog(user_id=u1.id, food_id=foods[1].id, log_date=d, grams=200))

        # Biometrics for premium_plus user (index 3 is plus@demo.fr)
        uplus = users[3]
        now = datetime.utcnow()
        for i in range(7):
            ts = now - timedelta(days=6-i)
            db.add(Biometrics(user_id=uplus.id, measured_at=ts, heart_rate_bpm=60+i, sleep_hours=7.0+i*0.1, weight_kg=75.0-i*0.1))

        # ETL runs + errors
        run1 = EtlRun(source_name="Fitness Tracker", status="success", started_at=now - timedelta(hours=2), ended_at=now - timedelta(hours=2, minutes=-2),
                      rows_in=1200, rows_out=1180, errors_count=2)
        run2 = EtlRun(source_name="Nutrition", status="partial", started_at=now - timedelta(hours=1), ended_at=now - timedelta(hours=1, minutes=-1),
                      rows_in=950, rows_out=910, errors_count=5)
        db.add_all([run1, run2])
        db.flush()

        db.add_all([
            EtlError(run_id=run1.id, severity="warn", row_reference="activity:102", message="distance_km manquant", created_at=now - timedelta(hours=2)),
            EtlError(run_id=run1.id, severity="warn", row_reference="activity:487", message="calories_out hors plage, corrigé", created_at=now - timedelta(hours=2)),
            EtlError(run_id=run2.id, severity="error", row_reference="log:12", message="food_id inconnu", created_at=now - timedelta(hours=1)),
            EtlError(run_id=run2.id, severity="error", row_reference="log:44", message="grams négatif", created_at=now - timedelta(hours=1)),
        ])

        db.commit()
    finally:
        db.close()


def _parse_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val) if val and val.strip().lower() not in ("", "nan", "none") else default
    except (ValueError, TypeError):
        return default


def _activity_level_to_int(level: str) -> int:
    mapping = {"sedentary": 1, "moderate": 3, "active": 5}
    return mapping.get(level.lower().strip(), 2)


def _activity_level_to_freq(level: str) -> int:
    mapping = {"sedentary": 1, "moderate": 3, "active": 5}
    return mapping.get(level.lower().strip(), 2)


def _bmi_to_fat_pct(bmi: float, gender: str) -> float:
    """Derive rough fat % from BMI (Deurenberg formula)."""
    age = 35  # average
    sex = 1 if gender.lower() == "male" else 0
    fat = 1.20 * bmi + 0.23 * age - 10.8 * sex - 5.4
    return round(max(5.0, min(55.0, fat)), 1)


def _seed_bdd():
    """Seed des tables du schéma métier BDD HealthAI depuis le dataset Kaggle."""
    db: Session = SessionLocal()
    try:
        if db.query(Utilisateur).count() > 0:
            return

        # ── B2B Companies ───────────────────────────────────────────────────
        companies = [
            B2BCompany(name_entreprise="TechCorp Solutions"),
            B2BCompany(name_entreprise="HealthFirst SA"),
            B2BCompany(name_entreprise="FitnessPro SAS"),
            B2BCompany(name_entreprise="WellnessGroup"),
            B2BCompany(name_entreprise="MedikaPro"),
        ]
        db.add_all(companies)
        db.flush()
        company_ids = [c.id for c in companies]

        # ── Aliments de référence (nutriments communs) ───────────────────────
        aliments_ref = [
            Aliment(food_item="Poulet grillé", calories=165, protein=31, carbohydrates=0, fat=3.6, fiber=0, sugars=0, sodium=74, cholesterol=85),
            Aliment(food_item="Riz brun cuit", calories=112, protein=2.6, carbohydrates=24, fat=0.9, fiber=1.8, sugars=0.4, sodium=5, cholesterol=0),
            Aliment(food_item="Saumon au four", calories=208, protein=20, carbohydrates=0, fat=13, fiber=0, sugars=0, sodium=59, cholesterol=63),
            Aliment(food_item="Brocoli vapeur", calories=35, protein=2.4, carbohydrates=7, fat=0.4, fiber=2.6, sugars=1.7, sodium=33, cholesterol=0),
            Aliment(food_item="Yaourt grec 0%", calories=59, protein=10, carbohydrates=3.6, fat=0.4, fiber=0, sugars=3.2, sodium=36, cholesterol=5),
            Aliment(food_item="Avocat", calories=160, protein=2, carbohydrates=9, fat=15, fiber=7, sugars=0.7, sodium=7, cholesterol=0),
            Aliment(food_item="Patate douce cuite", calories=90, protein=2, carbohydrates=21, fat=0.1, fiber=3.3, sugars=6.5, sodium=36, cholesterol=0),
        ]
        db.add_all(aliments_ref)
        db.flush()

        # ── Load Kaggle CSV ──────────────────────────────────────────────────
        rows = []
        if os.path.exists(_DIET_CSV):
            with open(_DIET_CSV, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        # Fallback: 5 hardcoded patients if CSV missing
        if not rows:
            rows = [
                {"Patient_ID": "P0001", "Age": "35", "Gender": "Male", "Weight_kg": "82.5", "Height_cm": "178",
                 "BMI": "26.0", "Disease_Type": "None", "Severity": "None", "Physical_Activity_Level": "Moderate",
                 "Daily_Caloric_Intake": "2200", "Cholesterol_mg/dL": "195", "Blood_Pressure_mmHg": "120",
                 "Glucose_mg/dL": "95", "Dietary_Restrictions": "None", "Allergies": "None",
                 "Preferred_Cuisine": "Italian", "Weekly_Exercise_Hours": "4.0",
                 "Adherence_to_Diet_Plan": "75.0", "Dietary_Nutrient_Imbalance_Score": "2.0",
                 "Diet_Recommendation": "Balanced"},
            ]

        # Subscription plan assignment by index
        sub_plans = [
            ("Freemium", 0.0),
            ("Premium", 9.99),
            ("Premium Plus", 19.99),
            ("B2B", 49.99),
        ]

        meal_contexts = ["Petit-déjeuner", "Déjeuner", "Dîner", "Collation"]
        workout_types = ["Cardio", "Musculation", "Yoga", "HIIT", "Natation", "Vélo", "Course"]

        for idx, row in enumerate(rows):
            pid        = row.get("Patient_ID", f"P{idx:04d}")
            age        = int(_parse_float(row.get("Age", "30")))
            gender     = row.get("Gender", "Male")
            weight     = _parse_float(row.get("Weight_kg", "70"))
            height     = _parse_float(row.get("Height_cm", "170"))
            bmi        = _parse_float(row.get("BMI", "24"))
            disease    = row.get("Disease_Type", "None")
            severity   = row.get("Severity", "None")
            pal        = row.get("Physical_Activity_Level", "Moderate")
            cal_intake = int(_parse_float(row.get("Daily_Caloric_Intake", "2000")))
            chol       = _parse_float(row.get("Cholesterol_mg/dL", "180"))
            bp         = _parse_float(row.get("Blood_Pressure_mmHg", "120"))
            glucose    = _parse_float(row.get("Glucose_mg/dL", "90"))
            diet_restr = row.get("Dietary_Restrictions", "None") or "None"
            allergies  = row.get("Allergies", "None") or "None"
            cuisine    = row.get("Preferred_Cuisine", "International")
            wk_ex_hrs  = _parse_float(row.get("Weekly_Exercise_Hours", "3"))
            adherence  = _parse_float(row.get("Adherence_to_Diet_Plan", "70"))
            imbalance  = _parse_float(row.get("Dietary_Nutrient_Imbalance_Score", "2"))
            diet_rec   = row.get("Diet_Recommendation", "Balanced")

            exp_level  = _activity_level_to_int(pal)
            freq       = _activity_level_to_freq(pal)
            ex_hours_d = round(wk_ex_hrs / 7, 2)
            fat_pct    = _bmi_to_fat_pct(bmi, gender)

            # Derive BPM from activity level & age
            max_bpm    = int(220 - age + (exp_level - 3) * 5)
            rest_bpm   = int(72 - exp_level * 3)
            avg_bpm    = int((max_bpm + rest_bpm) / 2)
            cal_burned = int(cal_intake * 0.2 + wk_ex_hrs * 50 / 7)

            # Booleans for diet recommendation
            low_carb  = diet_rec == "Low_Carb"
            low_sodium = diet_rec == "Low_Sodium"
            balanced   = diet_rec == "Balanced"

            # HealthData
            hd = HealthData(
                experience_level=exp_level,
                disease_type=disease,
                severity=severity,
                physical_activity_level=pal,
                cholesterol_mg_dl=chol,
                blood_pressure_mmhg=bp,
                glucose_mg_dl=glucose,
            )
            db.add(hd)
            db.flush()

            # HealthNutrition
            hn = HealthNutrition(
                meal_context=meal_contexts[idx % len(meal_contexts)],
                adherence_to_diet_plan=adherence,
                preferred_cuisine=cuisine,
                water_intake=round(2.0 + bmi * 0.01, 1),
                diet_recommendation=diet_rec,
                dietary_restrictions=diet_restr,
                dietary_nutrient_imbalance_score=imbalance,
                allergies=allergies,
                low_carb=low_carb,
                low_sodium=low_sodium,
                balanced=balanced,
            )
            db.add(hn)
            db.flush()

            # DailyData
            dd = DailyData(
                max_bpm=max_bpm,
                resting_bpm=rest_bpm,
                avg_bpm=avg_bpm,
                exercise_hours=ex_hours_d,
                calories_burned=cal_burned,
                daily_caloric_intake=cal_intake,
                workout_type=workout_types[idx % len(workout_types)],
            )
            db.add(dd)
            db.flush()

            # WeeklyData
            wd = WeeklyData(
                weight=weight,
                workout_frequency=freq,
                fat_percentage=fat_pct,
                bmi=round(bmi, 1),
            )
            db.add(wd)
            db.flush()

            # Assign company to every 3rd patient (B2B)
            cid = company_ids[idx % len(company_ids)] if idx % 3 == 0 else None

            # Utilisateur — generate email & name from Patient_ID
            email = f"{pid.lower()}@healthai.fr"
            name  = f"Patient {pid}"

            u = Utilisateur(
                age=age,
                gender=gender[0].upper() if gender else "M",
                name=name,
                email=email,
                company_id=cid,
                health_data_id=hd.id,
                nutrition_id=hn.id,
                daily_data_id=dd.id,
                weekly_data_id=wd.id,
            )
            db.add(u)
            db.flush()

            # Abonnement
            plan_name, price = sub_plans[idx % len(sub_plans)]
            db.add(Abonnement(utilisateur_id=u.id, name=plan_name, price=price))

            # Commit every 100 rows to avoid huge transactions
            if (idx + 1) % 100 == 0:
                db.commit()

        db.commit()
    finally:
        db.close()


def seed_bdd_if_empty():
    """Wrapper public pour main.py."""
    _seed_bdd()


def seed_exercises_cache():
    """Pré-charge 50 exercices dans exercise_cache pour fonctionner sans API externe."""
    db: Session = SessionLocal()
    try:
        if db.query(ExerciseCache).count() > 0:
            return

        IMG = "https://cdn.exercisedb.dev/media/w/images"
        exercises = [
            # CHEST
            {"exerciseId":"ex001","name":"Barbell Bench Press","imageUrl":f"{IMG}/EsVOYBdhDN.jpg","bodyParts":["CHEST"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR"],"secondaryMuscles":["ANTERIOR DELTOID","TRICEPS BRACHII"]},
            {"exerciseId":"ex002","name":"Dumbbell Fly","imageUrl":f"{IMG}/RB7NBcf79I.jpg","bodyParts":["CHEST"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR"],"secondaryMuscles":["ANTERIOR DELTOID"]},
            {"exerciseId":"ex003","name":"Push-Up","imageUrl":f"{IMG}/9fW96RFqRZ.jpg","bodyParts":["CHEST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR"],"secondaryMuscles":["TRICEPS BRACHII","ANTERIOR DELTOID"]},
            {"exerciseId":"ex004","name":"Incline Dumbbell Press","imageUrl":f"{IMG}/MruSDlnk0M.jpg","bodyParts":["CHEST"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR CLAVICULAR HEAD"],"secondaryMuscles":["ANTERIOR DELTOID","TRICEPS BRACHII"]},
            # BACK
            {"exerciseId":"ex005","name":"Deadlift","imageUrl":f"{IMG}/qkXo99D6UI.jpg","bodyParts":["BACK"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["ERECTOR SPINAE"],"secondaryMuscles":["GLUTEUS MAXIMUS","QUADRICEPS","HAMSTRINGS"]},
            {"exerciseId":"ex006","name":"Pull-Up","imageUrl":f"{IMG}/AwDLoYPc84.jpg","bodyParts":["BACK"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["LATISSIMUS DORSI"],"secondaryMuscles":["BICEPS BRACHII","TERES MAJOR"]},
            {"exerciseId":"ex007","name":"Barbell Row","imageUrl":f"{IMG}/YfCTLiECo2.jpg","bodyParts":["BACK"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["LATISSIMUS DORSI"],"secondaryMuscles":["RHOMBOIDS","BICEPS BRACHII"]},
            {"exerciseId":"ex008","name":"Seated Cable Row","imageUrl":f"{IMG}/bAEQLWIqH4.jpg","bodyParts":["BACK"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["LATISSIMUS DORSI","RHOMBOIDS"],"secondaryMuscles":["BICEPS BRACHII","POSTERIOR DELTOID"]},
            # SHOULDERS
            {"exerciseId":"ex009","name":"Overhead Press","imageUrl":f"{IMG}/AcGb20UoJg.jpg","bodyParts":["SHOULDERS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["ANTERIOR DELTOID"],"secondaryMuscles":["TRICEPS BRACHII","TRAPEZIUS"]},
            {"exerciseId":"ex010","name":"Dumbbell Lateral Raise","imageUrl":f"{IMG}/sGKkXKxdYy.jpg","bodyParts":["SHOULDERS"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["LATERAL DELTOID"],"secondaryMuscles":["ANTERIOR DELTOID","TRAPEZIUS UPPER FIBERS"]},
            {"exerciseId":"ex011","name":"Face Pull","imageUrl":f"{IMG}/EsVOYBdhDN.jpg","bodyParts":["SHOULDERS"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["POSTERIOR DELTOID"],"secondaryMuscles":["RHOMBOIDS","TRAPEZIUS"]},
            # BICEPS
            {"exerciseId":"ex012","name":"Barbell Curl","imageUrl":f"{IMG}/RB7NBcf79I.jpg","bodyParts":["BICEPS","UPPER ARMS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["BICEPS BRACHII"],"secondaryMuscles":["BRACHIALIS","BRACHIORADIALIS"]},
            {"exerciseId":"ex013","name":"Dumbbell Hammer Curl","imageUrl":f"{IMG}/9fW96RFqRZ.jpg","bodyParts":["BICEPS","UPPER ARMS"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["BRACHIALIS"],"secondaryMuscles":["BICEPS BRACHII","BRACHIORADIALIS"]},
            {"exerciseId":"ex014","name":"Concentration Curl","imageUrl":f"{IMG}/MruSDlnk0M.jpg","bodyParts":["BICEPS","UPPER ARMS"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["BICEPS BRACHII"],"secondaryMuscles":["BRACHIALIS"]},
            # TRICEPS
            {"exerciseId":"ex015","name":"Triceps Dip","imageUrl":f"{IMG}/qkXo99D6UI.jpg","bodyParts":["TRICEPS","UPPER ARMS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["TRICEPS BRACHII"],"secondaryMuscles":["PECTORALIS MAJOR","ANTERIOR DELTOID"]},
            {"exerciseId":"ex016","name":"Triceps Pushdown","imageUrl":f"{IMG}/AwDLoYPc84.jpg","bodyParts":["TRICEPS","UPPER ARMS"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["TRICEPS BRACHII"],"secondaryMuscles":[]},
            {"exerciseId":"ex017","name":"Skull Crusher","imageUrl":f"{IMG}/YfCTLiECo2.jpg","bodyParts":["TRICEPS","UPPER ARMS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["TRICEPS BRACHII"],"secondaryMuscles":[]},
            # QUADRICEPS / THIGHS
            {"exerciseId":"ex018","name":"Squat","imageUrl":f"{IMG}/bAEQLWIqH4.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["GLUTEUS MAXIMUS","HAMSTRINGS","ADDUCTOR MAGNUS"]},
            {"exerciseId":"ex019","name":"Leg Press","imageUrl":f"{IMG}/AcGb20UoJg.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["MACHINE"],"exerciseType":"STRENGTH","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["GLUTEUS MAXIMUS","HAMSTRINGS"]},
            {"exerciseId":"ex020","name":"Lunge","imageUrl":f"{IMG}/sGKkXKxdYy.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["GLUTEUS MAXIMUS","HAMSTRINGS"]},
            {"exerciseId":"ex021","name":"Jump Squat","imageUrl":f"{IMG}/EsVOYBdhDN.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["QUADRICEPS","GLUTEUS MAXIMUS"],"secondaryMuscles":["SOLEUS","ADDUCTOR MAGNUS"]},
            {"exerciseId":"ex022","name":"Bulgarian Split Squat","imageUrl":f"{IMG}/RB7NBcf79I.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["GLUTEUS MAXIMUS","ADDUCTOR MAGNUS"]},
            # BACK / WAIST
            {"exerciseId":"ex023","name":"Plank","imageUrl":f"{IMG}/9fW96RFqRZ.jpg","bodyParts":["WAIST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["RECTUS ABDOMINIS"],"secondaryMuscles":["OBLIQUES","TRANSVERSUS ABDOMINIS"]},
            {"exerciseId":"ex024","name":"Crunch","imageUrl":f"{IMG}/MruSDlnk0M.jpg","bodyParts":["WAIST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["RECTUS ABDOMINIS"],"secondaryMuscles":["OBLIQUES"]},
            {"exerciseId":"ex025","name":"Russian Twist","imageUrl":f"{IMG}/qkXo99D6UI.jpg","bodyParts":["WAIST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["OBLIQUES"],"secondaryMuscles":["RECTUS ABDOMINIS"]},
            {"exerciseId":"ex026","name":"Mountain Climber","imageUrl":f"{IMG}/AwDLoYPc84.jpg","bodyParts":["WAIST"],"equipments":["BODY WEIGHT"],"exerciseType":"CARDIO","targetMuscles":["OBLIQUES"],"secondaryMuscles":["QUADRICEPS","RECTUS ABDOMINIS"]},
            {"exerciseId":"ex027","name":"Cable Crunch","imageUrl":f"{IMG}/YfCTLiECo2.jpg","bodyParts":["WAIST"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["RECTUS ABDOMINIS"],"secondaryMuscles":["OBLIQUES"]},
            # CALVES
            {"exerciseId":"ex028","name":"Standing Calf Raise","imageUrl":f"{IMG}/bAEQLWIqH4.jpg","bodyParts":["CALVES"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["GASTROCNEMIUS"],"secondaryMuscles":["SOLEUS"]},
            {"exerciseId":"ex029","name":"Seated Calf Raise","imageUrl":f"{IMG}/AcGb20UoJg.jpg","bodyParts":["CALVES"],"equipments":["MACHINE"],"exerciseType":"STRENGTH","targetMuscles":["SOLEUS"],"secondaryMuscles":["GASTROCNEMIUS"]},
            # HIPS / GLUTES
            {"exerciseId":"ex030","name":"Hip Thrust","imageUrl":f"{IMG}/sGKkXKxdYy.jpg","bodyParts":["HIPS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["GLUTEUS MAXIMUS"],"secondaryMuscles":["HAMSTRINGS","ADDUCTOR MAGNUS"]},
            {"exerciseId":"ex031","name":"Glute Bridge","imageUrl":f"{IMG}/EsVOYBdhDN.jpg","bodyParts":["HIPS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["GLUTEUS MAXIMUS"],"secondaryMuscles":["HAMSTRINGS","ERECTOR SPINAE"]},
            {"exerciseId":"ex032","name":"Cable Kickback","imageUrl":f"{IMG}/RB7NBcf79I.jpg","bodyParts":["HIPS"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["GLUTEUS MAXIMUS"],"secondaryMuscles":["HAMSTRINGS"]},
            # CARDIO
            {"exerciseId":"ex033","name":"Burpee","imageUrl":f"{IMG}/9fW96RFqRZ.jpg","bodyParts":["CHEST","WAIST","QUADRICEPS"],"equipments":["BODY WEIGHT"],"exerciseType":"CARDIO","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["RECTUS ABDOMINIS","PECTORALIS MAJOR"]},
            {"exerciseId":"ex034","name":"Jumping Jack","imageUrl":f"{IMG}/MruSDlnk0M.jpg","bodyParts":["QUADRICEPS","SHOULDERS"],"equipments":["BODY WEIGHT"],"exerciseType":"CARDIO","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["ANTERIOR DELTOID","LATERAL DELTOID"]},
            {"exerciseId":"ex035","name":"Box Jump","imageUrl":f"{IMG}/qkXo99D6UI.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["BODY WEIGHT"],"exerciseType":"CARDIO","targetMuscles":["GLUTEUS MAXIMUS","QUADRICEPS"],"secondaryMuscles":["HAMSTRINGS","SOLEUS"]},
            {"exerciseId":"ex036","name":"Rowing Machine","imageUrl":f"{IMG}/AwDLoYPc84.jpg","bodyParts":["BACK","SHOULDERS"],"equipments":["MACHINE"],"exerciseType":"CARDIO","targetMuscles":["LATISSIMUS DORSI"],"secondaryMuscles":["TRAPEZIUS","BICEPS BRACHII","ERECTOR SPINAE"]},
            # STRETCHING
            {"exerciseId":"ex037","name":"Downward Dog","imageUrl":f"{IMG}/YfCTLiECo2.jpg","bodyParts":["BACK","CALVES"],"equipments":["BODY WEIGHT"],"exerciseType":"STRETCHING","targetMuscles":["HAMSTRINGS"],"secondaryMuscles":["GASTROCNEMIUS","ERECTOR SPINAE"]},
            {"exerciseId":"ex038","name":"Pigeon Pose","imageUrl":f"{IMG}/bAEQLWIqH4.jpg","bodyParts":["HIPS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRETCHING","targetMuscles":["GLUTEUS MAXIMUS"],"secondaryMuscles":["ILIOPSOAS","PIRIFORMIS"]},
            {"exerciseId":"ex039","name":"Standing Quad Stretch","imageUrl":f"{IMG}/AcGb20UoJg.jpg","bodyParts":["QUADRICEPS","THIGHS"],"equipments":["BODY WEIGHT"],"exerciseType":"STRETCHING","targetMuscles":["QUADRICEPS"],"secondaryMuscles":["ILIOPSOAS"]},
            {"exerciseId":"ex040","name":"Child's Pose","imageUrl":f"{IMG}/sGKkXKxdYy.jpg","bodyParts":["BACK","WAIST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRETCHING","targetMuscles":["ERECTOR SPINAE"],"secondaryMuscles":["GLUTEUS MAXIMUS","LATISSIMUS DORSI"]},
            # LOWER ARMS
            {"exerciseId":"ex041","name":"Wrist Curl","imageUrl":f"{IMG}/EsVOYBdhDN.jpg","bodyParts":["LOWER ARMS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["FLEXORS WRIST"],"secondaryMuscles":[]},
            {"exerciseId":"ex042","name":"Reverse Wrist Curl","imageUrl":f"{IMG}/RB7NBcf79I.jpg","bodyParts":["LOWER ARMS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["EXTENSORS WRIST"],"secondaryMuscles":[]},
            # NECK
            {"exerciseId":"ex043","name":"Neck Flexion Stretch","imageUrl":f"{IMG}/9fW96RFqRZ.jpg","bodyParts":["NECK"],"equipments":["BODY WEIGHT"],"exerciseType":"STRETCHING","targetMuscles":["STERNOCLEIDOMASTOID"],"secondaryMuscles":["SCALENES"]},
            # UPPER LEGS (Hamstrings)
            {"exerciseId":"ex044","name":"Romanian Deadlift","imageUrl":f"{IMG}/MruSDlnk0M.jpg","bodyParts":["UPPER LEGS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["HAMSTRINGS"],"secondaryMuscles":["GLUTEUS MAXIMUS","ERECTOR SPINAE"]},
            {"exerciseId":"ex045","name":"Leg Curl","imageUrl":f"{IMG}/qkXo99D6UI.jpg","bodyParts":["UPPER LEGS"],"equipments":["MACHINE"],"exerciseType":"STRENGTH","targetMuscles":["HAMSTRINGS"],"secondaryMuscles":["GASTROCNEMIUS"]},
            {"exerciseId":"ex046","name":"Good Morning","imageUrl":f"{IMG}/AwDLoYPc84.jpg","bodyParts":["UPPER LEGS","BACK"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["HAMSTRINGS"],"secondaryMuscles":["ERECTOR SPINAE","GLUTEUS MAXIMUS"]},
            # SHOULDERS extra
            {"exerciseId":"ex047","name":"Arnold Press","imageUrl":f"{IMG}/YfCTLiECo2.jpg","bodyParts":["SHOULDERS"],"equipments":["DUMBBELL"],"exerciseType":"STRENGTH","targetMuscles":["ANTERIOR DELTOID"],"secondaryMuscles":["LATERAL DELTOID","TRICEPS BRACHII"]},
            {"exerciseId":"ex048","name":"Upright Row","imageUrl":f"{IMG}/bAEQLWIqH4.jpg","bodyParts":["SHOULDERS"],"equipments":["BARBELL"],"exerciseType":"STRENGTH","targetMuscles":["LATERAL DELTOID"],"secondaryMuscles":["TRAPEZIUS UPPER FIBERS","BICEPS BRACHII"]},
            # CHEST extra
            {"exerciseId":"ex049","name":"Cable Crossover","imageUrl":f"{IMG}/AcGb20UoJg.jpg","bodyParts":["CHEST"],"equipments":["CABLE"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR"],"secondaryMuscles":["ANTERIOR DELTOID"]},
            {"exerciseId":"ex050","name":"Chest Dip","imageUrl":f"{IMG}/sGKkXKxdYy.jpg","bodyParts":["CHEST"],"equipments":["BODY WEIGHT"],"exerciseType":"STRENGTH","targetMuscles":["PECTORALIS MAJOR STERNAL HEAD"],"secondaryMuscles":["TRICEPS BRACHII","ANTERIOR DELTOID"]},
        ]

        payload = json.dumps({
            "success": True,
            "meta": {"total": len(exercises), "hasNextPage": False, "hasPreviousPage": False, "nextCursor": None},
            "data": exercises
        })
        db.add(ExerciseCache(
            cache_key="/exercises?limit=20",
            payload=payload,
            created_at=datetime.utcnow()
        ))
        db.commit()
    finally:
        db.close()


def seed_food_catalog():
    """Charge le catalogue alimentaire (651 items) depuis le CSV Kaggle."""

    def _safe_int(val, default=None):
        try:
            return int(float(val)) if val and str(val).strip() else default
        except (ValueError, TypeError):
            return default

    def _safe_float(val, default=None):
        try:
            return float(val) if val and str(val).strip() else default
        except (ValueError, TypeError):
            return default

    db: Session = SessionLocal()
    try:
        if db.query(Food).count() >= 100:
            return
        if not os.path.exists(_FOOD_CSV):
            print("[seed] daily_food_nutrition.csv introuvable – catalogue ignoré")
            return
        inserted = 0
        with open(_FOOD_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.add(Food(
                    name=row.get("Food_Item", "").strip(),
                    category=row.get("Category", "").strip() or None,
                    calories_kcal=_safe_int(row.get("Calories (kcal)")),
                    protein_g=_safe_float(row.get("Protein (g)")),
                    carbs_g=_safe_float(row.get("Carbohydrates (g)")),
                    fat_g=_safe_float(row.get("Fat (g)")),
                    fiber_g=_safe_float(row.get("Fiber (g)")),
                    sugars_g=_safe_float(row.get("Sugars (g)")),
                    sodium_mg=_safe_float(row.get("Sodium (mg)")),
                    cholesterol_mg=_safe_float(row.get("Cholesterol (mg)")),
                    meal_type=row.get("Meal_Type", "").strip() or None,
                    water_intake_ml=_safe_int(row.get("Water_Intake (ml)")),
                ))
                inserted += 1
        db.commit()
        print(f"[seed] Catalogue alimentaire : {inserted} items insérés")
    finally:
        db.close()


def seed_fitness_update():
    """Enrichit DailyData et WeeklyData des patients existants avec les vraies
    métriques du dataset fitness (BPM, calories, workout type, fat%, BMI…)."""
    db: Session = SessionLocal()
    try:
        # Déjà appliqué si le premier daily_data a un max_bpm non nul
        first = db.query(DailyData).first()
        if first and first.max_bpm is not None:
            return
        if not os.path.exists(_FITNESS_CSV):
            print("[seed] fitness_tracker.csv introuvable – enrichissement ignoré")
            return

        with open(_FITNESS_CSV, newline="", encoding="utf-8") as f:
            fitness_rows = list(csv.DictReader(f))

        if not fitness_rows:
            return

        utilisateurs = db.query(Utilisateur).all()
        n_fit = len(fitness_rows)
        updated = 0

        for idx, u in enumerate(utilisateurs):
            row = fitness_rows[idx % n_fit]

            def _fi(col, default=None):
                try:
                    v = row.get(col, "")
                    return float(v) if v and str(v).strip() else default
                except (ValueError, TypeError):
                    return default

            if u.daily_data_id:
                dd = db.query(DailyData).filter(DailyData.id == u.daily_data_id).first()
                if dd:
                    dd.max_bpm = int(_fi("Max_BPM") or 0) or dd.max_bpm
                    dd.avg_bpm = int(_fi("Avg_BPM") or 0) or dd.avg_bpm
                    dd.resting_bpm = int(_fi("Resting_BPM") or 0) or dd.resting_bpm
                    dd.exercise_hours = round(_fi("Session_Duration (hours)") or 0) or dd.exercise_hours
                    dd.calories_burned = int(_fi("Calories_Burned") or 0) or dd.calories_burned
                    wt = row.get("Workout_Type", "").strip()
                    if wt:
                        dd.workout_type = wt

            if u.weekly_data_id:
                wd = db.query(WeeklyData).filter(WeeklyData.id == u.weekly_data_id).first()
                if wd:
                    w = _fi("Weight (kg)")
                    if w:
                        wd.weight = round(w, 1)
                    fp = _fi("Fat_Percentage")
                    if fp:
                        wd.fat_percentage = round(fp, 1)
                    bmi = _fi("BMI")
                    if bmi:
                        wd.bmi = round(bmi, 1)
                    wf = _fi("Workout_Frequency (days/week)")
                    if wf:
                        wd.workout_frequency = int(wf)

            if u.health_data_id:
                hd = db.query(HealthData).filter(HealthData.id == u.health_data_id).first()
                if hd:
                    el = _fi("Experience_Level")
                    if el:
                        hd.experience_level = int(el)

            if u.nutrition_id:
                hn = db.query(HealthNutrition).filter(HealthNutrition.id == u.nutrition_id).first()
                if hn:
                    wi = _fi("Water_Intake (liters)")
                    if wi:
                        hn.water_intake = round(wi, 1)

            updated += 1
            if updated % 100 == 0:
                db.commit()

        db.commit()
        print(f"[seed] Fitness update : {updated} patients enrichis")
    finally:
        db.close()
