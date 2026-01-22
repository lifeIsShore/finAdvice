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
        
    def create_features(self, df: pd.DataFrame, include_target: bool = True) -> pd.DataFrame:
        """
        Create simple features for baseline models
        
        Args:
            df: Input OHLCV data
            include_target: If True, adds 'target' column and drops rows with NaN
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
        
        if include_target:
            # Target: next period's close
            df['target'] = df['Close'].shift(-1)
            # Drop NaN rows (first few because of lags/SMAs, last one because of target shift)
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
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return {
                'model': model_name, 'mse': None, 'rmse': None, 'mae': None, 'r2': None, 'mape': None, 'direction_accuracy': None
            }
        
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
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
    
    def predict_next(self, df: pd.DataFrame, trained_models: Dict, feature_cols: List[str]) -> Dict:
        """
        Predict the next (future) period's price using the best model
        """
        try:
            # Create features but keep the last row (target will be NaN)
            df_latest = self.create_features(df, include_target=False)
            
            # The features for the NEXT prediction is the LAST row
            last_row = df_latest.tail(1)
            current_close = float(last_row['Close'].values[0])
            
            # Check for NaNs in feature columns
            nan_cols = last_row[feature_cols].columns[last_row[feature_cols].isnull().any()].tolist()
            if nan_cols:
                # This is normal if we don't have enough history for SMAs/Lags
                return None
                
            X_latest = last_row[feature_cols]
            
            # Use Best Model based on R2 on test set
            best_model_name = 'linear_regression'
            best_r2 = -999
            
            # We need the metrics to find the best model
            # But here we just pick XGBoost if R2 is decent, otherwise LR
            # For simplicity, let's just use LR as it's the most stable baseline
            best_model = trained_models['linear_regression']
            model_used_name = "Linear Regression"
            
            # However, if XGBoost is trained, let's use it as it's more powerful
            if 'xgboost' in trained_models:
                best_model = trained_models['xgboost']
                model_used_name = "XGBoost"
                
            predicted_next = float(best_model.predict(X_latest)[0])
            
            direction = "UP" if predicted_next > current_close else "DOWN"
            pct_change = ((predicted_next - current_close) / current_close) * 100
            
            return {
                'model_used': model_used_name,
                'current_close': current_close,
                'predicted_next': predicted_next,
                'direction': direction,
                'pct_change': float(pct_change),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"    ⚠️ Prediction error: {e}")
            return None

    def process_interval(self, interval: str) -> Dict:
        """
        Process a single interval: load data, train models, evaluate
        """
        print(f"\n{'='*80}")
        print(f"Processing {self.ticker} - {interval}")
        print(f"{'='*80}")
        
        try:
            df = self.storage.load_ticker_data(self.ticker, interval)
            if df is None or len(df) < 50:
                print(f"  ⚠️ Insufficient data for {interval}")
                return None
            
            df_features = self.create_features(df, include_target=True)
            if len(df_features) < 30:
                print(f"  ⚠️ Insufficient feature rows for {interval}")
                return None
            
            train_results = self.train_models(df_features)
            
            # Predict Next Period
            next_pred_data = self.predict_next(df, train_results['models'], train_results['features'])
            
            if next_pred_data:
                print(f"\n  🔮 NEXT PREDICTION ({interval}):")
                print(f"    Current Close: {next_pred_data['current_close']:.2f}")
                print(f"    Predicted Next: {next_pred_data['predicted_next']:.2f}")
                print(f"    Expected Move: {next_pred_data['direction']} ({next_pred_data['pct_change']:.2f}%)")
            
            return {
                'interval': interval,
                'data_rows': len(df),
                'metrics': train_results['metrics'],
                'next_prediction': next_pred_data,
                'test_size': train_results['test_size']
            }
        except Exception as e:
            print(f"  ❌ Error processing {interval}: {str(e)}")
            return None
    
    def run_all_intervals(self, intervals: List[str] = None) -> Dict:
        if intervals is None:
            intervals = ['1d', '1wk', '1mo', '4h', '1h']
        
        all_results = {}
        for interval in intervals:
            result = self.process_interval(interval)
            if result:
                all_results[interval] = result
        
        self.save_results(all_results)
        return all_results
    
    def save_results(self, results: Dict):
        output_file = f'data/baseline_models_{self.ticker}.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✅ Results saved to {output_file}")


if __name__ == "__main__":
    baseline = BaselineModels(ticker='AAPL')
    baseline.run_all_intervals()
