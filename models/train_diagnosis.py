import os
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "datasets", "ML Car Diagnostic Agent AI Assistant.csv")
MODEL_DIR = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports", "evaluation")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def build_expert_rules(df):
    """
    Construct an industrial expert knowledge base mapping classifications & symptoms
    to exact diagnosis, severity, replacement/repair parts, and actionable fix steps.
    """
    rules = {
        "categories": {},
        "symptoms": {}
    }
    
    # Category level aggregation
    for cat, grp in df.groupby("Problem Classification"):
        diagnoses = grp["Diagnosis"].dropna().unique().tolist()
        fixes = grp["How to Fix the Problem"].dropna().unique().tolist()
        solutions = grp["Solution Used"].dropna().unique().tolist()
        severities = grp["Severity"].dropna().unique().tolist()
        
        # Categorize solutions into Replace vs Repair
        replace_parts = []
        repair_actions = []
        for sol in solutions:
            sol_str = str(sol).strip()
            if any(w in sol_str.lower() for w in ["replace", "install", "new", "swap"]):
                replace_parts.append(sol_str)
            else:
                repair_actions.append(sol_str)
        
        rules["categories"][str(cat)] = {
            "common_diagnoses": diagnoses[:8],
            "recommended_fixes": fixes[:6],
            "replace_parts": list(set(replace_parts))[:8],
            "repair_actions": list(set(repair_actions))[:8],
            "default_severity": severities[0] if severities else "Medium"
        }

    # Symptom level lookup
    for _, row in df.iterrows():
        desc = str(row.get("Problem Description", "")).strip().lower()
        if not desc or desc in rules["symptoms"]:
            continue
        
        sol = str(row.get("Solution Used", "")).strip()
        is_replace = any(w in sol.lower() for w in ["replace", "install", "new", "swap"])
        
        rules["symptoms"][desc] = {
            "problem_classification": str(row.get("Problem Classification", "General")),
            "severity": str(row.get("Severity", "Medium")),
            "diagnosis": str(row.get("Diagnosis", "Component Wear / Inspection Required")),
            "how_to_fix": str(row.get("How to Fix the Problem", "Inspect and service affected component")),
            "replace_parts": [sol] if is_replace and sol else ["Inspect & replace damaged component"],
            "repair_actions": [sol] if not is_replace and sol else ["Clean, tighten, or recalibrate component"]
        }

    return rules


def main():
    print("=" * 80)
    print("TRAINING VEHICLE DIAGNOSIS & PARTS RECOMMENDATION AGENT")
    print("=" * 80)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Diagnostic dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, low_memory=False)
    print(f"Loaded diagnostic dataset: {df.shape}")

    df = df.dropna(subset=["Problem Description", "Problem Classification"])
    
    # Feature text: combine problem description, service history, and ECU Data if available
    df["ECU Data"] = df["ECU Data"].fillna("No ECU Error")
    df["Service History"] = df["Service History"].fillna("No Prior History")
    
    X_text = (df["Problem Description"].astype(str) + " " + df["ECU Data"].astype(str) + " " + df["Service History"].astype(str)).values
    y = df["Problem Classification"].astype(str).values

    X_train, X_test, y_train, y_test = train_test_split(X_text, y, test_size=0.2, random_state=42, stratify=y)

    # Pure ML Pipeline: TF-IDF Vectorizer + Random Forest Classifier
    diag_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1))
    ])

    print("Fitting TF-IDF + Random Forest diagnostic classifier...")
    diag_pipeline.fit(X_train, y_train)

    preds = diag_pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Diagnostic Model Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:\n", classification_report(y_test, preds))

    # Save Model Artifact
    model_path = os.path.join(MODEL_DIR, "diag_model.pkl")
    joblib.dump(diag_pipeline, model_path)
    print(f"Diagnostic Model saved to: {model_path}")

    # Build and Save Rule-Based Knowledge Base
    rules = build_expert_rules(df)
    rules_path = os.path.join(MODEL_DIR, "diag_rules.json")
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    print(f"Expert Rules & Parts Matrix saved to: {rules_path}")

    # Save Diagnostic Evaluation Report
    diag_report_path = os.path.join(REPORTS_DIR, "diagnostic_report.json")
    with open(diag_report_path, "w", encoding="utf-8") as f:
        json.dump({
            "accuracy": round(float(acc), 4),
            "classes": sorted(list(set(y))),
            "sample_test_size": len(y_test)
        }, f, indent=2)

    print("=" * 80)
    print("DIAGNOSIS & PARTS RECOMMENDATION TRAINING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
