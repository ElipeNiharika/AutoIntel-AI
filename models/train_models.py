import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
from xgboost import XGBRegressor, XGBClassifier

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from preprocessing.transformers import FrequencyEncoder

DATA_PATH = os.path.join(ROOT, "datasets", "cleaned", "main_cleaned.csv")
MODEL_DIR = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports", "evaluation")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def regression_metrics(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return {
        "MAE": round(mae, 4),
        "MSE": round(float(mse), 4),
        "RMSE": round(rmse, 4),
        "R2_Score": round(r2, 4)
    }


def classification_metrics(y_true, y_pred, y_proba=None):
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    metrics = {
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1_Score": round(f1, 4),
        "Confusion_Matrix": confusion_matrix(y_true, y_pred).tolist()
    }
    if y_proba is not None:
        try:
            if y_proba.ndim == 2 and y_proba.shape[1] > 1:
                metrics["ROC_AUC"] = round(float(roc_auc_score(y_true, y_proba[:, 1])), 4)
            else:
                metrics["ROC_AUC"] = round(float(roc_auc_score(y_true, y_proba)), 4)
        except Exception:
            metrics["ROC_AUC"] = None
    return metrics


def main():
    print("=" * 80)
    print("AI VEHICLE SERVICE - PURE MACHINE LEARNING MODEL TRAINING PIPELINE")
    print("=" * 80)
    
    # Load FE Pipeline
    fe_path = os.path.join(MODEL_DIR, "fe_pipeline.pkl")
    if not os.path.exists(fe_path):
        raise FileNotFoundError(f"Feature engineering artifact not found at {fe_path}")
    
    fe_dict = joblib.load(fe_path)
    preprocessor = fe_dict["pipeline"]
    feature_cols = fe_dict["feature_cols"]

    print(f"Loading cleaned dataset: {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH, nrows=75000, low_memory=False)
    print(f"Loaded {len(df)} samples for robust multi-model training and cross-validation.")

    # Prepare features X
    X_raw = df[feature_cols]
    print("Transforming features with ColumnTransformer...")
    X = preprocessor.transform(X_raw)
    print(f"Transformed feature matrix X shape: {X.shape}")

    all_metrics = {}

    # -------------------------------------------------------------
    # TASK 1: REPAIR COST PREDICTION (REGRESSION)
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> TASK 1: REPAIR COST PREDICTION (Target: Total Cost)")
    print("-" * 60)
    y_cost = df["Total Cost"].values
    X_tr_c, X_te_c, y_tr_c, y_te_c = train_test_split(X, y_cost, test_size=0.2, random_state=42)

    # 1. Linear Regression
    lr_cost = LinearRegression()
    lr_cost.fit(X_tr_c, y_tr_c)
    pred_lr_cost = lr_cost.predict(X_te_c)
    m_lr_cost = regression_metrics(y_te_c, pred_lr_cost)
    print("  [1] Linear Regression Metrics:      ", m_lr_cost)

    # 2. Random Forest Regressor
    rf_cost = RandomForestRegressor(n_estimators=100, max_depth=16, random_state=42, n_jobs=-1)
    rf_cost.fit(X_tr_c, y_tr_c)
    pred_rf_cost = rf_cost.predict(X_te_c)
    m_rf_cost = regression_metrics(y_te_c, pred_rf_cost)
    print("  [2] Random Forest Regressor Metrics:", m_rf_cost)

    # 3. XGBoost Regressor
    xgb_cost = XGBRegressor(n_estimators=180, max_depth=6, learning_rate=0.08, random_state=42, n_jobs=-1)
    xgb_cost.fit(X_tr_c, y_tr_c)
    pred_xgb_cost = xgb_cost.predict(X_te_c)
    m_xgb_cost = regression_metrics(y_te_c, pred_xgb_cost)
    print("  [3] XGBoost Regressor Metrics:      ", m_xgb_cost)

    # Choose best model (highest R2)
    models_cost = {"LinearRegression": (lr_cost, m_lr_cost), "RandomForest": (rf_cost, m_rf_cost), "XGBoost": (xgb_cost, m_xgb_cost)}
    best_cost_name = max(models_cost, key=lambda k: models_cost[k][1]["R2_Score"])
    best_cost_model = models_cost[best_cost_name][0]
    joblib.dump(best_cost_model, os.path.join(MODEL_DIR, "cost_model.pkl"))
    print(f"  >>> BEST COST MODEL: {best_cost_name} saved to models/cost_model.pkl")

    all_metrics["Repair_Cost_Prediction"] = {
        "LinearRegression": m_lr_cost,
        "RandomForest": m_rf_cost,
        "XGBoost": m_xgb_cost,
        "Best_Model": best_cost_name
    }

    # -------------------------------------------------------------
    # TASK 2: REPAIR TIME PREDICTION (REGRESSION)
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> TASK 2: REPAIR TIME PREDICTION (Target: Service Duration Hours)")
    print("-" * 60)
    y_time = df["Service Duration Hours"].values
    X_tr_t, X_te_t, y_tr_t, y_te_t = train_test_split(X, y_time, test_size=0.2, random_state=42)

    # 1. Linear Regression
    lr_time = LinearRegression()
    lr_time.fit(X_tr_t, y_tr_t)
    pred_lr_time = lr_time.predict(X_te_t)
    m_lr_time = regression_metrics(y_te_t, pred_lr_time)
    print("  [1] Linear Regression Metrics:      ", m_lr_time)

    # 2. Random Forest Regressor
    rf_time = RandomForestRegressor(n_estimators=100, max_depth=16, random_state=42, n_jobs=-1)
    rf_time.fit(X_tr_t, y_tr_t)
    pred_rf_time = rf_time.predict(X_te_t)
    m_rf_time = regression_metrics(y_te_t, pred_rf_time)
    print("  [2] Random Forest Regressor Metrics:", m_rf_time)

    # 3. XGBoost Regressor
    xgb_time = XGBRegressor(n_estimators=180, max_depth=6, learning_rate=0.08, random_state=42, n_jobs=-1)
    xgb_time.fit(X_tr_t, y_tr_t)
    pred_xgb_time = xgb_time.predict(X_te_t)
    m_xgb_time = regression_metrics(y_te_t, pred_xgb_time)
    print("  [3] XGBoost Regressor Metrics:      ", m_xgb_time)

    models_time = {"LinearRegression": (lr_time, m_lr_time), "RandomForest": (rf_time, m_rf_time), "XGBoost": (xgb_time, m_xgb_time)}
    best_time_name = max(models_time, key=lambda k: models_time[k][1]["R2_Score"])
    best_time_model = models_time[best_time_name][0]
    joblib.dump(best_time_model, os.path.join(MODEL_DIR, "time_model.pkl"))
    print(f"  >>> BEST TIME MODEL: {best_time_name} saved to models/time_model.pkl")

    all_metrics["Repair_Time_Prediction"] = {
        "LinearRegression": m_lr_time,
        "RandomForest": m_rf_time,
        "XGBoost": m_xgb_time,
        "Best_Model": best_time_name
    }

    # -------------------------------------------------------------
    # TASK 3: INSURANCE CLAIM PREDICTION (CLASSIFICATION)
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> TASK 3: INSURANCE CLAIM PREDICTION (Target: Insurance Claim Used_flag)")
    print("-" * 60)
    y_ins = df["Insurance Claim Used_flag"].astype(int).values
    X_tr_i, X_te_i, y_tr_i, y_te_i = train_test_split(X, y_ins, test_size=0.2, random_state=42, stratify=y_ins)

    # 1. Logistic Regression
    log_ins = LogisticRegression(max_iter=1000, random_state=42)
    log_ins.fit(X_tr_i, y_tr_i)
    pred_log_ins = log_ins.predict(X_te_i)
    prob_log_ins = log_ins.predict_proba(X_te_i)
    m_log_ins = classification_metrics(y_te_i, pred_log_ins, prob_log_ins)
    print("  [1] Logistic Regression Metrics:    ", {k: v for k, v in m_log_ins.items() if k != "Confusion_Matrix"})

    # 2. Random Forest Classifier
    rf_ins = RandomForestClassifier(n_estimators=120, max_depth=14, random_state=42, n_jobs=-1)
    rf_ins.fit(X_tr_i, y_tr_i)
    pred_rf_ins = rf_ins.predict(X_te_i)
    prob_rf_ins = rf_ins.predict_proba(X_te_i)
    m_rf_ins = classification_metrics(y_te_i, pred_rf_ins, prob_rf_ins)
    print("  [2] Random Forest Classifier Metrics:", {k: v for k, v in m_rf_ins.items() if k != "Confusion_Matrix"})

    # 3. XGBoost Classifier
    xgb_ins = XGBClassifier(n_estimators=180, max_depth=6, learning_rate=0.08, eval_metric="logloss", random_state=42, n_jobs=-1)
    xgb_ins.fit(X_tr_i, y_tr_i)
    pred_xgb_ins = xgb_ins.predict(X_te_i)
    prob_xgb_ins = xgb_ins.predict_proba(X_te_i)
    m_xgb_ins = classification_metrics(y_te_i, pred_xgb_ins, prob_xgb_ins)
    print("  [3] XGBoost Classifier Metrics:     ", {k: v for k, v in m_xgb_ins.items() if k != "Confusion_Matrix"})

    models_ins = {"LogisticRegression": (log_ins, m_log_ins), "RandomForest": (rf_ins, m_rf_ins), "XGBoost": (xgb_ins, m_xgb_ins)}
    best_ins_name = max(models_ins, key=lambda k: models_ins[k][1]["F1_Score"])
    best_ins_model = models_ins[best_ins_name][0]
    joblib.dump(best_ins_model, os.path.join(MODEL_DIR, "insurance_model.pkl"))
    print(f"  >>> BEST INSURANCE MODEL: {best_ins_name} saved to models/insurance_model.pkl")

    all_metrics["Insurance_Claim_Prediction"] = {
        "LogisticRegression": m_log_ins,
        "RandomForest": m_rf_ins,
        "XGBoost": m_xgb_ins,
        "Best_Model": best_ins_name
    }

    # Save comprehensive metrics JSON
    metrics_path = os.path.join(REPORTS_DIR, "training_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    print("\n" + "=" * 80)
    print(f"All model metrics exported to: {metrics_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
