# 🚗 AI Vehicle Service, Repair & Insurance Intelligence System

> **Enterprise-Grade Pure Machine Learning Platform for Automotive Service Cost Forecasting, Turnaround Scheduling, Insurance Claim Feasibility, Fraud Detection, and Intelligent Diagnostics.**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-orange.svg)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2+-red.svg)](https://xgboost.readthedocs.io/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![Pure ML](https://img.shields.io/badge/Architecture-Pure%20Tabular%20ML-purple.svg)](#)

---

## 🌟 Executive System Overview

The **AI Vehicle Service, Repair & Insurance Intelligence System** is an end-to-end industry software solution engineered to solve multi-faceted operational and predictive challenges across the automotive aftermarket, fleet management, and motor insurance underwriting sectors.

Constructed strictly with **Pure Tabular Machine Learning models** (Zero Deep Learning, YOLO, CNN, or Computer Vision), this platform integrates 4 structured real-world repositories to deliver 10 comprehensive business modules:

```
+---------------------------------------------------------------------------------------------------+
|                     AI VEHICLE SERVICE, REPAIR & INSURANCE INTELLIGENCE SUITE                    |
+---------------------------------------------------------------------------------------------------+
|  [Module 1] User Registration & Login (Session Auth & Role-Based Access Control: Admin / Tech)    |
|  [Module 2] Vehicle Details & Fleet Intake (Dynamic Brand -> Model cascading specs & odometer)    |
|  [Module 3] Service Workorder Intake (Estimated Cost, Urgency, Tow Distance, Parts Used)         |
|  [Module 4] Repair Cost Prediction (Linear Regression & Tree Ensembles -> R² = 0.9942, MAE $18.50) |
|  [Module 5] Turnaround Duration Prediction (Service Duration Hours Regressor -> MAE 1.18 hrs)    |
|  [Module 6] Insurance Claim Prediction (Calibrated XGBoost Classifier -> 0.627 ROC-AUC)           |
|  [Module 7] Insurance Fraud Detection (Dedicated Cost-Sensitive XGBoost -> 0.8308 ROC-AUC)        |
|  [Module 8] Diagnostic Agent (NLP TF-IDF + Random Forest -> 90.9% Accuracy on 5 Subsystems)       |
|  [Module 9] Parts Recommendation Engine (Deterministic Expert Rule Matrix: Replace vs. Repair)    |
|  [Module 10] Prediction History & Audit Log (Normalized MySQL Relational Persistence)             |
|  [Module 11] Executive Admin Dashboard (Chart.js KPI Visualizations, Live CSV & PDF Generators)    |
+---------------------------------------------------------------------------------------------------+
```

---

## 📊 Datasets Strategy & Architectural Rationale

| Dataset Name | Primary Purpose | Role in Architecture | Separate vs. Merge Decision |
| :--- | :--- | :--- | :--- |
| **`enhanced_motor_vehicle_repair_towing_dataset.csv`** (Main, ~506 MB) | 2,000,000 service events with make, model, parts used, technician rating, duration, and total cost. | **Core ML Workhorse**: Trains Multi-Model Cost, Time, and Insurance Claim predictors. | **Core Standalone Pipeline**: Represents the operational truth for workorders. |
| **`Used_Car_Dataset.csv`** (~2.6 MB) | 14,990+ vehicle sales listings with engine capacity, transmission, body type, and age. | **Metadata Reference & Catalog**: Dynamically populates vehicle dropdowns and computes market depreciation benchmarks. | **Separate Reference Lookup**: Prevents Cartesian explosion and data leakage. |
| **`fraud_oracle.csv`** (~3.6 MB) | 15,420 insurance claim records with driver ratings, policy types, and fault designations. | **Dedicated Insurance Fraud Detection**: Identifies deceptive policy claims using cost-sensitive XGBoost. | **Separate Benchmark Engine**: Prevents data leakage between policy claims and shop workorders. |
| **`ML Car Diagnostic Agent AI Assistant.csv`** (~1.6 MB) | 10,000 symptom-to-solution mappings with OBD-II codes and maintenance histories. | **Expert Diagnostic Knowledge Base**: Trains TF-IDF symptom classifier and builds rule-based parts matrix. | **Separate Knowledge Base**: Operates on unstructured customer symptoms and OBD-II codes. |

---

## 🤖 Machine Learning Lifecycle & Model Benchmarks

### 1. Feature Engineering Pipeline (`preprocessing/transformers.py`)
- **Frequency Encoding**: Encodes high-cardinality categorical features (`Brand`, `Model`) into observed distribution frequencies $P(X = c)$.
- **Multi-Hot Parts Extraction**: Extracts the top 20 most frequent automotive parts (`brake_pads`, `oil_filter`, `battery`, `spark_plugs`, `alternator`, etc.) from freeform workorder logs.
- **Service Description Indicators**: Text-keyword boolean mapping (`engine`, `transmission`, `brake`, `electrical`, `overheating`).
- **Standard Scaling & Imputation**: Handles missing numerical values with median strategies and categorical values with `Unknown` tokens.

### 2. Empirical Model Evaluation

#### 🎯 Task 1: Repair Cost Prediction (Regression - Target: `Total Cost` $)
| Algorithm | MAE ($) | MSE | RMSE ($) | R² Score | Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Linear Regression** | **$18.50** | **981.87** | **$31.33** | **0.9942** | **Production Selected (Fast & Highly Interpretable)** |
| **Random Forest Regressor** | $18.74 | 1037.32 | $32.21 | 0.9938 | Robust to extreme outliers |
| **XGBoost Regressor** | $18.56 | 1067.95 | $32.68 | 0.9936 | Gradient Boosted Ensemble |

#### 🎯 Task 2: Service Duration Hours (Regression - Target: `Duration Hours`)
| Algorithm | MAE (Hours) | MSE | RMSE (Hours) | R² Score | Architecture |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Linear Regression** | **1.18** | **2.10** | **1.45** | **Baseline** | OLS Formulation |
| **Random Forest Regressor** | 1.18 | 2.11 | 1.45 | Non-linear Tree | 100 Estimators, Depth 16 |
| **XGBoost Regressor** | 1.18 | 2.13 | 1.46 | Gradient Boosted | 180 Estimators, LR 0.08 |

#### 🎯 Task 3: Insurance Claim Used (Binary Classification)
| Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | 57.31% | 0.5006 | 0.4585 | 0.4786 | **0.6268** |
| **Random Forest Classifier** | 56.95% | 0.4964 | 0.5002 | 0.4983 | 0.6231 |
| **XGBoost Classifier** | **57.07%** | **0.4977** | **0.5069** | **0.5022** | **0.6261** |

#### 🎯 Task 4: Dedicated Insurance Fraud Detection (Target: `FraudFound_P`)
| Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Production Selected |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Balanced)** | 64.23% | 0.1316 | **0.8865** | 0.2292 | 0.8074 | Baseline Classifier |
| **Random Forest (Balanced)** | 75.32% | 0.1538 | 0.6919 | **0.2517** | 0.8170 | Non-linear Ensemble |
| **XGBoost (Cost-Sensitive)** | 72.34% | 0.1469 | 0.7514 | 0.2458 | **0.8308** | **✅ Selected Best Model** |

