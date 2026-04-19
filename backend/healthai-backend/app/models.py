from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="freemium")  # freemium|premium|premium_plus|b2b
    role = Column(String(50), nullable=False, default="user")  # user|admin
    created_at = Column(DateTime, default=datetime.utcnow)

    activities = relationship("Activity", back_populates="user")
    nutrition_logs = relationship("NutritionLog", back_populates="user")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_date = Column(Date, nullable=False)
    steps = Column(Integer, nullable=True)
    active_minutes = Column(Integer, nullable=True)
    calories_out = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    workout_type = Column(String(50), nullable=True)   # Cardio, Strength, Yoga…
    sleep_hours = Column(Float, nullable=True)
    water_ml = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)

    user = relationship("User", back_populates="activities")

class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), nullable=True)
    calories_kcal = Column(Integer, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sugars_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)
    meal_type = Column(String(50), nullable=True)
    water_intake_ml = Column(Integer, nullable=True)

class NutritionLog(Base):
    __tablename__ = "nutrition_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    grams = Column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="nutrition_logs")
    food = relationship("Food")

class Biometrics(Base):
    __tablename__ = "biometrics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    measured_at = Column(DateTime, nullable=False)
    heart_rate_bpm = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

class EtlRun(Base):
    __tablename__ = "etl_runs"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)  # success|partial|failed
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    rows_in = Column(Integer, nullable=False, default=0)
    rows_out = Column(Integer, nullable=False, default=0)
    errors_count = Column(Integer, nullable=False, default=0)

class EtlError(Base):
    __tablename__ = "etl_errors"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("etl_runs.id"), nullable=False)
    severity = Column(String(10), nullable=False)  # info|warn|error
    row_reference = Column(String(80), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(30), nullable=False)  # nutrition|sport
    preferred_slot = Column(String(40), nullable=True)
    status = Column(String(20), nullable=False, default="requested")
    created_at = Column(DateTime, default=datetime.utcnow)

# ── BDD HealthAI — tables du schéma métier ──────────────────────────────────

class HealthData(Base):
    """Données médicales et sanitaires (table Data du schéma SQL)."""
    __tablename__ = "health_data"
    id = Column(Integer, primary_key=True, index=True)
    experience_level = Column(Integer, nullable=True)
    disease_type = Column(String(50), nullable=True)
    severity = Column(String(50), nullable=True)
    physical_activity_level = Column(String(50), nullable=True)
    cholesterol_mg_dl = Column(Float, nullable=True)
    blood_pressure_mmhg = Column(Float, nullable=True)
    glucose_mg_dl = Column(Float, nullable=True)

    utilisateurs = relationship("Utilisateur", back_populates="health_data")


class HealthNutrition(Base):
    """Profil nutritionnel et préférences alimentaires (table Nutrition du schéma SQL)."""
    __tablename__ = "health_nutrition"
    id = Column(Integer, primary_key=True, index=True)
    meal_context = Column(String(50), nullable=True)
    adherence_to_diet_plan = Column(Float, nullable=True)
    preferred_cuisine = Column(String(50), nullable=True)
    water_intake = Column(Float, nullable=True)
    diet_recommendation = Column(String(50), nullable=True)
    dietary_restrictions = Column(String(50), nullable=True)
    dietary_nutrient_imbalance_score = Column(Float, nullable=True)
    allergies = Column(String(50), nullable=True)
    low_carb = Column(Boolean, nullable=True, default=False)
    low_sodium = Column(Boolean, nullable=True, default=False)
    balanced = Column(Boolean, nullable=True, default=False)

    utilisateurs = relationship("Utilisateur", back_populates="nutrition_profile")
    aliments = relationship("Aliment", back_populates="nutrition", foreign_keys="Aliment.nutrition_id")


class DailyData(Base):
    """Métriques quotidiennes d'activité (table Daily_Data du schéma SQL)."""
    __tablename__ = "daily_data"
    id = Column(Integer, primary_key=True, index=True)
    max_bpm = Column(Integer, nullable=True)
    resting_bpm = Column(Integer, nullable=True)
    avg_bpm = Column(Integer, nullable=True)
    exercise_hours = Column(Integer, nullable=True)
    calories_burned = Column(Integer, nullable=True)
    daily_caloric_intake = Column(Integer, nullable=True)
    workout_type = Column(String(50), nullable=True)

    utilisateurs = relationship("Utilisateur", back_populates="daily_data")


class WeeklyData(Base):
    """Métriques hebdomadaires de composition corporelle (table Weekly_Data du schéma SQL)."""
    __tablename__ = "weekly_data"
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float, nullable=True)
    workout_frequency = Column(Integer, nullable=True)
    fat_percentage = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)

    utilisateurs = relationship("Utilisateur", back_populates="weekly_data")


class B2BCompany(Base):
    """Entreprises partenaires (table B2B du schéma SQL)."""
    __tablename__ = "b2b_companies"
    id = Column(Integer, primary_key=True, index=True)
    name_entreprise = Column(String(50), nullable=False)

    utilisateurs = relationship("Utilisateur", back_populates="company")


class Utilisateur(Base):
    """Profil utilisateur métier étendu (table Utilisateur du schéma SQL)."""
    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    name = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("b2b_companies.id"), nullable=True)
    health_data_id = Column(Integer, ForeignKey("health_data.id"), nullable=True)
    nutrition_id = Column(Integer, ForeignKey("health_nutrition.id"), nullable=True)
    daily_data_id = Column(Integer, ForeignKey("daily_data.id"), nullable=True)
    weekly_data_id = Column(Integer, ForeignKey("weekly_data.id"), nullable=True)

    company = relationship("B2BCompany", back_populates="utilisateurs")
    health_data = relationship("HealthData", back_populates="utilisateurs")
    nutrition_profile = relationship("HealthNutrition", back_populates="utilisateurs")
    daily_data = relationship("DailyData", back_populates="utilisateurs")
    weekly_data = relationship("WeeklyData", back_populates="utilisateurs")
    abonnements = relationship("Abonnement", back_populates="utilisateur", foreign_keys="Abonnement.utilisateur_id")


class Abonnement(Base):
    """Plans d'abonnement (table Abonnement du schéma SQL)."""
    __tablename__ = "abonnements"
    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    name = Column(String(50), nullable=False)  # Freemium | Premium | Premium+
    price = Column(Float, nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="abonnements", foreign_keys=[utilisateur_id])


class Aliment(Base):
    """Catalogue des aliments (table Aliment du schéma SQL)."""
    __tablename__ = "aliments"
    id = Column(Integer, primary_key=True, index=True)
    nutrition_id = Column(Integer, ForeignKey("health_nutrition.id"), nullable=True)
    food_item = Column(String(50), nullable=False)
    calories = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    fiber = Column(Float, nullable=True)
    sugars = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    cholesterol = Column(Float, nullable=True)

    nutrition = relationship("HealthNutrition", back_populates="aliments", foreign_keys=[nutrition_id])


class ExerciseCache(Base):
    """Cache persistant pour les exercices ExerciseDB (évite les 429 rate-limit)."""
    __tablename__ = "exercise_cache"
    cache_key = Column(String(255), primary_key=True)
    payload = Column(Text, nullable=False)  # JSON sérialisé
    created_at = Column(DateTime, default=datetime.utcnow)
