# AlgoTrade DataScience App

## Phase 1: Dataset Creation (US-01, US-02, US-03) ✅

A comprehensive data pipeline for fetching, validating, and storing multi-timeframe financial market data.

### Features

#### ✅ US-01: Asset Universe Selection
- Manual ticker input (stocks & crypto)
- Automatic top 10 S&P 500 selection
- Ticker validation via yfinance
- Detailed validation reports

#### ✅ US-02: Multi-Resolution Data Fetching
- **5 timeframes**: 4h, 1d, 1wk, 1mo, 3mo
- Specific lookback periods per timeframe
- Automatic retry logic for failed fetches
- Data quality validation during fetch
- Exact timestamp preservation

#### ✅ US-03: Raw Data Storage
- CSV format with consistent OHLCV schema
- Organized directory structure: `data/raw/{ticker}/`
- Comprehensive metadata tracking (JSON)
- Reusable datasets outside the application

### Installation

```bash
# Navigate to the project directory
cd algotrade_datascience

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Quick Start - Auto Mode (Top 5 S&P 500)
```bash
python main_data_pipeline.py --mode auto --count 5
```

#### Manual Ticker Selection
```bash
python main_data_pipeline.py --mode manual --tickers AAPL TSLA MSFT NVDA
```

#### With Crypto Support
```bash
python main_data_pipeline.py --mode manual --tickers AAPL BTC-USD ETH-USD
```

### Data Quality Checking

After running the pipeline, validate dataset quality:

```bash
python data_quality_checker.py
```

This will:
- Check all stored CSV files
- Validate row counts, missing data, OHLC logic
- Generate a quality report JSON
- Print detailed metrics

### Output Structure

```
algotrade_datascience/
├── data/
│   ├── raw/
│   │   ├── AAPL/
│   │   │   ├── AAPL_4h_20260122.csv
│   │   │   ├── AAPL_1d_20260122.csv
│   │   │   ├── AAPL_1wk_20260122.csv
│   │   │   ├── AAPL_1mo_20260122.csv
│   │   │   └── AAPL_3mo_20260122.csv
│   │   └── TSLA/
│   │       └── ...
│   ├── metadata.json
│   └── quality_report.json
├── data_pipeline.log
└── ...
```

### CSV Schema

All CSV files follow this structure:

| Column | Type     | Description              |
|--------|----------|--------------------------|
| Date   | datetime | Exact timestamp          |
| Open   | float    | Opening price            |
| High   | float    | Highest price            |
| Low    | float    | Lowest price             |
| Close  | float    | Closing price            |
| Volume | int      | Trading volume           |

### Quality Checks

The quality checker validates:
- ✅ Minimum row count per timeframe
- ✅ No missing required columns
- ✅ Missing data <10% threshold
- ✅ Date continuity (no large gaps)
- ✅ No negative prices
- ✅ Valid OHLC logic (High >= Open/Close/Low, Low <= all)
- ✅ Volume data present

### Example Output

```
================================================================================
ALGOTRADE DATA SCIENCE - PHASE 1: DATASET CREATION
================================================================================

STEP 1: TICKER SELECTION (US-01)
Mode: Automatic top 5 S&P 500 selection
Validating tickers...
✓ Valid ticker: AAPL
✓ Valid ticker: MSFT
✓ Valid ticker: GOOGL
✓ Valid ticker: AMZN
✓ Valid ticker: NVDA

STEP 2: MULTI-TIMEFRAME DATA FETCHING (US-02)
Fetching 5 timeframes: 4h, 1d, 1wk, 1mo, 3mo
✓ Successfully fetched 84 rows for AAPL at 4h
✓ Successfully fetched 30 rows for AAPL at 1d
...

STEP 3: CSV STORAGE & METADATA (US-03)
✓ Saved AAPL 4h to data/raw/AAPL/AAPL_4h_20260122.csv (84 rows)
...

✅ Phase 1 Complete!
Total files saved: 25/25
Success rate: 100.0%
```

### Configuration

Edit `config.py` to customize:
- Default tickers
- Timeframe intervals and lookback periods
- Minimum row counts
- Data quality thresholds
- Retry logic parameters

### Next Steps

- **Phase 2**: Feature Engineering (US-04 through US-11)
- **Phase 3**: ML Modeling (US-12, US-13)
- **Phase 4**: Explainability (US-14)
- **Phase 5**: Visualization Dashboard (US-15)

### Troubleshooting

**No data returned for ticker:**
- Check if ticker symbol is correct
- Verify internet connection
- Some tickers may have limited historical data

**Failed quality checks:**
- Review `data/quality_report.json` for details
- Check data gaps in date range
- Verify yfinance returned complete data

**Import errors:**
- Ensure all requirements installed: `pip install -r requirements.txt`
- Use Python 3.8+

### License

MIT License - See LICENSE file for details

### Contact

For issues or questions, please open an issue on GitHub.
