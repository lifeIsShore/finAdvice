"""
Decision Making ML Application for Stock Trading (Enhanced)
Predicts "Get In" (buy) and "Get Out" (sell) points with Multi-Timeframe Consensus.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

import sys
import os

# Add the current directory to sys.path to allow imports from core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.data_storage import DataStorage
from core.news_fetcher import NewsFetcher
from features.sentiment_analysis import SentimentProcessor
from baseline_models import BaselineModels
import xgboost as xgb
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from consensus_engine import MultiTimeframeConsensus

class DecisionMakingML:
    def __init__(self, ticker: str = 'AAPL'):
        self.ticker = ticker
        # Use the parent directory of algotrade_datascience as base
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Go up one level from algotrade_datascience
        self.storage = DataStorage(base_dir=parent_dir)
        self.news_fetcher = NewsFetcher()
        try:
            self.sentiment_processor = SentimentProcessor()
        except Exception as e:
            print(f"Warning: Could not initialize SentimentProcessor: {e}")
            self.sentiment_processor = None
        
        # Initialize Baseline Models for Competition
        self.baseline_models = BaselineModels(ticker)
        
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add robust technical indicators for better decision making"""
        try:
            df = df.copy()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Moving Averages & Crossovers
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_10_20_cross'] = df['SMA_10'] - df['SMA_20']
            
            # Bollinger Bands
            df['BB_Mid'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
            df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(window=14).mean()
            
            # Momentum & Volatility (Standardized)
            df['Momentum'] = df['Close'].pct_change(5) * 100
            df['Volatility'] = df['Close'].pct_change().rolling(window=20).std() * 100
            
            # Volume Ratio (Standardized)
            df['volume_ratio'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
            
            # Lagged Return features (Standardized)
            for i in range(1, 4):
                df[f'Lag_{i}'] = df['Close'].pct_change().shift(i) * 100
            
            # CRITICAL FIX: Drop NaN values after all calculations
            df = df.dropna()
            
            if len(df) < 20:
                print(f"Warning: Not enough data after adding indicators. Got {len(df)} rows")
                return None
                
            return df
        except Exception as e:
            print(f"Error adding technical indicators: {e}")
            return None

    def prepare_targets(self, df: pd.DataFrame, horizon: int = 20) -> pd.DataFrame:
        """Prepare targets for ML: Max High and Min Low % return in next N days"""
        try:
            df = df.copy()
            future_max = df['High'].shift(-horizon).rolling(window=horizon, min_periods=1).max()
            future_min = df['Low'].shift(-horizon).rolling(window=horizon, min_periods=1).min()
            
            df['target_max_return'] = (future_max - df['Close']) / df['Close']
            df['target_min_return'] = (future_min - df['Close']) / df['Close']
            
            # Remove NaN and infinite values
            df = df.dropna()
            df = df[~np.isinf(df['target_max_return'])]
            df = df[~np.isinf(df['target_min_return'])]
            
            return df
        except Exception as e:
            print(f"Error preparing targets: {e}")
            return None

    def get_sentiment_multiplier(self):
        """Analyze current news sentiment to adjust targets"""
        if not self.sentiment_processor:
            return 1.0, 0.0
        
        try:
            news_df = self.news_fetcher.fetch_ticker_news(self.ticker)
            if news_df.empty:
                return 1.0, 0.0
            
            heads = [str(t) for t in news_df['title'].head(10).tolist() if t and str(t).strip()]
            if not heads:
                return 1.0, 0.0
            results = self.sentiment_processor.analyze_sentiment(heads)
            
            avg_score = sum(r['sentiment_score'] for r in results) / len(results)
            
            # Bullish sentiment (>0.3) can boost target by up to 5%
            # Bearish sentiment (<-0.3) can lower target by up to 5%
            multiplier = 1.0 + (avg_score * 0.05) if abs(avg_score) > 0.2 else 1.0
            return multiplier, avg_score
        except Exception as e:
            print(f"Sentiment Analysis failed: {e}")
            return 1.0, 0.0
            
    def get_sentiment_level(self, pct_change: float) -> dict:
        """Return emoji, color, and level based on % change"""
        if pct_change > 2.0:
            return {"level": "Dramatic UP", "emoji": "+++", "color": "#00C853", "label": "DRAMATICALLY_UP"}
        elif pct_change > 1.0:
            return {"level": "Strong UP", "emoji": "++", "color": "#2ecc71", "label": "STRONGLY_UP"}
        elif pct_change > 0.2:
            return {"level": "Up", "emoji": "+", "color": "#3498db", "label": "UP"}
        elif pct_change > -0.2:
            return {"level": "Neutral", "emoji": "=", "color": "#95a5a6", "label": "NEUTRAL"}
        elif pct_change > -1.0:
            return {"level": "Down", "emoji": "-", "color": "#e74c3c", "label": "DOWN"}
        elif pct_change > -2.0:
            return {"level": "Strong DOWN", "emoji": "--", "color": "#c0392b", "label": "STRONGLY_DOWN"}
        else:
            return {"level": "Dramatic DOWN", "emoji": "---", "color": "#2c3e50", "label": "DRAMATICALLY_DOWN"}


    def get_multi_timeframe_consensus(self, baseline_results: Dict = None):
        """
        Run a full model competition for EACH timeframe using the Consensus Engine.
        Optional: Use pre-calculated baseline_results to ensure consistency.
        """
        try:
            print("\n=== MULTI-TIMEFRAME ML CONSENSUS ===")
            print(f"Running model competition for {self.ticker}...")
            
            engine = MultiTimeframeConsensus(self.storage, self.ticker)
            report = engine.generate_consensus()
            
            if not report:
                print("  [Warning] Could not generate consensus report")
                return 0.0, {}
            
            # PATCH: Overwrite consensus metrics with baseline metrics if provided
            # This ensures Dashboard and Analytics match EXACTLY
            if baseline_results:
                print("  [Sync] Patching consensus metrics with baseline models results...")
                for interval, results in baseline_results.items():
                    if interval in report.intervals:
                        consensus_interval = report.intervals[interval]
                        baseline_metrics = results['metrics']
                        
                        # Map metrics by model name (normalization)
                        for c_model in consensus_interval.models:
                            # Normalize names for matching
                            m_name_lookup = c_model.model_name.lower().replace(' ', '_')
                            if m_name_lookup in baseline_metrics:
                                b_m = baseline_metrics[m_name_lookup]
                                c_model.accuracy = b_m['direction_accuracy']
                                c_model.rmse = b_m['rmse']
                                c_model.r2_score = b_m['r2']
                                c_model.mape = b_m['mape']
                
                # Re-select winning models after patching to ensure consistency in best_model
                for interval, data in report.intervals.items():
                    if data.models:
                        min_rmse = min([m.rmse for m in data.models])
                        data.best_model = max(data.models, key=lambda m: (m.accuracy * 0.8) + ((min_rmse / (m.rmse + 1e-9)) * 20))
            
            # Print summary to console
            print(f"  Consensus Generated! Confidence: {report.overall_confidence:.1f}%")
            return report.overall_confidence, report.to_dict()['intervals']
            
        except Exception as e:
            print(f"[CRITICAL ERROR] Consensus generation failed: {e}")
            import traceback
            traceback.print_exc()
            return 0.0, {}

    def is_crypto(self):
        ticker_up = self.ticker.upper()
        return "-USD" in ticker_up or "-EUR" in ticker_up or ticker_up in ['BTC', 'ETH', 'SOL']

    def _build_model_competition_data(self, consensus_details: dict) -> dict:
        """Helper to format consensus model data for the UI competition table"""
        try:
            # Use '1d' as the primary source for competition metrics, fallback to '4h' or first available
            target_interval = '1d'
            if target_interval not in consensus_details:
                if '4h' in consensus_details:
                    target_interval = '4h'
                elif consensus_details:
                    target_interval = list(consensus_details.keys())[0]
                else:
                    return {}

            data = consensus_details[target_interval]
            winner = data.get('best_model', 'Unknown')
            models = data.get('models', [])
            
            metrics = {}
            for m in models:
                # Map consensus fields to UI expected fields
                # UI expects: direction_accuracy, rmse
                # Consensus has: accuracy, rmse
                metrics[m['model_name']] = {
                    'direction_accuracy': m.get('accuracy', 0.0),
                    'rmse': m.get('rmse', 0.0),
                    'r2': m.get('r2_score', 0.0),
                    'mae': m.get('mape', 0.0)
                }
            
            return {
                "winner": winner,
                "metrics": metrics
            }
        except Exception as e:
            print(f"Error building model competition data: {e}")
            return {}

    def train_and_predict(self, df: pd.DataFrame, horizon: int = 60, risk: str = 'conservative', baseline_results: Dict = None):
        """Train models and make predictions for the current date"""
        try:
            df_rich = self.add_technical_indicators(df)
            if df_rich is None:
                raise ValueError("Failed to add technical indicators")
            
            df_prepared = self.prepare_targets(df_rich, horizon=horizon)
            if df_prepared is None or len(df_prepared) == 0:
                raise ValueError("Failed to prepare targets or insufficient data")
            
            feature_cols = [
                'Close', 'RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_10_20_cross',
                'BB_Upper', 'BB_Lower', 'MACD', 'Signal_Line', 'ATR', 'Momentum', 'Volatility',
                'volume_ratio', 'Lag_1', 'Lag_2', 'Lag_3'
            ]
            
            # Verify all feature columns exist
            missing_cols = [col for col in feature_cols if col not in df_prepared.columns]
            if missing_cols:
                raise ValueError(f"Missing columns: {missing_cols}")
            
            X = df_prepared[feature_cols]
            
            # Remove any NaN or infinite values
            valid_mask = ~(X.isna().any(axis=1) | np.isinf(X.values).any(axis=1))
            X = X[valid_mask]
            y_max = df_prepared.loc[valid_mask, 'target_max_return']
            y_min = df_prepared.loc[valid_mask, 'target_min_return']
            
            if len(X) < 20:
                raise ValueError(f"Insufficient data for training. Got {len(X)} rows")
            
            # Train High/Low models
            model_high = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
            model_low = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
            
            model_high.fit(X, y_max)
            model_low.fit(X, y_min)
            
            X_latest = df_rich[feature_cols].dropna().tail(1)
            if len(X_latest) == 0:
                raise ValueError("No valid data for latest prediction")
            
            latest_data = df_rich.loc[X_latest.index]
            
            current_price = float(latest_data['Close'].values[0])
            current_date = latest_data.index[0] if hasattr(latest_data.index[0], 'isoformat') else str(latest_data.index[0])
            
            predicted_max_ret = float(np.nan_to_num(model_high.predict(X_latest)[0], nan=0.0))
            predicted_min_ret = float(np.nan_to_num(model_low.predict(X_latest)[0], nan=0.0))
            
            # IMPORTANT: Run the NEW Multi-Timeframe Consensus with baseline synchronization
            confidence, consensus_details = self.get_multi_timeframe_consensus(baseline_results=baseline_results)
            
            # Apply sentiment multiplier
            s_multiplier, s_score = self.get_sentiment_multiplier()
            if s_multiplier > 1.0:
                predicted_max_ret *= s_multiplier
                
            is_crypto = self.is_crypto()
            
            # Risk thresholds
            if risk == 'aggressive':
                dip_threshold = -0.05 if not is_crypto else -0.08
                exit_threshold = 0.08 if not is_crypto else 0.15
                stop_loss_pct = 0.05 if not is_crypto else 0.10
            else: # conservative
                dip_threshold = -0.08 if not is_crypto else -0.15
                exit_threshold = 0.05 if not is_crypto else 0.10
                stop_loss_pct = 0.03 if not is_crypto else 0.07

            final_dip_ret = min(predicted_min_ret, dip_threshold)
            final_exit_ret = max(predicted_max_ret, exit_threshold)
            
            final_exit_ret = min(final_exit_ret, 1.0)
            final_dip_ret = max(final_dip_ret, -0.5)

            get_in_point = current_price * (1 + final_dip_ret)
            get_out_point = current_price * (1 + final_exit_ret)
            stop_loss = get_in_point * (1 - stop_loss_pct)
            
            pred_change_pct = predicted_max_ret * 100
            main_sentiment = self.get_sentiment_level(pred_change_pct)
                
            return {
                'ticker': self.ticker,
                'current_date': str(current_date),
                'current_price': float(current_price),
                'confidence_score': float(confidence),
                'consensus': consensus_details, # The RICH consensus
                'model_competition': self._build_model_competition_data(consensus_details),
                'predicted_max_high': float(current_price * (1 + predicted_max_ret)),
                'predicted_min_low': float(current_price * (1 + predicted_min_ret)),
                'recommended_get_in': float(get_in_point),
                'recommended_get_out': float(get_out_point),
                'recommended_stop_loss': float(stop_loss),
                'potential_gain': float(((get_out_point - get_in_point) / get_in_point) * 100) if get_in_point > 0 else 0.0,
                'sentiment_score': float(s_score),
                'asset_type': 'Crypto' if is_crypto else 'Stock',
                'risk_mode': risk,
                'market_sentiment_label': main_sentiment['label'],
                'market_sentiment_icon': main_sentiment['emoji'],
                'predicted_change_pct': float(pred_change_pct)
            }
        except Exception as e:
            print(f"Error in train_and_predict: {e}")
            import traceback
            traceback.print_exc()
            raise

    def run(self, horizon: int = 60, risk: str = 'conservative'):
        df = self.storage.load_ticker_data(self.ticker, '1d')
        if df is None or len(df) == 0:
            print(f"No 1d data for {self.ticker}. Did you run the pipeline?")
            return
            
        print(f"\n--- {self.ticker} Analysis ({'CRYPTO' if self.is_crypto() else 'STOCK'}) ---")
        print(f"Prediction Horizon: {horizon} days | Mode: {risk.upper()}")
        
        try:
            # Shifted order: Run baseline models FIRST to use as Single Source of Truth for metrics
            print(f"Generating comprehensive model results...")
            baseline_results = self.baseline_models.run_all_intervals()
            
            predictions = self.train_and_predict(df, horizon=horizon, risk=risk, baseline_results=baseline_results)
        except Exception as e:
            print(f"Failed to generate predictions: {e}")
            import traceback
            traceback.print_exc()
            return

        print("\n=== PREMIUM STRATEGY REPORT ===")
        print(f"Ticker: {self.ticker} | Date: {predictions['current_date']}")
        print(f"Current Price: ${predictions['current_price']:.2f}")
        print("-" * 30)
        print(f"GET IN (Target Entry):    ${predictions['recommended_get_in']:.2f}")
        print(f"STOP LOSS (Protection):   ${predictions['recommended_stop_loss']:.2f}")
        print(f"GET OUT (Target Exit):    ${predictions['recommended_get_out']:.2f}")
        print("-" * 30)
        print(f"Potential Trade Gain:     {predictions['potential_gain']:.2f}%")
        print(f"Confidence Level:         {predictions['confidence_score']:.1f}%")
        print("=" * 30)

        # Save results
        output_dir = Path("data/decisions")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / f"{self.ticker}_premium_decision.json", 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=4, ensure_ascii=False)
        print(f"Saved decision to data/decisions/{self.ticker}_premium_decision.json")

        # Baseline models are now run BEFORE predictions for sync
        print("OK: All metrics and diagnostics synchronized")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Agile Decision Making ML')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol')
    parser.add_argument('--horizon', type=int, default=60, help='Prediction horizon in days')
    parser.add_argument('--risk', type=str, default='conservative', choices=['conservative', 'aggressive'], help='Risk mode')
    args = parser.parse_args()
    
    dm = DecisionMakingML(ticker=args.ticker)
    dm.run(horizon=args.horizon, risk=args.risk)