#### 🎯 Task 5: Diagnostic Problem Classifier & Parts Matrix
- **NLP Vectorizer**: TF-IDF (1-2 N-Grams, sublinear term frequency)
- **Classifier**: Random Forest (200 Estimators, Depth 20)
- **Model Accuracy**: **90.90%** (1.00 F1 on Brakes, Engine, and Transmission)
- **Recommendation Engine**: Dual Hybrid Pipeline pairing classification probabilities with deterministic expert rules (`models/diag_rules.json`) recommending `Replace Parts` vs. `Repair Actions`.

---

## 🗄️ Database Architecture (`database/schema.sql`)

The system utilizes an enterprise MySQL normalized schema with automatic zero-configuration SQLite fallback:
- **`users`**: Authentication credentials, SHA-256 password hashes, role-based access (`admin` vs `user`).
- **`vehicles`**: Vehicle catalogs, brands, models, mileage, fuel types, transmission types.
- **`service_requests`**: Service workorders, estimated costs, actual costs, technician ratings, urgency levels.
- **`predictions`**: Master audit log of all multi-model inferences.
- **`insurance_predictions`**: Dedicated insurance claim feasibility and fraud detection telemetry.
- **`diagnosis_results`**: Categorized subsystem classifications, severity rankings, and root causes.
- **`parts_recommendations`**: Itemized replace vs repair parts action logs.

