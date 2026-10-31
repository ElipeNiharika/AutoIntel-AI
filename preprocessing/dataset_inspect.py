import os
import sys
import io
import pandas as pd
import numpy as np

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATASET_DIR = r"c:\AI_Vehicle_Service_Repair_Insurance_Intelligence\datasets"

files = [
    "enhanced_motor_vehicle_repair_towing_dataset.csv",
    "Used_Car_Dataset.csv",
    "fraud_oracle.csv",
    "ML Car Diagnostic Agent AI Assistant.csv"
]

print("="*80)
print("EXPLORING ALL 4 DATASETS IN DETAIL")
print("="*80)

for f in files:
    file_path = os.path.join(DATASET_DIR, f)
    if not os.path.exists(file_path):
        print(f"FILE NOT FOUND: {f}")
        continue
    
    print(f"\n{'='*40}")
    print(f">>> DATASET: {f}")
    print(f"File Size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    
    # Read sample
    df_sample = pd.read_csv(file_path, nrows=5)
    print(f"Number of columns: {len(df_sample.columns)}")
    print("Columns and first sample value:")
    for col in df_sample.columns:
        val = df_sample[col].values[0] if len(df_sample)>0 else 'N/A'
        print(f"  - {col}: {repr(val)[:60]}")
        
    df_preview = pd.read_csv(file_path, nrows=2000)
    print(f"\nPreview Shape (first 2000 rows): {df_preview.shape}")
    print("Summary of columns:")
    for col in df_preview.columns:
        null_cnt = df_preview[col].isnull().sum()
        dtype = df_preview[col].dtype
        unique_cnt = df_preview[col].nunique()
        print(f"  * {col:38s} | Type: {str(dtype):10s} | Nulls in 2k: {null_cnt:4d} | Unique in 2k: {unique_cnt:4d}")

print("\n" + "="*80)
print("INSPECTION COMPLETE")
print("="*80)

