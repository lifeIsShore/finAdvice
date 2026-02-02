"""
Backtesting Engine for FinAdvice ML Models
Simulates real-world trading by walking forward through historical data.
Zero data leakage ensures reliable results.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add parent directory to path to import other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_storage import DataStorage
from consensus_engine import MultiTimeframeConsensus, Sentiment

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    type: str  # 'BUY' or 'SELL'
    date: datetime
    price: float
    amount: float
    value: float
    fee: float
    consensus: float

@dataclass
class BacktestResult:
    ticker: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return_pct: float
    buy_and_hold_return_pct: float
    max_drawdown_pct: float
    trade_count: int
    trades: List[Trade]
    equity_curve: pd.DataFrame

class BacktestEngine:
    """
    Simulates trading strategy using walk-forward validation
    """
    
    def __init__(self, 
                 ticker: str, 
                 start_date: str, 
                 end_date: Optional[str] = None,
                 initial_capital: float = 10000.0,
                 fee_pct: float = 0.001):  # 0.1% fee
        self.ticker = ticker
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date) if end_date else datetime.now()
        self.initial_capital = initial_capital
        self.fee_pct = fee_pct
        
        self.storage = DataStorage(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        self.portfolio = {
            'cash': initial_capital,
            'position': 0.0,  # Number of units held
            'equity': initial_capital
        }
        self.trades = []
        self.equity_history = []
        
    def run(self, interval: str = '1d', consensus_threshold: float = 50.0, sell_threshold: float = 0.0) -> BacktestResult:
        """
        Run the simulation
        """
        print(f"\n[BACKTEST] Starting simulation for {self.ticker}...")
        print(f"  Range: {self.start_date.date()} to {self.end_date.date()}")
        print(f"  Interval: {interval}, Buy Threshold: {consensus_threshold}%, Sell Threshold: {sell_threshold}%")
        
        # Load full historical data for the ticker interval
        full_df = self.storage.load_ticker_data(self.ticker, interval)
        if full_df is None:
            raise ValueError(f"No data found for {self.ticker} {interval}")
            
        # Ensure Date column is datetime
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df = full_df.sort_values('Date')
        
        # Filter for the backtest range (but we need some history before start_date for training)
        backtest_dates = full_df[(full_df['Date'] >= self.start_date) & 
                                 (full_df['Date'] <= self.end_date)]['Date'].unique()
        
        if len(backtest_dates) == 0:
            raise ValueError(f"No data points in backtest range {self.start_date} to {self.end_date}")

        # Main Simulation Loop
        for sim_date in backtest_dates:
            sim_date = pd.to_datetime(sim_date)
            
            # 1. Truncate data to simulate "today" (No Leakage)
            # We only show the model data that existed before sim_date
            current_df = full_df[full_df['Date'] < sim_date]
            
            if len(current_df) < 50: # Need enough data to train
                continue
                
            # Current price (at the open of sim_date or close of previous date)
            # We use the 'Close' of the latest available row as our execution price
            price_row = full_df[full_df['Date'] == sim_date].iloc[0]
            current_price = price_row['Open'] # We buy at open of the day we make the decision
            
            # 2. Run Consensus Engine
            # Note: For efficiency in backtest, we might want a lightweight consensus
            # but for accuracy, we use the real one.
            consensus_val, confidence = self._get_simulated_consensus(sim_date, full_df)
            
            # 3. Apply Trading Signal (Long Only)
            if consensus_val >= consensus_threshold:
                # BUY Signal
                if self.portfolio['cash'] > 10: # Only buy if we have cash
                    self._execute_trade('BUY', sim_date, current_price, consensus_val)
            elif consensus_val <= sell_threshold: # SELL Signal
                # SELL Signal
                if self.portfolio['position'] > 0:
                    self._execute_trade('SELL', sim_date, current_price, consensus_val)
            
            # Record Equity Tracker
            total_value = self.portfolio['cash'] + (self.portfolio['position'] * price_row['Close'])
            self.equity_history.append({
                'Date': sim_date,
                'Cash': self.portfolio['cash'],
                'Position': self.portfolio['position'],
                'Price': price_row['Close'],
                'Total_Value': total_value,
                'Consensus': consensus_val
            })
            
            # Print progress every 10 steps
            if len(self.equity_history) % 10 == 0:
                print(f"  {sim_date.date()} | Equity: {total_value:.2f} | Consensus: {consensus_val:.1f}%")

        return self._finalize_results(full_df)

    def _get_simulated_consensus(self, sim_date: datetime, full_df: pd.DataFrame) -> tuple:
        """
        Calculates consensus for a specific historical point in time.
        In a real backtest, we should call MultiTimeframeConsensus, 
        but we must mock the DataStorage to only return data UP TO sim_date.
        """
        # Temporal Storage Mock
        class MockStorage:
            def __init__(self, full_df, sim_date):
                self.full_df = full_df
                self.sim_date = sim_date
            def load_ticker_data(self, ticker, interval):
                # We assume the user has multiple intervals? 
                # For this simple backtest, we only use the primary interval data
                return self.full_df[self.full_df['Date'] < self.sim_date]

        # Use the actual engine
        mock_storage = MockStorage(full_df, sim_date)
        engine = MultiTimeframeConsensus(mock_storage, self.ticker)
        
        # We only generate consensus for the primary interval to save time in backtest
        # Real world would check 1h, 4h, 1d... but we don't have all data synced for old dates easily
        # So we adapt: We run models on the truncated single-interval data
        prediction = engine.predict_interval(mock_storage.load_ticker_data(self.ticker, None), 'backtest_interval')
        
        if prediction:
            return prediction.confidence if prediction.change_percent > 0 else -prediction.confidence, prediction.confidence
        return 0, 0

    def _execute_trade(self, side: str, date: datetime, price: float, consensus: float):
        if side == 'BUY':
            # Buy with all available cash
            fee = self.portfolio['cash'] * self.fee_pct
            net_cash = self.portfolio['cash'] - fee
            amount = net_cash / price
            value = net_cash
            
            self.portfolio['position'] += amount
            self.portfolio['cash'] = 0.0
            
            trade = Trade('BUY', date, price, amount, value, fee, consensus)
            self.trades.append(trade)
            print(f"  >>> BUY at {price:.2f} (Consensus: {consensus:.1f}%)")
            
        elif side == 'SELL':
            # Sell all positions
            value = self.portfolio['position'] * price
            fee = value * self.fee_pct
            net_value = value - fee
            
            amount = self.portfolio['position']
            self.portfolio['cash'] += net_value
            self.portfolio['position'] = 0.0
            
            trade = Trade('SELL', date, price, amount, net_value, fee, consensus)
            self.trades.append(trade)
            print(f"  <<< SELL at {price:.2f} (Consensus: {consensus:.1f}%)")

    def _finalize_results(self, full_df: pd.DataFrame) -> BacktestResult:
        equity_df = pd.DataFrame(self.equity_history)
        
        if equity_df.empty:
            return None
            
        final_value = equity_df.iloc[-1]['Total_Value']
        total_return = ((final_value / self.initial_capital) - 1) * 100
        
        # Buy and Hold return
        start_price = equity_df.iloc[0]['Price']
        end_price = equity_df.iloc[-1]['Price']
        bh_return = ((end_price / start_price) - 1) * 100
        
        # Max Drawdown
        equity_df['Peak'] = equity_df['Total_Value'].cummax()
        equity_df['Drawdown'] = (equity_df['Total_Value'] - equity_df['Peak']) / equity_df['Peak'] * 100
        max_dd = equity_df['Drawdown'].min()
        
        return BacktestResult(
            ticker=self.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return_pct=total_return,
            buy_and_hold_return_pct=bh_return,
            max_drawdown_pct=max_dd,
            trade_count=len(self.trades),
            trades=self.trades,
            equity_curve=equity_df
        )

if __name__ == "__main__":
    # Test execution
    engine = BacktestEngine(ticker='AAPL', start_date='2024-01-01', initial_capital=1000)
    # result = engine.run(interval='1d')
    # print(f"Final Return: {result.total_return_pct:.2f}%")
