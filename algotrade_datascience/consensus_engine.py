"""
Multi-Timeframe Consensus Engine
Generates predictions for multiple intervals with model competition
Best practices: Modular, scalable, testable
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime

class Sentiment(Enum):
    """Sentiment levels with text representations (Unicode-safe)"""
    DRAMATICALLY_UP = ("+++", "Dramatic UP", 2.0, "#27ae60")
    STRONGLY_UP = ("++", "Strong UP", 1.5, "#2ecc71")
    UP = ("+", "Up", 1.0, "#3498db")
    NEUTRAL = ("=", "Neutral", 0.0, "#95a5a6")
    DOWN = ("-", "Down", -1.0, "#e74c3c")
    STRONGLY_DOWN = ("--", "Strong DOWN", -1.5, "#c0392b")
    DRAMATICALLY_DOWN = ("---", "Dramatic DOWN", -2.0, "#8b0000")

    @property
    def emoji(self):
        return self.value[0]
    
    @property
    def label(self):
        return self.value[1]
    
    @property
    def strength(self):
        return self.value[2]
    
    @property
    def color(self):
        return self.value[3]

@dataclass
class ModelPrediction:
    """Single model prediction for an interval"""
    model_name: str
    accuracy: float  # Direction accuracy %
    rmse: float
    r2_score: float
    mape: float
    change_percent: float = 0.0  # Expected percentage change
    is_winner: bool = False

@dataclass
class IntervalPrediction:
    """Complete prediction for a specific timeframe"""
    interval: str  # '1h', '4h', '1d', '1wk', '1mo', '3mo'
    sentiment: Sentiment
    change_percent: float
    confidence: float  # 0-100
    models: List[ModelPrediction]
    best_model: Optional[ModelPrediction] = None
    
    def to_dict(self):
        return {
            'interval': self.interval,
            'sentiment': self.sentiment.name,
            'sentiment_label': self.sentiment.label,
            'sentiment_emoji': self.sentiment.emoji,
            'sentiment_color': self.sentiment.color,
            'change_percent': round(self.change_percent, 2),
            'confidence': round(self.confidence, 1),
            'best_model': self.best_model.model_name if self.best_model else None,
            'model_count': len(self.models),
            'accuracy_best': round(self.best_model.accuracy, 1) if self.best_model else 0,
            'models': [asdict(m) for m in self.models]
        }

@dataclass
class ConsensusReport:
    """Complete consensus across all timeframes"""
    ticker: str
    timestamp: str
    overall_sentiment: Sentiment
    overall_confidence: float  # 0-100
    intervals: Dict[str, IntervalPrediction]
    agreement_score: float  # How much intervals agree
    
    def to_dict(self):
        return {
            'ticker': self.ticker,
            'timestamp': self.timestamp,
            'overall_sentiment': self.overall_sentiment.name,
            'overall_sentiment_label': self.overall_sentiment.label,
            'overall_sentiment_emoji': self.overall_sentiment.emoji,
            'overall_confidence': round(self.overall_confidence, 1),
            'agreement_score': round(self.agreement_score, 1),
            'intervals': {k: v.to_dict() for k, v in self.intervals.items()}
        }

class MultiTimeframeConsensus:
    """
    Manages multi-timeframe predictions with per-interval model competition
    
    Architecture:
    1. Load data for each timeframe
    2. Run multiple models on each timeframe
    3. Select best model per timeframe
    4. Calculate sentiment for each timeframe
    5. Compute overall consensus
    """
    
    TIMEFRAMES = ['1h', '4h', '1d', '1wk', '1mo']
    SENTIMENT_THRESHOLDS = [
        (2.0, Sentiment.DRAMATICALLY_UP),      # > 2% per period
        (1.0, Sentiment.STRONGLY_UP),           # > 1%
        (0.2, Sentiment.UP),                   # > 0.2%
        (-0.2, Sentiment.NEUTRAL),             # > -0.2%
        (-1.0, Sentiment.DOWN),                # > -1%
        (-2.0, Sentiment.STRONGLY_DOWN),       # > -2%
        (-float('inf'), Sentiment.DRAMATICALLY_DOWN)  # <= -2%
    ]
    
    def __init__(self, storage, ticker: str):
        """
        Args:
            storage: DataStorage instance for loading market data
            ticker: Stock/crypto ticker
        """
        self.storage = storage
        self.ticker = ticker
        self.predictions: Dict[str, IntervalPrediction] = {}
    
    def classify_sentiment(self, change_percent: float) -> Sentiment:
        """
        Classify change percentage into sentiment level
        
        Args:
            change_percent: Expected percentage change
            
        Returns:
            Sentiment enum value
        """
        for threshold, sentiment in self.SENTIMENT_THRESHOLDS:
            if change_percent > threshold:
                return sentiment
        return Sentiment.DRAMATICALLY_DOWN
    
    def predict_interval(self, df: pd.DataFrame, interval: str) -> Optional[IntervalPrediction]:
        """
        Generate prediction for a specific timeframe
        Runs multiple models and selects the best
        
        Args:
            df: OHLCV dataframe for the interval
            interval: Timeframe code ('1h', '4h', etc)
            
        Returns:
            IntervalPrediction with model comparison
        """
        if df is None or len(df) < 20:
            print(f"  [Consensus] {interval}: Insufficient raw data ({len(df) if df is not None else 0} rows)")
            return None
        
        # Add technical indicators
        df = self._add_indicators(df)
        
        if df is None or len(df) == 0:
            print(f"  [Consensus] {interval}: Failed to add indicators or data became empty")
            return None
        
        # Run multiple models
        models_results = []
        
        # Model 1: XGBoost Regressor
        xgb_result = self._run_xgboost(df, interval)
        if xgb_result:
            models_results.append(xgb_result)
        
        # Model 2: Random Forest
        rf_result = self._run_random_forest(df, interval)
        if rf_result:
            models_results.append(rf_result)
        
        # Model 3: Linear Regression (baseline)
        lr_result = self._run_linear_regression(df, interval)
        if lr_result:
            models_results.append(lr_result)
        
        # Model 4: LSTM/Time Series (if enough data)
        if len(df) > 50:
            lstm_result = self._run_lstm(df, interval)
            if lstm_result:
                models_results.append(lstm_result)
        
        if not models_results:
            print(f"  [Consensus] {interval}: All models failed to generate predictions")
            return None
        
        # Select best model (Composite score: 80% Accuracy + 20% RMSE Score)
        # We normalize RMSE by comparing against the best RMSE in the set
        min_rmse = min([m.rmse for m in models_results]) if models_results else 1.0
        best_model = max(models_results, key=lambda m: (m.accuracy * 0.8) + ((min_rmse / (m.rmse + 1e-9)) * 20))
        
        # Calculate ensemble prediction (average of all models)
        avg_change = np.mean([m.change_percent for m in models_results])
        avg_confidence = np.mean([m.accuracy for m in models_results])
        
        # Classify sentiment
        sentiment = self.classify_sentiment(avg_change)
        
        # Create interval prediction
        prediction = IntervalPrediction(
            interval=interval,
            sentiment=sentiment,
            change_percent=avg_change,
            confidence=avg_confidence,
            models=models_results,
            best_model=best_model
        )
        
        return prediction
    
    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators for predictions"""
        try:
            df = df.copy()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            # Bollinger Bands
            df['BB_Mid'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
            df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
            
            # Volatility (Standardized to 5-period to match baseline_models)
            pct_change = df['Close'].pct_change()
            df['volatility_5'] = pct_change.rolling(window=5).std() * 100
            
            # Volume Ratio
            df['volume_ratio'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
            
            # Lag returns
            for i in range(1, 4):
                df[f'Lag_{i}'] = pct_change.shift(i) * 100
            
            # CRITICAL: Drop NaN values only AFTER all feature calculations
            # But we keep targets for the training loop specifically.
            # In Consensus Engine, we drop NaNs here for general "indicators" prep.
            df = df.dropna()
            
            if len(df) < 20:
                print(f"  [Indicators] Data reduced to {len(df)} rows after cleaning (need 20+)")
                return None
                
            return df
        except Exception as e:
            print(f"Error adding indicators: {e}")
            return None
    
    def _run_xgboost(self, df: pd.DataFrame, interval: str) -> Optional[ModelPrediction]:
        """Run XGBoost model"""
        try:
            import xgboost as xgb
            from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
            
            features = ['RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'MACD', 'Signal_Line', 
                       'BB_Upper', 'BB_Lower', 'volatility_5', 'volume_ratio', 'Lag_1', 'Lag_2', 'Lag_3']
            
            # Verify all features exist and no NaN values
            X = df[features].copy()
            # FIX: Use shift(-1) to predict NEXT period change (Forecasting)
            # Old code was using current period (Nowcasting/Leakage)
            y = df['Close'].pct_change().shift(-1) * 100
            
            # Drop NaN values from y (first row will be NaN)
            valid_idx = ~y.isna()
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < 20 or len(y) < 20:
                print(f"  [XGBoost] Insufficient data after initial filter (X={len(X)})")
                return None
            
            # Remove any remaining NaN or inf values
            mask = ~(X.isna().any(axis=1) | np.isinf(X.values).any(axis=1) | 
                    y.isna() | np.isinf(y.values))
            X = X[mask]
            y = y[mask]
            
            if len(X) < 20:
                print(f"  [XGBoost] Insufficient data after strict cleaning (X={len(X)})")
                return None
            
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            change_pct = float(np.nan_to_num(y_pred[-1], nan=0.0))
            # Standardized Directional Classification: Is the percentage change positive (UP) or negative (DOWN)?
            true_direction = (y_test > 0).astype(int)
            pred_direction = (y_pred > 0).astype(int)
            accuracy = float(np.mean(true_direction == pred_direction) * 100)
            r2 = float(np.nan_to_num(r2_score(y_test, y_pred), nan=0.0))
            rmse = float(np.nan_to_num(np.sqrt(mean_squared_error(y_test, y_pred)), nan=0.0))
            mape = float(np.nan_to_num(np.mean(np.abs((y_test - y_pred) / (np.abs(y_test) + 1e-9))) * 100, nan=0.0))
            
            return ModelPrediction(
                model_name='XGBoost',
                accuracy=accuracy,
                rmse=rmse,
                r2_score=r2,
                mape=mape,
                change_percent=change_pct
            )
        except Exception as e:
            print(f"XGBoost error for {interval}: {e}")
            return None
    
    def _run_random_forest(self, df: pd.DataFrame, interval: str) -> Optional[ModelPrediction]:
        """Run Random Forest model"""
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
            
            features = ['RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'MACD', 'Signal_Line', 
                       'BB_Upper', 'BB_Lower', 'volatility_5', 'volume_ratio', 'Lag_1', 'Lag_2', 'Lag_3']
            
            X = df[features].copy()
            # FIX: Use shift(-1) for forecasting
            y = df['Close'].pct_change().shift(-1) * 100
            
            # Drop NaN values
            valid_idx = ~y.isna()
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < 20 or len(y) < 20:
                return None
            
            # Remove any remaining NaN or inf values
            mask = ~(X.isna().any(axis=1) | np.isinf(X.values).any(axis=1) | 
                    y.isna() | np.isinf(y.values))
            X = X[mask]
            y = y[mask]
            
            if len(X) < 20:
                return None
            
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            change_pct = float(np.nan_to_num(y_pred[-1], nan=0.0))
            # Standardized Directional Classification: Is the percentage change positive (UP) or negative (DOWN)?
            true_direction = (y_test > 0).astype(int)
            pred_direction = (y_pred > 0).astype(int)
            accuracy = float(np.mean(true_direction == pred_direction) * 100)
            r2 = float(np.nan_to_num(r2_score(y_test, y_pred), nan=0.0))
            rmse = float(np.nan_to_num(np.sqrt(mean_squared_error(y_test, y_pred)), nan=0.0))
            mape = float(np.nan_to_num(np.mean(np.abs((y_test - y_pred) / (np.abs(y_test) + 1e-9))) * 100, nan=0.0))
            
            return ModelPrediction(
                model_name='Random Forest',
                accuracy=accuracy,
                rmse=rmse,
                r2_score=r2,
                mape=mape,
                change_percent=change_pct
            )
        except Exception as e:
            print(f"Random Forest error for {interval}: {e}")
            return None
    
    def _run_linear_regression(self, df: pd.DataFrame, interval: str) -> Optional[ModelPrediction]:
        """Run Linear Regression (baseline)"""
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
            
            features = ['RSI', 'SMA_10', 'SMA_20', 'SMA_50', 'MACD', 'Signal_Line', 
                       'BB_Upper', 'BB_Lower', 'volatility_5', 'volume_ratio', 'Lag_1', 'Lag_2', 'Lag_3']
            
            X = df[features].copy()
            # FIX: Use shift(-1) for forecasting
            y = df['Close'].pct_change().shift(-1) * 100
            
            # Drop NaN values
            valid_idx = ~y.isna()
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < 20 or len(y) < 20:
                return None
            
            # Remove any remaining NaN or inf values
            mask = ~(X.isna().any(axis=1) | np.isinf(X.values).any(axis=1) | 
                    y.isna() | np.isinf(y.values))
            X = X[mask]
            y = y[mask]
            
            if len(X) < 20:
                return None
            
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            change_pct = float(np.nan_to_num(y_pred[-1], nan=0.0))
            # Standardized Directional Classification: Is the percentage change positive (UP) or negative (DOWN)?
            true_direction = (y_test > 0).astype(int)
            pred_direction = (y_pred > 0).astype(int)
            accuracy = float(np.mean(true_direction == pred_direction) * 100)
            r2 = float(np.nan_to_num(r2_score(y_test, y_pred), nan=0.0))
            rmse = float(np.nan_to_num(np.sqrt(mean_squared_error(y_test, y_pred)), nan=0.0))
            mape = float(np.nan_to_num(np.mean(np.abs((y_test - y_pred) / (np.abs(y_test) + 1e-9))) * 100, nan=0.0))
            
            return ModelPrediction(
                model_name='Linear Regression',
                accuracy=accuracy,
                rmse=rmse,
                r2_score=r2,
                mape=mape,
                change_percent=change_pct
            )
        except Exception as e:
            print(f"Linear Regression error for {interval}: {e}")
            return None
    
    def _run_lstm(self, df: pd.DataFrame, interval: str) -> Optional[ModelPrediction]:
        """Run LSTM model for time series prediction"""
        try:
            # LSTM implementation would require TensorFlow/Keras
            # Simplified version here - can be expanded
            return None
        except Exception as e:
            print(f"LSTM error for {interval}: {e}")
            return None
    
    def generate_consensus(self) -> Optional[ConsensusReport]:
        """
        Generate complete consensus report across all timeframes
        
        Returns:
            ConsensusReport with all timeframe predictions
        """
        self.predictions = {}
        
        # Generate predictions for each timeframe
        for interval in self.TIMEFRAMES:
            try:
                df = self.storage.load_ticker_data(self.ticker, interval)
                if df is None:
                    print(f"  [Consensus] No data found for {interval}")
                    continue
                
                print(f"  [Consensus] processing {interval} ({len(df)} rows)...")
                prediction = self.predict_interval(df, interval)
                
                if prediction:
                    self.predictions[interval] = prediction
                    print(f"  [Consensus] SUCCESS for {interval}: {prediction.sentiment.name}")
                else:
                    print(f"  [Consensus] FAILED to generate prediction for {interval}")
            except Exception as e:
                print(f"Failed to generate prediction for {interval}: {e}")
                continue
        
        if not self.predictions:
            return None
        
        # Calculate overall sentiment (consensus)
        sentiments = [p.sentiment for p in self.predictions.values()]
        overall_strength = np.mean([s.strength for s in sentiments])
        overall_sentiment = self.classify_sentiment(overall_strength)
        
        # Calculate agreement score (how much do intervals agree)
        sentiment_names = [s.name for s in sentiments]
        unique_sentiments = len(set(sentiment_names))
        agreement_score = (1 - (unique_sentiments - 1) / len(sentiments)) * 100 if len(sentiments) > 1 else 100
        
        # Average confidence
        overall_confidence = np.mean([p.confidence for p in self.predictions.values()])
        
        report = ConsensusReport(
            ticker=self.ticker,
            timestamp=datetime.now().isoformat(),
            overall_sentiment=overall_sentiment,
            overall_confidence=overall_confidence,
            intervals=self.predictions,
            agreement_score=agreement_score
        )
        
        return report
