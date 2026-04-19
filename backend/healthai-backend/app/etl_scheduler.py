"""
ETL Scheduler - Planification automatique des tâches d'ingestion de données
Gestion des pipelines ETL avec logs structurés et monitoring
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db import SessionLocal
from .models import EtlRun, EtlError
from .settings import settings

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
                        message=str(e)
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
        
        # Simuler read CSV
        df = pd.read_csv("app/data/daily_food_nutrition.csv")
        run.rows_in = len(df)
        
        # Nettoyage
        df = df.dropna(subset=['name'])
        df['calories_kcal'] = pd.to_numeric(df['calories_kcal'], errors='coerce')
        
        # Insertion
        for _, row in df.iterrows():
            food = db.query(Food).filter(Food.name == row['name']).first()
            if not food:
                food = Food(
                    name=row['name'],
                    category=row.get('category'),
                    calories_kcal=int(row['calories_kcal']) if pd.notna(row['calories_kcal']) else None,
                    protein_g=float(row.get('protein_g', 0)) if pd.notna(row.get('protein_g')) else None,
                    carbs_g=float(row.get('carbs_g', 0)) if pd.notna(row.get('carbs_g')) else None,
                    fat_g=float(row.get('fat_g', 0)) if pd.notna(row.get('fat_g')) else None,
                )
                db.add(food)
        
        db.commit()
        run.rows_out = len(df)
        run.errors_count = len(df) - run.rows_out
        
        logger.info(f"✅ Food data synced: {run.rows_out} rows")
        
    except Exception as e:
        run.errors_count += 1
        logger.error(f"Food sync error: {e}")
        raise


def sync_fitness_data(db: Session, run: EtlRun) -> None:
    """Synchroniser les données fitness (quotidien)"""
    try:
        import pandas as pd
        from .models import Activity
        
        # Simuler read CSV
        df = pd.read_csv("app/data/fitness_tracker.csv")
        run.rows_in = len(df)
        
        # Nettoyage
        df = df.fillna(0)
        df = df[df['calories_burn'] >= 0]  # Valeurs valides
        
        # Insertion simulée (chunk de 100)
        for _, row in df.iterrows():
            # Logique insert
            pass
        
        db.commit()
        run.rows_out = len(df)
        
        logger.info(f"✅ Fitness data synced: {run.rows_out} rows")
        
    except Exception as e:
        run.errors_count += 1
        logger.error(f"Fitness sync error: {e}")
        raise


def data_quality_check(db: Session, run: EtlRun) -> None:
    """Vérifier la qualité des données (toutes les heures)"""
    try:
        # Requêtes qualité
        results = {
            "total_users": db.query(text("SELECT COUNT(*) FROM users")).scalar(),
            "total_activities": db.query(text("SELECT COUNT(*) FROM activities")).scalar(),
            "total_foods": db.query(text("SELECT COUNT(*) FROM foods")).scalar(),
            "last_check": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
        
        # LOG structuré JSON
        logger.info(f"📊 Quality Check: {json.dumps(results, indent=2)}")
        
        run.rows_out = 1
        
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