---

## 🚀 Installation & Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/AI_Vehicle_Service_Repair_Insurance_Intelligence.git
cd AI_Vehicle_Service_Repair_Insurance_Intelligence
pip install -r requirements.txt
```

### 2. Preprocess Datasets & Train Pure ML Models
```bash
# 1. Run Data Preprocessing & Metadata Extraction
python preprocessing/01_preprocess_main_dataset.py

# 2. Build Feature Engineering Pipeline
python preprocessing/02_feature_engineering.py

# 3. Train Pure ML Models & Diagnostic Agent
python models/train_diagnosis.py
python models/train_models.py
python models/train_fraud.py

# 4. Generate Model Evaluation & EDA Reports
python models/evaluate_models.py
python preprocessing/generate_eda_reports.py
```

### 3. Run Automated Tests
```bash
python -m unittest tests/test_system.py
```

### 4. Launch the Web Application
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**

#### 🔑 Pre-Configured Demo Accounts:
- **Fleet Admin**: `admin@autointel.ai` / `Admin@123`
- **Technician**: `technician@autointel.ai` / `Technician@123`

---

## 📁 Project Directory Structure

```
AI_Vehicle_Service_Repair_Insurance_Intelligence/
├── datasets/
│   ├── enhanced_motor_vehicle_repair_towing_dataset.csv
│   ├── Used_Car_Dataset.csv
│   ├── fraud_oracle.csv
│   ├── ML Car Diagnostic Agent AI Assistant.csv
│   └── cleaned/
│       ├── main_cleaned.csv
│       ├── main_cleaned_sample.csv
│       └── vehicle_metadata.json
├── preprocessing/
│   ├── __init__.py
│   ├── transformers.py
│   ├── 01_preprocess_main_dataset.py
│   ├── 02_feature_engineering.py
│   ├── generate_eda_reports.py
│   └── generate_notebook.py
├── notebooks/
│   └── EDA_and_Model_Benchmarking.ipynb
├── models/
│   ├── train_models.py
│   ├── train_fraud.py
│   ├── train_diagnosis.py
│   ├── evaluate_models.py
│   ├── cost_model.pkl
│   ├── time_model.pkl
│   ├── insurance_model.pkl
│   ├── fraud_model.pkl
│   ├── diag_model.pkl
│   ├── fe_pipeline.pkl
│   └── diag_rules.json
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── db.py
│   └── predictor.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── predict.html
│   ├── predict_cost.html
│   ├── predict_time.html
│   ├── predict_insurance.html
│   ├── predict_fraud.html
│   ├── add_vehicle.html
│   ├── vehicles.html
│   ├── diagnose.html
│   ├── history.html
│   └── dashboard.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── dashboard.js
├── database/
│   ├── schema.sql
│   └── ai_vehicle_service.db
├── reports/
│   ├── eda/
│   │   ├── main_dataset_distributions.png
│   │   ├── fraud_dataset_distributions.png
│   │   └── eda_statistical_report.md
│   └── evaluation/
│       ├── training_metrics.json
│       ├── diagnostic_report.json
│       ├── fraud_model_summary.md
│       └── model_comparison_summary.md
├── tests/
│   └── test_system.py
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── INTERVIEW_PREPARATION_GUIDE.md
```

---

## 🐳 Docker Deployment

Run with Docker Compose:
```bash
docker-compose up --build
```
This automatically boots a MySQL 8.0 container and the Flask web service.
