import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from preprocessing.transformers import FrequencyEncoder

DATA_CLEAN = os.path.join(ROOT, "datasets", "cleaned", "main_cleaned.csv")
MODEL_DIR = os.path.join(ROOT, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_pipeline(df):
    # High cardinality categoricals for frequency encoding
    freq_cols = ["Brand", "Model"]
    
    # Standard low cardinality categoricals for one-hot encoding
    onehot_cols = ["Vehicle Type", "Service Type", "Urgency Level", "Customer Type", "Warranty Information"]
    
    # Explicit well-defined numeric and engineered features
    part_cols = [c for c in df.columns if c.startswith("part_") and c != "Parts_Clean"]
    desc_cols = [c for c in df.columns if c.startswith("desc_has_")]
    
    base_numeric = [
        "Estimated Cost", "Mileage at Service", "Technician Rating", 
        "Tow Distance Miles", "Parts_Count", "Days_Between_Tow_and_Repair",
        "Repair_Month", "Repair_Weekday", "Service_Desc_Len",
        "Is Warranty Valid_flag", "Follow-up Needed_flag"
    ]
    
    numeric_cols = [c for c in base_numeric if c in df.columns] + part_cols + desc_cols
    onehot_cols = [c for c in onehot_cols if c in df.columns]
    freq_cols = [c for c in freq_cols if c in df.columns]

    print(f"Feature Engineering Column Breakdown:")
    print(f"  - Numeric & Binary Flag features ({len(numeric_cols)}): {numeric_cols[:6]} ...")
    print(f"  - One-Hot Categorical features ({len(onehot_cols)}): {onehot_cols}")
    print(f"  - Frequency Encoded features ({len(freq_cols)}): {freq_cols}")

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    freq_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("freq", FrequencyEncoder())
    ])

    transformers = [
        ("num", num_pipeline, numeric_cols),
        ("cat", cat_pipeline, onehot_cols),
        ("freq", freq_pipeline, freq_cols)
    ]

    preprocessor = ColumnTransformer(transformers, remainder="drop")
    return preprocessor, numeric_cols, onehot_cols, freq_cols


def main():
    print("=" * 80)
    print("FEATURE ENGINEERING & PREPROCESSING PIPELINE FIT")
    print("=" * 80)
    print(f"Loading cleaned dataset from {DATA_CLEAN}...")
    df = pd.read_csv(DATA_CLEAN, low_memory=False)

    preprocessor, numeric_cols, onehot_cols, freq_cols = build_pipeline(df)
    
    feature_cols = numeric_cols + onehot_cols + freq_cols
    X = df[feature_cols]
    
    print("Fitting ColumnTransformer on features...")
    preprocessor.fit(X)
    
    transformed_sample = preprocessor.transform(X.head(10))
    print(f"Transformed output features dimension: {transformed_sample.shape[1]}")

    fe_artifact = {
        "pipeline": preprocessor,
        "feature_cols": feature_cols,
        "numeric_cols": numeric_cols,
        "onehot_cols": onehot_cols,
        "freq_cols": freq_cols,
        "output_dim": transformed_sample.shape[1]
    }

    out_path = os.path.join(MODEL_DIR, "fe_pipeline.pkl")
    joblib.dump(fe_artifact, out_path)
    print(f"Feature Engineering Pipeline serialized and saved to: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
