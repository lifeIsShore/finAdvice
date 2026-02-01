# 📊 FinAdvice AI - Advanced Trading Intelligence

> A production-ready AI trading assistant that combines multi-timeframe market data, FinBERT sentiment analysis, and competitive machine learning models (XGBoost, Random Forest) to provide actionable buy/sell recommendations in an interactive dashboard.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success.svg)](algotrade_datascience/START_HERE.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Project Overview

**FinAdvice AI** goes beyond simple technical analysis by integrating three powerful engines into a single dashboard:

1.  **Quantitative Engine**: Fetches and analyzes multi-timeframe data (1h, 4h, 1d, 1wk, 1mo) from Yahoo Finance.
2.  **Sentiment Engine**: Uses **FinBERT** (Financial BERT) to analyze real-time news headlines and adjust price targets based on market sentiment.
3.  **ML Competition Engine**: Pits multiple models (XGBoost, Random Forest, Linear Regression) against each other for every prediction, dynamically selecting the winner based on recent accuracy.

The result is a simple, actionable "Command Center" for traders.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Internet connection (for data & news fetching)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd finAdvice

# Install dependencies (including ML & Flask)
pip install -r algotrade_datascience/requirements.txt
```

### Launch the Dashboard

```bash
# Run the web application
python dashboard_app.py
```

*   Open your browser to **http://localhost:5000**
*   Select a ticker (e.g., AAPL, BTC-USD) or enter a custom one.
*   Click **"Predict"** to run the full analysis pipeline (Data -> Sentiment -> ML).

---

## 📁 Project Structure

```
finAdvice/
├── dashboard_app.py                   # Main Flask Web Server
├── README.md                          # This file
├── algotrade_datascience/             # Core Data Science Engine
│   ├── decision_making_ml.py          # Main ML Logic & Prediction Pipeline
│   ├── baseline_models.py             # Model Competition (RF, XGB, LR)
│   ├── main_data_pipeline.py          # Data Ingestion Orchestrator
│   ├── core/                          # Data Fetching & Storage Modules
│   └── features/                      # Sentiment Analysis (FinBERT)
├── static/                            # Frontend Assets (JS, CSS)
├── templates/                         # HTML Templates
└── data/                              # Local Data Store (CSV & JSON)
```

---

## 🧠 Key Features

### 1. 🤖 Multi-Model Competition
Instead of relying on one algorithm, FinAdvice trains **three models** on the fly for every request:
*   **XGBoost Regressor**: Optimized for gradient boosting on structured data.
*   **Random Forest**: Robust against overfitting and noisy market data.
*   **Linear Regression**: A baseline to ensure complex models are actually adding value.

The system evaluates all three on a hold-out validation set and purely uses the **"Winner"** for the final prediction.

### 2. 📰 AI Sentiment Analysis
*   Fetches the latest news articles for the specific ticker.
*   Uses **FinBERT** (a BERT model fine-tuned on financial text) to score headlines.
*   Classifies sentiment as *Bullish*, *Bearish*, or *Neutral*.
*   **Impact**: Strongly positive/negative sentiment dynamically adjusts the ML price targets (e.g., +5% for "Dramatically Up" sentiment).

### 3. ⏱️ Multi-Timeframe Consensus
Before making a recommendation, the system checks trends across **4 different timeframes**:
*   **1 Hour**: Intraday momentum
*   **4 Hour**: Short-term swing
*   **1 Week**: Medium-term trend
*   **1 Month**: Long-term macro view

A "Confidence Score" is generated based on how many timeframes agree with the primary daily prediction.

---

## 💻 Dashboard Features

*   **Interactive Charts**: Zoomable price history with ML-predicted Support (Buy) and Resistance (Sell) levels.
*   **Live Metrics**: Real-time display of Model R², MAE (Mean Absolute Error), and Confidence Scores.
*   **Diagnostics Page**: Deep dive into model performance with Confusion Matrices, ROC Curves, and Feature Importance charts.
*   **Crypto Support**: Full support for cryptocurrencies (BTC-USD, ETH-USD, etc.) with 24/7 data fetching.

---

## 🛠️ Configuration

You can tweak the ML settings in `algotrade_datascience/config.py` or directly via the UI (Risk Mode: Aggressive/Conservative).

**Risk Modes:**
*   **Conservative**: Wider stop-losses, requires deeper dips to buy, aims for smaller consistent gains.
*   **Aggressive**: Tighter stops, enters trades earlier, aims for maximum breakout potential.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install dev dependencies
pip install pytest flake8 black

# Run tests
pytest tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Built for the Future of Trading.*
