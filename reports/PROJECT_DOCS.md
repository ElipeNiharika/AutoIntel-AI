Project Architecture
--------------------

- Data layer: `datasets/` (raw) → `preprocessing/` scripts → `datasets/cleaned/`
- Modeling: `models/train_models.py` produces `models/*.pkl` artifacts
- Backend: Flask app at `backend/app.py` exposes prediction endpoints and serves templates
- Frontend: minimal templates in `templates/` + CSS in `static/`
- Database: MySQL schema in `database/schema.sql` for users, vehicles, services, predictions

Datasets and usage
- `enhanced_motor_vehicle_repair_towing_dataset.csv` — main dataset for repair cost/time and insurance claim tasks. Preprocessing produces `datasets/cleaned/main_cleaned.csv`.
- `Used_Car_Dataset.csv` — used for vehicle details, dropdowns and optional enrichment.
- `fraud_oracle.csv` — standalone fraud detection and advanced insurance analytics.
- `ML Car Diagnostic Agent AI Assistant.csv` — vehicle problem classification, severity, and rule-based recommendations.

Why keep datasets separate
- Each dataset serves distinct modeling needs and merging without reliable keys can introduce noise. Use lookup joins for brand/model enrichment when string matching confidence is high.

Next steps
- Run preprocessing, inspect `datasets/cleaned/missing_values_report.csv` and `main_cleaned.csv`.
- Open `notebooks/` (to be created) for EDA and visualization.
- Train models via `models/train_models.py`, then start `backend/app.py` to test predictions.
