# UI + ML Pipeline - Detailed User Stories

## 🎯 Project Overview

**Goal**: Create a simple web interface where users input a ticker, the system fetches/uses existing data, trains multiple ML models for different time horizons (1min, 3min, 5min, 15min, 30min, 1h, 1d), and displays predictions with performance metrics.

**Tech Stack**:
- **Backend**: Python (FastAPI)
- **Frontend**: HTML + Vanilla CSS + JavaScript
- **ML Models**: LightGBM, XGBoost, Random Forest, LSTM
- **Visualization**: Plotly.js (interactive charts)
- **Data**: Existing pipeline (Phase 1) + new minute-level data

---

## Epic 1: Simple Web Interface

### US-UI-001: Ticker Input Page
**Priority**: Critical  
**Story Points**: 3

**As a** user  
**I want** a simple web page to input a stock ticker  
**So that** I can start the prediction pipeline

**Acceptance Criteria:**
- [ ] Single-page web interface with clean design
- [ ] Input field for ticker symbol (e.g., "AAPL", "BTC-USD")
- [ ] "Start Analysis" button
- [ ] Input validation (uppercase conversion, max 10 characters)
- [ ] Loading spinner while checking dataset existence
- [ ] Error messages for invalid tickers

**UI Mockup:**
```
┌─────────────────────────────────────────┐
│   📈 Financial ML Prediction Platform   │
├─────────────────────────────────────────┤
│                                         │
│   Enter Stock Ticker:                   │
│   ┌─────────────────┐                   │
│   │ AAPL            │  [Start Analysis] │
│   └─────────────────┘                   │
│                                         │
│   Status: ⏳ Checking dataset...        │
│                                         │
└─────────────────────────────────────────┘
```

**Technical Implementation:**
```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial ML Platform</title>
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>📈 Financial ML Prediction Platform</h1>
        
        <div class="input-section">
            <label for="ticker">Enter Stock Ticker:</label>
            <input type="text" id="ticker" placeholder="AAPL" maxlength="10">
            <button id="startBtn" onclick="startAnalysis()">Start Analysis</button>
        </div>
        
        <div id="status" class="status-message"></div>
        <div id="loading" class="loading hidden">
            <div class="spinner"></div>
            <p>Processing...</p>
        </div>
    </div>
    
    <script src="static/js/app.js"></script>
</body>
</html>
```

```javascript
// static/js/app.js
async function startAnalysis() {
    const ticker = document.getElementById('ticker').value.toUpperCase().trim();
    
    if (!ticker) {
        showStatus('Please enter a ticker symbol', 'error');
        return;
    }
    
    showLoading(true);
    showStatus('Checking dataset...', 'info');
    
    try {
        const response = await fetch(`/api/check-dataset/${ticker}`);
        const data = await response.json();
        
        if (data.exists) {
            showStatus(`Dataset found! Using existing data (${data.rows} rows)`, 'success');
            runPipeline(ticker);
        } else {
            showStatus('Dataset not found. Creating new dataset...', 'info');
            await createDataset(ticker);
            runPipeline(ticker);
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        showLoading(false);
    }
}
```

---

### US-UI-002: Dataset Status Check & Creation
**Priority**: Critical  
**Story Points**: 5

**As a** user  
**I want** the system to automatically check if a dataset exists  
**So that** I don't waste time re-fetching existing data

**Acceptance Criteria:**
- [ ] API endpoint: `GET /api/check-dataset/{ticker}`
- [ ] Returns: `{exists: bool, rows: int, last_updated: datetime, intervals: []}`
- [ ] If dataset exists, show summary (rows, date range, intervals)
- [ ] If dataset doesn't exist, trigger data creation pipeline
- [ ] Progress bar during data fetching
- [ ] Estimated time remaining display

**API Response:**
```json
{
    "ticker": "AAPL",
    "exists": true,
    "rows": 1000,
    "last_updated": "2026-01-22T16:30:00Z",
    "intervals": ["1min", "5min", "15min", "1h", "1d"],
    "date_range": {
        "start": "2026-01-15T09:30:00Z",
        "end": "2026-01-22T16:00:00Z"
    }
}
```

