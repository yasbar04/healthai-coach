"""Tests for ML model training and prediction endpoints."""

import os
import pathlib
import pytest


DATA_DIR = pathlib.Path(__file__).parent.parent / "app" / "data"


def test_fitness_csv_exists():
    assert (DATA_DIR / "fitness_tracker.csv").exists(), "fitness_tracker.csv manquant"


def test_diet_csv_exists():
    assert (DATA_DIR / "diet_recommendations.csv").exists(), "diet_recommendations.csv manquant"


def test_train_fitness_model():
    from app.ml.train import train_fitness_model
    metrics = train_fitness_model(verbose=False)
    assert "workout_type_classifier" in metrics
    assert "calories_regressor" in metrics
    clf = metrics["workout_type_classifier"]
    # Données synthétiques sans signal fort — on vérifie la structure, pas l'accuracy absolue
    assert 0 <= clf["accuracy"] <= 1
    assert "f1_macro" in clf
    assert "precision_macro" in clf
    assert "recall_macro" in clf
    assert "classes" in clf
    reg = metrics["calories_regressor"]
    assert "mae" in reg
    assert "rmse" in reg
    assert "r2" in reg


def test_train_diet_model():
    from app.ml.train import train_diet_model
    metrics = train_diet_model(verbose=False)
    assert "accuracy" in metrics
    assert 0 <= metrics["accuracy"] <= 1
    assert "f1_macro" in metrics
    assert "precision_macro" in metrics
    assert "recall_macro" in metrics
    assert "classes" in metrics


def test_predict_workout_type():
    from app.ml.train import train_fitness_model
    train_fitness_model(verbose=False)
    from app.ml.predict import _fitness_clf_cache
    import app.ml.predict as pred_module
    pred_module._fitness_clf_cache = None  # force reload

    result = pred_module.predict_workout_type(
        age=28, weight_kg=75, height_m=1.78,
        max_bpm=180, avg_bpm=150, resting_bpm=60,
        session_duration_h=1.0, fat_percentage=18.0,
        water_intake_l=2.5, workout_frequency=4.0,
        experience_level=2.0, bmi=23.7, gender="Male",
    )
    assert "predicted_workout_type" in result
    assert "confidence" in result
    assert result["confidence"] > 0


def test_predict_calories():
    from app.ml.train import train_fitness_model
    train_fitness_model(verbose=False)
    import app.ml.predict as pred_module
    pred_module._fitness_reg_cache = None

    result = pred_module.predict_calories_burned(
        age=28, weight_kg=75, height_m=1.78,
        max_bpm=180, avg_bpm=150, resting_bpm=60,
        session_duration_h=1.0, fat_percentage=18.0,
        water_intake_l=2.5, workout_frequency=4.0,
        experience_level=2.0, bmi=23.7, gender="Male",
    )
    assert "predicted_calories_burned" in result
    assert result["predicted_calories_burned"] > 0


def test_predict_diet():
    from app.ml.train import train_diet_model
    train_diet_model(verbose=False)
    import app.ml.predict as pred_module
    pred_module._diet_clf_cache = None

    result = pred_module.predict_diet_recommendation(
        age=45, weight_kg=82, height_cm=175, bmi=26.8,
        daily_caloric_intake=2200, weekly_exercise_hours=3.5,
        adherence_to_diet_plan=75.0, dietary_nutrient_imbalance_score=2.0,
        gender="Male", disease_type="Diabetes", severity="Mild",
        physical_activity_level="Moderate",
    )
    assert "predicted_diet" in result
    assert "confidence" in result


def test_ml_status_endpoint(client, auth_headers):
    resp = client.get("/ml/status")
    assert resp.status_code == 200
    assert "models_trained" in resp.json()


def test_ml_metrics_endpoint_after_training(client, auth_headers):
    from app.ml.train import train_all
    train_all(verbose=False)
    resp = client.get("/ml/metrics", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "fitness" in data
    assert "diet" in data
