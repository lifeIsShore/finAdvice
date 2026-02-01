"""
Data Quality Checker
Validates the quality of fetched datasets
"""

import logging
import pandas as pd
from typing import Dict, List
from pathlib import Path
import json
from core.data_storage import DataStorage
from config import REQUIRED_COLUMNS, MIN_ROWS, MAX_MISSING_PCT

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Performs comprehensive quality checks on stored datasets
    """
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or DataStorage()
        self.quality_report = {
            'tickers_checked': 0,
            'files_checked': 0,
            'passed': 0,
            'failed': 0,
            'issues': []
        }
    
    def check_file(self, ticker: str, interval: str) -> dict:
        """
        Check quality of a single file
        
        Returns:
            Dictionary with quality metrics
        """
        report = {
            'ticker': ticker,
            'interval': interval,
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Load data
        df = self.storage.load_ticker_data(ticker, interval)
        
        if df is None:
            report['passed'] = False
            report['issues'].append('File not found or could not be loaded')
            return report
        
        # Check 1: Row count
        min_expected = MIN_ROWS.get(interval, 10)
        report['metrics']['row_count'] = len(df)
        report['metrics']['min_expected_rows'] = min_expected
        
        if len(df) < min_expected:
            report['passed'] = False
            report['issues'].append(
                f"Insufficient rows: {len(df)} < {min_expected} expected"
            )
        
        # Check 2: Required columns
        missing_cols = set(['Date'] + REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            report['passed'] = False
            report['issues'].append(f"Missing columns: {missing_cols}")
        
        # Check 3: Missing data percentage
        missing_data = {}
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                missing_pct = df[col].isna().sum() / len(df)
                missing_data[col] = missing_pct
                
                if missing_pct > MAX_MISSING_PCT:
                    report['passed'] = False
                    report['issues'].append(
                        f"{col} has {missing_pct:.1%} missing data (max allowed: {MAX_MISSING_PCT:.1%})"
                    )
        
        report['metrics']['missing_data'] = missing_data
        
        # Check 4: Date continuity
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            date_gaps = df['Date'].diff()
            
            # For daily data, check for large gaps
            if interval == '1d':
                large_gaps = date_gaps[date_gaps > pd.Timedelta(days=7)]
                if len(large_gaps) > 0:
                    report['issues'].append(
                        f"Found {len(large_gaps)} gaps >7 days in daily data"
                    )
            
            report['metrics']['date_range'] = {
                'start': str(df['Date'].min()),
                'end': str(df['Date'].max()),
                'span_days': (df['Date'].max() - df['Date'].min()).days
            }
        
        # Check 5: Data anomalies
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                # Check for zeros
                zero_count = (df[col] == 0).sum()
                if zero_count > 0:
                    report['issues'].append(f"{col} has {zero_count} zero values")
                
                # Check for negative values
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    report['passed'] = False
                    report['issues'].append(f"{col} has {neg_count} negative values")
        
        # Check 6: OHLC logic
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            # High should be >= all others
            high_violations = (
                (df['High'] < df['Open']) |
                (df['High'] < df['Low']) |
                (df['High'] < df['Close'])
            ).sum()
            
            # Low should be <= all others
            low_violations = (
                (df['Low'] > df['Open']) |
                (df['Low'] > df['High']) |
                (df['Low'] > df['Close'])
            ).sum()
            
            if high_violations > 0 or low_violations > 0:
                report['issues'].append(
                    f"OHLC logic violations: High({high_violations}), Low({low_violations})"
                )
        
        # Check 7: Volume
        if 'Volume' in df.columns:
            zero_volume_pct = (df['Volume'] == 0).sum() / len(df)
            report['metrics']['zero_volume_pct'] = zero_volume_pct
            
            if zero_volume_pct > 0.5:  # More than 50% zero volume
                report['issues'].append(
                    f"{zero_volume_pct:.1%} of rows have zero volume"
                )
        
        return report
    
    def check_all_files(self) -> dict:
        """
        Check all stored files
        
        Returns:
            Comprehensive quality report
        """
        storage_summary = self.storage.get_storage_summary()
        
        print("\n" + "="*80)
        print("DATA QUALITY CHECK")
        print("="*80)
        print(f"Checking {storage_summary['total_files']} files...")
        
        detailed_reports = []
        
        # Get all unique ticker/interval combinations from metadata
        for fetch in self.storage.metadata.get('fetches', []):
            ticker = fetch['ticker']
            interval = fetch['interval']
            
            print(f"\nChecking {ticker} - {interval}...")
            report = self.check_file(ticker, interval)
            detailed_reports.append(report)
            
            self.quality_report['files_checked'] += 1
            
            if report['passed']:
                self.quality_report['passed'] += 1
                print(f"  [OK] PASSED")
            else:
                self.quality_report['failed'] += 1
                print(f"  [FAIL] FAILED")
                for issue in report['issues']:
                    print(f"    - {issue}")
        
        self.quality_report['detailed_reports'] = detailed_reports
        self.quality_report['tickers_checked'] = len(storage_summary['tickers'])
        
        # Print summary
        print("\n" + "="*80)
        print("QUALITY CHECK SUMMARY")
        print("="*80)
        print(f"Tickers checked: {self.quality_report['tickers_checked']}")
        print(f"Files checked: {self.quality_report['files_checked']}")
        print(f"Passed: {self.quality_report['passed']}")
        print(f"Failed: {self.quality_report['failed']}")
        
        if self.quality_report['failed'] == 0:
            print("\nALL QUALITY CHECKS PASSED!")
        else:
            print(f"\nWARNING: {self.quality_report['failed']} files failed quality checks")
        
        print("="*80 + "\n")
        
        return self.quality_report
    
    def save_quality_report(self, filepath: str = 'data/quality_report.json'):
        """Save quality report to JSON file"""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(self.quality_report, f, indent=2, default=str)
            
            print(f"[OK] Quality report saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save quality report: {e}")


if __name__ == "__main__":
    # Run quality check on all stored data
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    storage = DataStorage()
    checker = DataQualityChecker(storage)
    report = checker.check_all_files()
    checker.save_quality_report()
    
    print("\nDetailed metrics for first file:")
    if report['detailed_reports']:
        first = report['detailed_reports'][0]
        print(f"\nTicker: {first['ticker']} - {first['interval']}")
        print(f"Metrics: {json.dumps(first['metrics'], indent=2)}")
