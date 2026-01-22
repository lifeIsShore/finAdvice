# System Architecture

## 📐 Overview

FinAdvice is designed as a **modular, pipeline-based architecture** with clear separation of concerns. The system follows a data flow from ingestion through feature engineering to modeling and visualization.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│              (Streamlit Dashboard - Phase 4)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    VISUALIZATION LAYER                           │
│   • Candlestick Charts    • SHAP Plots    • Performance Metrics │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      MODELING LAYER                              │
│   • XGBoost/LightGBM    • LSTM (Optional)    • SHAP Explainer  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 FEATURE ENGINEERING LAYER                        │
│   • Technical Indicators    • Rolling Windows    • Labels       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    DATA STORAGE LAYER                            │
│   • CSV Files    • Metadata (JSON)    • Quality Reports         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   DATA INGESTION LAYER                           │
│   • Ticker Selection    • Multi-Timeframe Fetching    • API     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      EXTERNAL DATA SOURCES                       │
│              (Yahoo Finance via yfinance)                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Architecture

### Phase 1: Data Ingestion (✅ Complete)

```
┌─────────────────────────────────────────────────────────────┐
│                   TICKER SELECTION (US-01)                   │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Manual     │         │  Automatic   │                 │
│  │   Input      │         │  S&P 500     │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         └────────┬───────────────┘                          │
│                  │                                          │
│         ┌────────▼────────┐                                 │
│         │  Validation     │                                 │
│         │  (yfinance)     │                                 │
│         └────────┬────────┘                                 │
└──────────────────┼──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              MULTI-TIMEFRAME FETCHING (US-02)               │
│                                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │  4H  │  │  1D  │  │  1W  │  │  1M  │  │  3M  │         │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘         │
│     │         │         │         │         │              │
│     └─────────┴─────────┴─────────┴─────────┘              │
│                         │                                   │
│                ┌────────▼────────┐                          │
│                │  Quality Check  │                          │
│                │  & Validation   │                          │
│                └────────┬────────┘                          │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  DATA STORAGE (US-03)                        │
│                                                              │
│  data/raw/{TICKER}/                                          │
│  ├── {TICKER}_4h_{DATE}.csv                                 │
│  ├── {TICKER}_1d_{DATE}.csv                                 │
│  ├── {TICKER}_1wk_{DATE}.csv                                │
│  ├── {TICKER}_1mo_{DATE}.csv                                │
│  └── {TICKER}_3mo_{DATE}.csv                                │
│                                                              │
│  data/metadata.json                                          │
│  data/quality_report.json                                    │
└──────────────────────────────────────────────────────────────┘
```

### Phase 2: Feature Engineering (📋 Planned)

```
┌──────────────────────────────────────────────────────────────┐
│                    FEATURE PIPELINE                           │
│                                                               │
│  Raw Data (CSV)                                               │
│       │                                                       │
│       ├─► Rolling Windows (US-04)                            │
│       │   └─► [5, 10, 20, 60, 90 days]                       │
│       │                                                       │
│       ├─► Price Features (US-05)                             │
│       │   └─► Returns, Volatility, Cumulative Returns        │
│       │                                                       │
│       ├─► Extremes (US-06)                                   │
│       │   └─► High/Low, Distance to extremes                 │
│       │                                                       │
│       ├─► Momentum (US-07)                                   │
│       │   └─► SMA, EMA, RSI, MACD, ROC                       │
│       │                                                       │
│       ├─► Volatility (US-08)                                 │
│       │   └─► ATR, Bollinger Bands, Drawdown                 │
│       │                                                       │
│       ├─► Volume (US-09)                                     │
│       │   └─► OBV, VWAP, Volume Spikes                       │
│       │                                                       │
│       ├─► Time Features (US-10)                              │
│       │   └─► Day/Week/Month, Gaps                           │
│       │                                                       │
│       └─► Cross-Asset (US-11)                                │
│           └─► Beta, Correlation, Relative Strength           │
│                                                               │
│  Engineered Features DataFrame                               │
│       │                                                       │
│       └─► data/processed/{TICKER}_features.csv               │
└───────────────────────────────────────────────────────────────┘
```

### Phase 3: Modeling (📋 Planned)

