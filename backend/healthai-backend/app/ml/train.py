"""
Training script for HealthAI ML models.

Two models are trained:
  1. Fitness model (fitness_tracker.csv)
     - Classifier: predict Workout_Type (Yoga/Strength/Cardio/HIIT)
     - Regressor:  predict Calories_Burned
  2. Diet model (diet_recommendations.csv)
     - Classifier: predict Diet_Recommendation

Run directly:  python -m app.ml.train
"""

import os
import json
import pickle
import pathlib
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report,
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
MODEL_DIR = pathlib.Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# FITNESS MODEL
# ─────────────────────────────────────────────

def train_fitness_model(verbose: bool = True) -> dict:
    df = pd.read_csv(DATA_DIR / "fitness_tracker.csv")

    numeric_cols = [
        "Age", "Weight (kg)", "Height (m)",
        "Max_BPM", "Avg_BPM", "Resting_BPM",
        "Session_Duration (hours)", "Fat_Percentage",
        "Water_Intake (liters)", "Workout_Frequency (days/week)",
        "Experience_Level", "BMI",
    ]
    categorical_cols = ["Gender"]
    target_class = "Workout_Type"
    target_reg = "Calories_Burned"

    # Drop rows with missing targets
    df = df.dropna(subset=[target_class, target_reg])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    # Features
    X_num = df[numeric_cols].values
    X_cat = df[categorical_cols].copy()
    X_cat["Gender"] = X_cat["Gender"].map({"Male": 0, "Female": 1}).fillna(0).astype(int).values

    X = np.hstack([X_num, X_cat.values])
    feature_names = numeric_cols + categorical_cols

    # ── Classifier: Workout_Type ──────────────────
    le = LabelEncoder()
    y_class = le.fit_transform(df[target_class])

    X_tr, X_te, y_tr, y_te = train_test_split(X, y_class, test_size=0.2, random_state=42, stratify=y_class)

    # Hyperparameter tuning via GridSearchCV (cv=3 for speed)
    param_grid_clf = {
        "n_estimators": [50, 100, 200],
        "max_depth": [8, 12, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
    }
    grid_clf = GridSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1),
        param_grid_clf,
        cv=3,
        scoring="f1_macro",
        n_jobs=-1,
        refit=True,
    )
    grid_clf.fit(X_tr, y_tr)
    clf = grid_clf.best_estimator_
    best_clf_params = grid_clf.best_params_
    if verbose:
        print(f"  [GridSearch Fitness Clf] best params: {best_clf_params}")

    y_pred_cls = clf.predict(X_te)

    clf_metrics = {
        "accuracy": round(float(accuracy_score(y_te, y_pred_cls)), 4),
        "precision_macro": round(float(precision_score(y_te, y_pred_cls, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_te, y_pred_cls, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_te, y_pred_cls, average="macro", zero_division=0)), 4),
        "classes": list(le.classes_),
        "best_params": best_clf_params,
        "cv_best_score": round(float(grid_clf.best_score_), 4),
        "report": classification_report(y_te, y_pred_cls, target_names=le.classes_, output_dict=True),
    }

    # ── Regressor: Calories_Burned (include Workout_Type as feature) ──
    y_class_encoded = le.transform(df[target_class])
    X_with_wt = np.hstack([X, y_class_encoded.reshape(-1, 1)])
    y_reg = df[target_reg].values
    X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X_with_wt, y_reg, test_size=0.2, random_state=42)
    reg = RandomForestRegressor(n_estimators=150, max_depth=15, random_state=42, n_jobs=-1)
    reg.fit(X_tr2, y_tr2)
    y_pred_reg = reg.predict(X_te2)

    reg_metrics = {
        "mae": round(float(mean_absolute_error(y_te2, y_pred_reg)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_te2, y_pred_reg))), 4),
        "r2": round(float(r2_score(y_te2, y_pred_reg)), 4),
    }

    # Feature importances
    fi = {name: round(float(imp), 4) for name, imp in zip(feature_names, clf.feature_importances_)}

    # Save models
    with open(MODEL_DIR / "fitness_classifier.pkl", "wb") as f:
        pickle.dump({"model": clf, "label_encoder": le, "feature_names": feature_names}, f)
    with open(MODEL_DIR / "fitness_regressor.pkl", "wb") as f:
        pickle.dump({"model": reg, "label_encoder": le, "feature_names": feature_names + ["Workout_Type_encoded"]}, f)

    metrics = {
        "workout_type_classifier": clf_metrics,
        "calories_regressor": reg_metrics,
        "feature_importances": fi,
        "training_samples": int(len(X_tr)),
        "test_samples": int(len(X_te)),
    }

    if verbose:
        print(f"[Fitness Classifier] accuracy={clf_metrics['accuracy']}  f1={clf_metrics['f1_macro']}")
        print(f"[Calories Regressor] MAE={reg_metrics['mae']}  RMSE={reg_metrics['rmse']}  R2={reg_metrics['r2']}")

    return metrics


