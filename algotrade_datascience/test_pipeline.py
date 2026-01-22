"""
Quick Test Script
Run this to test the Phase 1 implementation with a small dataset
"""

import logging
import sys
from main_data_pipeline import run_pipeline
from data_quality_checker import DataQualityChecker
from core.data_storage import DataStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("\n" + "="*80)
print("QUICK TEST: Phase 1 Dataset Creation")
print("="*80)
print("\nThis will fetch data for 2 tickers (AAPL, MSFT) across 5 timeframes.")
print("Estimated time: 2-3 minutes\n")

try:
    # Run pipeline with 2 tickers
    print("Starting pipeline...")
    result = run_pipeline(
        mode='manual',
        tickers=['AAPL', 'MSFT'],
        count=None
    )
    
    # Run quality check
    print("\n" + "="*80)
    print("Running quality checks...")
    print("="*80)
    
    storage = DataStorage()
    checker = DataQualityChecker(storage)
    quality_report = checker.check_all_files()
    checker.save_quality_report()
    
    # Final summary
    print("\n" + "="*80)
    print("TEST COMPLETE!")
    print("="*80)
    
    if quality_report['failed'] == 0:
        print("\n✅ SUCCESS! All datasets passed quality checks.")
        print("\nYou can now:")
        print("1. Check data/raw/ folder for CSV files")
        print("2. Review data/metadata.json for details")
        print("3. Read data/quality_report.json for metrics")
    else:
        print(f"\n⚠️ WARNING: {quality_report['failed']} files failed quality checks")
        print("Review data/quality_report.json for details")
    
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
