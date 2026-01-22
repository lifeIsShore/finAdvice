# Project Structure

This document provides a complete overview of the FinAdvice project directory structure.

---

## Complete Directory Tree

```
finAdvice/
│
├── README.md                                    # Project overview and quick start
├── LICENSE                                      # MIT License
├── .gitignore                                   # Git ignore rules
├── user-stories.json                            # Complete user stories (US-01 to US-15)
│
├── docs/                                        # Documentation
│   ├── ARCHITECTURE.md                          # System architecture and design
│   ├── API.md                                   # API documentation
│   ├── CONTRIBUTING.md                          # Contribution guidelines
│   ├── CHANGELOG.md                             # Version history and changes
│   └── PROJECT_STRUCTURE.md                     # This file
│
├── algotrade_datascience/                       # Main application directory
│   │
│   ├── README.md                                # Application-specific documentation
│   ├── START_HERE.md                            # Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md                # Technical implementation details
│   ├── QUICKSTART.py                            # Quick reference commands
│   │
│   ├── config.py                                # Configuration constants
│   ├── requirements.txt                         # Production dependencies
│   ├── requirements-dev.txt                     # Development dependencies
│   │
│   ├── main_data_pipeline.py                    # Main entry point
│   ├── test_pipeline.py                         # Quick test script
│   ├── data_quality_checker.py                  # Quality validation utility
│   │
│   ├── core/                                    # Core modules (Phase 1) ✅
│   │   ├── __init__.py                          # Package initialization
│   │   ├── ticker_selector.py                   # US-01: Ticker selection & validation
│   │   ├── data_fetcher.py                      # US-02: Multi-timeframe data fetching
│   │   └── data_storage.py                      # US-03: CSV storage & metadata
│   │
│   ├── features/                                # Feature engineering (Phase 2) 📋
│   │   ├── __init__.py                          # Package initialization
│   │   ├── rolling_windows.py                   # US-04: Rolling window generation (planned)
│   │   ├── price_features.py                    # US-05: Core price features (planned)
│   │   ├── extremes.py                          # US-06: High/low extremes (planned)
│   │   ├── momentum.py                          # US-07: Momentum indicators (planned)
│   │   ├── volatility.py                        # US-08: Volatility metrics (planned)
│   │   ├── volume.py                            # US-09: Volume indicators (planned)
│   │   ├── time_features.py                     # US-10: Time features (planned)
│   │   └── cross_asset.py                       # US-11: Cross-asset features (planned)
│   │
│   ├── modeling/                                # ML modeling (Phase 3) 📋
│   │   ├── __init__.py                          # Package initialization
│   │   ├── labels.py                            # US-12: Label generation (planned)
│   │   ├── trainers.py                          # US-13: Model training (planned)
│   │   └── explainability.py                    # US-14: SHAP explainability (planned)
│   │
│   ├── visualization/                           # Dashboard (Phase 4) 📋
│   │   ├── __init__.py                          # Package initialization
│   │   ├── app.py                               # US-15: Streamlit dashboard (planned)
│   │   └── components/                          # UI components (planned)
│   │       ├── charts.py                        # Chart components
│   │       ├── indicators.py                    # Indicator visualizations
│   │       └── shap_plots.py                    # SHAP visualizations
│   │
│   ├── utils/                                   # Utility modules
│   │   ├── __init__.py                          # Package initialization
│   │   ├── logger.py                            # Logging utilities (planned)
│   │   ├── validators.py                        # Validation utilities (planned)
│   │   └── helpers.py                           # Helper functions (planned)
│   │
│   ├── data/                                    # Data storage (auto-created)
│   │   ├── raw/                                 # Raw CSV files
│   │   │   ├── .gitkeep                         # Git tracking (empty dir)
│   │   │   ├── AAPL/                            # Example ticker directory
│   │   │   │   ├── AAPL_4h_20260122.csv        # 4-hour data
│   │   │   │   ├── AAPL_1d_20260122.csv        # Daily data
│   │   │   │   ├── AAPL_1wk_20260122.csv       # Weekly data
│   │   │   │   ├── AAPL_1mo_20260122.csv       # Monthly data
│   │   │   │   └── AAPL_3mo_20260122.csv       # Quarterly data
│   │   │   └── MSFT/                            # Another ticker
│   │   │       └── ...                          # 5 CSV files
│   │   │
│   │   ├── processed/                           # Engineered features (Phase 2)
│   │   │   ├── .gitkeep                         # Git tracking
│   │   │   └── {TICKER}_features.csv            # Feature files (planned)
│   │   │
│   │   ├── models/                              # Trained models (Phase 3)
│   │   │   ├── .gitkeep                         # Git tracking
│   │   │   ├── {TICKER}_model.pkl               # Model files (planned)
│   │   │   ├── {TICKER}_shap.pkl                # SHAP values (planned)
│   │   │   └── {TICKER}_metrics.json            # Metrics (planned)
│   │   │
│   │   ├── metadata.json                        # Fetch tracking metadata
│   │   └── quality_report.json                  # Quality validation report
│   │
│   ├── __pycache__/                             # Python cache (ignored by git)
│   └── data_pipeline.log                        # Execution logs (ignored by git)
│
└── tests/                                       # Test suite
    ├── __init__.py                              # Package initialization
    ├── test_ticker_selector.py                  # Tests for US-01 (planned)
    ├── test_data_fetcher.py                     # Tests for US-02 (planned)
    ├── test_data_storage.py                     # Tests for US-03 (planned)
    ├── test_features.py                         # Tests for features (planned)
    ├── test_modeling.py                         # Tests for modeling (planned)
    └── fixtures/                                # Test fixtures
        ├── sample_data.csv                      # Sample test data (planned)
        └── sample_metadata.json                 # Sample metadata (planned)
```