**Backend Implementation:**
```python
# app/api/dataset.py
from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

router = APIRouter()

@router.get("/check-dataset/{ticker}")
async def check_dataset(ticker: str):
    ticker = ticker.upper()
    data_dir = Path(f"data/raw/{ticker}")
    
    if not data_dir.exists():
        return {
            "ticker": ticker,
            "exists": False
        }
    
    # Find all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        return {"ticker": ticker, "exists": False}
    
    # Read one file to get metadata
    sample_df = pd.read_csv(csv_files[0])
    
    return {
        "ticker": ticker,
        "exists": True,
        "rows": len(sample_df),
        "last_updated": sample_df['Date'].max(),
        "intervals": [f.stem.split('_')[1] for f in csv_files],
        "date_range": {
            "start": sample_df['Date'].min(),
            "end": sample_df['Date'].max()
        }
    }
```

---

### US-UI-003: Real-time Pipeline Progress Display
**Priority**: High  
**Story Points**: 5

**As a** user  
**I want** to see real-time progress of the ML pipeline  
**So that** I know the system is working and how long to wait

**Acceptance Criteria:**
- [ ] Progress bar showing: Data Fetch → Feature Engineering → Model Training → Prediction
- [ ] Step-by-step status updates (e.g., "Training LightGBM for 1min horizon...")
- [ ] Estimated time remaining
- [ ] Current step highlighted
- [ ] WebSocket connection for real-time updates

**UI Design:**
```
┌─────────────────────────────────────────────────────────┐
│ Pipeline Progress for AAPL                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ Data Fetching         [████████████] 100%           │
│ ✅ Feature Engineering   [████████████] 100%           │
│ ⏳ Model Training        [████████░░░░] 75%            │
│    └─ Training LightGBM for 5min horizon...            │
│ ⏸️  Prediction           [░░░░░░░░░░░░] 0%             │
│                                                         │
│ Estimated time remaining: 2m 15s                        │
└─────────────────────────────────────────────────────────┘
```

**WebSocket Implementation:**
```python
# app/api/websocket.py
from fastapi import WebSocket
import asyncio

@router.websocket("/ws/progress/{ticker}")
async def websocket_progress(websocket: WebSocket, ticker: str):
    await websocket.accept()
    
    try:
        # Send progress updates
        await websocket.send_json({
            "step": "data_fetch",
            "progress": 0,
            "message": "Starting data fetch..."
        })
        
        # ... pipeline execution with progress updates
        
        await websocket.send_json({
            "step": "complete",
            "progress": 100,
            "message": "Pipeline complete!"
        })
    except Exception as e:
        await websocket.send_json({
            "step": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
```

---

## Epic 2: Multi-Interval Data Fetching

### US-DATA-001: Minute-Level Data Fetching
**Priority**: Critical  
**Story Points**: 8

**As a** data engineer  
**I want** to fetch 1-minute OHLCV data for the last 7 days  
**So that** I can train ultra-short-term prediction models

**Acceptance Criteria:**
- [ ] Fetch 1-minute bars for last 7 days (~2,730 rows)
- [ ] Fetch 5-minute bars for last 30 days (~3,600 rows)
- [ ] Fetch 15-minute bars for last 60 days (~3,840 rows)
- [ ] Handle API rate limits (yfinance: 2000 requests/hour)
- [ ] Retry logic with exponential backoff
- [ ] Data validation (no gaps, OHLC logic)
- [ ] Store in same format as existing pipeline

**Data Intervals:**
| Interval | Lookback | Expected Rows | Use Case |
|----------|----------|---------------|----------|
| 1min     | 7 days   | ~2,730        | 1min, 3min predictions |
| 5min     | 30 days  | ~3,600        | 5min, 15min predictions |
| 15min    | 60 days  | ~3,840        | 30min predictions |
| 1h       | 6 months | ~1,000        | 1h predictions |
| 1d       | 2 years  | ~500          | 1d predictions |

