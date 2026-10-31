import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "datasets", "fraud_oracle.csv")
MODEL_OUT = os.path.join(ROOT, "models", "fraud_model.pkl")
REPORT_OUT = os.path.join(ROOT, "reports", "evaluation", "fraud_model_summary.md")
os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)

print("=" * 80)
print(">>> TRAINING DEDICATED INSURANCE FRAUD DETECTION MODELS (DATASET 3) <<<")
print("=" * 80)

# 1. Load Data
df = pd.read_csv(DATA_PATH)
print(f"Loaded fraud_oracle.csv with shape: {df.shape}")

target_col = "FraudFound_P"
drop_cols = ["PolicyNumber", "RepNumber"] # Drop administrative IDs
feature_df = df.drop(columns=[target_col] + [c for c in drop_cols if c in df.columns])
y = df[target_col].astype(int).values

# Identify categorical and numerical columns
num_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()

print(f"Numerical Features ({len(num_cols)}): {num_cols}")
print(f"Categorical Features ({len(cat_cols)}): {cat_cols}")

# Preprocessing Pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
    ]
)

# Train/Test Split (Stratified on Imbalanced Fraud Target)
X_train, X_test, y_train, y_test = train_test_split(
    feature_df, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training split: {X_train.shape[0]} | Testing split: {X_test.shape[0]}")
print(f"Positive Fraud Cases in Test Set: {y_test.sum()} / {len(y_test)} ({y_test.sum()/len(y_test)*100:.2f}%)")

# Preprocess
X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc = preprocessor.transform(X_test)

# Candidate Models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    "Random Forest Classifier": RandomForestClassifier(n_estimators=100, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1),
    "XGBoost Classifier": xgb.XGBClassifier(
        n_estimators=120, max_depth=5, learning_rate=0.08, scale_pos_weight=15, 
        eval_metric="logloss", random_state=42
    )
}

results = {}
best_model_name = None
best_roc_auc = 0.0

for name, model in models.items():
    print(f"\n--- Training {name} ---")
    model.fit(X_train_proc, y_train)
    preds = model.predict(X_test_proc)
    probs = model.predict_proba(X_test_proc)[:, 1] if hasattr(model, "predict_proba") else preds
    
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    roc = roc_auc_score(y_test, probs)
    cm = confusion_matrix(y_test, preds).tolist()
    
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc:.4f}")
    print(f"Confusion Matrix: {cm}")
    
    results[name] = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc), 4),
        "confusion_matrix": cm
    }
    
    if roc > best_roc_auc:
        best_roc_auc = roc
        best_model_name = name

print(f"\n>>> Best Fraud Detection Model: {best_model_name} (ROC-AUC = {best_roc_auc:.4f})")

# Save the best model artifact bundle
bundle = {
    "model_name": best_model_name,
    "model": models[best_model_name],
    "preprocessor": preprocessor,
    "feature_cols": feature_df.columns.tolist(),
    "num_cols": num_cols,
    "cat_cols": cat_cols,
    "sample_input_template": feature_df.iloc[0].to_dict(),
    "metrics": results[best_model_name]
}

joblib.dump(bundle, MODEL_OUT)
print(f"Saved best fraud detection model bundle to: {MODEL_OUT}")

# Generate Markdown Report
md_report = f"""# 🛡️ Insurance Fraud Detection Model Benchmark Report (Dataset 3)
*Target: `FraudFound_P` (0 = Genuine Claim, 1 = Fraudulent Claim)*
*Dataset: `fraud_oracle.csv` (15,420 total policy claim records)*

---

## 📊 Comparative Performance Summary

| Model Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Production Selected |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Balanced)** | {results['Logistic Regression']['accuracy']*100:.2f}% | {results['Logistic Regression']['precision']:.4f} | {results['Logistic Regression']['recall']:.4f} | {results['Logistic Regression']['f1_score']:.4f} | {results['Logistic Regression']['roc_auc']:.4f} | {'✅ Yes' if best_model_name == 'Logistic Regression' else 'No'} |
| **Random Forest (Balanced)** | {results['Random Forest Classifier']['accuracy']*100:.2f}% | {results['Random Forest Classifier']['precision']:.4f} | {results['Random Forest Classifier']['recall']:.4f} | {results['Random Forest Classifier']['f1_score']:.4f} | {results['Random Forest Classifier']['roc_auc']:.4f} | {'✅ Yes' if best_model_name == 'Random Forest Classifier' else 'No'} |
| **XGBoost (Cost-Sensitive)** | {results['XGBoost Classifier']['accuracy']*100:.2f}% | {results['XGBoost Classifier']['precision']:.4f} | {results['XGBoost Classifier']['recall']:.4f} | {results['XGBoost Classifier']['f1_score']:.4f} | {results['XGBoost Classifier']['roc_auc']:.4f} | {'✅ Yes' if best_model_name == 'XGBoost Classifier' else 'No'} |

---

## 🎯 Key Architectural Distinction: Claim Approval vs. Fraud Detection

In our architecture:
1. **Insurance Claim Prediction (Dataset 1)** forecasts whether routine automotive repair items are reimbursable under standard policy warranties.
2. **Insurance Fraud Detection (Dataset 3)** identifies deceptive policy claims by analyzing driver demographics, accident reporting delays, policy tenure, and previous claim histories.
"""

with open(REPORT_OUT, "w", encoding="utf-8") as f:
    f.write(md_report)

print(f"Generated fraud benchmark report at: {REPORT_OUT}")
