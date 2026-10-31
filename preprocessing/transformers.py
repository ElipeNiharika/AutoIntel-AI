import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class FrequencyEncoder(BaseEstimator, TransformerMixin):
    """
    Frequency / Count Encoder for high cardinality categorical features (Brand, Model).
    Replaces categories with their observed frequencies in training data.
    """
    def __init__(self):
        self.maps_ = {}

    def fit(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            for col in X.columns:
                vc = X[col].value_counts(normalize=True, dropna=False)
                self.maps_[col] = vc.to_dict()
        elif isinstance(X, pd.Series):
            self.maps_[X.name or 0] = X.value_counts(normalize=True, dropna=False).to_dict()
        else:
            X_df = pd.DataFrame(X)
            for col in X_df.columns:
                self.maps_[col] = X_df[col].value_counts(normalize=True, dropna=False).to_dict()
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X_out = X.copy()
            for col in X_out.columns:
                mapping = self.maps_.get(col, {})
                X_out[col] = X_out[col].map(mapping).fillna(0.0).astype(float)
            return X_out.values
        elif isinstance(X, pd.Series):
            mapping = self.maps_.get(X.name or 0, {})
            return X.map(mapping).fillna(0.0).astype(float).values.reshape(-1, 1)
        else:
            X_df = pd.DataFrame(X)
            for col in X_df.columns:
                mapping = self.maps_.get(col, {})
                X_df[col] = X_df[col].map(mapping).fillna(0.0).astype(float)
            return X_df.values
