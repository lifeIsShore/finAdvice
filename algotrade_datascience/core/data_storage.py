"""
US-03: Raw Data Storage
Handles saving fetched data as CSV files with proper structure and metadata
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import pandas as pd
from config import (
    RAW_DATA_DIR,
    METADATA_FILE,
    CSV_FILENAME_TEMPLATE,
    REQUIRED_COLUMNS
)

logger = logging.getLogger(__name__)


class DataStorage:
    """
    Manages storage of raw OHLCV data to CSV files
    Maintains metadata and ensures data persistence
    """
    
    def __init__(self, base_dir: str = '.'):
        self.base_dir = base_dir
        self.raw_data_path = os.path.join(base_dir, RAW_DATA_DIR)
        self.metadata_path = os.path.join(base_dir, METADATA_FILE)
        self.metadata = self._load_metadata()
        
        # Ensure directories exist
        Path(self.raw_data_path).mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> dict:
        """Load existing metadata or create new"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}. Creating new.")
                return {'fetches': []}
        return {'fetches': []}
    
    def _save_metadata(self):
        """Save metadata to JSON file"""
        try:
            # Ensure parent directory exists
            Path(self.metadata_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
            logger.info(f"Metadata saved to {self.metadata_path}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def save_ticker_data(self, ticker: str, interval: str, df: pd.DataFrame) -> str:
        """
        Save a single DataFrame as CSV
        
        Args:
            ticker: Stock symbol
            interval: Timeframe identifier (e.g., '1d', '1wk')
            df: DataFrame with OHLCV data
            
        Returns:
            Path to saved file
        """
        # Create ticker subdirectory
        ticker_dir = os.path.join(self.raw_data_path, ticker)
        Path(ticker_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with current date
        date_str = datetime.now().strftime('%Y%m%d')
        filename = CSV_FILENAME_TEMPLATE.format(
            ticker=ticker,
            interval=interval,
            date=date_str
        )
        filepath = os.path.join(ticker_dir, filename)
        
        # Validate DataFrame structure
        if not self._validate_dataframe(df, ticker, interval):
            logger.error(f"DataFrame validation failed for {ticker} {interval}")
            return None
        
        try:
            # Save to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"✓ Saved {ticker} {interval} to {filepath} ({len(df)} rows)")
            
            # Update metadata
            self._update_metadata(ticker, interval, filepath, len(df))
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save {ticker} {interval}: {e}")
            return None
    
    def _validate_dataframe(self, df: pd.DataFrame, ticker: str, interval: str) -> bool:
        """
        Validate DataFrame structure before saving
        
        Args:
            df: DataFrame to validate
            ticker: Stock symbol
            interval: Timeframe identifier
            
        Returns:
            True if valid
        """
        # Check if DataFrame is empty
        if df.empty:
            logger.error(f"{ticker} {interval}: DataFrame is empty")
            return False
        
        # Check for required columns
        expected_cols = ['Date'] + REQUIRED_COLUMNS
        missing_cols = set(expected_cols) - set(df.columns)
        if missing_cols:
            logger.error(f"{ticker} {interval}: Missing columns {missing_cols}")
            return False
        
        # Check Date column
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
            logger.error(f"{ticker} {interval}: Date column is not datetime type")
            return False
        
        # Check for NaN in Date
        if df['Date'].isna().any():
            logger.error(f"{ticker} {interval}: Date column contains NaN values")
            return False
        
        return True
    
    def _update_metadata(self, ticker: str, interval: str, filepath: str, row_count: int):
        """Update metadata with information about saved file"""
        fetch_info = {
            'ticker': ticker,
            'interval': interval,
            'filepath': filepath,
            'row_count': row_count,
            'timestamp': datetime.now().isoformat(),
            'date_range': {
                'start': None,
                'end': None
            }
        }
        
        # Try to read the saved file to get date range
        try:
            df = pd.read_csv(filepath)
            fetch_info['date_range']['start'] = str(df['Date'].min())
            fetch_info['date_range']['end'] = str(df['Date'].max())
        except:
            pass
        
        self.metadata['fetches'].append(fetch_info)
        self._save_metadata()
    
    def save_all_ticker_data(self, ticker: str, data_dict: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Save all timeframes for a ticker
        
        Args:
            ticker: Stock symbol
            data_dict: Dictionary mapping interval to DataFrame
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        
        for interval, df in data_dict.items():
            if df is not None and not df.empty:
                filepath = self.save_ticker_data(ticker, interval, df)
                if filepath:
                    saved_files.append(filepath)
        
        return saved_files
    
    def save_multiple_tickers(self, all_data: Dict[str, Dict[str, pd.DataFrame]]) -> dict:
        """
        Save data for multiple tickers
        
        Args:
            all_data: Nested dict {ticker: {interval: DataFrame}}
            
        Returns:
            Summary of save operations
        """
        total_files = 0
        successful_saves = 0
        all_saved_files = {}
        
        for ticker, ticker_data in all_data.items():
            logger.info(f"\nSaving all timeframes for {ticker}")
            saved_files = self.save_all_ticker_data(ticker, ticker_data)
            all_saved_files[ticker] = saved_files
            
            total_files += len(ticker_data)
            successful_saves += len(saved_files)
        
        summary = {
            'total_tickers': len(all_data),
            'total_files_attempted': total_files,
            'successful_saves': successful_saves,
            'failed_saves': total_files - successful_saves,
            'success_rate': successful_saves / total_files if total_files > 0 else 0,
            'saved_files': all_saved_files
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SAVE SUMMARY:")
        logger.info(f"Saved {successful_saves}/{total_files} files")
        logger.info(f"Success rate: {summary['success_rate']:.1%}")
        logger.info(f"{'='*60}")
        
        return summary
    
    def load_ticker_data(self, ticker: str, interval: str) -> pd.DataFrame:
        """
        Load a specific ticker/interval from CSV
        
        Args:
            ticker: Stock symbol
            interval: Timeframe identifier
            
        Returns:
            DataFrame or None if not found
        """
        # Find most recent file for this ticker/interval
        ticker_dir = os.path.join(self.raw_data_path, ticker)
        
        if not os.path.exists(ticker_dir):
            logger.error(f"No data directory found for {ticker}")
            return None
        
        # Look for files matching pattern
        pattern = f"{ticker}_{interval}_*.csv"
        import glob
        files = glob.glob(os.path.join(ticker_dir, pattern))
        
        if not files:
            logger.error(f"No files found for {ticker} {interval}")
            return None
        
        # Get most recent file
        latest_file = max(files, key=os.path.getctime)
        
        try:
            df = pd.read_csv(latest_file, parse_dates=['Date'])
            logger.info(f"Loaded {ticker} {interval} from {latest_file} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Failed to load {latest_file}: {e}")
            return None
    
    def get_storage_summary(self) -> dict:
        """
        Get summary of all stored data
        
        Returns:
            Dictionary with storage statistics
        """
        tickers = set()
        intervals = set()
        total_rows = 0
        
        for fetch in self.metadata.get('fetches', []):
            tickers.add(fetch['ticker'])
            intervals.add(fetch['interval'])
            total_rows += fetch.get('row_count', 0)
        
        return {
            'total_tickers': len(tickers),
            'total_intervals': len(intervals),
            'total_files': len(self.metadata.get('fetches', [])),
            'total_rows': total_rows,
            'tickers': sorted(list(tickers)),
            'intervals': sorted(list(intervals)),
            'metadata_path': self.metadata_path,
            'raw_data_path': self.raw_data_path
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
        'Open': [100 + i for i in range(30)],
        'High': [105 + i for i in range(30)],
        'Low': [95 + i for i in range(30)],
        'Close': [102 + i for i in range(30)],
        'Volume': [1000000 + i * 10000 for i in range(30)]
    })
    
    # Test storage
    storage = DataStorage()
    filepath = storage.save_ticker_data('TEST', '1d', sample_data)
    print(f"\nSaved test data to: {filepath}")
    
    # Load it back
    loaded = storage.load_ticker_data('TEST', '1d')
    print(f"\nLoaded {len(loaded)} rows")
    print(loaded.head())
    
    # Show summary
    print("\n" + "=" * 60)
    print("STORAGE SUMMARY:")
    print("=" * 60)
    summary = storage.get_storage_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
