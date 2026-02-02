"""
Run Backtest for FinAdvice ML
User entry point for simulating historical strategy performance.
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'algotrade_datascience')))

from backtest.backtest_engine import BacktestEngine

def run_simulation(ticker, start_date, initial_capital, interval, threshold):
    print("\n" + "="*60)
    print(f"FINADVICE BACKTEST: {ticker}")
    print("="*60)
    
    engine = BacktestEngine(
        ticker=ticker,
        start_date=start_date,
        initial_capital=initial_capital
    )
    
    result = engine.run(interval=interval, consensus_threshold=threshold)
    
    if not result:
        print("[ERROR] Backtest produced no results. Check your date range and data availability.")
        return
    
    # Print Summary
    print("\n" + "="*60)
    print("BACKTEST RESULTS SUMMARY")
    print("="*60)
    print(f"Ticker: {ticker}")
    print(f"Period: {result.start_date.date()} to {result.end_date.date()}")
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Value:     ${result.final_value:,.2f}")
    print("-" * 30)
    print(f"Strategy Return:     {result.total_return_pct:+.2f}%")
    print(f"Buy & Hold Return:   {result.buy_and_hold_return_pct:+.2f}%")
    print(f"Alpha (vs B&H):      {result.total_return_pct - result.buy_and_hold_return_pct:+.2f}%")
    print(f"Max Drawdown:        {result.max_drawdown_pct:.2f}%")
    print(f"Total Trades:        {result.trade_count}")
    print("="*60)
    
    # Save results to file
    output_dir = os.path.join('data', 'backtests')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{ticker}_{result.start_date.strftime('%Y%p%d')}_{interval}_results.json"
    filepath = os.path.join(output_dir, filename)
    
    # Prepare serializable dict
    report = {
        'summary': {
            'ticker': result.ticker,
            'start_date': str(result.start_date),
            'end_date': str(result.end_date),
            'initial_capital': result.initial_capital,
            'final_value': result.final_value,
            'total_return': result.total_return_pct,
            'bh_return': result.buy_and_hold_return_pct,
            'max_drawdown': result.max_drawdown_pct,
            'trade_count': result.trade_count
        },
        'trades': [t.__dict__ for t in result.trades]
    }
    
    # Convert dates in trades to string
    for t in report['trades']:
        t['date'] = str(t['date'])
        
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"\n[OK] Detailed report saved to {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run FinAdvice ML Backtest')
    parser.add_argument('--ticker', type=str, default='BTC-USD', help='Ticker symbol')
    parser.add_argument('--start', type=str, default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=10000.0, help='Initial capital in USD')
    parser.add_argument('--interval', type=str, default='1d', help='Data interval (1d, 1wk, 4h, etc.)')
    parser.add_argument('--threshold', type=float, default=50.0, help='Consensus accuracy threshold (0-100)')
    
    args = parser.parse_args()
    
    run_simulation(args.ticker, args.start, args.capital, args.interval, args.threshold)
