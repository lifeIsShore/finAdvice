"""
US-02: Multi-Resolution Market Data Fetching
Fetches historical OHLCV data for multiple intervals and horizons
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf
from config import (
    TIMEFRAME_CONFIG, 
    REQUIRED_COLUMNS,
    YFINANCE_TIMEOUT,
    YFINANCE_RETRY_ATTEMPTS,
    YFINANCE_RETRY_DELAY,
    MIN_ROWS
)

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches multi-resolution OHLCV data for given tickers
    Handles retries, validation, and data quality checks
    """
    
    def __init__(self):
        self.data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.fetch_errors: List[dict] = []
    
    def fetch_ticker_data(self, ticker: str, interval_key: str) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single ticker at a specific interval
        
        Args:
            ticker: Stock symbol
            interval_key: Key from TIMEFRAME_CONFIG ('4h', '1d', '1wk', etc.)
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        config = TIMEFRAME_CONFIG.get(interval_key)
        if not config:
            logger.error(f"Invalid interval key: {interval_key}")
            return None
        
        interval = config['interval']
        period = config['period']
        
        for attempt in range(YFINANCE_RETRY_ATTEMPTS):
            try:
                logger.info(f"Fetching {ticker} - {interval_key} (attempt {attempt + 1}/{YFINANCE_RETRY_ATTEMPTS})")
                
                # Download data from yfinance
                df = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    timeout=YFINANCE_TIMEOUT
                )
                
                if df.empty:
                    logger.warning(f"No data returned for {ticker} at {interval_key}")
                    if attempt < YFINANCE_RETRY_ATTEMPTS - 1:
                        time.sleep(YFINANCE_RETRY_DELAY)
                        continue
                    return None
                
                # Handle multi-level columns from yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                
                # Ensure we have all required columns
                missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
                if missing_cols:
                    logger.error(f"Missing columns for {ticker}: {missing_cols}")
                    return None
                
                # Resample to 4h if needed
                if interval_key == '4h' and interval == '1h':
                    df = self._resample_to_4h(df)
                
                # Resample to 3m if needed (from 1m data)
                if interval_key == '3m' and interval == '1m':
                    df = self._resample_to_3m(df)
                
                # Filter to exact lookback period
                # Handle both lookback_days and lookback_hours
                if 'lookback_hours' in config:
                    lookback_hours = config['lookback_hours']
                    # Handle timezone-aware index from yfinance
                    if df.index.tz is not None:
                        # Index is timezone-aware, use UTC for cutoff_date
                        cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(hours=lookback_hours)
                    else:
                        # Index is naive, use naive datetime
                        cutoff_date = datetime.now() - timedelta(hours=lookback_hours)
                else:
                    lookback_days = config.get('lookback_days', 7)
                    # Handle timezone-aware index from yfinance
                    if df.index.tz is not None:
                        # Index is timezone-aware, use UTC for cutoff_date
                        cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=lookback_days)
                    else:
                        # Index is naive, use naive datetime
                        cutoff_date = datetime.now() - timedelta(days=lookback_days)
                df = df[df.index >= cutoff_date]
                
                # Validate data quality
                if not self._validate_data_quality(df, ticker, interval_key):
                    logger.warning(f"Data quality check failed for {ticker} at {interval_key}")
                    if attempt < YFINANCE_RETRY_ATTEMPTS - 1:
                        time.sleep(YFINANCE_RETRY_DELAY)
                        continue
                
                # Reset index to make datetime a column
                df = df.reset_index()
                df = df.rename(columns={'index': 'Date', 'Datetime': 'Date'})
                
                # Ensure exact timestamp preservation
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Select only required columns in correct order
                df = df[['Date'] + REQUIRED_COLUMNS]
                
                logger.info(f"[OK] Successfully fetched {len(df)} rows for {ticker} at {interval_key}")
                return df
                
            except Exception as e:
                logger.error(f"Error fetching {ticker} at {interval_key}: {str(e)}")
                self.fetch_errors.append({
                    'ticker': ticker,
                    'interval': interval_key,
                    'error': str(e),
                    'attempt': attempt + 1
                })
                
                if attempt < YFINANCE_RETRY_ATTEMPTS - 1:
                    time.sleep(YFINANCE_RETRY_DELAY)
                else:
                    return None
        
        return None
    
    def _resample_to_4h(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample hourly data to 4-hour intervals
        
        Args:
            df: DataFrame with hourly OHLCV data
            
        Returns:
            Resampled DataFrame
        """
        logger.info("Resampling hourly data to 4-hour intervals")
        
        resampled = df.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return resampled
    
    def _resample_to_3m(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample 1-minute data to 3-minute intervals
        
        Args:
            df: DataFrame with 1-minute OHLCV data
            
        Returns:
            Resampled DataFrame
        """
        logger.info("Resampling 1-minute data to 3-minute intervals")
        
        resampled = df.resample('3min').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return resampled
    
    def _validate_data_quality(self, df: pd.DataFrame, ticker: str, interval_key: str) -> bool:
        """
        Validate data quality (minimum rows, no excessive NaNs)
        
        Args:
            df: DataFrame to validate
            ticker: Stock symbol
            interval_key: Timeframe identifier
            
        Returns:
            True if data passes quality checks
        """
        # Check minimum rows
        min_expected = MIN_ROWS.get(interval_key, 10)
        if len(df) < min_expected:
            logger.warning(f"{ticker} {interval_key}: Only {len(df)} rows (expected >= {min_expected})")
            return False
        
        # Check for excessive missing data
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                missing_pct = df[col].isna().sum() / len(df)
                if missing_pct > 0.1:  # More than 10% missing
                    logger.warning(f"{ticker} {interval_key}: {col} has {missing_pct:.1%} missing data")
                    return False
        
        # Check for zero volume (suspicious)
        if 'Volume' in df.columns:
            zero_volume_pct = (df['Volume'] == 0).sum() / len(df)
            if zero_volume_pct > 0.3:  # More than 30% zero volume
                logger.warning(f"{ticker} {interval_key}: {zero_volume_pct:.1%} rows have zero volume")
        
        return True
    
    def fetch_all_timeframes(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all timeframes for a given ticker
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary mapping interval_key to DataFrame
        """
        results = {}
        
        for interval_key in TIMEFRAME_CONFIG.keys():
            df = self.fetch_ticker_data(ticker, interval_key)
            if df is not None:
                results[interval_key] = df
            else:
                logger.error(f"Failed to fetch {ticker} at {interval_key}")
        
        # Cache the results
        self.data_cache[ticker] = results
        
        return results
    
    def fetch_multiple_tickers(self, tickers: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Fetch all timeframes for multiple tickers
        
        Args:
            tickers: List of stock symbols
            
        Returns:
            Nested dictionary: {ticker: {interval: DataFrame}}
        """
        all_data = {}
        
        for ticker in tickers:
            logger.info(f"\n{'='*60}")
            logger.info(f"Fetching all timeframes for {ticker}")
            logger.info(f"{'='*60}")
            
            ticker_data = self.fetch_all_timeframes(ticker)
            all_data[ticker] = ticker_data
            
            # Small delay between tickers to avoid rate limiting
            time.sleep(1)
        
        return all_data
    
    def get_fetch_summary(self) -> dict:
        """
        Get summary of fetch operations
        
        Returns:
            Dictionary with fetch statistics
        """
        total_fetches = 0
        successful_fetches = 0
        
        for ticker_data in self.data_cache.values():
            total_fetches += len(TIMEFRAME_CONFIG)
            successful_fetches += len(ticker_data)
        
        return {
            'total_tickers': len(self.data_cache),
            'total_attempted_fetches': total_fetches,
            'successful_fetches': successful_fetches,
            'failed_fetches': total_fetches - successful_fetches,
            'success_rate': successful_fetches / total_fetches if total_fetches > 0 else 0,
            'errors': self.fetch_errors
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test with a single ticker
    print("=" * 60)
    print("TEST: Fetching AAPL data for all timeframes")
    print("=" * 60)
    
    fetcher = DataFetcher()
    data = fetcher.fetch_all_timeframes('AAPL')
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for interval, df in data.items():
        if df is not None:
            print(f"\n{interval}: {len(df)} rows")
            print(df.head(3))
            print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    print("\n" + "=" * 60)
    print("FETCH SUMMARY:")
    print("=" * 60)
    print(fetcher.get_fetch_summary())
