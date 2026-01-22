# API Documentation

## Overview

This document provides detailed API documentation for all public modules and functions in the FinAdvice AlgoTrade DataScience Application.

---

## Table of Contents

- [Core Modules](#core-modules)
  - [ticker_selector](#ticker_selector)
  - [data_fetcher](#data_fetcher)
  - [data_storage](#data_storage)
- [Utilities](#utilities)
  - [data_quality_checker](#data_quality_checker)
- [Configuration](#configuration)
- [Data Schemas](#data-schemas)

---

## Core Modules

### ticker_selector

**Module**: `algotrade_datascience.core.ticker_selector`

#### TickerSelector

Main class for ticker selection and validation.

```python
from algotrade_datascience.core.ticker_selector import TickerSelector

selector = TickerSelector()
```

##### Methods

###### `get_manual_tickers(tickers: List[str]) -> List[str]`

Validate and return manual ticker list.

**Parameters:**
- `tickers` (List[str]): List of ticker symbols to validate

**Returns:**
- List[str]: Validated ticker symbols

**Raises:**
- `ValueError`: If no valid tickers provided

**Example:**
```python
tickers = selector.get_manual_tickers(['AAPL', 'MSFT', 'GOOGL'])
# Returns: ['AAPL', 'MSFT', 'GOOGL']
```

---

###### `get_sp500_tickers(count: int = 10) -> List[str]`

Get top N S&P 500 tickers by market cap.

**Parameters:**
- `count` (int, optional): Number of tickers to return. Default: 10

**Returns:**
- List[str]: Top N S&P 500 ticker symbols

**Example:**
```python
tickers = selector.get_sp500_tickers(count=5)
# Returns: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
```

---

###### `validate_ticker(ticker: str) -> bool`

Validate a single ticker symbol.

**Parameters:**
- `ticker` (str): Ticker symbol to validate

**Returns:**
- bool: True if valid, False otherwise

**Example:**
```python
is_valid = selector.validate_ticker('AAPL')
# Returns: True

is_valid = selector.validate_ticker('INVALID123')
# Returns: False
```

---

### data_fetcher

**Module**: `algotrade_datascience.core.data_fetcher`

#### DataFetcher

Main class for fetching multi-timeframe market data.

```python
from algotrade_datascience.core.data_fetcher import DataFetcher

fetcher = DataFetcher()
```

##### Methods

###### `fetch_timeframe(ticker: str, interval: str, period: str) -> pd.DataFrame`

Fetch data for a single timeframe.

**Parameters:**
- `ticker` (str): Ticker symbol
- `interval` (str): Time interval ('4h', '1d', '1wk', '1mo', '3mo')
- `period` (str): Lookback period ('14d', '30d', '3mo', '1y', '2y')

**Returns:**
- pd.DataFrame: OHLCV data with columns: Date, Open, High, Low, Close, Volume

**Raises:**
- `ValueError`: If ticker is invalid or data fetch fails

**Example:**
```python
data = fetcher.fetch_timeframe('AAPL', '1d', '30d')
print(data.head())
#                      Open    High     Low   Close     Volume
# Date                                                         
# 2025-12-23  150.50  152.30  149.80  151.20  50000000
```

---

###### `fetch_all_timeframes(ticker: str) -> Dict[str, pd.DataFrame]`

Fetch all configured timeframes for a ticker.

**Parameters:**
- `ticker` (str): Ticker symbol

**Returns:**
- Dict[str, pd.DataFrame]: Dictionary mapping interval to DataFrame

**Example:**
```python
all_data = fetcher.fetch_all_timeframes('AAPL')
# Returns: {'4h': DataFrame, '1d': DataFrame, '1wk': DataFrame, ...}

daily_data = all_data['1d']
```

---

### data_storage

**Module**: `algotrade_datascience.core.data_storage`

#### DataStorage

Main class for storing data and managing metadata.

```python
from algotrade_datascience.core.data_storage import DataStorage

storage = DataStorage()
```

##### Methods

###### `save_csv(ticker: str, interval: str, data: pd.DataFrame) -> str`

Save DataFrame to CSV file.

**Parameters:**
- `ticker` (str): Ticker symbol
- `interval` (str): Time interval
- `data` (pd.DataFrame): OHLCV data to save

**Returns:**
- str: Path to saved file

**Example:**
```python
file_path = storage.save_csv('AAPL', '1d', data)
# Returns: 'data/raw/AAPL/AAPL_1d_20260122.csv'
```

---

###### `update_metadata(ticker: str, interval: str, info: Dict) -> None`

Update metadata tracking file.

**Parameters:**
- `ticker` (str): Ticker symbol
- `interval` (str): Time interval
- `info` (Dict): Metadata information

**Example:**
```python
storage.update_metadata('AAPL', '1d', {
    'row_count': 30,
    'date_range': '2025-12-23 to 2026-01-22'
})
```

---

###### `load_csv(ticker: str, interval: str) -> pd.DataFrame`

Load CSV file for a ticker and interval.

**Parameters:**
- `ticker` (str): Ticker symbol
- `interval` (str): Time interval

**Returns:**
- pd.DataFrame: Loaded OHLCV data

**Raises:**
- `FileNotFoundError`: If file doesn't exist

**Example:**
```python
data = storage.load_csv('AAPL', '1d')
```

---

## Utilities

### data_quality_checker

**Module**: `algotrade_datascience.data_quality_checker`

#### DataQualityChecker

Validate data quality for all stored datasets.

```python
from algotrade_datascience.data_quality_checker import DataQualityChecker

checker = DataQualityChecker()
```

##### Methods

###### `check_all_files() -> Dict`

Check quality of all CSV files in data/raw/.

**Returns:**
- Dict: Quality report with detailed results

**Example:**
```python
report = checker.check_all_files()
print(f"Files checked: {report['files_checked']}")
print(f"Passed: {report['passed']}")
print(f"Failed: {report['failed']}")
```

---

###### `check_file(file_path: str) -> Dict`

Check quality of a single CSV file.

**Parameters:**
- `file_path` (str): Path to CSV file

**Returns:**
- Dict: Quality check results

**Example:**
```python
result = checker.check_file('data/raw/AAPL/AAPL_1d_20260122.csv')
if result['passed']:
    print("Quality check passed!")
else:
    print(f"Issues: {result['issues']}")
```

---

## Configuration

### config.py

**Module**: `algotrade_datascience.config`

#### Constants

##### `TIMEFRAMES`

Dictionary defining all timeframe configurations.

```python
TIMEFRAMES = {
    '4h': {
        'period': '14d',
        'min_rows': 20,
        'description': '4-hour interval, last 2 weeks'
    },
    '1d': {
        'period': '30d',
        'min_rows': 20,
        'description': '1-day interval, last 30 days'
    },
    '1wk': {
        'period': '3mo',
        'min_rows': 10,
        'description': '1-week interval, last 3 months'
    },
    '1mo': {
        'period': '1y',
        'min_rows': 10,
        'description': '1-month interval, last 12 months'
    },
    '3mo': {
        'period': '2y',
        'min_rows': 6,
        'description': '3-month interval, last 24 months'
    }
}
```

---

##### `QUALITY_THRESHOLDS`

Quality validation thresholds.

```python
QUALITY_THRESHOLDS = {
    'max_missing_pct': 10.0,      # Maximum % of missing data allowed
    'max_date_gap_days': 7,        # Maximum gap in days between dates
    'min_volume': 0                # Minimum volume (0 = any positive)
}
```

---

##### `DATA_DIR`

Base directory for data storage.

```python
DATA_DIR = 'data'
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'
MODELS_DIR = 'data/models'
```

---

## Data Schemas

### CSV File Schema

All CSV files follow this standardized schema:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `Date` | datetime | Timestamp (timezone-aware) | `2026-01-22 09:30:00` |
| `Open` | float | Opening price | `150.50` |
| `High` | float | Highest price in period | `152.30` |
| `Low` | float | Lowest price in period | `149.80` |
| `Close` | float | Closing price | `151.20` |
| `Volume` | int | Trading volume | `50000000` |

**Example CSV:**
```csv
Date,Open,High,Low,Close,Volume
2026-01-22 09:30:00,150.50,152.30,149.80,151.20,50000000
2026-01-23 09:30:00,151.20,153.10,150.50,152.80,45000000
```

---

### Metadata Schema

**File**: `data/metadata.json`

```json
{
  "last_updated": "2026-01-22T17:00:00",
  "total_tickers": 2,
  "total_files": 10,
  "fetches": [
    {
      "ticker": "AAPL",
      "interval": "1d",
      "period": "30d",
      "fetch_date": "2026-01-22",
      "fetch_time": "17:00:00",
      "row_count": 30,
      "date_range": "2025-12-23 to 2026-01-22",
      "file_path": "data/raw/AAPL/AAPL_1d_20260122.csv",
      "file_size_bytes": 2048
    }
  ]
}
```

---

### Quality Report Schema

**File**: `data/quality_report.json`

```json
{
  "check_date": "2026-01-22",
  "check_time": "17:05:00",
  "files_checked": 10,
  "passed": 10,
  "failed": 0,
  "detailed_reports": [
    {
      "ticker": "AAPL",
      "interval": "1d",
      "file_path": "data/raw/AAPL/AAPL_1d_20260122.csv",
      "passed": true,
      "checks": {
        "row_count": {"passed": true, "value": 30, "threshold": 20},
        "missing_data": {"passed": true, "pct": 0.0, "threshold": 10.0},
        "ohlc_logic": {"passed": true, "violations": 0},
        "negative_prices": {"passed": true, "count": 0},
        "volume_present": {"passed": true}
      },
      "issues": []
    }
  ]
}
```

---

## Error Handling

All modules use consistent error handling:

### Common Exceptions

- `ValueError`: Invalid input parameters
- `FileNotFoundError`: Required file not found
- `ConnectionError`: Network/API errors
- `DataValidationError`: Data quality issues

### Example Error Handling

```python
from algotrade_datascience.core.data_fetcher import DataFetcher

fetcher = DataFetcher()

try:
    data = fetcher.fetch_timeframe('INVALID', '1d', '30d')
except ValueError as e:
    print(f"Invalid ticker: {e}")
except ConnectionError as e:
    print(f"Network error: {e}")
```

---

## Logging

All modules use Python's logging module:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log'),
        logging.StreamHandler()
    ]
)
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (non-critical issues)
- `ERROR`: Error messages (failures)
- `CRITICAL`: Critical errors (system failures)

---

## Command-Line Interface

### main_data_pipeline.py

```bash
python main_data_pipeline.py --mode [auto|manual] [options]
```

**Options:**
- `--mode`: Selection mode ('auto' or 'manual')
- `--tickers`: Space-separated ticker list (manual mode)
- `--count`: Number of S&P 500 tickers (auto mode)

**Examples:**
```bash
# Auto mode - top 5 S&P 500
python main_data_pipeline.py --mode auto --count 5

# Manual mode - specific tickers
python main_data_pipeline.py --mode manual --tickers AAPL MSFT GOOGL

# With crypto
python main_data_pipeline.py --mode manual --tickers AAPL BTC-USD ETH-USD
```

---

### test_pipeline.py

Quick test with 2 tickers (AAPL, MSFT):

```bash
python test_pipeline.py
```

No arguments required.

---

### data_quality_checker.py

Validate all stored datasets:

```bash
python data_quality_checker.py
```

Generates `data/quality_report.json`.

---

## Version Information

**Current Version**: 1.0.0 (Phase 1 Complete)

**API Stability**: 
- Core modules (ticker_selector, data_fetcher, data_storage): **Stable**
- Feature modules: **Experimental** (not yet implemented)
- Modeling modules: **Experimental** (not yet implemented)

---

## Support

For API questions or issues:
- Review this documentation
- Check the [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub

---

**Last Updated**: January 2026  
**API Version**: 1.0.0
