# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-02-01

### 🚀 MVP Release - Full Stack AI Dashboard

#### Added

**Web Dashboard**
- Interactive Flask application (`dashboard_app.py`) serving a modern UI.
- Real-time Chart.js visualizations with zoom and pan.
- Dynamic ticker search and selection.
- "Predict" button workflow (Data -> Sentiment -> ML -> UI).

**Machine Learning Engine**
- **Multi-Model Competition**: Automatically trains RF, XGBoost, and Linear Regression for every prediction.
- **Dynamic Model Selection**: Picks the "Winner" based on validation set performance.
- **Diagnostics API**: Exposes confusion matrices, ROC curves, and feature importance.

**Sentiment Analysis**
- integrated `ProsusAI/finbert` for financial sentiment classification.
- Real-time news scraping from Yahoo Finance.
- Sentiment scoring impact on price targets.

**Multi-Timeframe Consensus**
- Analysis across 1h, 4h, 1d, 1wk, 1mo intervals.
- Confidence scoring system.

#### Changed
- Promoted `algotrade_datascience` pipeline to production backend.
- Updated `README.md` and `START_HERE.md` to reflect full-stack capabilities.

---

## [1.1.0] - 2026-01-22

### 🧹 Codebase Tidying & Reorganization

#### Added

**Project Structure & Organization**
- Created modular package structure with clear separation of concerns:
  - `core/` - Phase 1 modules (ticker_selector, data_fetcher, data_storage)
  - `features/` - Ready for Phase 2 feature engineering modules
  - `modeling/` - Ready for Phase 3 ML modeling modules
  - `visualization/` - Ready for Phase 4 dashboard modules
  - `utils/` - Common utility functions
- Created `data/processed/` directory for engineered features
- Created `data/models/` directory for trained model artifacts
- Created `tests/` directory structure with fixtures folder
- Added `__init__.py` files to all packages with proper docstrings

**Comprehensive Documentation (13 Files, ~123KB)**
- `README.md` - Enhanced root README with badges, quick start, and roadmap (11KB)
- `LICENSE` - MIT License
- `.gitignore` - Comprehensive ignore rules for Python projects
- `QUICK_REFERENCE.md` - Quick navigation guide for all documentation (8KB)
- `TIDYING_SUMMARY.md` - Overview of tidying work performed (10KB)
- `CLEANUP_COMPLETE.md` - Final cleanup summary (9KB)
- `docs/INDEX.md` - Complete documentation index (10KB)
- `docs/ARCHITECTURE.md` - System architecture and design patterns (23KB)
- `docs/API.md` - Complete API reference with examples (12KB)
- `docs/CONTRIBUTING.md` - Contribution guidelines and coding standards (13KB)
- `docs/CHANGELOG.md` - This file - version history (8KB)
- `docs/PROJECT_STRUCTURE.md` - Directory structure guide (16KB)
- `requirements-dev.txt` - Development dependencies (pytest, black, flake8, etc.)

**Git Configuration**
- `.gitignore` configured to exclude:
  - Python cache files (`__pycache__/`, `*.pyc`)
  - Virtual environments (`venv/`, `env/`)
  - Generated data files (`data/raw/*`, `data/processed/*`)
  - Logs (`*.log`)
  - Model artifacts (`*.pkl`, `*.h5`)
  - IDE files (`.vscode/`, `.idea/`)
- `.gitkeep` files in empty directories to preserve structure

#### Changed

**Code Organization**
- Moved core modules into `core/` package:
  - `ticker_selector.py` → `core/ticker_selector.py`
  - `data_fetcher.py` → `core/data_fetcher.py`
  - `data_storage.py` → `core/data_storage.py`
- Updated all import statements to use new package structure:
  - `main_data_pipeline.py` - Updated to import from `core` package
  - `test_pipeline.py` - Updated to import from `core` package
  - `data_quality_checker.py` - Updated to import from `core` package

**Data Directory Structure**
- Consolidated all data from root `data/` into `algotrade_datascience/data/`
- Organized data directory with clear subdirectories:
  - `data/raw/` - Raw CSV files from data fetching
  - `data/processed/` - Engineered features (ready for Phase 2)
  - `data/models/` - Trained models (ready for Phase 3)

#### Removed

**Duplicates & Cleanup**
- Removed duplicate `data/` directory from project root
- Removed temporary `directory_structure.txt` file
- Consolidated all data files into single location

#### Documentation Improvements

**Architecture Documentation**
- Complete system architecture with diagrams
- Data flow documentation for all phases
- Component architecture breakdown
- Design principles and patterns
- Performance considerations
- Future enhancement roadmap

**API Documentation**
- Complete API reference for all public modules
- Method signatures with type hints
- Parameter descriptions and examples
- Return types and error handling
- Data schemas (CSV, JSON)
- CLI documentation

**Contributing Guidelines**
- Code of conduct
- Development workflow and branch naming
- Coding standards (PEP 8 + enhancements)
- Type hints and docstring guidelines (Google-style)
- Testing guidelines with pytest
- Pull request process
- Issue reporting templates

**Project Structure Guide**
- Complete directory tree
- File naming conventions
- Git tracking strategy
- Module import paths
- Development workflow
- Maintenance guidelines

#### Technical Details

**Package Structure**
- All packages now have proper `__init__.py` files
- Version information in package metadata
- `__all__` exports defined for public APIs
- Consistent docstring format (Google-style)

**Import Paths**
- Before: `from ticker_selector import TickerSelector`
- After: `from core.ticker_selector import TickerSelector`

**Development Tools**
- Added `requirements-dev.txt` with:
  - Testing: pytest, pytest-cov, pytest-mock
  - Code quality: black, flake8, pylint, mypy
  - Documentation: sphinx, sphinx-rtd-theme
  - Development: ipython, jupyter

#### Benefits

**For Developers**
- Clear package organization makes code easier to navigate
- Comprehensive documentation reduces onboarding time
- Coding standards ensure consistent code quality
- Test structure ready for TDD approach

**For Users**
- Professional README with quick start guide
- Multiple entry points for documentation
- Clear roadmap and feature status
- Easy to understand project structure

**For Maintainers**
- Git ignore rules prevent accidental commits
- Directory structure scales for future phases
- Documentation is comprehensive and up-to-date
- Clear contribution guidelines

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

### [1.1.0] - 2026-01-22
- **Codebase Tidying**: Complete reorganization and documentation
- Created modular package structure (core, features, modeling, visualization, utils)
- Added 13 comprehensive documentation files (~123KB)
- Moved core modules into organized packages
- Updated all import statements
- Removed duplicates and consolidated data directory
- Added development dependencies and tools
- Created test directory structure
- Professional .gitignore and LICENSE

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