```
┌──────────────────────────────────────────────────────────────┐
│                      MODELING PIPELINE                        │
│                                                               │
│  Features + Labels                                            │
│       │                                                       │
│       ├─► Label Generation (US-12)                           │
│       │   └─► Forward Returns, Binary Targets                │
│       │                                                       │
│       ├─► Train/Test Split (Time-Aware)                      │
│       │   └─► No shuffle, preserve temporal order            │
│       │                                                       │
│       ├─► Model Training (US-13)                             │
│       │   ├─► XGBoost                                        │
│       │   ├─► LightGBM                                       │
│       │   └─► LSTM (Optional)                                │
│       │                                                       │
│       ├─► Cross-Validation                                   │
│       │   └─► TimeSeriesSplit (Walk-Forward)                 │
│       │                                                       │
│       ├─► Explainability (US-14)                             │
│       │   └─► SHAP Values, Feature Importance                │
│       │                                                       │
│       └─► Model Artifacts                                    │
│           ├─► models/{TICKER}_model.pkl                      │
│           ├─► models/{TICKER}_shap.pkl                       │
│           └─► models/{TICKER}_metrics.json                   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Directory Structure

```
finAdvice/
│
├── algotrade_datascience/          # Main application
│   │
│   ├── config.py                   # Configuration constants
│   ├── requirements.txt            # Dependencies
│   │
│   ├── core/                       # Core modules (Phase 1)
│   │   ├── __init__.py
│   │   ├── ticker_selector.py     # US-01
│   │   ├── data_fetcher.py        # US-02
│   │   └── data_storage.py        # US-03
│   │
│   ├── features/                   # Feature engineering (Phase 2)
│   │   ├── __init__.py
│   │   ├── rolling_windows.py     # US-04
│   │   ├── price_features.py      # US-05
│   │   ├── extremes.py            # US-06
│   │   ├── momentum.py            # US-07
│   │   ├── volatility.py          # US-08
│   │   ├── volume.py              # US-09
│   │   ├── time_features.py       # US-10
│   │   └── cross_asset.py         # US-11
│   │
│   ├── modeling/                   # ML models (Phase 3)
│   │   ├── __init__.py
│   │   ├── labels.py              # US-12
│   │   ├── trainers.py            # US-13
│   │   └── explainability.py      # US-14
│   │
│   ├── visualization/              # Dashboard (Phase 4)
│   │   ├── __init__.py
│   │   ├── app.py                 # US-15
│   │   └── components/
│   │       ├── charts.py
│   │       ├── indicators.py
│   │       └── shap_plots.py
│   │
│   ├── utils/                      # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── helpers.py
│   │
│   ├── data/                       # Data storage
│   │   ├── raw/                   # Raw CSV files
│   │   ├── processed/             # Engineered features
│   │   ├── models/                # Trained models
│   │   ├── metadata.json
│   │   └── quality_report.json
│   │
│   ├── main_data_pipeline.py      # Main entry point
│   ├── test_pipeline.py           # Quick test
│   └── data_quality_checker.py    # Quality validation
│
├── tests/                          # Test suite
│   ├── test_ticker_selector.py
│   ├── test_data_fetcher.py
│   ├── test_features.py
│   └── fixtures/
│
├── docs/                           # Documentation
│   ├── ARCHITECTURE.md            # This file
│   ├── CONTRIBUTING.md
│   ├── API.md
│   └── CHANGELOG.md
│
├── README.md                       # Project overview
├── LICENSE                         # MIT License
└── user-stories.json              # Feature specifications
```

---

## 🔄 Data Flow

### 1. Data Ingestion Flow

```
User Input (Tickers)
    │
    ▼
Ticker Validation (yfinance)
    │
    ▼
Multi-Timeframe Fetch (5 intervals)
    │
    ▼
Quality Validation
    │
    ▼
CSV Storage + Metadata
    │
    ▼
Quality Report Generation
```

### 2. Feature Engineering Flow (Planned)

```
Raw CSV Files
    │
    ▼
Load & Validate
    │
    ▼
Apply Rolling Windows
    │
    ▼
Calculate Features (Parallel)
    ├─► Price Features
    ├─► Momentum Indicators
    ├─► Volatility Metrics
    ├─► Volume Indicators
    ├─► Time Features
    └─► Cross-Asset Features
    │
    ▼
Merge All Features
    │
    ▼
Save Processed Data
```

### 3. Modeling Flow (Planned)

```
Processed Features
    │
    ▼
Generate Labels (Forward-Looking)
    │
    ▼
Train/Test Split (Time-Aware)
    │
    ▼
Model Training (XGBoost/LightGBM)
    │
    ▼
Cross-Validation (TimeSeriesSplit)
    │
    ▼
SHAP Explanation
    │
    ▼