**Implementation:**
```python
# core/data_fetcher.py (extend existing)
import yfinance as yf
from datetime import datetime, timedelta

class DataFetcher:
    MINUTE_INTERVALS = {
        '1min': {'period': '7d', 'interval': '1m'},
        '5min': {'period': '1mo', 'interval': '5m'},
        '15min': {'period': '60d', 'interval': '15m'},
        '1h': {'period': '6mo', 'interval': '1h'},
        '1d': {'period': '2y', 'interval': '1d'},
    }
    
    def fetch_minute_data(self, ticker: str, interval: str) -> pd.DataFrame:
        """Fetch minute-level data for given interval"""
        config = self.MINUTE_INTERVALS[interval]
        
        try:
            data = yf.download(
                ticker,
                period=config['period'],
                interval=config['interval'],
                progress=False
            )
            
            if data.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # Validate data
            self._validate_ohlc(data)
            
            return data
        except Exception as e:
            self.logger.error(f"Error fetching {interval} data: {e}")
            raise
    
    def fetch_all_intervals(self, ticker: str) -> dict:
        """Fetch all intervals for a ticker"""
        results = {}
        
        for interval in self.MINUTE_INTERVALS.keys():
            self.logger.info(f"Fetching {interval} data for {ticker}...")
            results[interval] = self.fetch_minute_data(ticker, interval)
            time.sleep(1)  # Rate limiting
        
        return results
```

---

## Epic 3: Feature Engineering for Multiple Horizons

### US-FEAT-001: Multi-Horizon Feature Engineering
**Priority**: Critical  
**Story Points**: 13

**As a** ML engineer  
**I want** to create features optimized for each prediction horizon  
**So that** each model has the most relevant inputs

**Acceptance Criteria:**
- [ ] Features computed for each interval (1min, 5min, 15min, 1h, 1d)
- [ ] Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands
- [ ] Price features: returns, log returns, volatility
- [ ] Volume features: volume ratio, VWAP
- [ ] Time features: hour of day, day of week
- [ ] Lag features: previous N bars
- [ ] No data leakage (only use past data)

**Feature Matrix by Horizon:**

| Feature Category | 1min | 5min | 15min | 1h | 1d |
|-----------------|------|------|-------|----|----|
| Price Returns (1,3,5,10 bars) | ✓ | ✓ | ✓ | ✓ | ✓ |
| SMA (5,10,20,50) | ✓ | ✓ | ✓ | ✓ | ✓ |
| EMA (5,10,20) | ✓ | ✓ | ✓ | ✓ | ✓ |
| RSI (14) | ✓ | ✓ | ✓ | ✓ | ✓ |
| MACD | ✗ | ✓ | ✓ | ✓ | ✓ |
| Bollinger Bands | ✗ | ✓ | ✓ | ✓ | ✓ |
| Volume Ratio | ✓ | ✓ | ✓ | ✓ | ✓ |
| VWAP | ✓ | ✓ | ✓ | ✓ | ✗ |
| Hour of Day | ✓ | ✓ | ✓ | ✓ | ✗ |
| Day of Week | ✗ | ✗ | ✗ | ✓ | ✓ |

**Implementation:**
```python
# features/technical_indicators.py
import pandas as pd
import numpy as np
import ta  # Technical Analysis library

class FeatureEngineer:
    def __init__(self, interval: str):
        self.interval = interval
        self.feature_config = self._get_feature_config()
    
    def _get_feature_config(self) -> dict:
        """Get feature configuration based on interval"""
        configs = {
            '1min': {
                'sma_periods': [5, 10, 20],
                'ema_periods': [5, 10],
                'rsi_period': 14,
                'lag_features': [1, 2, 3, 5],
                'include_macd': False,
                'include_bollinger': False,
            },
            '5min': {
                'sma_periods': [5, 10, 20, 50],
                'ema_periods': [5, 10, 20],
                'rsi_period': 14,
                'lag_features': [1, 2, 3, 5, 10],
                'include_macd': True,
                'include_bollinger': True,
            },
            '1d': {
                'sma_periods': [5, 10, 20, 50, 200],
                'ema_periods': [5, 10, 20, 50],
                'rsi_period': 14,
                'lag_features': [1, 2, 3, 5, 10, 20],
                'include_macd': True,
                'include_bollinger': True,
            }
        }
        return configs.get(self.interval, configs['5min'])
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create all features for the given interval"""
        df = df.copy()
        
        # Price features
        df = self._add_price_features(df)
        
        # Technical indicators
        df = self._add_technical_indicators(df)
        
        # Volume features
        df = self._add_volume_features(df)
        
        # Time features
        df = self._add_time_features(df)
        
        # Lag features
        df = self._add_lag_features(df)
        
        # Drop NaN rows created by indicators
        df = df.dropna()
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        # Returns
        df['return_1'] = df['Close'].pct_change(1)
        df['return_3'] = df['Close'].pct_change(3)
        df['return_5'] = df['Close'].pct_change(5)
        
        # Log returns
        df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Volatility (rolling std of returns)
        df['volatility_5'] = df['return_1'].rolling(5).std()
        df['volatility_10'] = df['return_1'].rolling(10).std()
        
        # High-Low range
        df['hl_range'] = (df['High'] - df['Low']) / df['Low']
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
        config = self.feature_config
        
        # Simple Moving Averages
        for period in config['sma_periods']:
            df[f'sma_{period}'] = df['Close'].rolling(period).mean()
            df[f'price_to_sma_{period}'] = (df['Close'] - df[f'sma_{period}']) / df[f'sma_{period}']
        
        # Exponential Moving Averages
        for period in config['ema_periods']:
            df[f'ema_{period}'] = df['Close'].ewm(span=period).mean()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=config['rsi_period']).rsi()
        
        # Stochastic Oscillator (New)
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        # MACD (if enabled)
        if config['include_macd']:
            macd = ta.trend.MACD(df['Close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
        
        # Bollinger Bands (if enabled)
        if config['include_bollinger']:
            bb = ta.volatility.BollingerBands(df['Close'])
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['Close']
            df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        # Volume ratio (current / average)
        df['volume_ratio_5'] = df['Volume'] / df['Volume'].rolling(5).mean()
        df['volume_ratio_20'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        # VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['price_to_vwap'] = (df['Close'] - df['vwap']) / df['vwap']
        
        return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        if self.interval in ['1min', '5min', '15min', '1h']:
            df['hour'] = df.index.hour
            df['minute'] = df.index.minute
        
        if self.interval in ['1h', '1d']:
            df['day_of_week'] = df.index.dayofweek
        
        if self.interval == '1d':
            df['month'] = df.index.month
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features"""
        for lag in self.feature_config['lag_features']:
            df[f'close_lag_{lag}'] = df['Close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['Volume'].shift(lag)
        
        return df
```

