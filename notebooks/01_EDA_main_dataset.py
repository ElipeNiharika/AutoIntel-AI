"""
Lightweight EDA script for main_cleaned.csv
Generates missing value report, target distributions, and top-service statistics.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_CLEAN = os.path.join(ROOT, 'datasets', 'cleaned', 'main_cleaned.csv')
OUT_DIR = os.path.join(ROOT, 'reports', 'eda')
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    print('Loading', DATA_CLEAN)
    df = pd.read_csv(DATA_CLEAN)
    print('Shape:', df.shape)

    # Missing value summary
    miss = df.isnull().sum().sort_values(ascending=False)
    miss.to_csv(os.path.join(OUT_DIR, 'missing_values.csv'), header=['missing_count'])

    # Distribution of Total Cost
    if 'Total Cost' in df.columns:
        plt.figure(figsize=(8,5))
        sns.histplot(df['Total Cost'].dropna(), bins=100, kde=True)
        plt.title('Total Cost distribution')
        plt.savefig(os.path.join(OUT_DIR, 'total_cost_dist.png'))
        plt.close()

    # Distribution of Service Duration Hours
    if 'Service Duration Hours' in df.columns:
        plt.figure(figsize=(8,5))
        sns.histplot(df['Service Duration Hours'].dropna(), bins=50, kde=True)
        plt.title('Service Duration Hours distribution')
        plt.savefig(os.path.join(OUT_DIR, 'service_duration_dist.png'))
        plt.close()

    # Top Service Types
    if 'Service Type' in df.columns:
        top = df['Service Type'].value_counts().head(20)
        top.to_csv(os.path.join(OUT_DIR, 'top_service_types.csv'))
        plt.figure(figsize=(10,6))
        sns.barplot(x=top.values, y=top.index)
        plt.title('Top Service Types')
        plt.savefig(os.path.join(OUT_DIR, 'top_service_types.png'))
        plt.close()

    print('EDA outputs saved to', OUT_DIR)


if __name__ == '__main__':
    main()