---

## Directory Descriptions

### Root Level

| Directory/File | Purpose |
|----------------|---------|
| `README.md` | Main project documentation with overview, installation, and usage |
| `LICENSE` | MIT License for the project |
| `.gitignore` | Git ignore rules for generated files, logs, and data |
| `user-stories.json` | Complete user story specifications (US-01 to US-15) |

### docs/

Documentation directory containing all project documentation:

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | System architecture, design principles, and data flow |
| `API.md` | Complete API documentation for all modules |
| `CONTRIBUTING.md` | Contribution guidelines, coding standards, and PR process |
| `CHANGELOG.md` | Version history and release notes |
| `PROJECT_STRUCTURE.md` | This file - complete directory structure |

### algotrade_datascience/

Main application directory:

| Directory/File | Purpose |
|----------------|---------|
| `config.py` | Centralized configuration (timeframes, thresholds, paths) |
| `requirements.txt` | Production Python dependencies |
| `requirements-dev.txt` | Development dependencies (testing, linting, docs) |
| `main_data_pipeline.py` | Main orchestration script (CLI entry point) |
| `test_pipeline.py` | Quick test script for 2 tickers |
| `data_quality_checker.py` | Data quality validation utility |

### algotrade_datascience/core/

**Status**: ✅ Phase 1 Complete

Core data ingestion modules:

| File | User Story | Purpose |
|------|------------|---------|
| `ticker_selector.py` | US-01 | Ticker selection and validation |
| `data_fetcher.py` | US-02 | Multi-timeframe data fetching |
| `data_storage.py` | US-03 | CSV storage and metadata management |

### algotrade_datascience/features/

**Status**: 📋 Planned (Phase 2)

Feature engineering modules:

| File | User Story | Purpose |
|------|------------|---------|
| `rolling_windows.py` | US-04 | Rolling window generation |
| `price_features.py` | US-05 | Returns, volatility, cumulative returns |
| `extremes.py` | US-06 | High/low detection and regime analysis |
| `momentum.py` | US-07 | SMA, EMA, RSI, MACD, ROC |
| `volatility.py` | US-08 | ATR, Bollinger Bands, drawdown |
| `volume.py` | US-09 | OBV, VWAP, volume spikes |
| `time_features.py` | US-10 | Day/week/month, gaps |
| `cross_asset.py` | US-11 | Beta, correlation, relative strength |

### algotrade_datascience/modeling/

**Status**: 📋 Planned (Phase 3)

Machine learning modules:

| File | User Story | Purpose |
|------|------------|---------|
| `labels.py` | US-12 | Forward-looking label generation |
| `trainers.py` | US-13 | XGBoost/LightGBM/LSTM training |
| `explainability.py` | US-14 | SHAP-based model interpretation |

### algotrade_datascience/visualization/

**Status**: 📋 Planned (Phase 4)

Dashboard and visualization:

| File | User Story | Purpose |
|------|------------|---------|
| `app.py` | US-15 | Streamlit dashboard main app |
| `components/charts.py` | US-15 | Candlestick and price charts |
| `components/indicators.py` | US-15 | Technical indicator overlays |
| `components/shap_plots.py` | US-15 | SHAP visualization components |

