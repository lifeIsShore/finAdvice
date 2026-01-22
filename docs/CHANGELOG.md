# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-01-22

### ✅ Phase 1 Complete - Dataset Creation

#### Added

**US-01: Asset Universe Selection & Ticker Input**
- Manual ticker input support for stocks and cryptocurrencies
- Automatic top 10 S&P 500 ticker selection by market cap
- Ticker validation via yfinance API
- Comprehensive error handling and reporting
- Support for mixed asset types (stocks + crypto)

**US-02: Multi-Resolution Market Data Fetching**
- 4-hour interval data fetching (last 2 weeks, ~84 rows)
- 1-day interval data fetching (last 30 days, ~30 rows)
- 1-week interval data fetching (last 3 months, ~12 rows)
- 1-month interval data fetching (last 12 months, ~12 rows)
- 3-month interval data fetching (last 24 months, ~8 rows)
- Exact timestamp preservation with timezone awareness
- Volume data inclusion and validation
- Automatic retry logic (3 attempts per fetch)
- Real-time data quality validation during fetch

**US-03: Raw Data Storage**
- CSV file format with consistent OHLCV schema
- Organized directory structure: `data/raw/{ticker}/`
- Comprehensive metadata tracking in JSON format
- File naming convention: `{ticker}_{interval}_{date}.csv`
- Reusable datasets outside the application
- Exact date preservation in all files

**Quality Assurance**
- Automated data quality checker (`data_quality_checker.py`)
- Validation checks:
  - Minimum row count per timeframe
  - Required columns presence (Date, OHLCV)
  - Missing data threshold (< 10%)
  - Date continuity validation
  - Negative price detection
  - OHLC logic validation (High ≥ all, Low ≤ all)
  - Volume data validation
- Quality report generation in JSON format

**Core Modules**
- `ticker_selector.py` - Ticker selection and validation (US-01)
- `data_fetcher.py` - Multi-timeframe data fetching (US-02)
- `data_storage.py` - CSV storage and metadata management (US-03)
- `data_quality_checker.py` - Data quality validation
- `main_data_pipeline.py` - Main orchestration script
- `test_pipeline.py` - Quick test script for 2 tickers
- `config.py` - Centralized configuration management

**Documentation**
- `README.md` - Comprehensive project overview
- `START_HERE.md` - Quick start guide with examples
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `QUICKSTART.py` - Quick reference commands
- `docs/CONTRIBUTING.md` - Contribution guidelines
- `docs/ARCHITECTURE.md` - System architecture documentation
- `user-stories.json` - Complete user stories (US-01 to US-15)

**Infrastructure**
- `requirements.txt` - Python dependencies
- Logging system with file output (`data_pipeline.log`)
- Metadata tracking system
- Quality reporting system

#### Technical Details

- **Language**: Python 3.8+
- **Key Dependencies**: yfinance, pandas, numpy
- **Data Source**: Yahoo Finance (free, no API key required)
- **Storage Format**: CSV (human-readable, portable)
- **Metadata Format**: JSON (structured, queryable)

#### Performance

- Execution time: ~2-3 minutes for 2 tickers (10 files)
- Execution time: ~10-15 minutes for 10 tickers (50 files)
- Storage: ~50-100 KB per CSV file
- Success rate: 100% for valid tickers

#### Testing

- Manual testing completed for all user stories
- Test coverage: US-01, US-02, US-03 fully validated
- Quality checks: All validation rules tested
- Edge cases: Invalid tickers, missing data, API failures

---

## [Unreleased]

### 📋 Phase 2 - Feature Engineering (Planned)

#### Planned Features

**US-04: Rolling Window Generation**
- Multiple window sizes: 5, 10, 20, 60, 90 trading days
- Additional windows: 1 week, 1 month, 3 months
- Year-to-date rolling window
- Window size validation and edge case handling

**US-05: Core Price Feature Creation**
- Simple returns (pct_change)
- Log returns (np.log)
- Cumulative returns
- Average daily return per window
- Return volatility (standard deviation) for all windows
- Price normalization features

