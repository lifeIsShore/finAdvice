"""
==============================================================================
  ALGOTRADE DATASCIENCE - QUICK START GUIDE
  Phase 1: Dataset Creation (US-01, US-02, US-03)
==============================================================================

STEP 1: Install Dependencies
-----------------------------
cd algotrade_datascience
pip install -r requirements.txt


STEP 2: Run Quick Test (2 tickers)
-----------------------------------
python test_pipeline.py

Expected output:
- Fetches AAPL and MSFT data
- 5 timeframes per ticker (4h, 1d, 1wk, 1mo, 3mo)
- Saves 10 CSV files to data/raw/
- Runs quality checks
- Time: ~2-3 minutes


STEP 3: Check Your Data
------------------------
Look in these locations:
  data/raw/AAPL/           - AAPL CSV files (5 files)
  data/raw/MSFT/           - MSFT CSV files (5 files)
  data/metadata.json       - Tracking info
  data/quality_report.json - Quality metrics
  data_pipeline.log        - Execution log


STEP 4: Run Your Own Tickers
-----------------------------
# Manual mode with your chosen tickers:
python main_data_pipeline.py --mode manual --tickers AAPL TSLA NVDA

# Auto mode (top 5 S&P 500):
python main_data_pipeline.py --mode auto --count 5

# With crypto:
python main_data_pipeline.py --mode manual --tickers BTC-USD ETH-USD AAPL


STEP 5: Validate Data Quality
------------------------------
python data_quality_checker.py

This checks:
- Minimum row counts
- Missing data percentage
- OHLC logic
- Date continuity
- Volume presence


WHAT YOU GET
============
For each ticker, 5 CSV files with this structure:

    Date,Open,High,Low,Close,Volume
    2024-01-01 09:30:00,150.5,152.3,149.8,151.2,50000000
    2024-01-02 09:30:00,151.2,153.1,150.5,152.8,45000000
    ...

Timeframes:
  4h   - Last 2 weeks  (~84 rows)
  1d   - Last 30 days  (~30 rows)
  1wk  - Last 3 months (~12 rows)
  1mo  - Last 12 months (~12 rows)
  3mo  - Last 24 months (~8 rows)


COMMON ISSUES
=============

1. "ModuleNotFoundError: No module named 'yfinance'"
   → pip install yfinance pandas

2. "No valid tickers to process"
   → Check ticker spelling (must be uppercase)
   → Verify internet connection
   → Try: python ticker_selector.py

3. Quality checks failing
   → Review data/quality_report.json
   → Some tickers may have limited historical data
   → Re-run for specific tickers

4. Slow execution
   → Normal! yfinance rate limits requests
   → Expect ~30 seconds per ticker
   → Reduce ticker count for faster testing


NEXT STEPS
==========
Once Phase 1 data is validated:
→ Phase 2: Feature Engineering (coming next)
   - Rolling windows
   - Technical indicators (RSI, MACD, Bollinger Bands)
   - Momentum, volatility, volume features


SUPPORT
=======
Check these files for help:
  README.md                  - Full documentation
  IMPLEMENTATION_SUMMARY.md  - Detailed implementation guide
  data_pipeline.log          - Execution logs
  data/quality_report.json   - Data quality metrics

==============================================================================
                    Ready to build your trading model! 🚀
==============================================================================
"""

# This is a documentation file - no code execution needed
print(__doc__)
