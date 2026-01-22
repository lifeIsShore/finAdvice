# 📊 FinAdvice - AlgoTrade DataScience Application

> A comprehensive algorithmic trading data science platform for stock and cryptocurrency analysis, featuring multi-timeframe data ingestion, advanced feature engineering, machine learning modeling, and explainable AI (XAI) visualizations.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Phase%201%20Complete-success.svg)](algotrade_datascience/START_HERE.md)

---

## 🎯 Project Overview

**FinAdvice** is a modular, production-ready data science application designed for quantitative traders and data scientists. It provides a complete pipeline from data ingestion to model deployment, with a focus on:

- **Multi-Resolution Data Fetching**: 5 timeframes (4H, 1D, 1W, 1M, 3M) for comprehensive market analysis
- **Advanced Feature Engineering**: 60+ technical indicators, momentum, volatility, and volume features
- **Machine Learning Models**: XGBoost, LightGBM, and optional LSTM/Transformer support
- **Explainable AI**: SHAP-based model interpretability for transparent decision-making
- **Interactive Dashboard**: Streamlit-based UI for visualization and analysis

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection (for data fetching)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd finAdvice

# Navigate to the main application
cd algotrade_datascience

# Install dependencies
pip install -r requirements.txt
```

### Run Your First Test

```bash
# Test the pipeline with 2 tickers (AAPL, MSFT)
python test_pipeline.py

# Validate data quality
python data_quality_checker.py
```

**Expected Output**: 10 CSV files (5 timeframes × 2 tickers) in `data/raw/` with quality validation report.

---

## 📁 Project Structure

```
finAdvice/
├── README.md                          # This file - project overview
├── LICENSE                            # MIT License
├── user-stories.json                  # Complete user stories (US-01 to US-15)
│
├── algotrade_datascience/             # Main application directory
│   ├── START_HERE.md                  # 🎯 START HERE - Quick guide
│   ├── README.md                      # Detailed application documentation
│   ├── IMPLEMENTATION_SUMMARY.md      # Technical implementation details
│   ├── QUICKSTART.py                  # Quick reference commands
│   │
│   ├── config.py                      # Configuration constants
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── ticker_selector.py             # US-01: Ticker selection & validation
│   ├── data_fetcher.py                # US-02: Multi-timeframe data fetching
│   ├── data_storage.py                # US-03: CSV storage & metadata
│   ├── data_quality_checker.py        # Quality validation tool
│   ├── main_data_pipeline.py          # Main orchestration script
│   ├── test_pipeline.py               # Quick test script
│   │
│   ├── data/                          # Data directory (auto-created)
│   │   ├── raw/                       # Raw CSV files by ticker
│   │   ├── metadata.json              # Fetch tracking metadata
│   │   └── quality_report.json        # Quality validation results
│   │
│   └── data_pipeline.log              # Execution logs
│
└── docs/                              # Documentation (see DOCS.md)
    ├── ARCHITECTURE.md                # System architecture
    ├── API.md                         # API documentation
    ├── CONTRIBUTING.md                # Contribution guidelines
    └── CHANGELOG.md                   # Version history
```

---

## 🎓 Features by Phase

### ✅ Phase 1: Dataset Creation (COMPLETE)

| User Story | Feature | Status |
|------------|---------|--------|
| **US-01** | Asset Universe Selection & Ticker Input | ✅ Complete |
| **US-02** | Multi-Resolution Market Data Fetching | ✅ Complete |
| **US-03** | Raw Data Storage | ✅ Complete |

**Capabilities:**
- Manual ticker input or automatic top 10 S&P 500 selection
- 5 timeframes with specific lookback periods
- CSV storage with comprehensive metadata
- Automated quality validation

### 🔄 Phase 2: Feature Engineering (PLANNED)

| User Story | Feature | Status |
|------------|---------|--------|
| **US-04** | Rolling Window Generation | 📋 Planned |
| **US-05** | Core Price Features | 📋 Planned |
| **US-06** | High/Low Extreme Detection | 📋 Planned |
| **US-07** | Trend & Momentum Indicators | 📋 Planned |
| **US-08** | Volatility & Risk Metrics | 📋 Planned |
| **US-09** | Volume-Based Indicators | 📋 Planned |
| **US-10** | Time & Structural Features | 📋 Planned |
| **US-11** | Relative & Cross-Asset Features | 📋 Planned |

### 🔄 Phase 3: ML Modeling (PLANNED)

| User Story | Feature | Status |
|------------|---------|--------|
| **US-12** | Leakage-Safe Label Generation | 📋 Planned |
| **US-13** | Model Training & Time-Series Validation | 📋 Planned |
| **US-14** | Model Explainability with SHAP | 📋 Planned |

### 🔄 Phase 4: Visualization (PLANNED)

| User Story | Feature | Status |
|------------|---------|--------|
| **US-15** | Minimal Analytical Dashboard | 📋 Planned |

---

## 💻 Usage Examples

### Fetch Data for Specific Tickers

```bash
# Manual ticker selection
python main_data_pipeline.py --mode manual --tickers AAPL TSLA MSFT NVDA GOOGL