Save Model + Metrics
```

---

## 🔌 External Dependencies

### Data Sources

- **Yahoo Finance** (via yfinance)
  - OHLCV data for stocks and crypto
  - S&P 500 ticker list
  - Free, no API key required

### Python Libraries

**Core:**
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `yfinance` - Market data fetching

**Feature Engineering:**
- `ta-lib` or `pandas-ta` - Technical indicators
- `scipy` - Statistical functions
- `statsmodels` - Time series analysis

**Modeling:**
- `xgboost` - Gradient boosting
- `lightgbm` - Fast gradient boosting
- `scikit-learn` - ML utilities
- `optuna` - Hyperparameter tuning

**Explainability:**
- `shap` - Model interpretability

**Visualization:**
- `streamlit` - Dashboard framework
- `plotly` - Interactive charts
- `matplotlib` - Static plots

---

## 🔒 Design Principles

### 1. Modularity

Each component is self-contained and can be used independently:

```python
# Use ticker selector standalone
from ticker_selector import TickerSelector
selector = TickerSelector()
tickers = selector.get_sp500_tickers(10)

# Use data fetcher standalone
from data_fetcher import DataFetcher
fetcher = DataFetcher()
data = fetcher.fetch_timeframe('AAPL', '1d', '30d')
```

### 2. Separation of Concerns

- **Data Layer**: Handles all data I/O
- **Business Logic**: Feature calculations, model training
- **Presentation**: Visualization and UI

### 3. Configuration-Driven

All constants in `config.py`:

```python
TIMEFRAMES = {
    '4h': {'period': '14d', 'min_rows': 20},
    '1d': {'period': '30d', 'min_rows': 20},
    # ...
}
```

### 4. Error Handling

Graceful degradation with comprehensive logging:

```python
try:
    data = fetch_data(ticker)
except Exception as e:
    logging.error(f"Failed to fetch {ticker}: {e}")
    # Continue with other tickers
```

### 5. Time-Series Awareness

**Critical**: No lookahead bias in features or validation:

```python
# Labels use shift(-n) for forward-looking
labels = returns.shift(-5)  # 5-day forward return

# Train/test split preserves time order
train = data[:split_date]
test = data[split_date:]  # No shuffle!
```

---

## 📊 Data Schema

### Raw Data (CSV)

```
Date,Open,High,Low,Close,Volume
2026-01-01 09:30:00,150.50,152.30,149.80,151.20,50000000
2026-01-02 09:30:00,151.20,153.10,150.50,152.80,45000000
```

### Metadata (JSON)

```json
{
  "fetches": [
    {
      "ticker": "AAPL",
      "interval": "1d",
      "period": "30d",
      "fetch_date": "2026-01-22",
      "row_count": 30,
      "date_range": "2025-12-23 to 2026-01-22",
      "file_path": "data/raw/AAPL/AAPL_1d_20260122.csv"
    }
  ]
}
```

### Quality Report (JSON)

```json
{
  "check_date": "2026-01-22",
  "files_checked": 10,
  "passed": 10,
  "failed": 0,
  "detailed_reports": [
    {
      "ticker": "AAPL",
      "interval": "1d",
      "passed": true,
      "row_count": 30,
      "missing_pct": 0.0,
      "issues": []
    }
  ]
}
```

---

## 🚀 Performance Considerations

### Optimization Strategies

1. **Vectorization**: Use pandas/numpy operations instead of loops
2. **Caching**: Cache S&P 500 list, avoid redundant API calls
3. **Parallel Processing**: Use multiprocessing for multiple tickers
4. **Incremental Updates**: Only fetch new data, not full history
5. **Lazy Loading**: Load data only when needed

### Scalability

- **Current**: Handles 10-50 tickers efficiently
- **Future**: Can scale to 500+ with Dask/parallel processing
- **Storage**: ~100KB per ticker per timeframe

---

## 🔐 Security Considerations

1. **API Keys**: No API keys required (yfinance is free)
2. **Data Validation**: All inputs validated before processing
3. **Error Handling**: No sensitive data in error messages
4. **Logging**: Sanitize logs to avoid exposing user data

---

## 📈 Future Architecture Enhancements

### Planned Improvements

1. **Database Integration**: PostgreSQL/TimescaleDB for better querying
2. **Real-Time Data**: WebSocket integration for live data
3. **Distributed Computing**: Dask/Ray for large-scale processing
4. **API Layer**: REST API for external integrations
5. **Containerization**: Docker for easy deployment
6. **CI/CD**: Automated testing and deployment

---

**Last Updated**: January 2026  
**Version**: 1.0.0 (Phase 1)
