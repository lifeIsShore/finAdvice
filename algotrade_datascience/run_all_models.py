"""
Run baseline models for multiple tickers including Bitcoin
"""

from baseline_models import BaselineModels
from config import DEFAULT_TICKERS

if __name__ == "__main__":
    print("="*80)
    print("BASELINE ML MODELS - ALL TICKERS")
    print("="*80)
    
    tickers = DEFAULT_TICKERS
    
    for ticker in tickers:
        print(f"\n{'='*80}")
        print(f"Processing {ticker}")
        print(f"{'='*80}")
        
        baseline = BaselineModels(ticker=ticker)
        results = baseline.run_all_intervals()
    
    print(f"\n{'='*80}")
    print("SUCCESS: ALL TICKERS COMPLETE!")
    print(f"{'='*80}")
    print("\nResults saved:")
    for ticker in tickers:
        print(f"  - data/baseline_models_{ticker}.json")
