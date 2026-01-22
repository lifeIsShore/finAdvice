"""
Baseline ML Models for Price Prediction
Creates simple models for each interval to predict next period's closing price

Models:
1. Linear Regression (baseline)
2. Random Forest
3. XGBoost
4. Simple Moving Average (benchmark)

For each interval, we predict the next period's close price.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

# Import from core
from core.data_storage import DataStorage


class BaselineModels:
    """
    Create and evaluate baseline ML models for price prediction
    """
    
    def __init__(self, ticker: str = 'AAPL'):
        self.ticker = ticker
        self.storage = DataStorage()
        self.results = {}
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create simple features for baseline models
        
        Features:
        - Previous N closes (lag features)
        - Simple moving averages
        - Returns
        """
        df = df.copy()
        
        # Lag features (previous closes)
        for i in range(1, 6):
            df[f'close_lag_{i}'] = df['Close'].shift(i)
        
        # Moving averages
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_10'] = df['Close'].rolling(window=10).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        
        # Returns
        df['return_1'] = df['Close'].pct_change(1)
        df['return_5'] = df['Close'].pct_change(5)
        
        # Volatility
        df['volatility_5'] = df['Close'].rolling(window=5).std()
        df['volatility_10'] = df['Close'].rolling(window=10).std()
        
        # Volume features
        df['volume_sma_5'] = df['Volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_5']
        
        # Target: next period's close
        df['target'] = df['Close'].shift(-1)
        
        # Drop NaN rows
        df = df.dropna()
        
        return df
    
    def train_models(self, df: pd.DataFrame) -> Dict:
        """
        Train multiple baseline models and return metrics
        """
        # Prepare features and target
        feature_cols = [col for col in df.columns if col not in ['Date', 'target', 'Open', 'High', 'Low', 'Close', 'Volume']]
        X = df[feature_cols]
        y = df['target']
        
        # Time series split (80/20)
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        models = {}
        metrics = {}
        
        # 1. Linear Regression
        print("  Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        y_pred_lr = lr.predict(X_test)
        models['linear_regression'] = lr
        metrics['linear_regression'] = self.calculate_metrics(y_test, y_pred_lr, 'Linear Regression')
        
        # 2. Random Forest
        print("  Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        y_pred_rf = rf.predict(X_test)
        models['random_forest'] = rf
        metrics['random_forest'] = self.calculate_metrics(y_test, y_pred_rf, 'Random Forest')
        
        # 3. XGBoost
        print("  Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        y_pred_xgb = xgb_model.predict(X_test)
        models['xgboost'] = xgb_model
        metrics['xgboost'] = self.calculate_metrics(y_test, y_pred_xgb, 'XGBoost')
        
        # 4. Simple Moving Average (benchmark)
        print("  Calculating SMA Benchmark...")
        # Use last 5 periods average as prediction
        sma_pred = df['Close'].rolling(window=5).mean().shift(1)[split_idx:].values
        # Align with test set
        sma_pred = sma_pred[:len(y_test)]
        y_test_aligned = y_test[:len(sma_pred)]
        metrics['sma_benchmark'] = self.calculate_metrics(y_test_aligned, sma_pred, 'SMA Benchmark')
        
        return {
            'models': models,
            'metrics': metrics,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'features': feature_cols
        }
    
    def calculate_metrics(self, y_true, y_pred, model_name: str) -> Dict:
        """
        Calculate comprehensive metrics for model evaluation
        """
        # Remove any NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return {
                'model': model_name,
                'mse': None,
                'rmse': None,
                'mae': None,
                'r2': None,
                'mape': None,
                'direction_accuracy': None
            }
        
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Direction accuracy (did we predict up/down correctly?)
        y_true_series = pd.Series(y_true).reset_index(drop=True)
        y_pred_series = pd.Series(y_pred).reset_index(drop=True)
        
        true_direction = (y_true_series.diff() > 0).astype(int)
        pred_direction = (y_pred_series.diff() > 0).astype(int)
        
        direction_accuracy = (true_direction == pred_direction).sum() / len(true_direction) * 100
        
        return {
            'model': model_name,
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'mape': float(mape),
            'direction_accuracy': float(direction_accuracy)
        }
    
    def process_interval(self, interval: str) -> Dict:
        """
        Process a single interval: load data, train models, evaluate
        """
        print(f"\n{'='*80}")
        print(f"Processing {self.ticker} - {interval}")
        print(f"{'='*80}")
        
        try:
            # Load data
            df = self.storage.load_ticker_data(self.ticker, interval)
            
            if df is None or len(df) < 50:
                print(f"  ⚠️ Insufficient data for {interval} (need at least 50 rows)")
                return None
            
            print(f"  Loaded {len(df)} rows")
            
            # Create features
            print("  Creating features...")
            df_features = self.create_features(df)
            print(f"  Created {len(df_features)} feature rows (after dropping NaN)")
            
            if len(df_features) < 30:
                print(f"  ⚠️ Insufficient feature rows for {interval}")
                return None
            
            # Train models
            print("  Training models...")
            results = self.train_models(df_features)
            
            # Print results
            print(f"\n  Results for {interval}:")
            print(f"  Train size: {results['train_size']}, Test size: {results['test_size']}")
            print(f"\n  Model Performance:")
            
            for model_name, metrics in results['metrics'].items():
                print(f"\n    {metrics['model']}:")
                print(f"      RMSE: {metrics['rmse']:.4f}")
                print(f"      MAE: {metrics['mae']:.4f}")
                print(f"      R²: {metrics['r2']:.4f}")
                print(f"      MAPE: {metrics['mape']:.2f}%")
                print(f"      Direction Accuracy: {metrics['direction_accuracy']:.2f}%")
            
            return {
                'interval': interval,
                'data_rows': len(df),
                'feature_rows': len(df_features),
                'train_size': results['train_size'],
                'test_size': results['test_size'],
                'features_used': results['features'],
                'metrics': results['metrics']
            }
            
        except Exception as e:
            print(f"  ❌ Error processing {interval}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_all_intervals(self, intervals: List[str] = None) -> Dict:
        """
        Run baseline models for all intervals
        """
        if intervals is None:
            # Focus on main intervals
            intervals = ['1d', '1wk', '1mo', '4h', '1h']
        
        print(f"\n{'='*80}")
        print(f"BASELINE ML MODELS - {self.ticker}")
        print(f"{'='*80}")
        print(f"Intervals to process: {', '.join(intervals)}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {}
        
        for interval in intervals:
            result = self.process_interval(interval)
            if result:
                all_results[interval] = result
        
        # Save results
        self.save_results(all_results)
        
        # Print summary
        self.print_summary(all_results)
        
        return all_results
    
    def save_results(self, results: Dict):
        """
        Save results to JSON file
        """
        output_file = f'data/baseline_models_{self.ticker}.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Results saved to {output_file}")
    
    def print_summary(self, results: Dict):
        """
        Print summary comparison of all models across intervals
        """
        print(f"\n{'='*80}")
        print("SUMMARY - BEST MODELS BY INTERVAL")
        print(f"{'='*80}")
        
        for interval, result in results.items():
            if result is None:
                continue
            
            metrics = result['metrics']
            
            # Find best model by R²
            best_model = max(metrics.items(), key=lambda x: x[1]['r2'] if x[1]['r2'] is not None else -999)
            
            print(f"\n{interval.upper()}:")
            print(f"  Best Model: {best_model[1]['model']}")
            print(f"  R²: {best_model[1]['r2']:.4f}")
            print(f"  RMSE: {best_model[1]['rmse']:.4f}")
            print(f"  Direction Accuracy: {best_model[1]['direction_accuracy']:.2f}%")
            print(f"  Test Size: {result['test_size']} samples")


if __name__ == "__main__":
    # Run baseline models for AAPL
    print("Starting Baseline ML Models...")
    
    baseline = BaselineModels(ticker='AAPL')
    results = baseline.run_all_intervals()
    
    print(f"\n{'='*80}")
    print("✅ BASELINE MODELS COMPLETE!")
    print(f"{'='*80}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nCheck data/baseline_models_AAPL.json for detailed results")
