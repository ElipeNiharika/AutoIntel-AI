# 🛡️ Insurance Fraud Detection Model Benchmark Report (Dataset 3)
*Target: `FraudFound_P` (0 = Genuine Claim, 1 = Fraudulent Claim)*
*Dataset: `fraud_oracle.csv` (15,420 total policy claim records)*

---

## 📊 Comparative Performance Summary

| Model Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Production Selected |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Balanced)** | 64.23% | 0.1316 | 0.8865 | 0.2292 | 0.8074 | No |
| **Random Forest (Balanced)** | 75.32% | 0.1538 | 0.6919 | 0.2517 | 0.8170 | No |
| **XGBoost (Cost-Sensitive)** | 72.34% | 0.1469 | 0.7514 | 0.2458 | 0.8308 | ✅ Yes |

---

## 🎯 Key Architectural Distinction: Claim Approval vs. Fraud Detection

In our architecture:
1. **Insurance Claim Prediction (Dataset 1)** forecasts whether routine automotive repair items are reimbursable under standard policy warranties.
2. **Insurance Fraud Detection (Dataset 3)** identifies deceptive policy claims by analyzing driver demographics, accident reporting delays, policy tenure, and previous claim histories.