### algotrade_datascience/utils/

**Status**: 📋 Planned

Utility modules for common functionality:

| File | Purpose |
|------|---------|
| `logger.py` | Centralized logging configuration |
| `validators.py` | Common validation functions |
| `helpers.py` | Miscellaneous helper functions |

### algotrade_datascience/data/

Data storage directory (auto-created on first run):

| Directory | Purpose | Git Tracked |
|-----------|---------|-------------|
| `raw/` | Raw CSV files by ticker | Structure only (.gitkeep) |
| `processed/` | Engineered feature files | Structure only (.gitkeep) |
| `models/` | Trained model artifacts | Structure only (.gitkeep) |
| `metadata.json` | Fetch tracking metadata | No (generated) |
| `quality_report.json` | Quality validation report | No (generated) |

### tests/

Test suite directory:

| File | Purpose |
|------|---------|
| `test_ticker_selector.py` | Unit tests for ticker selection |
| `test_data_fetcher.py` | Unit tests for data fetching |
| `test_data_storage.py` | Unit tests for storage |
| `test_features.py` | Unit tests for feature engineering |
| `test_modeling.py` | Unit tests for modeling |
| `fixtures/` | Test data and fixtures |

---

## File Naming Conventions

### CSV Files

```
{TICKER}_{INTERVAL}_{DATE}.csv

Examples:
- AAPL_1d_20260122.csv
- MSFT_4h_20260122.csv
- BTC-USD_1wk_20260122.csv
```

### Model Files

```
{TICKER}_model.pkl          # Trained model
{TICKER}_shap.pkl           # SHAP values
{TICKER}_metrics.json       # Performance metrics
```

### Feature Files

```
{TICKER}_features.csv       # Engineered features
```

---

## Git Tracking Strategy

### Tracked Files

- All source code (`.py` files)
- Documentation (`.md` files)
- Configuration (`config.py`, `requirements.txt`)
- Directory structure (`.gitkeep` files)
- User stories (`user-stories.json`)

### Ignored Files

- Generated data (`data/raw/*`, `data/processed/*`)
- Model artifacts (`*.pkl`, `*.h5`)
- Logs (`*.log`)
- Python cache (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- IDE files (`.vscode/`, `.idea/`)

See `.gitignore` for complete list.

---

## Module Import Paths

### Core Modules

```python
from algotrade_datascience.core.ticker_selector import TickerSelector
from algotrade_datascience.core.data_fetcher import DataFetcher
from algotrade_datascience.core.data_storage import DataStorage
```

### Feature Modules (Planned)

```python
from algotrade_datascience.features.momentum import calculate_rsi
from algotrade_datascience.features.volatility import calculate_bollinger_bands
```

### Modeling Modules (Planned)

```python
from algotrade_datascience.modeling.trainers import XGBoostTrainer
from algotrade_datascience.modeling.explainability import SHAPExplainer
```

---

## Scalability Considerations

### Current Structure

- **Supports**: 10-50 tickers efficiently
- **Storage**: ~100KB per ticker per timeframe
- **Total for 10 tickers**: ~5MB (50 files)

### Future Enhancements

When scaling to 500+ tickers:

1. **Database Integration**: Replace CSV with PostgreSQL/TimescaleDB
2. **Partitioning**: Organize by date ranges
3. **Compression**: Use Parquet instead of CSV
4. **Distributed Storage**: S3 or similar cloud storage

---

## Development Workflow

### Adding New Features

1. Create module in appropriate package (`features/`, `modeling/`, etc.)
2. Add `__init__.py` imports
3. Write unit tests in `tests/`
4. Update documentation in `docs/API.md`
5. Add entry to `CHANGELOG.md`

### Example: Adding RSI Indicator

```
1. Create: algotrade_datascience/features/momentum.py
2. Update: algotrade_datascience/features/__init__.py
3. Create: tests/test_momentum.py
4. Update: docs/API.md (add RSI documentation)
5. Update: docs/CHANGELOG.md (add to Unreleased section)
```

---

## Maintenance

### Regular Tasks

- **Weekly**: Review and clean logs
- **Monthly**: Update dependencies
- **Quarterly**: Archive old data
- **Yearly**: Major version updates

### Cleanup Commands

```bash
# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove logs
rm algotrade_datascience/data_pipeline.log

# Remove generated reports
rm algotrade_datascience/data/metadata.json
rm algotrade_datascience/data/quality_report.json
```

---

**Last Updated**: January 2026  
**Version**: 1.0.0 (Phase 1 Complete)