---

## Epic 4: Multi-Model Training Pipeline

### US-MODEL-001: Multi-Model Training for Each Horizon
**Priority**: Critical  
**Story Points**: 21

**As a** ML engineer  
**I want** to train multiple models (LightGBM, XGBoost, RandomForest, LSTM) for each time horizon  
**So that** I can compare performance and select the best model

**Acceptance Criteria:**
- [ ] Train 4 models per horizon: LightGBM, XGBoost, RandomForest, LSTM
- [ ] Total models: 5 horizons × 4 models = 20 models
- [ ] Time-series cross-validation (walk-forward)
- [ ] Hyperparameter tuning with Optuna (50 trials per model)
- [ ] Model versioning and persistence
- [ ] Training metrics logged (RMSE, MAE, R², Directional Accuracy)

**Model Configuration:**

```python
# modeling/model_trainer.py
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import optuna

class MultiModelTrainer:
    def __init__(self, horizon: str, target_column: str):
        self.horizon = horizon
        self.target_column = target_column
        self.models = {}
        self.metrics = {}
    
    def train_all_models(self, X_train, y_train, X_val, y_val):
        """Train all models for this horizon"""
        
        # 1. LightGBM
        print(f"Training LightGBM for {self.horizon}...")
        self.models['lightgbm'] = self._train_lightgbm(X_train, y_train, X_val, y_val)
        
        # 2. XGBoost
        print(f"Training XGBoost for {self.horizon}...")
        self.models['xgboost'] = self._train_xgboost(X_train, y_train, X_val, y_val)
        
        # 3. Random Forest
        print(f"Training RandomForest for {self.horizon}...")
        self.models['random_forest'] = self._train_random_forest(X_train, y_train, X_val, y_val)
        
        # 4. LSTM
        print(f"Training LSTM for {self.horizon}...")
        self.models['lstm'] = self._train_lstm(X_train, y_train, X_val, y_val)
        
        return self.models
    
    def _train_lightgbm(self, X_train, y_train, X_val, y_val):
        """Train LightGBM with Optuna hyperparameter tuning"""
        
        def objective(trial):
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'verbosity': -1,
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
            }
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                params,
                train_data,
                num_boost_round=1000,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
            )
            
            preds = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            
            return rmse
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=50, show_progress_bar=True)
        
        # Train final model with best params
        best_params = study.best_params
        best_params.update({'objective': 'regression', 'metric': 'rmse', 'verbosity': -1})
        
        train_data = lgb.Dataset(X_train, label=y_train)
        final_model = lgb.train(best_params, train_data, num_boost_round=1000)
        
        # Evaluate
        preds = final_model.predict(X_val)
        self.metrics['lightgbm'] = self._calculate_metrics(y_val, preds)
        
        return final_model
    
    def _train_xgboost(self, X_train, y_train, X_val, y_val):
        """Train XGBoost with Optuna"""
        
        def objective(trial):
            params = {
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse',
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            }
            
            model = xgb.XGBRegressor(**params)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=50, verbose=False)
            
            preds = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            
            return rmse
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=50)
        
        # Train final model
        final_model = xgb.XGBRegressor(**study.best_params)
        final_model.fit(X_train, y_train)
        
        preds = final_model.predict(X_val)
        self.metrics['xgboost'] = self._calculate_metrics(y_val, preds)
        
        return final_model
    
    def _train_random_forest(self, X_train, y_train, X_val, y_val):
        """Train Random Forest"""
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            n_jobs=-1,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        preds = model.predict(X_val)
        self.metrics['random_forest'] = self._calculate_metrics(y_val, preds)
        
        return model
    
    def _train_lstm(self, X_train, y_train, X_val, y_val):
        """Train LSTM model"""
        # Reshape for LSTM (samples, timesteps, features)
        X_train_lstm = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
        X_val_lstm = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))
        
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(1, X_train.shape[1]), return_sequences=True),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        model.fit(
            X_train_lstm, y_train,
            validation_data=(X_val_lstm, y_val),
            epochs=50,
            batch_size=32,
            verbose=0
        )
        
        preds = model.predict(X_val_lstm).flatten()
        self.metrics['lstm'] = self._calculate_metrics(y_val, preds)
        
        return model
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calculate comprehensive metrics"""
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        # Direction accuracy (did we predict up/down correctly?)
        y_true_direction = np.sign(y_true)
        y_pred_direction = np.sign(y_pred)
        direction_accuracy = np.mean(y_true_direction == y_pred_direction)
        
        return {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'direction_accuracy': direction_accuracy
        }
    
    def get_best_model(self):
        """Return the best performing model based on RMSE"""
        best_model_name = min(self.metrics, key=lambda k: self.metrics[k]['rmse'])
        return best_model_name, self.models[best_model_name], self.metrics[best_model_name]
```

