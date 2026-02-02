# FinAdvice AI: Institutional Multi-Timeframe Intelligence

Welcome to the FinAdvice AI master documentation. This project is a professional-grade quantitative trading and research environment that combines Multi-Timeframe Ensemble AI with a robust backtesting laboratory.

---

## System Architecture

The project is built on a modular "Engine-First" architecture, separating data acquisition, intelligence generation, and user interface.

### 1. Data Layer (core/)
- **DataStorage**: Handles local persistence of OHLCV data in JSON/CSV.
- **DataFetcher**: Automated integration with Yahoo Finance. It features adaptive resampling (e.g., creating 4h bars from 1h data) and automatic gap filling.

### 2. Intelligence Layer (algotrade_datascience/)
- **Consensus Engine (consensus_engine.py)**: 
  - **Ensemble Model**: Combines XGBoost, Random Forest, Linear Regression, and LSTM.
  - **Competition Logic**: Each timeframe (1h, 4h, 1d) runs all models, calculates their historical accuracy, and selects a "Winner" for the final consensus.
  - **Sentiment Analysis**: Converts raw prediction percentages into human-readable sentiment levels (from "Dramatic Down" to "Dramatic Up").

### 3. Execution & Validation (backtest/)
- **Backtest Engine**: A walk-forward simulator that tests strategies without data leakage. 
- **Pyramiding Logic**: Supports fractional position sizing (scaling in) based on AI confidence boosts.
- **Fail-safes**: Integrated Profit Guard (Breakeven protection) and percentage-based Stop Loss.

---

## Strategy Lab (Backtest Pro GUI)

The Backtest UI serves as a "Strategy Lab" where you can stress-test institutional trading parameters.

### Core Settings
- **Ticker**: Supports any Yahoo Finance symbol (e.g., BTC-USD, NVDA, TSLA).
- **Interval**: Choose between 1h, 4h, 1d, and 1wk timings.
- **Capital**: Your initial virtual starting bankroll.

### Advanced Strategy Parameters
- **Buy/Sell Thresholds**: Define the "Confidence Gate." If set to 75%, the bot only trades when the AI is 75% certain.
- **Position Scaling (Pyramiding)**: 
  - **Base Buy Size**: What % of cash to use on the first signal.
  - **Confidence Boost**: An extra "Power Buy" triggered if the AI hits a "Gold Mine" score (e.g., >85%).
- **Profit Guard**: Prevents the bot from selling at a price lower than our purchase point (unless Stop Loss is hit).

---

## Dashboard and Analytics

The project includes a web-based dashboard and a deep analytics tab.

- **Main Dashboard**: Real-time consensus scores and price targets.
- **Analytics Tab**: Deep dive into individual model performance, feature importance (which data point moved the needle?), and news sentiment relevance.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Requirements: pandas, numpy, xgboost, scikit-learn, yfinance, tkinter

### Running the Lab
1. **Launch Backtest UI**: Run start_backtest_ui.bat.
2. **Launch Web Dashboard**: Run python dashboard_app.py.

---

## AI Feature Engineering

The models are trained using a rich set of technical and market features:
- **Momentum**: RSI, MACD.
- **Volatility**: Bollinger Bands, 5-day volatility spread.
- **Trend**: SMA (10, 20, 50).
- **Volume**: Volume intensity and relative volume ratios.
- **Temporal**: Multi-day lags and momentum shifts.

---

## Performance and Scalability
- **Threaded Execution**: Backtests run on background threads to keep the UI responsive.
- **Adaptive Logging**: Real-time terminal output with unit quantities and lot details.
- **Timezone Aware**: Handles UTC/Naive discrepancies automatically for intraday trading.

---
*Created with institutional precision for the modern quantitative researcher.*

---
*Created with institutional precision for the modern quantitative researcher.*