# ─────────────────────────────────────────────
# DIET MODEL
# ─────────────────────────────────────────────

def train_diet_model(verbose: bool = True) -> dict:
    df = pd.read_csv(DATA_DIR / "diet_recommendations.csv")

    numeric_cols = [
        "Age", "Weight_kg", "Height_cm", "BMI",
        "Daily_Caloric_Intake", "Weekly_Exercise_Hours",
        "Adherence_to_Diet_Plan", "Dietary_Nutrient_Imbalance_Score",
    ]
    numeric_optional = ["Cholesterol_mg/dL", "Glucose_mg/dL"]
    cat_cols = ["Gender", "Disease_Type", "Severity", "Physical_Activity_Level"]
    target = "Diet_Recommendation"

    df = df.dropna(subset=[target])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in numeric_optional:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median() if col in df else 0)
    df = df.dropna(subset=numeric_cols)

    # Encode categoricals
    encoders: dict = {}
    for col in cat_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col + "_enc"] = le.fit_transform(df[col].astype(str).fillna("Unknown"))
            encoders[col] = le

    enc_cols = [c + "_enc" for c in cat_cols if c in df.columns]
    available_opt = [c for c in numeric_optional if c in df.columns]
    feature_names = numeric_cols + available_opt + enc_cols
    X = df[feature_names].values

    le_target = LabelEncoder()
    y = le_target.fit_transform(df[target])

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Hyperparameter tuning via GridSearchCV (cv=3 for speed)
    param_grid_diet = {
        "n_estimators": [50, 100, 200],
        "max_depth": [10, 15, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
    }
    grid_diet = GridSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1),
        param_grid_diet,
        cv=3,
        scoring="f1_macro",
        n_jobs=-1,
        refit=True,
    )
    grid_diet.fit(X_tr, y_tr)
    clf = grid_diet.best_estimator_
    best_diet_params = grid_diet.best_params_
    if verbose:
        print(f"  [GridSearch Diet Clf] best params: {best_diet_params}")

    y_pred = clf.predict(X_te)

    metrics = {
        "accuracy": round(float(accuracy_score(y_te, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_te, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_te, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_te, y_pred, average="macro", zero_division=0)), 4),
        "classes": list(le_target.classes_),
        "best_params": best_diet_params,
        "cv_best_score": round(float(grid_diet.best_score_), 4),
        "report": classification_report(y_te, y_pred, target_names=le_target.classes_, output_dict=True),
        "training_samples": int(len(X_tr)),
        "test_samples": int(len(X_te)),
        "feature_importances": {
            name: round(float(imp), 4)
            for name, imp in zip(feature_names, clf.feature_importances_)
        },
    }

    with open(MODEL_DIR / "diet_classifier.pkl", "wb") as f:
        pickle.dump({
            "model": clf,
            "label_encoder": le_target,
            "feature_encoders": encoders,
            "feature_names": feature_names,
            "numeric_cols": numeric_cols,
            "optional_cols": available_opt,
            "cat_cols": cat_cols,
        }, f)

    if verbose:
        print(f"[Diet Classifier] accuracy={metrics['accuracy']}  f1={metrics['f1_macro']}")

    return metrics


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def train_all(verbose: bool = True) -> dict:
    if verbose:
        print("Training fitness models…")
    fitness = train_fitness_model(verbose)

    if verbose:
        print("Training diet model…")
    diet = train_diet_model(verbose)

    report = {"fitness": fitness, "diet": diet}

    report_path = MODEL_DIR / "metrics_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"Metrics saved -> {report_path}")

    return report


if __name__ == "__main__":
    train_all(verbose=True)
