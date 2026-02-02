# Technical Strategy: Data Enrichment & Macro Filtering
**Architectural Specification for Automated Context-Aware ML**

## 1. The "GPS vs. Weather" Philosophy
As discussed, high-timeframe data (1-month charts / 20-year history) should act as a **Conditional Gate**, not a primary driver.

### The "Macro Filter" Logic:
1.  **Tactical (1h/4h):** Determines the "Execution" (Where do I put the order?).
2.  **Strategic (1d/1wk):** Determines the "Confidence" (How big is my position?).
3.  **Macro (1mo):** Determines the "Directional Permission" (Am I allowed to buy?).

> [!TIP]
> **Best Practice:** If the 1-month model shows a multi-year Bear Market trend, the system should strictly **disable "Strong Buy" signals** in the 1-hour model, limiting them to "Scalp Buys" (short-term bounces).

---

## 2. Advanced Data Brainstorming (Recursive/Automatic)
To keep the system fully automated, we focus on data that can be fetched via Python scripts without human input.

### A. Inter-market Analysis (Correlations)
*   **The "Dollar Wall" (DXY):** When the US Dollar is strong, Risk Assets (Crypto/Stocks) usually fall.
*   **The "Risk-On/Off" Proxy (S&P 500):** Fetching `^GSPC` data via your current `yfinance` pipeline adds "Global Sentiment" to your local ticker.
*   **Implementation:** Every time you fetch `BTC-USD`, your script should automatically fetch `DXY` and `SPY` and join them as columns.

### B. Macroeconomic Indicators (FRED API)
The Federal Reserve Economic Data (FRED) is free and has a Python library.
*   **Federal Funds Rate:** High rates usually cool down markets.
*   **CPI (Inflation):** High inflation forces the Fed to raise rates.
*   **Implementation:** Fetch these once a month (they don't change daily) and "pad" the values down to your 1-day or 4-hour datasets.

### C. On-Chain & Sentiment (APIs)
*   **Fear & Greed Index:** There is a free API (`https://api.alternative.me/fng/`) that gives a 0-100 score. 
    *   *Rule:* If Fear > 80, the "1-month model" should look for reversal patterns.
*   **Exchange Inflows:** (Requires a key like Glassnode/CryptoQuant) - High BTC inflow to exchanges usually means a sell-off is coming.

---

## 3. Best Practice: Preventing "Data Spoiling"
To use 2004 data without ruining 2024 results, we use **Temporal Weighting**.

### The "Decay" formula:
Instead of giving every row a weight of `1.0`, we use an exponential decay:
`Weight = e^( -lambda * (Current_Year - Data_Year) )`

*   **Result:** Data from 2024 has a weight of **1.0**. Data from 2004 might have a weight of **0.05**. The AI "learns" the lesson from 2004 (how a crash looks), but it prioritizes the "style" of 2024.

---

## 4. Proposed Feature: "Automatic Feature Crawler"
We can implement a new component: `algotrade_datascience/core/enrichment_engine.py`.

1.  **Trigger:** When `main_data_pipeline.py` starts.
2.  **Action:** It checks if `DXY`, `GOLD`, and `Interest_Rates` files exist/are fresh.
3.  **Merge:** It merges these into your `ticker_data.csv` so the ML models see the **full context** (e.g., "The price is falling, but so is the S&P 500, and Interest Rates just rose").

---
*Created by Antigravity AI - Strategy Document #2*
