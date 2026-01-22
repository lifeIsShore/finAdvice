"""
Baseline Models Visualization
Creates comparison charts for each ticker separately
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config import DEFAULT_TICKERS

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class ModelVisualizer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.results_file = Path(f'data/baseline_models_{ticker}.json')
        self.output_dir = Path(f'data/visualizations/{ticker}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found for {ticker}")
            
        with open(self.results_file, 'r') as f:
            self.results = json.load(f)

    def generate_all(self):
        print(f"  Generating comparison charts for {self.ticker}...")
        self.create_r2_comparison()
        self.create_direction_accuracy()
        self.create_mape_comparison()
        self.create_metrics_heatmap()

    def create_r2_comparison(self):
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Reg', 'Random Forest', 'XGBoost', 'SMA']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            r2_values = [self.results[interval]['metrics'][model]['r2'] if self.results[interval]['metrics'][model]['r2'] is not None else 0 for interval in intervals]
            ax.bar(x + i * width, r2_values, width, label=name)
        
        ax.set_title(f'R² Score by Interval - {self.ticker}')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'r2_comparison.png', dpi=150)
        plt.close()

    def create_direction_accuracy(self):
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Reg', 'Random Forest', 'XGBoost', 'SMA']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            acc_values = [self.results[interval]['metrics'][model]['direction_accuracy'] if self.results[interval]['metrics'][model]['direction_accuracy'] is not None else 0 for interval in intervals]
            ax.bar(x + i * width, acc_values, width, label=name)
        
        ax.set_title(f'Direction Accuracy (%) - {self.ticker}')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.axhline(50, color='red', linestyle='--', alpha=0.3)
        ax.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_accuracy.png', dpi=150)
        plt.close()

    def create_mape_comparison(self):
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Reg', 'Random Forest', 'XGBoost', 'SMA']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            mape_values = [self.results[interval]['metrics'][model]['mape'] if self.results[interval]['metrics'][model]['mape'] is not None else 0 for interval in intervals]
            ax.bar(x + i * width, mape_values, width, label=name)
        
        ax.set_title(f'MAPE (%) - {self.ticker} (Lower is Better)')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'mape_comparison.png', dpi=150)
        plt.close()

    def create_metrics_heatmap(self):
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Reg', 'Random Forest', 'XGBoost', 'SMA']
        
        data = []
        for model in models:
            row = [self.results[interval]['metrics'][model]['r2'] if self.results[interval]['metrics'][model]['r2'] is not None else 0 for interval in intervals]
            data.append(row)
        
        df = pd.DataFrame(data, index=model_names, columns=[i.upper() for i in intervals])
        plt.figure(figsize=(10, 4))
        sns.heatmap(df, annot=True, cmap='RdYlGn', vmin=-1, vmax=1)
        plt.title(f'R² Score Heatmap - {self.ticker}')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'metrics_heatmap.png', dpi=150)
        plt.close()


if __name__ == "__main__":
    print("\nStarting Multi-Ticker Comparison Analysis...")
    for ticker in DEFAULT_TICKERS:
        try:
            viz = ModelVisualizer(ticker)
            viz.generate_all()
        except Exception as e:
            print(f"  ⚠️ Skipping {ticker}: {str(e)}")
