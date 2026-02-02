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
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, confusion_matrix, roc_curve, auc, precision_score, recall_score, f1_score
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
            'features': feature_cols,
            'X_test': X_test,
            'y_test': y_test
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
            print(f"    [WARNING] Prediction error: {e}")
            return None
    
    def generate_diagnostics(self, y_true, y_pred, model, model_name: str, feature_cols: List[str]) -> Dict:
        """
        Generate comprehensive diagnostics for a model including ROC, confusion matrix, feature importance
        """
        diagnostics = {}
        
        # Clean data
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]
        
        if len(y_true_clean) < 10:
            return {}
        
        # 1. Residuals for scatter plot
        residuals = y_true_clean - y_pred_clean
        diagnostics['residuals'] = {
            'actual': y_true_clean.tolist(),
            'predicted': y_pred_clean.tolist(),
            'residuals': residuals.tolist()
        }
        
        # 2. Classification metrics (direction prediction)
        y_true_series = pd.Series(y_true_clean).reset_index(drop=True)
        y_pred_series = pd.Series(y_pred_clean).reset_index(drop=True)
        
        true_direction = (y_true_series.diff() > 0).astype(int).iloc[1:]  # Skip first NaN
        pred_direction = (y_pred_series.diff() > 0).astype(int).iloc[1:]
        
        if len(true_direction) > 0:
            # Confusion Matrix
            cm = confusion_matrix(true_direction, pred_direction)
            diagnostics['confusion_matrix'] = cm.tolist()
            
            # Precision, Recall, F1
            try:
                precision = precision_score(true_direction, pred_direction, zero_division=0)
                recall = recall_score(true_direction, pred_direction, zero_division=0)
                f1 = f1_score(true_direction, pred_direction, zero_division=0)
                
                diagnostics['classification_metrics'] = {
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1)
                }
            except:
                diagnostics['classification_metrics'] = {'precision': 0, 'recall': 0, 'f1_score': 0}
            
            # ROC Curve (using prediction probabilities if available, else use predictions as scores)
            try:
                fpr, tpr, thresholds = roc_curve(true_direction, pred_direction)
                roc_auc = auc(fpr, tpr)
                
                diagnostics['roc_curve'] = {
                    'fpr': fpr.tolist(),
                    'tpr': tpr.tolist(),
                    'auc': float(roc_auc)
                }
            except:
                diagnostics['roc_curve'] = {'fpr': [], 'tpr': [], 'auc': 0.5}
        
        # 3. Feature Importance (for tree-based models)
        if model_name in ['Random Forest', 'XGBoost'] and hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_importance = [
                {'feature': feat, 'importance': float(imp)} 
                for feat, imp in zip(feature_cols, importances)
            ]
            # Sort by importance
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            diagnostics['feature_importance'] = feature_importance[:10]  # Top 10
        
        return diagnostics
    
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
                print(f"  [!] Insufficient data for {interval}")
                return None
            
            df_features = self.create_features(df, include_target=True)
            if len(df_features) < 30:
                print(f"  [!] Insufficient feature rows for {interval}")
                return None
            
            train_results = self.train_models(df_features)
            
            # Generate diagnostics for each model
            diagnostics = {}
            X_test = train_results['X_test']
            y_test = train_results['y_test']
            feature_cols = train_results['features']
            
            for model_name, model in train_results['models'].items():
                y_pred = model.predict(X_test)
                diagnostics[model_name.lower().replace(' ', '_')] = self.generate_diagnostics(
                    y_test, y_pred, model, model_name, feature_cols
                )
            
            # Save diagnostics to file
            diagnostics_dir = Path('data/model_diagnostics')
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            diagnostics_file = diagnostics_dir / f"{self.ticker}_{interval}_diagnostics.json"
            with open(diagnostics_file, 'w') as f:
                json.dump(diagnostics, f, indent=2, default=str)
            
            # Predict Next Period
            next_pred_data = self.predict_next(df, train_results['models'], train_results['features'])
            
            if next_pred_data:
                print(f"\n  [PREDICTION] Next for {interval}:")
                print(f"    Current Close: {next_pred_data['current_close']:.2f}")
                print(f"    Predicted Next: {next_pred_data['predicted_next']:.2f}")
                print(f"    Expected Move: {next_pred_data['direction']} ({next_pred_data['pct_change']:.2f}%)")
            
            return {
                'interval': interval,
                'data_rows': len(df),
                'metrics': train_results['metrics'],
                'next_prediction': next_pred_data,
                'test_size': train_results['test_size'],
                'diagnostics_file': str(diagnostics_file)
            }
        except Exception as e:
            print(f"  [ERROR] Error processing {interval}: {str(e)}")
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
        print(f"\n[OK] Results saved to {output_file}")

    def identify_winner(self, metrics: Dict) -> str:
        """
        Identify the winning model based on a composite score.
        Score = (Direction_Accuracy * 0.6) + ((1 - normalized_rmse) * 0.4)
        """
        best_score = -float('inf')
        winner = "linear_regression" # Default fallback
        
        # We need to normalize RMSE to make it comparable
        # Find max RMSE to normalize
        all_rmses = [m['rmse'] for m in metrics.values() if m['rmse'] is not None]
        if not all_rmses:
            return winner
            
        max_rmse = max(all_rmses) if max(all_rmses) > 0 else 1.0
        
        print("\n*** MODEL COMPETITION ***")
        print(f"{'Model':<20} | {'Acc %':<8} | {'RMSE':<8} | {'Score':<8}")
        print("-" * 55)
        
        for model_name, m in metrics.items():
            if m['rmse'] is None: 
                continue
                
            # Direction Accuracy (0-100) -> normalize to 0-1
            acc = m['direction_accuracy'] / 100.0
            
            # RMSE Score (0-1): Lower RMSE is better. 
            # 1 - (rmse / max_rmse) gives 1 for best (0 error) and 0 for worst (max error)
            rmse_score = 1.0 - (m['rmse'] / max_rmse)
            
            # Composite Score
            # Weight Accuracy MUCH higher (0.8) because Direction is KEY for trading
            # RMSE is secondary (0.2) - we care more about getting direction right than exact price
            final_score = (acc * 0.8) + (rmse_score * 0.2)
            
            print(f"{model_name:<20} | {m['direction_accuracy']:<8.1f} | {m['rmse']:<8.4f} | {final_score:<8.4f}")
            
            if final_score > best_score:
                best_score = final_score
                winner = model_name
                
        print(f">> WINNER: {winner.upper()}\n")
        return winner


if __name__ == "__main__":
    baseline = BaselineModels(ticker='AAPL')
    baseline.run_all_intervals()
