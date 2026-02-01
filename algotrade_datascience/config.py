"""
Configuration file for AlgoTrade DataScience App
Defines all constants, timeframes, and data fetch parameters
"""

from datetime import datetime, timedelta
from typing import Dict, List

# ============================================================================
# US-01: Asset Universe Configuration
# ============================================================================

# Default tickers (Top 10 S&P 500 + Top 10 Crypto)
DEFAULT_TICKERS = [
    # Top 10 Stocks
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'BRK-B', 'TSLA', 'LLY', 'V',
    # Top 10 Crypto (excluding stablecoins)
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'AVAX-USD', 'DOGE-USD', 'DOT-USD', 'LINK-USD'
]

# Top S&P 500 by market cap (as of Jan 2025) - fallback if API fails
TOP_SP500_TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'BRK-B', 'TSLA', 'LLY', 'V'
]

# Support for crypto
CRYPTO_SUFFIX = '-USD'  # e.g., BTC-USD, ETH-USD


# ============================================================================
# US-02: Multi-Resolution Data Fetch Configuration
# ============================================================================

# Define all timeframes with intervals and lookback periods
# Best practices for data science/ML:
# - Daily data: 1-2 years minimum (for 200-day MA, rolling windows, ML training)
# - Weekly/Monthly: 2-5 years (for long-term patterns, multiple market cycles)
# - Intraday: 1-3 months (for pattern recognition, sufficient sample size)
# - Very short-term: Keep current (for real-time analysis)
TIMEFRAME_CONFIG = {
    '4h': {
        'interval': '1h',  # yfinance doesn't support 4h directly, we'll resample
        'period': '2mo',   # Get 2 months of hourly data, then resample to 4h
        'lookback_days': 60,  # ~2 months for better pattern recognition
        'description': '4-hour interval for last 2 months'
    },
    '1d': {
        'interval': '1d',
        'period': '2y',    # 2 years for comprehensive daily analysis
        'lookback_days': 504,  # ~2 years (504 trading days) - supports 200-day MA, rolling windows
        'description': '1-day interval for last 2 years (504 trading days)'
    },
    '1wk': {
        'interval': '1wk',
        'period': '2y',    # 2 years of weekly data
        'lookback_days': 730,  # ~2 years (104 weeks)
        'description': '1-week interval for last 2 years (104 weeks)'
    },
    '1mo': {
        'interval': '1mo',
        'period': '5y',    # 5 years for comprehensive monthly analysis
        'lookback_days': 1825,  # ~5 years (60 months) - captures multiple market cycles
        'description': '1-month interval for last 5 years (60 months)'
    },
    '3mo': {
        'interval': '3mo',
        'period': '5y',    # 5 years for quarterly analysis
        'lookback_days': 1825,  # ~5 years (20 quarters)
        'description': '3-month interval for last 5 years (20 quarters)'
    },
    '1h': {
        'interval': '1h',
        'period': '2mo',   # 2 months of hourly data
        'lookback_days': 60,  # ~2 months for intraday pattern analysis
        'description': '1-hour interval for last 2 months'
    },
    '30m': {
        'interval': '30m',
        'period': '1mo',   # Stay within Yahoo Finance 60-day limit for intraday
        'lookback_days': 30,
        'description': '30-minute interval for last 30 days'
    },
    '15m': {
        'interval': '15m',
        'period': '1mo',   # Stay within Yahoo Finance 60-day limit for intraday
        'lookback_days': 30,
        'description': '15-minute interval for last 30 days'
    },
    '5m': {
        'interval': '5m',
        'period': '5d',    # 5 days of 5-minute data
        'lookback_days': 5,  # 5 days for short-term intraday analysis
        'description': '5-minute interval for last 5 days'
    },
    '3m': {
        'interval': '1m',  # yfinance doesn't support 3m directly, we'll resample from 1m
        'period': '1d',
        'lookback_hours': 1,
        'description': '3-minute interval for last hour (resampled from 1m)'
    },
    '2m': {
        'interval': '2m',
        'period': '1d',
        'lookback_hours': 1,
        'description': '2-minute interval for last hour'
    },
    '1m': {
        'interval': '1m',
        'period': '1d',
        'lookback_hours': 1,
        'description': '1-minute interval for last hour'
    }
}

# Required OHLCV columns
REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']


# ============================================================================
# US-03: Data Storage Configuration
# ============================================================================

# Directory structure
DATA_DIR = 'data'
RAW_DATA_DIR = f'{DATA_DIR}/raw'
PROCESSED_DATA_DIR = f'{DATA_DIR}/processed'
METADATA_FILE = f'{DATA_DIR}/metadata.json'

# CSV naming convention: {ticker}_{interval}_{date}.csv
CSV_FILENAME_TEMPLATE = '{ticker}_{interval}_{date}.csv'


# ============================================================================
# Data Quality & Validation
# ============================================================================

# Minimum number of rows expected per timeframe
# Adjusted to reflect actual Yahoo Finance data availability
# Note: Yahoo Finance has limitations on historical data for shorter intervals
MIN_ROWS = {
    '4h': 100,   # ~2 months of 4h bars (Yahoo provides ~116 rows for 2 months)
    '1d': 300,   # ~2 years of daily bars (Yahoo provides ~345 rows for 2 years)
    '1wk': 80,   # ~2 years of weekly bars (Yahoo provides ~104 rows)
    '1mo': 50,   # ~5 years of monthly bars (Yahoo provides ~60 rows)
    '3mo': 15,   # ~5 years of quarterly bars (Yahoo provides ~20 rows)
    '1h': 250,   # ~2 months of hourly bars (Yahoo provides ~267 rows for 2 months)
    '30m': 50,   # Limited by Yahoo Finance (provides ~52 rows for recent data)
    '15m': 100,  # Limited by Yahoo Finance (provides ~104 rows for recent data)
    '5m': 150,   # ~5 days of 5m bars (Yahoo provides ~180 rows)
    '3m': 15,    # ~1 hour of 3m bars (Yahoo provides ~20 rows)
    '2m': 20,    # ~1 hour of 2m bars (Yahoo provides ~30 rows)
    '1m': 30     # ~1 hour of 1m bars (Yahoo provides ~60 rows)
}

# Maximum allowed missing data percentage
MAX_MISSING_PCT = 0.1  # 10%

# yfinance configuration
YFINANCE_TIMEOUT = 30  # seconds
YFINANCE_RETRY_ATTEMPTS = 3
YFINANCE_RETRY_DELAY = 2  # seconds


# ============================================================================
# Logging Configuration
# ============================================================================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = 'algotrade_datascience.log'
