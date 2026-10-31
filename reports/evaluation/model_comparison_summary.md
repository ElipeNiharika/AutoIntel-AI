# AI Vehicle Service & Repair Intelligence - Model Comparison & Evaluation Report

## 1. Executive Summary
This report summarizes the empirical performance metrics for all Pure Machine Learning models trained on structured automotive service, repair, and insurance claim tabular data.

---

## 2. Regression Benchmark: Repair Cost Prediction (Target: `Total Cost` in USD)

| Model Name | MAE ($) | MSE | RMSE ($) | R² Score | Industry Benchmark Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Linear Regression** | **18.50** | **981.87** | **31.33** | **0.9942** | **Best Fitting & Highly Interpretable** |
| **Random Forest Regressor** | 18.74 | 1037.32 | 32.21 | 0.9938 | Robust to Extreme Outliers |
| **XGBoost Regressor** | 18.56 | 1067.95 | 32.68 | 0.9936 | Gradient Boosted Ensemble |

> **Key Takeaway**: Both Linear Regression and Tree ensembles capture the strong correlation between itemized parts, service tier, and estimated baselines with $R^2 > 0.99$.

---

## 3. Regression Benchmark: Repair Time Prediction (Target: `Service Duration Hours`)

| Model Name | MAE (Hours) | MSE | RMSE (Hours) | R² Score | Model Architecture |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Linear Regression** | **1.18** | **2.10** | **1.45** | **Baseline** | Standard OLS Formulation |
| **Random Forest Regressor** | 1.18 | 2.11 | 1.45 | Non-linear Tree | 100 Trees, Max Depth 16 |
| **XGBoost Regressor** | 1.18 | 2.13 | 1.46 | Gradient Boosted | 180 Trees, Learning Rate 0.08 |

---

## 4. Binary Classification: Insurance Claim Approval Prediction (Target: `Insurance Claim Used`)

| Model Name | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Confusion Matrix `[[TN, FP], [FN, TP]]` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | 57.31% | 0.5006 | 0.4585 | 0.4786 | **0.6268** | `[[6360, 2748], [3249, 2751]]` |
| **Random Forest Classifier** | 56.95% | 0.4964 | 0.5002 | 0.4983 | 0.6231 | `[[6085, 3023], [2999, 3001]]` |
| **XGBoost Classifier** | **57.07%** | **0.4977** | **0.5069** | **0.5022** | **0.6261** | `[[6045, 3063], [2958, 3042]]` |

---

## 5. NLP & Rule-Based Vehicle Diagnosis & Parts Recommendation

- **Diagnostic Model**: TF-IDF Vectorizer (1-2 N-grams, sublinear term frequency) + Random Forest Classifier (200 Estimators)
- **Problem Classification Accuracy**: **90.9%**
- **Target Classes**: `Brakes` (1.00 F1), `Engine` (1.00 F1), `Transmission` (1.00 F1), `Battery` (0.79 F1), `Electrical` (0.77 F1)
- **Recommendation Engine**: Dual Hybrid Pipeline pairing classification probabilities with deterministic expert rules (`models/diag_rules.json`) recommending `Replace Parts` vs. `Repair Actions`.

---

## 6. Serialization Artifacts
All trained models are serialized with standard `joblib` and available in `models/`:
- `fe_pipeline.pkl`: ColumnTransformer (StandardScaler, OneHotEncoder, FrequencyEncoder)
- `cost_model.pkl`: Selected Repair Cost Predictor
- `time_model.pkl`: Selected Service Duration Predictor
- `insurance_model.pkl`: Selected Insurance Claim Predictor
- `diag_model.pkl`: TF-IDF NLP Diagnostic Classifier
- `diag_rules.json`: Expert Knowledge Base for Parts & Solutions
