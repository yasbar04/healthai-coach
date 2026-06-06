"""
Inference helpers — load pre-trained models and expose simple predict functions.
Models are loaded lazily on first call and cached in memory.
"""

import pathlib
import pickle
import json
from typing import Optional

import numpy as np

MODEL_DIR = pathlib.Path(__file__).parent / "models"

_fitness_clf_cache = None
_fitness_reg_cache = None
_diet_clf_cache = None


def _load_fitness_clf():
    global _fitness_clf_cache
    if _fitness_clf_cache is None:
        path = MODEL_DIR / "fitness_classifier.pkl"
        if not path.exists():
            raise FileNotFoundError("Fitness classifier not trained. Run app.ml.train first.")
        with open(path, "rb") as f:
            _fitness_clf_cache = pickle.load(f)
    return _fitness_clf_cache


def _load_fitness_reg():
    global _fitness_reg_cache
    if _fitness_reg_cache is None:
        path = MODEL_DIR / "fitness_regressor.pkl"
        if not path.exists():
            raise FileNotFoundError("Fitness regressor not trained. Run app.ml.train first.")
        with open(path, "rb") as f:
            _fitness_reg_cache = pickle.load(f)
    return _fitness_reg_cache


def _load_diet_clf():
    global _diet_clf_cache
    if _diet_clf_cache is None:
        path = MODEL_DIR / "diet_classifier.pkl"
        if not path.exists():
            raise FileNotFoundError("Diet classifier not trained. Run app.ml.train first.")
        with open(path, "rb") as f:
            _diet_clf_cache = pickle.load(f)
    return _diet_clf_cache


def predict_workout_type(
    age: float,
    weight_kg: float,
    height_m: float,
    max_bpm: float,
    avg_bpm: float,
    resting_bpm: float,
    session_duration_h: float,
    fat_percentage: float,
    water_intake_l: float,
    workout_frequency: float,
    experience_level: float,
    bmi: float,
    gender: str = "Male",
) -> dict:
    bundle = _load_fitness_clf()
    model = bundle["model"]
    le = bundle["label_encoder"]

    gender_enc = 1 if gender.lower() in ("female", "f", "femme") else 0
    features = np.array([[
        age, weight_kg, height_m, max_bpm, avg_bpm, resting_bpm,
        session_duration_h, fat_percentage, water_intake_l,
        workout_frequency, experience_level, bmi, gender_enc,
    ]])

    proba = model.predict_proba(features)[0]
    predicted_idx = int(np.argmax(proba))
    predicted_class = le.classes_[predicted_idx]

    return {
        "predicted_workout_type": predicted_class,
        "confidence": round(float(proba[predicted_idx]), 4),
        "probabilities": {
            cls: round(float(p), 4) for cls, p in zip(le.classes_, proba)
        },
    }


def predict_calories_burned(
    age: float,
    weight_kg: float,
    height_m: float,
    max_bpm: float,
    avg_bpm: float,
    resting_bpm: float,
    session_duration_h: float,
    fat_percentage: float,
    water_intake_l: float,
    workout_frequency: float,
    experience_level: float,
    bmi: float,
    gender: str = "Male",
    workout_type: Optional[str] = None,
) -> dict:
    bundle = _load_fitness_reg()
    model = bundle["model"]
    le = bundle.get("label_encoder")

    gender_enc = 1 if gender.lower() in ("female", "f", "femme") else 0

    # Encode workout_type if available, otherwise predict it first
    if workout_type and le is not None:
        try:
            wt_enc = int(le.transform([workout_type])[0])
        except ValueError:
            wt_enc = 0
    else:
        # Predict workout type first, then use it
        clf_bundle = _load_fitness_clf()
        base_features = np.array([[
            age, weight_kg, height_m, max_bpm, avg_bpm, resting_bpm,
            session_duration_h, fat_percentage, water_intake_l,
            workout_frequency, experience_level, bmi, gender_enc,
        ]])
        wt_enc = int(clf_bundle["model"].predict(base_features)[0])

    features = np.array([[
        age, weight_kg, height_m, max_bpm, avg_bpm, resting_bpm,
        session_duration_h, fat_percentage, water_intake_l,
        workout_frequency, experience_level, bmi, gender_enc, wt_enc,
    ]])

    predicted = float(model.predict(features)[0])
    return {"predicted_calories_burned": round(predicted, 1)}


def predict_diet_recommendation(
    age: float,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    daily_caloric_intake: float,
    weekly_exercise_hours: float,
    adherence_to_diet_plan: float,
    dietary_nutrient_imbalance_score: float,
    gender: str = "Male",
    disease_type: str = "None",
    severity: str = "Mild",
    physical_activity_level: str = "Moderate",
    cholesterol: Optional[float] = None,
    glucose: Optional[float] = None,
) -> dict:
    bundle = _load_diet_clf()
    model = bundle["model"]
    le_target = bundle["label_encoder"]
    feature_encoders = bundle["feature_encoders"]
    numeric_cols = bundle["numeric_cols"]
    optional_cols = bundle["optional_cols"]
    cat_cols = bundle["cat_cols"]

    numeric_values = [
        age, weight_kg, height_cm, bmi,
        daily_caloric_intake, weekly_exercise_hours,
        adherence_to_diet_plan, dietary_nutrient_imbalance_score,
    ]

    # Optional numeric columns
    opt_values = []
    for col in optional_cols:
        if "Cholesterol" in col:
            opt_values.append(cholesterol if cholesterol is not None else 180.0)
        elif "Glucose" in col:
            opt_values.append(glucose if glucose is not None else 100.0)

    # Categorical encoding
    cat_inputs = {
        "Gender": gender,
        "Disease_Type": disease_type,
        "Severity": severity,
        "Physical_Activity_Level": physical_activity_level,
    }
    cat_values = []
    for col in cat_cols:
        if col in feature_encoders and col in cat_inputs:
            le = feature_encoders[col]
            val = cat_inputs[col]
            try:
                enc = int(le.transform([val])[0])
            except ValueError:
                enc = 0
            cat_values.append(enc)

    features = np.array([numeric_values + opt_values + cat_values])
    proba = model.predict_proba(features)[0]
    predicted_idx = int(np.argmax(proba))
    predicted_class = le_target.classes_[predicted_idx]

    return {
        "predicted_diet": predicted_class,
        "confidence": round(float(proba[predicted_idx]), 4),
        "probabilities": {
            cls: round(float(p), 4) for cls, p in zip(le_target.classes_, proba)
        },
    }


def get_metrics_report() -> dict:
    path = MODEL_DIR / "metrics_report.json"
    if not path.exists():
        return {"error": "No metrics report found. Run training first."}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def models_trained() -> bool:
    return (
        (MODEL_DIR / "fitness_classifier.pkl").exists()
        and (MODEL_DIR / "fitness_regressor.pkl").exists()
        and (MODEL_DIR / "diet_classifier.pkl").exists()
    )
