"""
FinAdvice ML Backtester - GUI
A professional-grade interface for testing and refining ML strategies.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
import json
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtest.backtest_engine import BacktestEngine

class BacktestUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FinAdvice ML | Backtest Pro")
        self.root.geometry("900x700")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Main Container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Label
        title_label = ttk.Label(self.main_frame, text="Institutional Backtesting Suite", font=("Helvetica", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
        
        # --- Settings Panel ---
        settings_frame = ttk.LabelFrame(self.main_frame, text=" Strategy Configuration ", padding="15")
        settings_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Ticker
        ttk.Label(settings_frame, text="Ticker:").grid(row=0, column=0, sticky="w", pady=5)
        self.ticker_var = tk.StringVar(value="BTC-USD")
        self.ticker_entry = ttk.Entry(settings_frame, textvariable=self.ticker_var, width=15)
        self.ticker_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Start Date
        ttk.Label(settings_frame, text="Start Date:").grid(row=1, column=0, sticky="w", pady=5)
        self.start_date_var = tk.StringVar(value="2024-01-01")
        self.start_date_entry = ttk.Entry(settings_frame, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Capital
        ttk.Label(settings_frame, text="Initial Capital ($):").grid(row=2, column=0, sticky="w", pady=5)
        self.capital_var = tk.DoubleVar(value=10000.0)
        self.capital_entry = ttk.Entry(settings_frame, textvariable=self.capital_var, width=15)
        self.capital_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Interval
        ttk.Label(settings_frame, text="Interval:").grid(row=3, column=0, sticky="w", pady=5)
        self.interval_var = tk.StringVar(value="1d")
        self.interval_menu = ttk.Combobox(settings_frame, textvariable=self.interval_var, values=["1h", "4h", "1d", "1wk"], width=13)
        self.interval_menu.grid(row=3, column=1, sticky="w", pady=5)
        
        # Buy Threshold
        ttk.Label(settings_frame, text="Buy Threshold (%):").grid(row=4, column=0, sticky="w", pady=5)
        self.buy_thresh_var = tk.DoubleVar(value=50.0)
        self.buy_thresh_entry = ttk.Entry(settings_frame, textvariable=self.buy_thresh_var, width=15)
        self.buy_thresh_entry.grid(row=4, column=1, sticky="w", pady=5)
        
        # Sell Threshold
        ttk.Label(settings_frame, text="Sell Threshold (%):").grid(row=5, column=0, sticky="w", pady=5)
        self.sell_thresh_var = tk.DoubleVar(value=0.0)
        self.sell_thresh_entry = ttk.Entry(settings_frame, textvariable=self.sell_thresh_var, width=15)
        self.sell_thresh_entry.grid(row=5, column=1, sticky="w", pady=5)
        
        # Fee %
        ttk.Label(settings_frame, text="Trading Fee (%):").grid(row=6, column=0, sticky="w", pady=5)
        self.fee_var = tk.DoubleVar(value=0.1)
        self.fee_entry = ttk.Entry(settings_frame, textvariable=self.fee_var, width=15)
        self.fee_entry.grid(row=6, column=1, sticky="w", pady=5)
        
        # Run Button
        self.run_btn = ttk.Button(settings_frame, text=" START BACKTEST ", command=self.start_backtest_thread)
        self.run_btn.grid(row=7, column=0, columnspan=2, pady=20, sticky="ew")
        
        # --- Results Panel ---
        results_frame = ttk.LabelFrame(self.main_frame, text=" Performance Metrics ", padding="15")
        results_frame.grid(row=1, column=1, sticky="nsew")
        
        self.metrics_labels = {}
        metrics = [
            ("Strategy Return:", "strat_ret"),
            ("Buy & Hold Return:", "bh_ret"),
            ("Alpha:", "alpha"),
            ("Max Drawdown:", "mdd"),
            ("Total Trades:", "trades"),
            ("Final Value:", "final_val")
        ]
        
        for i, (label, key) in enumerate(metrics):
            ttk.Label(results_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.metrics_labels[key] = ttk.Label(results_frame, text="--", font=("Helvetica", 10, "bold"))
            self.metrics_labels[key].grid(row=i, column=1, sticky="e", pady=2, padx=(20, 0))
            
        # --- Log Console ---
        log_frame = ttk.LabelFrame(self.main_frame, text=" Real-time Execution Log ", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure layout weights
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        self.log("System Ready. Configure strategy and click Start.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def start_backtest_thread(self):
        self.run_btn.config(state=tk.DISABLED)
        self.log("Initializing Backtest Engine...")
        
        # Clear metrics
        for key in self.metrics_labels:
            self.metrics_labels[key].config(text="--", foreground="black")
            
        thread = threading.Thread(target=self.run_backtest, daemon=True)
        thread.start()

    def run_backtest(self):
        try:
            ticker = self.ticker_var.get()
            start_date = self.start_date_var.get()
            capital = self.capital_var.get()
            interval = self.interval_var.get()
            buy_thresh = self.buy_thresh_var.get()
            sell_thresh = self.sell_thresh_var.get()
            fee = self.fee_var.get() / 100.0 # Convert from % to ratio
            
            engine = BacktestEngine(
                ticker=ticker,
                start_date=start_date,
                initial_capital=capital,
                fee_pct=fee
            )
            
            # Redirect stdout to capture engine prints
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            # This is tricky because run() prints a lot. We'll wrap it or just log milestones.
            self.log(f"Starting {ticker} simulation at {interval} interval...")
            
            result = engine.run(
                interval=interval, 
                consensus_threshold=buy_thresh, 
                sell_threshold=sell_thresh
            )
            
            if result:
                self.root.after(0, lambda: self.update_results(result))
                self.log(f"Backtest Completed. Portfolio Value: ${result.final_value:.2f}")
            else:
                self.log("ERROR: No results generated. Check input data.")
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("Backtest Error", str(e))
        finally:
            self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))

    def update_results(self, result):
        m = self.metrics_labels
        
        # Set values
        m['strat_ret'].config(text=f"{result.total_return_pct:+.2f}%")
        m['bh_ret'].config(text=f"{result.buy_and_hold_return_pct:+.2f}%")
        
        alpha = result.total_return_pct - result.buy_and_hold_return_pct
        m['alpha'].config(text=f"{alpha:+.2f}%")
        
        m['mdd'].config(text=f"{result.max_drawdown_pct:.2f}%")
        m['trades'].config(text=f"{result.trade_count}")
        m['final_val'].config(text=f"${result.final_value:,.2f}")
        
        # Color coding
        if result.total_return_pct > 0:
            m['strat_ret'].config(foreground="#27ae60")
        else:
            m['strat_ret'].config(foreground="#c0392b")
            
        if alpha > 0:
            m['alpha'].config(foreground="#27ae60")
        else:
            m['alpha'].config(foreground="#c0392b")

if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestUI(root)
    root.mainloop()
