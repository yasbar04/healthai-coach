"""
ETL Scheduler - Planification automatique des tâches d'ingestion de données
Gestion des pipelines ETL avec logs structurés et monitoring
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import EtlRun, EtlError
from .settings import settings

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Configuration logging structuré
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLScheduler:
    """Gestionnaire de planification ETL avec monitoring"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        
    def register_job(
        self,
        job_id: str,
        func: Callable,
        trigger: str = "cron",
        **trigger_args
    ) -> None:
        """
        Enregistrer une tâche ETL
        
        Args:
            job_id: Identifiant unique
            func: Fonction à exécuter
            trigger: Type de trigger (cron, interval)
            **trigger_args: Arguments du trigger
        """
        wrapped_func = self._wrap_job(job_id, func)
        job = self.scheduler.add_job(
            wrapped_func,
            trigger,
            id=job_id,
            **trigger_args
        )
        self.jobs[job_id] = {
            "job": job,
            "func": func,
            "trigger": trigger,
            "trigger_args": trigger_args,
            "status": "registered"
        }
        logger.info(f"✅ ETL Job registered: {job_id}")
        
    def _wrap_job(self, job_id: str, func: Callable) -> Callable:
        """Wrapper pour capturer logs et erreurs"""
        def wrapped():
            db = SessionLocal()
            try:
                # Créer run ETL
                run = EtlRun(
                    source_name=job_id,
                    status="running",
                    started_at=datetime.utcnow(),
                    rows_in=0,
                    rows_out=0,
                    errors_count=0
                )
                db.add(run)
                db.commit()
                
                logger.info(f"🚀 Starting ETL: {job_id}")
                
                # Exécuter fonction
                result = func(db, run)
                
                # Mettre à jour statut
                run.status = "success"
                run.ended_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"✅ ETL completed: {job_id} - "
                          f"in={run.rows_in}, out={run.rows_out}, "
                          f"errors={run.errors_count}")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ ETL failed: {job_id} - {str(e)}")
                
                # Enregistrer erreur
                if 'run' in locals():
                    run.status = "failed"
                    run.ended_at = datetime.utcnow()
                    
                    error = EtlError(
                        run_id=run.id,
                        severity="critical",
                        row_reference="",
                        message=str(e),
                        created_at=datetime.utcnow()
                    )
                    db.add(error)
                    db.commit()
                
                raise
            finally:
                db.close()
        
        return wrapped
    
    def start(self) -> None:
        """Démarrer le scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ ETL Scheduler started")
    
    def stop(self) -> None:
        """Arrêter le scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⏹️ ETL Scheduler stopped")
    
    def get_jobs_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtenir statut de tous les jobs"""
        return {
            job_id: {
                "status": data["status"],
                "trigger": data["trigger"],
                "next_run": str(data["job"].next_run_time) if data["job"].next_run_time else None
            }
            for job_id, data in self.jobs.items()
        }


# Instance globale
etl_scheduler = ETLScheduler()


# =============================================================================
# TÂCHES ETL PLANIFIÉES
# =============================================================================

def sync_food_data(db: Session, run: EtlRun) -> None:
    """Synchroniser les données alimentaires (quotidien)"""
    try:
        import pandas as pd
        from .models import Food

        df = pd.read_csv(os.path.join(DATA_DIR, "daily_food_nutrition.csv"), on_bad_lines='skip')
        run.rows_in = len(df)

        df = df.dropna(subset=['Food_Item'])
        df['Calories (kcal)'] = pd.to_numeric(df['Calories (kcal)'], errors='coerce')

        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            name = str(row['Food_Item']).strip()
            if not name:
                skipped += 1
                continue
            existing = db.query(Food).filter(Food.name == name).first()
            if not existing:
                db.add(Food(
                    name=name,
                    category=row.get('Category') if pd.notna(row.get('Category')) else None,
                    calories_kcal=int(row['Calories (kcal)']) if pd.notna(row['Calories (kcal)']) else None,
                    protein_g=float(row['Protein (g)']) if pd.notna(row.get('Protein (g)')) else None,
                    carbs_g=float(row['Carbohydrates (g)']) if pd.notna(row.get('Carbohydrates (g)')) else None,
                    fat_g=float(row['Fat (g)']) if pd.notna(row.get('Fat (g)')) else None,
                    fiber_g=float(row['Fiber (g)']) if pd.notna(row.get('Fiber (g)')) else None,
                    sugars_g=float(row['Sugars (g)']) if pd.notna(row.get('Sugars (g)')) else None,
                    sodium_mg=float(row['Sodium (mg)']) if pd.notna(row.get('Sodium (mg)')) else None,
                    cholesterol_mg=float(row['Cholesterol (mg)']) if pd.notna(row.get('Cholesterol (mg)')) else None,
                    meal_type=row.get('Meal_Type') if pd.notna(row.get('Meal_Type')) else None,
                    water_intake_ml=int(row['Water_Intake (ml)']) if pd.notna(row.get('Water_Intake (ml)')) else None,
                ))
                inserted += 1

        db.commit()
        run.rows_out = inserted
        run.errors_count = skipped

        logger.info(f"✅ Food data synced: {inserted} inserted, {skipped} skipped")

    except Exception as e:
        run.errors_count += 1
        logger.error(f"Food sync error: {e}")
        raise


def sync_fitness_data(db: Session, run: EtlRun) -> None:
    """Synchroniser les données fitness (quotidien)"""
    try:
        import pandas as pd
        from .models import DailyData, WeeklyData

        df = pd.read_csv(os.path.join(DATA_DIR, "fitness_tracker.csv"), on_bad_lines='skip')
        # Nettoyer les éventuels espaces/tabs dans les colonnes numériques
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].astype(str).str.strip()
        df = pd.to_numeric(df.stack(), errors='coerce').unstack() if False else df
        for col in ['Max_BPM', 'Avg_BPM', 'Resting_BPM', 'Calories_Burned',
                    'Session_Duration (hours)', 'Workout_Frequency (days/week)',
                    'Weight (kg)', 'Fat_Percentage', 'BMI']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        run.rows_in = len(df)
        df = df[df['Calories_Burned'].fillna(0) >= 0]

        inserted = 0
        for _, row in df.iterrows():
            daily = DailyData(
                max_bpm=int(row['Max_BPM']) if pd.notna(row['Max_BPM']) else None,
                resting_bpm=int(row['Resting_BPM']) if pd.notna(row['Resting_BPM']) else None,
                avg_bpm=int(row['Avg_BPM']) if pd.notna(row['Avg_BPM']) else None,
                exercise_hours=int(row['Session_Duration (hours)']) if pd.notna(row['Session_Duration (hours)']) else None,
                calories_burned=int(row['Calories_Burned']) if pd.notna(row['Calories_Burned']) else None,
                workout_type=str(row['Workout_Type']).strip() if pd.notna(row.get('Workout_Type')) else None,
            )
            db.add(daily)
            db.flush()

            weekly = WeeklyData(
                weight=float(row['Weight (kg)']) if pd.notna(row['Weight (kg)']) else None,
                workout_frequency=int(row['Workout_Frequency (days/week)']) if pd.notna(row['Workout_Frequency (days/week)']) else None,
                fat_percentage=float(row['Fat_Percentage']) if pd.notna(row['Fat_Percentage']) else None,
                bmi=float(row['BMI']) if pd.notna(row['BMI']) else None,
            )
            db.add(weekly)
            inserted += 1

        db.commit()
        run.rows_out = inserted

        logger.info(f"✅ Fitness data synced: {inserted} rows")

    except Exception as e:
        run.errors_count += 1
        logger.error(f"Fitness sync error: {e}")
        raise


def data_quality_check(db: Session, run: EtlRun) -> None:
    """Vérifier la qualité des données (toutes les heures)"""
    try:
        from .models import User, Activity, Food, DailyData, WeeklyData

        total_users = db.query(User).count()
        total_activities = db.query(Activity).count()
        total_foods = db.query(Food).count()
        total_daily = db.query(DailyData).count()
        total_weekly = db.query(WeeklyData).count()

        issues = []
        if total_foods == 0:
            issues.append("foods table is empty")
        if total_daily == 0:
            issues.append("daily_data table is empty")

        status = "healthy" if not issues else "degraded"
        results = {
            "total_users": total_users,
            "total_activities": total_activities,
            "total_foods": total_foods,
            "total_daily_data": total_daily,
            "total_weekly_data": total_weekly,
            "issues": issues,
            "status": status,
        }

        logger.info(f"📊 Quality Check: {json.dumps(results, indent=2)}")

        run.rows_in = total_users + total_activities + total_foods
        run.rows_out = 1
        if issues:
            run.errors_count = len(issues)

    except Exception as e:
        run.errors_count += 1
        logger.error(f"Quality check error: {e}")
        raise


# =============================================================================
# ENREGISTREMENT DES JOBS PLANIFIÉS
# =============================================================================

def setup_etl_jobs() -> None:
    """Configurer les tâches ETL planifiées"""
    
    # Sync aliments quotidien (00h30)
    etl_scheduler.register_job(
        "sync_food_data",
        sync_food_data,
        trigger="cron",
        hour=0,
        minute=30
    )
    
    # Sync fitness quotidien (01h00)
    etl_scheduler.register_job(
        "sync_fitness_data",
        sync_fitness_data,
        trigger="cron",
        hour=1,
        minute=0
    )
    
    # Vérification qualité toutes les heures
    etl_scheduler.register_job(
        "data_quality_check",
        data_quality_check,
        trigger="interval",
        hours=1
    )
    
    logger.info("✅ ETL jobs configured")