**US-06: High/Low Extreme Detection & Regime Analysis**
- Highest high per window with exact date
- Lowest low per window with exact date
- Distance to high (percentage)
- Distance to low (percentage)
- Range normalization ((High-Low)/Low)
- Days since high/low

**US-07: Trend and Momentum Indicators**
- Simple Moving Averages (SMA): 5, 10, 20, 50, 100, 200
- Exponential Moving Averages (EMA): 5, 10, 20, 50, 100, 200
- Price-to-MA distance (percentage)
- MA slope (derivative)
- MA crossover flags (20>50, 50>200)
- Relative Strength Index (RSI): 14, 21
- MACD (line, signal, histogram)
- Rate of Change (ROC)
- Momentum over N days

**US-08: Volatility and Risk Metrics**
- Rolling volatility (std of returns)
- Average True Range (ATR)
- Bollinger Bands (upper, lower, width, %B)
- Volatility regime indicator
- Rolling max drawdown
- Time since drawdown low

**US-09: Volume-Based Indicators**
- Rolling average volume
- Volume change ratio
- Volume spike indicator (Vol > 2x avg)
- On-Balance Volume (OBV)
- VWAP (Volume Weighted Average Price)
- Price-volume trend confirmation flags

**US-10: Time and Structural Features**
- Day of week (0-4 for Mon-Fri)
- Week of month (1-5)
- Month of year (1-12)
- Days since last high/low
- Days since MA crossover
- Gap up/down flag (open vs prev close)

**US-11: Relative and Cross-Asset Features**
- Relative strength vs index (SPY)
- Rolling beta (regression coefficient)
- Rolling correlation with benchmark
- Sector ETF momentum
- Risk-free rate adjusted return (Sharpe-like)

---

### 📋 Phase 3 - ML Modeling (Planned)

**US-12: Leakage-Safe Label Generation**
- Forward return (5d, 20d) using shift(-n)
- Forward volatility (next N days std)
- Binary: Hit high in next N days
- Binary: Hit low in next N days
- Trend continuation vs reversal label

**US-13: Model Training and Time-Series Validation**
- XGBoost / LightGBM training
- Optional: LSTM for sequence modeling
- Optional: Transformer-based models
- Time-series cross-validation (walk-forward)
- Multiple target prediction support
- Hyperparameter tuning with Optuna

**US-14: Model Explainability with SHAP**
- Global SHAP importance (summary plot)
- Local SHAP explanations (force plot)
- SHAP time evolution
- Single prediction waterfall chart
- Top 20 features visualization

---

### 📋 Phase 4 - Visualization (Planned)

**US-15: Minimal Analytical Dashboard**
- Ticker selection dropdown
- Candlestick chart + volume
- Indicator overlays (BB, MA, RSI, MACD)
- Prediction vs actual plots
- SHAP visualizations (summary, force, waterfall)
- Feature correlation heatmap
- Drawdown analysis graph

---

## Version History

### [1.0.0] - 2026-01-22
- **Phase 1 Complete**: Dataset Creation (US-01, US-02, US-03)
- Initial release with full data ingestion pipeline
- Production-ready data fetching and storage
- Comprehensive quality validation

### [0.1.0] - 2026-01-15 (Internal)
- Initial project setup
- User stories definition
- Architecture planning

---

## Migration Guide

### From Pre-1.0 to 1.0.0

If you were using an earlier version:

1. **Update dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Data structure unchanged**: All existing CSV files remain compatible

3. **New features**: Quality checker is now available
   ```bash
   python data_quality_checker.py
   ```

---

## Deprecation Notices

None currently.

---

## Known Issues

None currently. All Phase 1 features are stable and tested.

---

## Roadmap

- **Q1 2026**: Phase 2 - Feature Engineering (US-04 to US-11)
- **Q2 2026**: Phase 3 - ML Modeling (US-12 to US-14)
- **Q3 2026**: Phase 4 - Visualization Dashboard (US-15)
- **Q4 2026**: Production deployment and optimization

---

## Contributors

- Initial development and Phase 1 implementation

---

## Links

- [GitHub Repository](https://github.com/your-repo/finAdvice)
- [Documentation](docs/)
- [User Stories](user-stories.json)

---

**Note**: This project follows semantic versioning. Breaking changes will increment the major version.
