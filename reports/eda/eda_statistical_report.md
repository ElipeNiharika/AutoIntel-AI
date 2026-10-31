# 📊 Exploratory Data Analysis & Statistical Telemetry Report

---

## 1. Dataset 1: Enhanced Vehicle Repair & Towing Dataset (`main_cleaned.csv`)
- **Total Workorders Analyzed**: 50,000 sampled records (from 2,000,000 full population).
- **Target 1 (`Total Cost`)**:
  - Mean: **$373.05** | Median: **$199.33** | Std: **$406.08**
  - Min: **$20.00** | Max: **$2713.13**
- **Target 2 (`Service Duration Hours`)**:
  - Mean: **3.03 hrs** | Std: **1.44 hrs**
- **Target 3 (`Insurance Claim Used`)**:
  - Claim Proportion: **43.0%**

---

## 2. Dataset 2: Used Car Specification Catalog (`Used_Car_Dataset.csv`)
- **Catalog Size**: 14,993 verified vehicle listings.
- **Top Manufacturers**: Toyota, Honda, Ford, BMW, Mercedes-Benz, Hyundai, Nissan, Chevrolet.
- **Transmission Split**: 72.4% Automatic, 27.6% Manual.

---

## 3. Dataset 3: Insurance Fraud Analytics (`fraud_oracle.csv`)
- **Total Policy Claims**: 15,420 insurance records.
- **Fraud Positive Cases**: 923 claims (**5.99% positive class incidence**).
- **Class Imbalance Handling**: Addressed via cost-sensitive gradient boosting (`scale_pos_weight = 15`) and balanced class weighting.

---

## 4. Dataset 4: Automotive Diagnostic Knowledge Base (`ML Car Diagnostic Agent AI Assistant.csv`)
- **Diagnostic Case Studies**: 10,000 categorized symptom-to-solution mappings.
- **Domain Coverage**: Brakes, Engine, Transmission, Battery, Electrical, Cooling.
- **NLP Vectorization**: TF-IDF n-grams (1,2) with sublinear term scaling.
