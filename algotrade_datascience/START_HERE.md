# 🚀 FinAdvice AI - Quick Start Guide

## ✅ MVP Status: COMPLETE

This project has evolved from a simple data pipeline into a full-stack AI trading assistant.
It successfully implements **Data Ingestion**, **Sentiment Analysis**, **ML Modeling**, and a **Web Dashboard**.

---

## ⚡ How to Start (The Easy Way)

### 1️⃣ Install Dependencies
Navigate to the project root and install the required packages:

```bash
cd finAdvice/algotrade_datascience
pip install -r requirements.txt
```

### 2️⃣ Run the Dashboard
Go back to the root folder and launch the app:

```bash
cd ..
python dashboard_app.py
```

*   **Access the App**: Open [http://localhost:5000](http://localhost:5000)
*   **Pick a Ticker**: Select `AAPL` or type `BTC-USD`.
*   **Click Predict**: The AI will fetch data, analyze news, train models, and give you a recommendation.

---

## 🔎 What's Under the Hood?

### The Core Pipeline
When you click "Predict", the following happens in real-time:

1.  **Data Fetching**:
    *   Downloads OHLCV data for `1h`, `4h`, `1d`, `1wk`, `1mo`.
    *   Validates data quality automatically.

2.  **Sentiment Engine (FinBERT)**:
    *   Scrapes news from Yahoo Finance.
    *   Runs headlines through `ProsusAI/finbert`.
    *   Calculates a "Sentiment Score" (-1 to +1).

3.  **ML Competition**:
    *   Trains **Random Forest**, **XGBoost**, and **Linear Regression**.
    *   Evaluates them on unseen data.
    *   Selects the "Winner" (best directional accuracy).

4.  **Decision Logic**:
    *   Combines the ML prediction with Sentiment and Multi-Timeframe Consensus.
    *   Outputs: **BUY Price**, **SELL Price**, **STOP LOSS**.

---

## 📊 Troubleshooting

**"No Data Found"**
*   Click the **"Sync Data"** button in the dashboard first.
*   Wait for the spinner to finish (it fetches 12 timeframes!).

**"Model Error"**
*   Check the terminal where you ran `python dashboard_app.py`.
*   Common issue: Missing `xgboost` or `torch` (for FinBERT). Run `pip install xgboost torch transformers`.

**"Browser Cache Issues"**
*   If the chart looks old, do a hard refresh (Ctrl+F5).

---

## 📁 Key Files for Developers

| File | Purpose |
|------|---------|
| `dashboard_app.py` | The web server (Flask). Start here. |
| `algotrade_datascience/decision_making_ml.py` | The "Brain". Contains the prediction logic. |
| `algotrade_datascience/baseline_models.py` | The ML Competition logic. |
| `algotrade_datascience/core/data_storage.py` | Handles CSV and News (JSON) caching. |
| `static/script.js` | Frontend logic (Charts, API calls). |

---

*Enjoy trading with AI!*