# Include cryptocurrency
python main_data_pipeline.py --mode manual --tickers AAPL BTC-USD ETH-USD

# Automatic top 10 S&P 500
python main_data_pipeline.py --mode auto --count 10
```

### Programmatic Usage

```python
import pandas as pd
from ticker_selector import TickerSelector
from data_fetcher import DataFetcher
from data_storage import DataStorage

# Select tickers
selector = TickerSelector()
tickers = selector.get_manual_tickers(['AAPL', 'MSFT'])

# Fetch data
fetcher = DataFetcher()
data = fetcher.fetch_all_timeframes('AAPL')

# Load saved data
df = pd.read_csv('data/raw/AAPL/AAPL_1d_20260122.csv', parse_dates=['Date'])
print(df.head())
```

---

## 📊 Data Schema

All CSV files follow this standardized schema:

| Column | Type | Description |
|--------|------|-------------|
| `Date` | datetime | Exact timestamp (timezone-aware) |
| `Open` | float | Opening price |
| `High` | float | Highest price in period |
| `Low` | float | Lowest price in period |
| `Close` | float | Closing price |
| `Volume` | int | Trading volume |

---

## 🔍 Quality Assurance

Every dataset is automatically validated for:

- ✅ Minimum row count per timeframe
- ✅ Required columns present (Date, OHLCV)
- ✅ Missing data < 10% threshold
- ✅ No negative or zero prices
- ✅ Valid OHLC logic (High ≥ all, Low ≤ all)
- ✅ Date continuity (no large gaps)
- ✅ Volume data present and reasonable

Run quality checks:

```bash
python data_quality_checker.py
```

Results are saved to `data/quality_report.json`.

---

## 🛠️ Configuration

Edit `config.py` to customize:

```python
# Timeframe configurations
TIMEFRAMES = {
    '4h': {'period': '14d', 'min_rows': 20},
    '1d': {'period': '30d', 'min_rows': 20},
    '1wk': {'period': '3mo', 'min_rows': 10},
    '1mo': {'period': '1y', 'min_rows': 10},
    '3mo': {'period': '2y', 'min_rows': 6}
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    'max_missing_pct': 10.0,
    'max_date_gap_days': 7
}
```

---

## 📚 Documentation

- **[START_HERE.md](algotrade_datascience/START_HERE.md)** - Quick start guide with examples
- **[IMPLEMENTATION_SUMMARY.md](algotrade_datascience/IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[User Stories](user-stories.json)** - Complete feature specifications
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'yfinance'` | Run `pip install -r requirements.txt` |
| No valid tickers found | Check ticker symbols (must be UPPERCASE) |
| Quality checks failing | Review `data/quality_report.json` for details |
| Slow execution | Normal - yfinance has rate limits (~30s per ticker) |
| Import errors | Ensure Python 3.8+ and all dependencies installed |

### Getting Help

1. Check `data_pipeline.log` for detailed error messages
2. Review `data/quality_report.json` for data issues
3. Consult the [IMPLEMENTATION_SUMMARY.md](algotrade_datascience/IMPLEMENTATION_SUMMARY.md)
4. Open an issue on GitHub

---

## 🧪 Testing

```bash
# Quick test with 2 tickers
python test_pipeline.py

# Validate data quality
python data_quality_checker.py

# Test individual components
python ticker_selector.py
python data_fetcher.py
python data_storage.py
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: Dataset Creation (US-01 to US-03) - ✅ Complete
- [ ] **Phase 2**: Feature Engineering (US-04 to US-11) - 🔄 In Progress
- [ ] **Phase 3**: ML Modeling (US-12 to US-14) - 📋 Planned
- [ ] **Phase 4**: Visualization Dashboard (US-15) - 📋 Planned

See [user-stories.json](user-stories.json) for detailed specifications.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 algotrade_datascience/
black algotrade_datascience/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **yfinance** - For providing free market data access
- **pandas** - For powerful data manipulation
- **XGBoost/LightGBM** - For state-of-the-art ML models
- **SHAP** - For model explainability

---

## 📞 Contact

For questions, issues, or suggestions:

- Open an issue on GitHub
- Review the documentation in `docs/`
- Check the logs in `data_pipeline.log`

---

## 📈 Project Status

**Current Version**: 1.0.0 (Phase 1 Complete)  
**Last Updated**: January 2026  
**Status**: Production-ready for data ingestion and storage

🚀 **Ready to use RIGHT NOW!**

---

*Built with ❤️ for algorithmic trading and data science*
