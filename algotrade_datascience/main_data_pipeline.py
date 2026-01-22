"""
Main Pipeline for Phase 1: Dataset Creation
Implements US-01, US-02, US-03

This script orchestrates:
1. Ticker selection (manual or auto)
2. Multi-timeframe data fetching
3. CSV storage with metadata

Usage:
    python main_data_pipeline.py --mode manual --tickers AAPL TSLA MSFT
    python main_data_pipeline.py --mode auto --count 5
"""

import logging
import argparse
import sys
from datetime import datetime
from core.ticker_selector import TickerSelector
from core.data_fetcher import DataFetcher
from core.data_storage import DataStorage
from config import TIMEFRAME_CONFIG


def setup_logging():
    """Configure logging for the pipeline"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data_pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_pipeline(mode: str = 'auto', tickers: list = None, count: int = 10):
    """
    Run the complete data ingestion pipeline
    
    Args:
        mode: 'manual' or 'auto'
        tickers: List of tickers (for manual mode)
        count: Number of top S&P 500 stocks (for auto mode)
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("ALGOTRADE DATA SCIENCE - PHASE 1: DATASET CREATION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # ========================================================================
    # STEP 1: Ticker Selection (US-01)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 1: TICKER SELECTION (US-01)")
    print("="*80)
    
    selector = TickerSelector()
    
    if mode == 'manual':
        if not tickers:
            raise ValueError("Manual mode requires ticker list")
        print(f"Mode: Manual ticker selection")
        print(f"Input tickers: {tickers}")
        selector.set_manual_tickers(tickers)
    else:
        print(f"Mode: Automatic top {count} S&P 500 selection")
        selector.set_top_sp500(count)
    
    print("\nValidating tickers...")
    selector.validate_tickers()
    
    validation_report = selector.get_validation_report()
    print("\n--- Validation Report ---")
    print(f"Total tickers: {validation_report['total_tickers']}")
    print(f"Valid tickers: {validation_report['valid_tickers']}")
    print(f"Invalid tickers: {validation_report['invalid_tickers']}")
    print(f"Success rate: {validation_report['success_rate']:.1%}")
    
    if validation_report['invalid_list']:
        print(f"❌ Invalid: {validation_report['invalid_list']}")
    
    print(f"✓ Proceeding with: {validation_report['validated_list']}")
    
    validated_tickers = selector.get_validated_tickers()
    
    if not validated_tickers:
        print("\n❌ ERROR: No valid tickers to process")
        return
    
    # ========================================================================
    # STEP 2: Data Fetching (US-02)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 2: MULTI-TIMEFRAME DATA FETCHING (US-02)")
    print("="*80)
    timeframe_list = ', '.join(TIMEFRAME_CONFIG.keys())
    print(f"Fetching {len(TIMEFRAME_CONFIG)} timeframes: {timeframe_list}")
    print(f"Processing {len(validated_tickers)} tickers...")
    
    fetcher = DataFetcher()
    all_data = fetcher.fetch_multiple_tickers(validated_tickers)
    
    fetch_summary = fetcher.get_fetch_summary()
    print("\n--- Fetch Summary ---")
    print(f"Total tickers: {fetch_summary['total_tickers']}")
    print(f"Successful fetches: {fetch_summary['successful_fetches']}/{fetch_summary['total_attempted_fetches']}")
    print(f"Failed fetches: {fetch_summary['failed_fetches']}")
    print(f"Success rate: {fetch_summary['success_rate']:.1%}")
    
    if fetch_summary['errors']:
        print(f"\n⚠️ Errors encountered: {len(fetch_summary['errors'])}")
        for error in fetch_summary['errors'][:5]:  # Show first 5 errors
            print(f"  - {error['ticker']} {error['interval']}: {error['error']}")
    
    # ========================================================================
    # STEP 3: Data Storage (US-03)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 3: CSV STORAGE & METADATA (US-03)")
    print("="*80)
    print("Saving datasets to data/raw/ directory...")
    
    storage = DataStorage()
    save_summary = storage.save_multiple_tickers(all_data)
    
    print("\n--- Save Summary ---")
    print(f"Total files saved: {save_summary['successful_saves']}/{save_summary['total_files_attempted']}")
    print(f"Success rate: {save_summary['success_rate']:.1%}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("PIPELINE COMPLETE - FINAL SUMMARY")
    print("="*80)
    
    storage_summary = storage.get_storage_summary()
    print(f"\n📊 Dataset Summary:")
    print(f"  - Tickers stored: {storage_summary['total_tickers']}")
    print(f"  - Total files: {storage_summary['total_files']}")
    print(f"  - Total data rows: {storage_summary['total_rows']:,}")
    print(f"  - Storage location: {storage_summary['raw_data_path']}")
    print(f"  - Metadata file: {storage_summary['metadata_path']}")
    
    print(f"\n✅ Phase 1 Complete!")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Return summary for programmatic use
    return {
        'validation': validation_report,
        'fetch': fetch_summary,
        'storage': save_summary,
        'final': storage_summary
    }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='AlgoTrade DataScience - Phase 1: Dataset Creation'
    )
    
    parser.add_argument(
        '--mode',
        choices=['manual', 'auto'],
        default='auto',
        help='Ticker selection mode (default: auto)'
    )
    
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='List of tickers for manual mode (e.g., AAPL TSLA MSFT)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='Number of top S&P 500 stocks for auto mode (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Run pipeline
    try:
        run_pipeline(
            mode=args.mode,
            tickers=args.tickers,
            count=args.count
        )
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
