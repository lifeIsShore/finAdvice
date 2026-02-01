"""
Enhanced Model Visualizations with Candlestick Charts
Shows actual vs predicted prices on candlestick charts
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
from pathlib import Path
from datetime import datetime
from core.data_storage import DataStorage
from sklearn.linear_model import LinearRegression

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class CandlestickVisualizer:
    """
    Create candlestick charts with model predictions
    """
    
    def __init__(self, ticker: str = 'AAPL', results_file: str = None):
        self.ticker = ticker
        self.storage = DataStorage()
        self.output_dir = Path(f'data/visualizations/{ticker}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if results_file:
            with open(results_file, 'r') as f:
                self.results = json.load(f)
        else:
            self.results = None
    
    def create_features_simple(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create simple features for prediction"""
        df = df.copy()
        
        # Lag features
        for i in range(1, 6):
            df[f'close_lag_{i}'] = df['Close'].shift(i)
        
        # Moving averages
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_10'] = df['Close'].rolling(window=10).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        
        # Returns
        df['return_1'] = df['Close'].pct_change(1)
        df['return_5'] = df['Close'].pct_change(5)
        
        # Volatility
        df['volatility_5'] = df['Close'].rolling(window=5).std()
        df['volatility_10'] = df['Close'].rolling(window=10).std()
        
        # Volume features
        df['volume_sma_5'] = df['Volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_5']
        
        # Target
        df['target'] = df['Close'].shift(-1)
        
        return df
    
    def plot_candlestick_with_predictions(self, interval: str, num_candles: int = 50):
        """
        Create candlestick chart with model predictions
        """
        print(f"  Creating candlestick chart for {interval}...")
        
        # Load data
        df = self.storage.load_ticker_data(self.ticker, interval)
        if df is None or len(df) < num_candles:
            print(f"    WARNING: Insufficient data for {interval}")
            return None
        
        # Get last N candles
        df_plot = df.tail(num_candles).copy()
        df_plot.reset_index(drop=True, inplace=True)
        
        # Create features and train quick model
        df_features = self.create_features_simple(df)
        df_features = df_features.dropna()
        
        if len(df_features) < 30:
            print(f"    WARNING: Insufficient feature data for {interval}")
            return None
        
        # Train model
        feature_cols = [col for col in df_features.columns 
                       if col not in ['Date', 'target', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        split_idx = int(len(df_features) * 0.8)
        X_train = df_features[feature_cols][:split_idx]
        y_train = df_features['target'][:split_idx]
        X_test = df_features[feature_cols][split_idx:]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Get predictions for plot period
        df_plot_features = self.create_features_simple(df_plot)
        df_plot_features = df_plot_features.dropna()
        
        if len(df_plot_features) > 0:
            X_plot = df_plot_features[feature_cols]
            predictions = model.predict(X_plot)
            
            # Align predictions with plot data
            pred_indices = df_plot_features.index
            df_plot.loc[pred_indices, 'Predicted'] = predictions
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot candlesticks
        for idx in range(len(df_plot)):
            row = df_plot.iloc[idx]
            
            # Determine color
            if row['Close'] >= row['Open']:
                color = '#26a69a'  # Green
                lower = row['Open']
                height = row['Close'] - row['Open']
            else:
                color = '#ef5350'  # Red
                lower = row['Close']
                height = row['Open'] - row['Close']
            
            # Draw candle body
            ax1.add_patch(Rectangle((idx - 0.3, lower), 0.6, height, 
                                    facecolor=color, edgecolor='black', linewidth=0.5))
            
            # Draw wicks
            ax1.plot([idx, idx], [row['Low'], row['High']], 
                    color='black', linewidth=0.5)
        
        # Plot predictions
        if 'Predicted' in df_plot.columns:
            pred_data = df_plot[df_plot['Predicted'].notna()]
            ax1.plot(pred_data.index, pred_data['Predicted'], 
                    'b--', linewidth=2, label='Predicted Close', alpha=0.7)
            ax1.scatter(pred_data.index, pred_data['Predicted'], 
                       color='blue', s=30, zorder=5, alpha=0.7)
        
        # Plot moving averages
        if len(df_plot) >= 20:
            sma20 = df_plot['Close'].rolling(window=20).mean()
            ax1.plot(df_plot.index, sma20, 'orange', linewidth=1.5, 
                    label='SMA 20', alpha=0.6)
        
        if len(df_plot) >= 10:
            sma10 = df_plot['Close'].rolling(window=10).mean()
            ax1.plot(df_plot.index, sma10, 'purple', linewidth=1.5, 
                    label='SMA 10', alpha=0.6)
        
        ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{self.ticker} - {interval.upper()} Candlestick Chart with Predictions\n'
                     f'Last {num_candles} Periods', 
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(-1, len(df_plot))
        
        # Volume subplot
        colors_vol = ['#26a69a' if df_plot.iloc[i]['Close'] >= df_plot.iloc[i]['Open'] 
                     else '#ef5350' for i in range(len(df_plot))]
        ax2.bar(df_plot.index, df_plot['Volume'], color=colors_vol, alpha=0.6)
        ax2.set_ylabel('Volume', fontsize=10, fontweight='bold')
        ax2.set_xlabel('Period', fontsize=10, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(-1, len(df_plot))
        
        plt.tight_layout()
        
        # Save
        output_file = self.output_dir / f'candlestick_{interval}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    [OK] Saved to {output_file}")
        return output_file
    
    def create_all_candlestick_charts(self, intervals: list = None):
        """Create candlestick charts for all intervals"""
        if intervals is None:
            intervals = ['1d', '1wk', '4h', '1h']
        
        print(f"\n{'='*80}")
        print(f"CREATING CANDLESTICK CHARTS - {self.ticker}")
        print(f"{'='*80}")
        
        created_files = []
        for interval in intervals:
            file = self.plot_candlestick_with_predictions(interval)
            if file:
                created_files.append(file)
        
        print(f"\nSUCCESS: Created {len(created_files)} candlestick charts for {self.ticker}")
        return created_files


def create_multi_ticker_report(tickers: list = ['AAPL', 'BTC-USD']):
    """
    Create candlestick charts for multiple tickers
    """
    print(f"\n{'='*80}")
    print("CREATING CANDLESTICK VISUALIZATIONS FOR MULTIPLE TICKERS")
    print(f"{'='*80}")
    print(f"Tickers: {', '.join(tickers)}")
    
    all_files = {}
    
    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        visualizer = CandlestickVisualizer(ticker=ticker)
        files = visualizer.create_all_candlestick_charts()
        all_files[ticker] = files
    
    print(f"\n{'='*80}")
    print("SUCCESS: ALL CANDLESTICK CHARTS CREATED!")
    print(f"{'='*80}")
    
    for ticker, files in all_files.items():
        print(f"\n{ticker}: {len(files)} charts")
        for file in files:
            print(f"  - {file}")
    
    return all_files


if __name__ == "__main__":
    from config import DEFAULT_TICKERS
    # Create candlestick charts for all tickers in config
    create_multi_ticker_report(tickers=DEFAULT_TICKERS)
