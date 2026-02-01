"""
Decision Making ML Application for Stock Trading
Predicts "Get In" (buy) and "Get Out" (sell) points for AAPL.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Import from core
import sys
import os

# Add the current directory to sys.path to allow imports from core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.data_storage import DataStorage
from core.news_fetcher import NewsFetcher
from features.sentiment_analysis import SentimentProcessor

class DecisionMakingML:
    def __init__(self, ticker: str = 'AAPL'):
        self.ticker = ticker
        # Use project root as base_dir for data
        self.storage = DataStorage(base_dir='.')
        self.news_fetcher = NewsFetcher()
        # Initialize SentimentProcessor (FinBERT)
        try:
            self.sentiment_processor = SentimentProcessor()
        except Exception as e:
            print(f"Warning: Could not initialize SentimentProcessor: {e}")
            self.sentiment_processor = None
        self.results = {}
        
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add robust technical indicators for better decision making"""
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
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
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
        
        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # Momentum & Volatility
        df['Momentum'] = df['Close'].pct_change(5)
        df['Volatility'] = df['Close'].rolling(window=20).std()
        
        # Lagged target features
        for i in range(1, 4):
            df[f'Lag_{i}'] = df['Close'].shift(i)
            
        return df

    def evaluate_model_performance(self, ticker: str, df: pd.DataFrame, horizon: int = 1):
        """Strict evaluation of model against baseline metrics"""
        from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
        import xgboost as xgb
        
        df_rich = self.add_technical_indicators(df)
        df_rich['target'] = df_rich['Close'].shift(-horizon)
        df_rich = df_rich.dropna()
        
        feature_cols = [
            'Close', 'RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_10_20_cross',
            'BB_Upper', 'BB_Lower', 'MACD', 'Signal_Line', 'ATR', 'Momentum', 'Volatility',
            'Lag_1', 'Lag_2', 'Lag_3'
        ]
        
        X = df_rich[feature_cols]
        y = df_rich['target']
        
        # Time Series Split (80/20)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Train our Advanced XGBoost Model
        model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.01,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Calculate Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Load Baseline Metrics for Comparison
        baseline_file = f'data/baseline_models_{ticker}.json'
        comparison = {}
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
                bl_metrics = baseline_data.get('1d', {}).get('metrics', {}).get('linear_regression', {})
                comparison = {
                    'baseline_mae': bl_metrics.get('mae'),
                    'baseline_r2': bl_metrics.get('r2'),
                    'is_better_mae': bool(mae < bl_metrics.get('mae', 999)),
                    'is_better_r2': bool(r2 > bl_metrics.get('r2', -999))
                }
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'comparison': comparison
        }

    def prepare_targets(self, df: pd.DataFrame, horizon: int = 20) -> pd.DataFrame:
        """Prepare targets for ML: Max High and Min Low % return in next N days"""
        df = df.copy()
        # Calculate future max/min relative to current close
        future_max = df['High'].shift(-horizon).rolling(window=horizon, min_periods=1).max()
        future_min = df['Low'].shift(-horizon).rolling(window=horizon, min_periods=1).min()
        
        # We predict % change (Decimal)
        df['target_max_return'] = (future_max - df['Close']) / df['Close']
        df['target_min_return'] = (future_min - df['Close']) / df['Close']
        
        return df.dropna()

    def get_sentiment_multiplier(self):
        """Analyze current news sentiment to adjust targets"""
        if not self.sentiment_processor:
            return 1.0, 0.0
        
        try:
            news_df = self.news_fetcher.fetch_ticker_news(self.ticker)
            if news_df.empty:
                return 1.0, 0.0
            
            # Analyze top 10 headlines (ensure they are strings)
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

    def get_multi_timeframe_consensus(self, primary_interval='1d'):
        """
        Double check: See if smaller and LARGER intervals agree with the primary trend.
        Returns a confidence score (0 to 100).
        """
        intervals = ['1h', '4h', '1wk', '1mo']
        consensus_score = 0
        details = {}
        
        # Check primary direction first
        df_primary = self.storage.load_ticker_data(self.ticker, primary_interval)
        if df_primary is None or len(df_primary) < 20:
            return 0, {}
            
        # Primary Trend: Average of last 5 days vs previous 5 days
        primary_avg_now = df_primary['Close'].tail(5).mean()
        primary_avg_prev = df_primary['Close'].iloc[-10:-5].mean()
        primary_trend = "UP" if primary_avg_now > primary_avg_prev else "DOWN"
        
        # We start with the primary trend itself
        up_count = 1 if primary_trend == "UP" else 0
        total_intervals = 1
        details[primary_interval] = primary_trend
        
        for interval in intervals:
            try:
                df_sub = self.storage.load_ticker_data(self.ticker, interval)
                if df_sub is not None and len(df_sub) >= 20:
                    # Smoothing: Average of last 10 periods vs previous 10 periods
                    # For 1wk and 1mo, we might have less data, so check length
                    lookback = min(10, len(df_sub) // 2)
                    if lookback < 2:
                        details[interval] = "NOT_ENOUGH_DATA"
                        continue
                        
                    sub_avg_now = df_sub['Close'].tail(lookback).mean()
                    sub_avg_prev = df_sub['Close'].iloc[-(lookback*2):-lookback].mean()
                    
                    direction = "UP" if sub_avg_now > sub_avg_prev else "DOWN"
                    details[interval] = direction
                    
                    if direction == primary_trend:
                        up_count += 1
                    total_intervals += 1
                else:
                    details[interval] = "NO_DATA"
            except Exception as e:
                details[interval] = f"ERROR_{str(e)[:10]}"
                continue
                
        confidence = (up_count / total_intervals) * 100
        return confidence, details

    def is_crypto(self):
        """Check if the ticker is a crypto asset"""
        ticker_up = self.ticker.upper()
        return "-USD" in ticker_up or "-EUR" in ticker_up or ticker_up in ['BTC', 'ETH', 'SOL']

    def train_and_predict(self, df: pd.DataFrame, horizon: int = 60, risk: str = 'conservative'):
        """Train models and make predictions for the current date"""
        df_rich = self.add_technical_indicators(df)
        df_prepared = self.prepare_targets(df_rich, horizon=horizon)
        
        feature_cols = [
            'Close', 'RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_10_20_cross',
            'BB_Upper', 'BB_Lower', 'MACD', 'Signal_Line', 'ATR', 'Momentum', 'Volatility',
            'Lag_1', 'Lag_2', 'Lag_3'
        ]
        X = df_prepared[feature_cols]
        
        import xgboost as xgb
        # Optimized XGBoost parameters for multi-target regression
        model_high = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
        model_low = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
        
        model_high.fit(X, df_prepared['target_max_return'])
        model_low.fit(X, df_prepared['target_min_return'])
        
        X_latest = df_rich[feature_cols].dropna().tail(1)
        latest_data = df_rich.loc[X_latest.index]
        
        current_price = float(latest_data['Close'].values[0])
        current_date = latest_data['Date'].values[0]
        
        # Predicted returns (e.g., 0.15 for +15%, -0.05 for -5%)
        predicted_max_ret = float(model_high.predict(X_latest)[0])
        predicted_min_ret = float(model_low.predict(X_latest)[0])
        
        # 1. Consensus Double Check
        confidence, consensus_details = self.get_multi_timeframe_consensus()
        
        # 2. Sentiment Multiplier
        s_multiplier, s_score = self.get_sentiment_multiplier()
        if s_multiplier > 1.0:
            predicted_max_ret *= s_multiplier
            
        # 3. Apply Decision Logic with Risk Mode
        # Conservative: Wants safer entry (deeper dip) and stable exit.
        # Aggressive: Willing to enter sooner and aim higher.
        
        is_crypto = self.is_crypto()
        
        if risk == 'aggressive':
            dip_threshold = -0.05 if not is_crypto else -0.08
            exit_threshold = 0.08 if not is_crypto else 0.15
            stop_loss_pct = 0.05 if not is_crypto else 0.10
        else: # conservative
            dip_threshold = -0.08 if not is_crypto else -0.15
            exit_threshold = 0.05 if not is_crypto else 0.10
            stop_loss_pct = 0.03 if not is_crypto else 0.07

        # Ensure predicted dip/rise is at least as much as our threshold, or use threshold
        # This prevents recommending targets too close to the current price
        final_dip_ret = min(predicted_min_ret, dip_threshold)
        final_exit_ret = max(predicted_max_ret, exit_threshold)
        
        # Clip excessive predictions to keep them realistic (e.g., max 100% gain)
        final_exit_ret = min(final_exit_ret, 1.0)
        final_dip_ret = max(final_dip_ret, -0.5)

        get_in_point = current_price * (1 + final_dip_ret)
        get_out_point = current_price * (1 + final_exit_ret)
        stop_loss = get_in_point * (1 - stop_loss_pct)
            
        return {
            'ticker': self.ticker,
            'current_date': str(current_date),
            'current_price': current_price,
            'confidence_score': confidence,
            'consensus': consensus_details,
            'predicted_max_high': current_price * (1 + predicted_max_ret),
            'predicted_min_low': current_price * (1 + predicted_min_ret),
            'recommended_get_in': float(get_in_point),
            'recommended_get_out': float(get_out_point),
            'recommended_stop_loss': float(stop_loss),
            'potential_gain': float(((get_out_point - get_in_point) / get_in_point) * 100),
            'sentiment_score': float(s_score),
            'asset_type': 'Crypto' if is_crypto else 'Stock',
            'risk_mode': risk
        }

    def run(self, horizon: int = 60, risk: str = 'conservative'):
        df = self.storage.load_ticker_data(self.ticker, '1d')
        if df is None:
            print(f"No 1d data for {self.ticker}. Did you run the pipeline?")
            return
            
        print(f"\n--- {self.ticker} Analysis ({'CRYPTO' if self.is_crypto() else 'STOCK'}) ---")
        print(f"Prediction Horizon: {horizon} days | Mode: {risk.upper()}")
        perf = self.evaluate_model_performance(self.ticker, df, horizon=1) # Keep evaluation at 1-day for stability
        predictions = self.train_and_predict(df, horizon=horizon, risk=risk)
        
        print("\n=== MULTI-TIMEFRAME CONSENSUS ===")
        print(f"Consensus Score: {predictions['confidence_score']:.1f}%")
        for interval, trend in predictions['consensus'].items():
            print(f"  - {interval} Micro-Trend: {trend}")
        print("-" * 30)

        print("\n=== THE 'BEAT THE BASELINE' PERFORMANCE ===")
        baseline_r2 = perf['comparison'].get('baseline_r2') if perf['comparison'].get('baseline_r2') is not None else 0.0
        print(f"Model R2: {perf['r2']:.4f} (Baseline: {baseline_r2:.4f})")
        print(f"Status: {'WINNER: BEATING BASELINE' if perf['comparison'].get('is_better_r2') else 'NEEDS RETRAINING'}")
        
        print("\n=== PREMIUM STRATEGY REPORT ===")
        print(f"Ticker: {self.ticker} | Date: {predictions['current_date']}")
        print(f"Current Price: ${predictions['current_price']:.2f}")
        print("-" * 30)
        print(f"GET IN (Target Entry):    ${predictions['recommended_get_in']:.2f}")
        print(f"STOP LOSS (Protection):   ${predictions['recommended_stop_loss']:.2f}")
        print(f"GET OUT (Target Exit):    ${predictions['recommended_get_out']:.2f}")
        print("-" * 30)
        print(f"Potential Trade Gain:     {predictions['potential_gain']:.2f}%")
        print(f"Sentiment Impact:         {predictions['sentiment_score']:.2f}")
        print(f"Confidence Level:         {predictions['confidence_score']:.1f}%")
        print("=" * 30)

        # Save results
        predictions['performance'] = perf
        predictions['last_trained'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_dir = Path("data/decisions")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / f"{self.ticker}_premium_decision.json", 'w') as f:
            json.dump(predictions, f, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Agile Decision Making ML')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol (e.g., AAPL, BTC-USD)')
    parser.add_argument('--horizon', type=int, default=60, help='Prediction horizon in days (default: 60)')
    parser.add_argument('--risk', type=str, default='conservative', choices=['conservative', 'aggressive'], help='Risk mode')
    args = parser.parse_args()
    
    dm = DecisionMakingML(ticker=args.ticker)
    dm.run(horizon=args.horizon, risk=args.risk)
