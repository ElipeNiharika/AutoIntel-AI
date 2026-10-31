import os
import re
import json
from collections import Counter
import numpy as np
import pandas as pd

DATA_DIR = "datasets"
MAIN_DATA_PATH = os.path.join(DATA_DIR, "enhanced_motor_vehicle_repair_towing_dataset.csv")
USED_CAR_PATH = os.path.join(DATA_DIR, "Used_Car_Dataset.csv")
DIAG_PATH = os.path.join(DATA_DIR, "ML Car Diagnostic Agent AI Assistant.csv")
FRAUD_PATH = os.path.join(DATA_DIR, "fraud_oracle.csv")
OUT_DIR = os.path.join(DATA_DIR, "cleaned")
os.makedirs(OUT_DIR, exist_ok=True)


def clean_currency(x):
    if pd.isna(x):
        return np.nan
    s = str(x)
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s) if s != "" else np.nan
    except:
        return np.nan


def clean_int(x):
    if pd.isna(x):
        return np.nan
    s = str(x)
    s = re.sub(r"[^0-9\-]", "", s)
    try:
        return int(s) if s != "" else np.nan
    except:
        return np.nan


def bool_map(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()
    if s in ("yes", "y", "true", "1"):
        return 1
    if s in ("no", "n", "false", "0"):
        return 0
    return np.nan


def preprocess_main_dataset():
    print("=" * 80)
    print("STEP 1: PREPROCESSING MAIN REPAIR & TOWING DATASET")
    print("=" * 80)
    print(f"Reading sample of 120,000 rows from {MAIN_DATA_PATH} for optimal ML training...")
    
    # Read chunk for robust training without memory overflow
    df = pd.read_csv(MAIN_DATA_PATH, nrows=120000, low_memory=False)
    print(f"Initial raw shape: {df.shape}")

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Drop PII
    if "Customer Name" in df.columns:
        df = df.drop(columns=["Customer Name"])
    if "Mechanic Name" in df.columns:
        df = df.drop(columns=["Mechanic Name"])
    if "Tow Truck Driver" in df.columns:
        df = df.drop(columns=["Tow Truck Driver"])

    # Remove duplicates
    if "Service ID" in df.columns:
        df = df.drop_duplicates(subset=["Service ID"])

    # Numeric cleaning
    for col in ["Total Cost", "Estimated Cost"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    if "Mileage at Service" in df.columns:
        df["Mileage at Service"] = df["Mileage at Service"].apply(clean_int)

    if "Tow Distance Miles" in df.columns:
        df["Tow Distance Miles"] = df["Tow Distance Miles"].apply(clean_currency)

    if "Technician Rating" in df.columns:
        df["Technician Rating"] = pd.to_numeric(df["Technician Rating"], errors="coerce")

    if "Service Duration Hours" in df.columns:
        df["Service Duration Hours"] = pd.to_numeric(df["Service Duration Hours"], errors="coerce")

    # Target & Flag columns
    for col in ["Insurance Claim Used", "Is Warranty Valid", "Follow-up Needed"]:
        if col in df.columns:
            df[col + "_flag"] = df[col].apply(bool_map)

    # Dates handling
    for col in ["Repair Date", "Towing Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "Repair Date" in df.columns and "Towing Date" in df.columns:
        df["Days_Between_Tow_and_Repair"] = (df["Repair Date"] - df["Towing Date"]).dt.days
        df["Days_Between_Tow_and_Repair"] = df["Days_Between_Tow_and_Repair"].fillna(0).clip(lower=0, upper=60)

    if "Repair Date" in df.columns:
        df["Repair_Month"] = df["Repair Date"].dt.month.fillna(1).astype(int)
        df["Repair_Weekday"] = df["Repair Date"].dt.weekday.fillna(0).astype(int)

    # Make & Model Decomposition
    if "Make and Model" in df.columns:
        def split_brand_model(x):
            if pd.isna(x):
                return ("Unknown", "Unknown")
            s = str(x).strip()
            parts = s.split(" ", 1)
            brand = parts[0].capitalize()
            model = parts[1].title() if len(parts) > 1 else "Standard"
            return (brand, model)

        bm = df["Make and Model"].apply(split_brand_model)
        df["Brand"] = bm.apply(lambda x: x[0])
        df["Model"] = bm.apply(lambda x: x[1])

    # Top Parts Extraction & Multi-Hot Encoding
    top_parts = [
        "brake pads", "oil filter", "battery", "spark plugs", "air filter",
        "alternator", "radiator", "starter motor", "transmission fluid", "clutch plate",
        "timing belt", "water pump", "struts", "brake rotor", "fuel pump",
        "oxygen sensor", "tires", "headlight bulb", "cabin filter", "wiper blades"
    ]

    parts_col = "Parts Used"
    if parts_col in df.columns:
        df["Parts_Clean"] = df[parts_col].fillna("").astype(str).apply(
            lambda s: [p.strip().lower() for p in s.split(",") if p.strip() != ""]
        )
        df["Parts_Count"] = df["Parts_Clean"].apply(len)
        for p in top_parts:
            colname = f"part_{re.sub(r'[^0-9a-zA-Z]+', '_', p)}"
            df[colname] = df["Parts_Clean"].apply(lambda lst: 1 if any(p in item for item in lst) else 0)

    # Text Keyword Features from Service Description
    if "Service Description" in df.columns:
        df["Service_Desc_Len"] = df["Service Description"].fillna("").astype(str).apply(len)
        keywords = ["engine", "transmission", "brake", "battery", "electrical", "oil", "clutch", "suspension", "towing", "overheating"]
        for kw in keywords:
            df[f"desc_has_{kw}"] = df["Service Description"].fillna("").astype(str).str.lower().str.contains(kw).astype(int)

    # Cost overrun calculation
    if "Estimated Cost" in df.columns and "Total Cost" in df.columns:
        df["cost_overrun_ratio"] = df.apply(
            lambda r: (r["Total Cost"] / r["Estimated Cost"]) if pd.notna(r.get("Total Cost")) and pd.notna(r.get("Estimated Cost")) and r.get("Estimated Cost", 0) > 0 else 1.0,
            axis=1
        )

    # Missing value imputation
    # Impute numeric medians
    num_cols = ["Total Cost", "Estimated Cost", "Service Duration Hours", "Mileage at Service", "Technician Rating", "Tow Distance Miles"]
    for c in num_cols:
        if c in df.columns:
            median_val = df[c].median()
            df[c] = df[c].fillna(median_val)

    # Impute binary flags
    flag_cols = ["Insurance Claim Used_flag", "Is Warranty Valid_flag", "Follow-up Needed_flag"]
    for c in flag_cols:
        if c in df.columns:
            df[c] = df[c].fillna(0).astype(int)

    # Categorical fills
    cat_cols = ["Vehicle Type", "Service Type", "Urgency Level", "Customer Type", "Warranty Information", "Brand", "Model"]
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown").astype(str)

    # Save Missing Value Report
    miss_report = df.isnull().sum().to_frame(name="missing_count")
    miss_report.to_csv(os.path.join(OUT_DIR, "missing_values_report.csv"))

    # Save cleaned training set
    cleaned_path = os.path.join(OUT_DIR, "main_cleaned.csv")
    sample_path = os.path.join(OUT_DIR, "main_cleaned_sample.csv")
    
    df.to_csv(cleaned_path, index=False)
    df.head(2000).to_csv(sample_path, index=False)
    print(f"Cleaned main dataset saved successfully!")
    print(f"Main Cleaned Shape: {df.shape} -> {cleaned_path}")
    print(f"Sample Cleaned Shape: (2000, {df.shape[1]}) -> {sample_path}")
    return df


def preprocess_used_car_metadata():
    print("\n" + "=" * 80)
    print("STEP 2: EXTRACTING VEHICLE CATALOG METADATA (Used_Car_Dataset.csv)")
    print("=" * 80)
    if not os.path.exists(USED_CAR_PATH):
        print(f"File not found: {USED_CAR_PATH}")
        return

    df_used = pd.read_csv(USED_CAR_PATH)
    print(f"Used Car Dataset Shape: {df_used.shape}")
    df_used.columns = [c.strip() for c in df_used.columns]

    # Extract unique brands and models mapping
    brand_models = {}
    if "Brand" in df_used.columns and "model" in df_used.columns:
        for brand, group in df_used.groupby("Brand"):
            models = sorted([str(m).strip() for m in group["model"].dropna().unique() if str(m).strip() != ""])
            if models:
                brand_models[str(brand).strip()] = models[:15]

    fuel_types = df_used["FuelType"].dropna().unique().tolist() if "FuelType" in df_used.columns else ["Petrol", "Diesel", "Electric", "Hybrid", "CNG"]
    transmissions = df_used["Transmission"].dropna().unique().tolist() if "Transmission" in df_used.columns else ["Manual", "Automatic"]

    vehicle_metadata = {
        "brands": sorted(list(brand_models.keys())) if brand_models else ["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes-Benz", "Hyundai", "Nissan", "Volkswagen", "Audi"],
        "brand_models": brand_models if brand_models else {
            "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma"],
            "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit"],
            "Ford": ["F-150", "Mustang", "Explorer", "Escape", "Focus"],
            "BMW": ["3 Series", "5 Series", "X3", "X5", "M3"],
            "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "GLE", "S-Class"],
            "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Creta"]
        },
        "vehicle_types": ["Sedan", "SUV", "Truck", "Coupe", "Hatchback", "Van", "Convertible"],
        "fuel_types": fuel_types,
        "transmissions": transmissions,
        "service_types": [
            "Routine Maintenance", "Oil Change & Inspection", "Brake System Service",
            "Transmission Repair", "Engine Diagnostics & Tune-up", "Battery & Electrical Repair",
            "Suspension & Steering Overhaul", "Cooling System Service", "Emergency Towing & Repair"
        ],
        "urgency_levels": ["Low", "Normal", "High", "Critical Emergency"],
        "customer_types": ["Individual Owner", "Commercial Fleet", "Rideshare Driver", "Corporate Partner"],
        "warranty_options": ["Standard Factory Warranty", "Extended Coverage", "Powertrain Warranty", "Expired / No Warranty"]
    }

    meta_path = os.path.join(OUT_DIR, "vehicle_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(vehicle_metadata, f, indent=2)
    print(f"Vehicle catalog metadata saved to: {meta_path}")


def main():
    preprocess_main_dataset()
    preprocess_used_car_metadata()
    print("\n" + "=" * 80)
    print("ALL PREPROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