---

## Epic 5: Results Visualization Dashboard

### US-VIZ-001: Interactive Prediction Dashboard
**Priority**: High  
**Story Points**: 13

**As a** user  
**I want** to see interactive charts comparing predictions vs actual prices  
**So that** I can evaluate model performance visually

**Acceptance Criteria:**
- [ ] Candlestick chart with actual prices
- [ ] Prediction lines for each model overlaid
- [ ] Separate chart for each time horizon (1min, 3min, 5min, etc.)
- [ ] Zoom and pan functionality
- [ ] Hover tooltips showing exact values
- [ ] Toggle models on/off
- [ ] Responsive design (works on mobile)

**Dashboard Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ AAPL - Prediction Results                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [1min] [3min] [5min] [15min] [30min] [1h] [1d] ← Tabs      │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │         Candlestick Chart + Predictions                 │ │
│ │                                                         │ │
│ │  Price                                                  │ │
│ │  180 ┤                    ╱╲                           │ │
│ │      │                  ╱    ╲                         │ │
│ │  175 ┤                ╱        ╲                       │ │
│ │      │              ╱            ╲                     │ │
│ │  170 ┤────────────╱                ╲─────────          │ │
│ │      └────────────────────────────────────────         │ │
│ │        9:30   10:00   10:30   11:00   11:30           │ │
│ │                                                         │ │
│ │  Legend: ── Actual  ── LightGBM  ── XGBoost            │ │
│ │          ── RandomForest  ── LSTM                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Model Performance Metrics:                                  │
│ ┌──────────┬────────┬────────┬──────┬──────────────────┐   │
│ │ Model    │ RMSE   │ MAE    │ R²   │ Dir. Accuracy    │   │
│ ├──────────┼────────┼────────┼──────┼──────────────────┤   │
│ │ LightGBM │ 0.0023 │ 0.0018 │ 0.87 │ 58.3% ⭐        │   │
│ │ XGBoost  │ 0.0025 │ 0.0019 │ 0.85 │ 57.1%           │   │
│ │ RandForest│ 0.0031 │ 0.0024 │ 0.79 │ 54.2%           │   │
│ │ LSTM     │ 0.0028 │ 0.0021 │ 0.82 │ 56.5%           │   │
│ └──────────┴────────┴────────┴──────┴──────────────────┘   │
│                                                             │
│ [Download Report] [Export Predictions CSV]                  │
└─────────────────────────────────────────────────────────────┘
```

**Implementation with Plotly:**
```javascript
// static/js/visualization.js
function createPredictionChart(data, horizon) {
    const trace_actual = {
        x: data.timestamps,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        type: 'candlestick',
        name: 'Actual Price',
        increasing: {line: {color: '#26a69a'}},
        decreasing: {line: {color: '#ef5350'}}
    };
    
    const trace_lightgbm = {
        x: data.timestamps,
        y: data.predictions.lightgbm,
        type: 'scatter',
        mode: 'lines',
        name: 'LightGBM',
        line: {color: '#2196F3', width: 2}
    };
    
    const trace_xgboost = {
        x: data.timestamps,
        y: data.predictions.xgboost,
        type: 'scatter',
        mode: 'lines',
        name: 'XGBoost',
        line: {color: '#FF9800', width: 2}
    };
    
    const trace_rf = {
        x: data.timestamps,
        y: data.predictions.random_forest,
        type: 'scatter',
        mode: 'lines',
        name: 'Random Forest',
        line: {color: '#9C27B0', width: 2}
    };
    
    const trace_lstm = {
        x: data.timestamps,
        y: data.predictions.lstm,
        type: 'scatter',
        mode: 'lines',
        name: 'LSTM',
        line: {color: '#4CAF50', width: 2}
    };
    
    const layout = {
        title: `${horizon} Predictions vs Actual`,
        xaxis: {
            title: 'Time',
            rangeslider: {visible: false}
        },
        yaxis: {
            title: 'Price ($)'
        },
        hovermode: 'x unified',
        height: 600
    };
    
    Plotly.newPlot('chart-container', 
        [trace_actual, trace_lightgbm, trace_xgboost, trace_rf, trace_lstm], 
        layout,
        {responsive: true}
    );
}
```

---

### US-VIZ-002: Model Comparison Metrics Table
**Priority**: High  
**Story Points**: 5

**As a** user  
**I want** to see a comparison table of all model metrics  
**So that** I can quickly identify the best performing model

**Acceptance Criteria:**
- [ ] Table showing RMSE, MAE, R², Directional Accuracy for each model
- [ ] Highlight best metric in each column (green)
- [ ] Sortable columns
- [ ] Export to CSV functionality
- [ ] Visual indicators (stars, colors) for top performers

**API Endpoint:**
```python
@router.get("/api/results/{ticker}/{horizon}")
async def get_results(ticker: str, horizon: str):
    return {
        "ticker": ticker,
        "horizon": horizon,
        "models": {
            "lightgbm": {
                "rmse": 0.0023,
                "mae": 0.0018,
                "r2": 0.87,
                "direction_accuracy": 0.583,
                "training_time": 12.5
            },
            "xgboost": {...},
            "random_forest": {...},
            "lstm": {...}
        },
        "best_model": "lightgbm",
        "predictions": [...],
        "actual": [...]
    }
