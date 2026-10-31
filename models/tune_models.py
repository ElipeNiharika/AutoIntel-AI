import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score
import xgboost as xgb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(ROOT, 'datasets', 'cleaned', 'main_cleaned.csv')
OUT_DIR = os.path.join(ROOT, 'reports', 'tuning')
os.makedirs(OUT_DIR, exist_ok=True)


def tune_cost():
    df = pd.read_csv(DATA_PATH)
    if 'Total Cost' not in df.columns:
        print('No Total Cost')
        return
    X = df.drop(columns=['Total Cost']).fillna(0)
    y = df['Total Cost']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    param_grid = {'n_estimators':[100,200], 'max_depth':[6,12]}
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    gs = GridSearchCV(model, param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
    gs.fit(X_train, y_train)
    best = gs.best_estimator_
    joblib.dump(best, os.path.join(ROOT,'models','cost_model.pkl'))
    with open(os.path.join(OUT_DIR,'cost_tuning.txt'),'w') as f:
        f.write(str(gs.best_params_))
    print('Cost tuning done')


def tune_insurance():
    df = pd.read_csv(DATA_PATH)
    if 'Insurance Claim Used_flag' not in df.columns:
        print('No insurance flag')
        return
    X = df.drop(columns=['Insurance Claim Used_flag']).fillna(0)
    y = df['Insurance Claim Used_flag'].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    param_grid = {'n_estimators':[100,200], 'max_depth':[6,12]}
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    gs = GridSearchCV(model, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    gs.fit(X_train, y_train)
    best = gs.best_estimator_
    joblib.dump(best, os.path.join(ROOT,'models','insurance_model.pkl'))
    with open(os.path.join(OUT_DIR,'insurance_tuning.txt'),'w') as f:
        f.write(str(gs.best_params_))
    print('Insurance tuning done')


def main():
    tune_cost()
    tune_insurance()


if __name__ == '__main__':
    main()