```

---

## Epic 6: Backend API & Orchestration

### US-API-001: FastAPI Backend Setup
**Priority**: Critical  
**Story Points**: 8

**As a** developer  
**I want** a FastAPI backend to orchestrate the entire pipeline  
**So that** the frontend can trigger and monitor the ML workflow

**Acceptance Criteria:**
- [ ] FastAPI application with CORS enabled
- [ ] Endpoints for: dataset check, data fetch, training, prediction, results
- [ ] WebSocket for real-time progress updates
- [ ] Background tasks for long-running operations
- [ ] Error handling and logging
- [ ] API documentation (Swagger UI)

**Project Structure:**
```
finAdvice/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── dataset.py       # Dataset endpoints
│   │   ├── training.py      # Training endpoints
│   │   ├── prediction.py    # Prediction endpoints
│   │   └── websocket.py     # WebSocket for progress
│   ├── services/
│   │   ├── pipeline_orchestrator.py
│   │   └── model_manager.py
│   └── schemas/
│       ├── dataset.py
│       └── prediction.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js
│   │   └── visualization.js
│   └── index.html
└── requirements.txt
```

**Main FastAPI App:**
```python
# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import dataset, training, prediction, websocket

app = FastAPI(title="Financial ML Platform", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(dataset.router, prefix="/api", tags=["dataset"])
app.include_router(training.router, prefix="/api", tags=["training"])
app.include_router(prediction.router, prefix="/api", tags=["prediction"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Financial ML Platform API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### US-API-002: Pipeline Orchestration Service
**Priority**: Critical  
**Story Points**: 13

**As a** backend developer  
**I want** a service to orchestrate the entire ML pipeline  
**So that** all steps execute in the correct order with error handling

**Acceptance Criteria:**
- [ ] Orchestrate: Data Fetch → Feature Engineering → Model Training → Prediction
- [ ] Progress tracking at each step
- [ ] Error recovery and retry logic
- [ ] Parallel model training (4 models simultaneously)
- [ ] Results caching
- [ ] Pipeline state persistence

**Implementation:**
```python
# app/services/pipeline_orchestrator.py
import asyncio
from typing import Dict, List
from app.services.model_manager import ModelManager

class PipelineOrchestrator:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.progress = {
            'data_fetch': 0,
            'feature_engineering': 0,
            'model_training': 0,
            'prediction': 0
        }
        self.results = {}
    
    async def run_pipeline(self, websocket=None):
        """Run the complete ML pipeline"""
        
        try:
            # Step 1: Data Fetch
            await self._update_progress('data_fetch', 0, 'Starting data fetch...', websocket)
            data = await self._fetch_data()
            await self._update_progress('data_fetch', 100, 'Data fetch complete', websocket)
            
            # Step 2: Feature Engineering
            await self._update_progress('feature_engineering', 0, 'Creating features...', websocket)
            features = await self._engineer_features(data)
            await self._update_progress('feature_engineering', 100, 'Features created', websocket)
            
            # Step 3: Model Training (parallel)
            await self._update_progress('model_training', 0, 'Training models...', websocket)
            models = await self._train_models(features, websocket)
            await self._update_progress('model_training', 100, 'All models trained', websocket)
            
            # Step 4: Prediction
            await self._update_progress('prediction', 0, 'Generating predictions...', websocket)
            predictions = await self._generate_predictions(models, features)
            await self._update_progress('prediction', 100, 'Pipeline complete!', websocket)
            
            self.results = {
                'models': models,
                'predictions': predictions,
                'metrics': self._calculate_metrics(models)
            }
            
            return self.results
            
        except Exception as e:
            await self._update_progress('error', 0, f'Error: {str(e)}', websocket)
            raise
    
    async def _train_models(self, features: Dict, websocket):
        """Train all models in parallel"""
        horizons = ['1min', '3min', '5min', '15min', '30min', '1h', '1d']
        all_models = {}
        
        for i, horizon in enumerate(horizons):
            progress = int((i / len(horizons)) * 100)
            await self._update_progress('model_training', progress, 
                                       f'Training models for {horizon}...', websocket)
            
            # Train 4 models in parallel for this horizon
            trainer = MultiModelTrainer(horizon, f'target_{horizon}')
            models = await asyncio.to_thread(
                trainer.train_all_models,
                features[horizon]['X_train'],
                features[horizon]['y_train'],
                features[horizon]['X_val'],
                features[horizon]['y_val']
            )
            
            all_models[horizon] = {
                'models': models,
                'metrics': trainer.metrics,
                'best_model': trainer.get_best_model()
            }
        
        return all_models
    
    async def _update_progress(self, step: str, progress: int, message: str, websocket):
        """Send progress update via WebSocket"""
        self.progress[step] = progress
        
        if websocket:
            await websocket.send_json({
                'step': step,
                'progress': progress,
                'message': message,
                'overall_progress': sum(self.progress.values()) / len(self.progress)
            })

---

## Epic 7: Cascading "Meta-Model" Architecture

### US-MODEL-002: Prediction-as-a-Feature (Cascading)
**Priority**: High  
**Story Points**: 13

**As a** data scientist  
**I want** to use the outputs of smaller (short-term) models as inputs for the long-term "Big Model"  
**So that** the long-term model can learn from local patterns identified by specialized models

**Acceptance Criteria:**
- [ ] Implement a `FeatureStacker` that collects predictions from 1min, 5min, and 1h models.
- [ ] Align timestamps correctly to prevent "future look-ahead" leakage.
- [ ] Create "Meta-Features":
    - Short-term consensus (average of short-term model predictions)
    - Prediction volatility (stdev of model outputs)
    - Momentum of predictions (change in short-term predictions over time)
- [ ] Train the 1-Day and 1-Month models using these stacked features.

---

## Epic 8: Popular Indicator Expansion

### US-FEAT-002: Advanced Technical Indicator Suite
**Priority**: Medium  
**Story Points**: 5

**As a** trader  
**I want** to include popular indicators like Stochastics and long-term MAs  
**So that** the models can capture standard chart patterns used by humans

**Acceptance Criteria:**
- [ ] **Stochastic Oscillator**: %K and %D lines.
- [ ] **Golden/Death Crosses**: Flag for SMA 50/200 crossovers.
- [ ] **Volume Weighted Moving Average (VWMA)**.
- [ ] **Commodity Channel Index (CCI)**.
- [ ] Indicators optimized for both crypto (volatile) and stocks.

---

## Epic 9: Explainable AI (XAI) & Interpretability

### US-XAI-001: Global Feature Importance Visualization
**Priority**: High  
**Story Points**: 5

**As a** trader  
**I want** to see which features are most important across the entire model  
**So that** I can understand the underlying logic of the predictions and trust the model more

**Acceptance Criteria:**
- [ ] Bar chart showing the top 10-20 features by importance (Weight/Gain for GBMs).
- [ ] Feature names are human-readable (e.g., "RSI (14)" instead of `rsi_14`).
- [ ] Toggle between different importance types (Gain, Cover, Weight).
- [ ] Visual distinction between technical indicators, sentiment, and cascading model features.

### US-XAI-002: Local Prediction Explanations (SHAP)
**Priority**: Medium  
**Story Points**: 8

**As a** trader  
**I want** to see *why* a specific prediction was made (e.g., why did the model predict a 2% jump?)  
**So that** I can see which specific indicator triggered the signal at that exact moment

**Acceptance Criteria:**
- [ ] Integration of SHAP (SHapley Additive exPlanations) for tree-based models.
- [ ] **Waterfall Plot** for a selected timestamp, showing how each feature pushed the price up or down.
- [ ] Hover tooltips on the main chart that show the "Top 3 Contributors" to that specific prediction.
- [ ] Explanation of the "Baseline" (what the model would predict without these features).

### US-XAI-003: Feature Dependency & Interaction Analysis
**Priority**: Low  
**Story Points**: 5

**As a** researcher  
**I want** to see how two features interact (e.g., how RSI and Volume work together)  
**So that** I can identify non-linear relationships in market dynamics

**Acceptance Criteria:**
- [ ] SHAP Dependency plots for top features.
- [ ] Heatmap of feature correlations specifically relating to the target variable.
```

---

## Summary & Implementation Plan

### **Phase 1: Foundation (Week 1)**
1. ✅ US-UI-001: Ticker input page
2. ✅ US-UI-002: Dataset check API
3. ✅ US-DATA-001: Minute-level data fetching
4. ✅ US-API-001: FastAPI backend setup

### **Phase 2: Features & Models (Week 2-3)**
5. ✅ US-FEAT-001: Multi-horizon feature engineering
6. ✅ US-MODEL-001: Multi-model training pipeline
7. ✅ US-API-002: Pipeline orchestration

### **Phase 3: Visualization (Week 4)**
8. ✅ US-UI-003: Real-time progress display
9. ✅ US-VIZ-001: Interactive prediction charts
10. ✅ US-VIZ-002: Model comparison metrics

### **Technology Stack:**
```yaml
Frontend:
  - HTML5 + Vanilla CSS + JavaScript
  - Plotly.js for interactive charts
  - WebSocket for real-time updates

Backend:
  - FastAPI (async Python web framework)
  - Uvicorn (ASGI server)
  - Background tasks for long-running operations

ML:
  - LightGBM, XGBoost, RandomForest (scikit-learn)
  - TensorFlow/Keras (LSTM)
  - Optuna (hyperparameter tuning)
  - ta (technical analysis library)

Data:
  - yfinance (market data)
  - pandas, numpy (data manipulation)
  - Existing Phase 1 pipeline

Deployment:
  - Docker container
  - Nginx reverse proxy
```

### **Next Steps:**
Would you like me to start implementing:
1. **The FastAPI backend** (US-API-001)?
2. **The simple UI** (US-UI-001)?
3. **Minute-level data fetching** (US-DATA-001)?

Let me know which part to tackle first! 🚀
