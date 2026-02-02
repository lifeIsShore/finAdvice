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
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtest.backtest_engine import BacktestEngine

class BacktestUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FinAdvice ML | Backtest Pro")
        self.root.geometry("1000x800")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        
        # Main Container
        self.main_frame = ttk.Frame(self.root, padding="25")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Institutional Backtesting Suite", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="v2.0 (Full Strategy Sync)", font=("Segoe UI", 9, "italic")).pack(side=tk.LEFT, padx=15, pady=(8, 0))
        
        # Content Layout: Settings Left, Metrics Right
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_col = ttk.Frame(content_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_col = ttk.Frame(content_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # --- Settings Panel ---
        settings_frame = ttk.LabelFrame(left_col, text=" Strategy Configuration ", padding="15")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Grid layout for inputs
        grid = ttk.Frame(settings_frame)
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        # Row 0: Ticker & Interval
        ttk.Label(grid, text="Ticker:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.ticker_var = tk.StringVar(value="BTC-USD")
        ttk.Entry(grid, textvariable=self.ticker_var).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(grid, text="Interval:").grid(row=0, column=2, sticky="w", pady=5, padx=5)
        self.interval_var = tk.StringVar(value="1d")
        ttk.Combobox(grid, textvariable=self.interval_var, values=["1h", "4h", "1d", "1wk"]).grid(row=0, column=3, sticky="ew", pady=5, padx=5)
        
        # Row 1: Start Date & Capital
        ttk.Label(grid, text="Start Date:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.start_date_var = tk.StringVar(value="2024-01-01")
        ttk.Entry(grid, textvariable=self.start_date_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(grid, text="Initial Capital:").grid(row=1, column=2, sticky="w", pady=5, padx=5)
        self.capital_var = tk.DoubleVar(value=10000.0)
        ttk.Entry(grid, textvariable=self.capital_var).grid(row=1, column=3, sticky="ew", pady=5, padx=5)
        
        # Row 2: Buy & Sell Thresholds
        ttk.Label(grid, text="Buy Thresh (%):").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.buy_thresh_var = tk.DoubleVar(value=50.0)
        ttk.Entry(grid, textvariable=self.buy_thresh_var).grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(grid, text="Sell Thresh (%):").grid(row=2, column=2, sticky="w", pady=5, padx=5)
        self.sell_thresh_var = tk.DoubleVar(value=0.0)
        ttk.Entry(grid, textvariable=self.sell_thresh_var).grid(row=2, column=3, sticky="ew", pady=5, padx=5)

        # Row 3: Fees & Options
        ttk.Label(grid, text="Fee (%):").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.fee_var = tk.DoubleVar(value=0.1)
        ttk.Entry(grid, textvariable=self.fee_var).grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        # --- Advanced Options ---
        adv_frame = ttk.Frame(settings_frame, padding=(0, 15))
        adv_frame.pack(fill=tk.X)
        
        self.profit_guard_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_frame, text="Profit Guard (Sell only if Price > Entry)", variable=self.profit_guard_var).pack(anchor="w", pady=2)
        
        stop_loss_row = ttk.Frame(adv_frame)
        stop_loss_row.pack(fill=tk.X, pady=2)
        self.sl_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(stop_loss_row, text="Enable Stop Loss (%)", variable=self.sl_enabled_var).pack(side=tk.LEFT)
        self.sl_val_var = tk.DoubleVar(value=5.0)
        ttk.Entry(stop_loss_row, textvariable=self.sl_val_var, width=8).pack(side=tk.LEFT, padx=10)

        # Run Button
        self.run_btn = ttk.Button(settings_frame, text="▶  LAUNCH SIMULATION", style="Action.TButton", command=self.start_backtest_thread)
        self.run_btn.pack(fill=tk.X, pady=(15, 0))
        
        # --- Metrics Dashboard ---
        metrics_frame = ttk.LabelFrame(right_col, text=" Live Stats ", padding="15")
        metrics_frame.pack(fill=tk.Y, expand=True)
        
        self.metrics_labels = {}
        metrics_list = [
            ("Strategy Return", "strat_ret"),
            ("Buy & Hold", "bh_ret"),
            ("Alpha (Edge)", "alpha"),
            ("Max Drawdown", "mdd"),
            ("Trade Count", "trades"),
            ("Account Balance", "final_val")
        ]
        
        for label, key in metrics_list:
            lbl_container = ttk.Frame(metrics_frame)
            lbl_container.pack(fill=tk.X, pady=8)
            ttk.Label(lbl_container, text=label, font=("Segoe UI", 9)).pack(anchor="w")
            self.metrics_labels[key] = ttk.Label(lbl_container, text="--", font=("Segoe UI", 12, "bold"))
            self.metrics_labels[key].pack(anchor="w")
            
        # --- Log Console ---
        log_container = ttk.LabelFrame(self.main_frame, text=" Execution Logs ", padding="10")
        log_container.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_area = scrolledtext.ScrolledText(log_container, height=15, font=("Consolas", 10), background="#1e1e1e", foreground="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        self.log("System Initialized. Using Dashboard ML Models.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def start_backtest_thread(self):
        self.run_btn.config(state=tk.DISABLED)
        # Clear log and metrics
        self.log_area.delete('1.0', tk.END)
        for key in self.metrics_labels:
            self.metrics_labels[key].config(text="--", foreground="black")
            
        self.log("Preparing Engine...")
        
        thread = threading.Thread(target=self.run_backtest, daemon=True)
        thread.start()

    def run_backtest(self):
        try:
            # Inputs
            ticker = self.ticker_var.get()
            start_date = self.start_date_var.get()
            capital = self.capital_var.get()
            interval = self.interval_var.get()
            buy_thresh = self.buy_thresh_var.get()
            sell_thresh = self.sell_thresh_var.get()
            fee = self.fee_var.get() / 100.0
            
            # Logic flags
            profit_guard = self.profit_guard_var.get()
            stop_loss = self.sl_val_var.get() if self.sl_enabled_var.get() else None
            
            # Create engine with log callback
            engine = BacktestEngine(
                ticker=ticker,
                start_date=start_date,
                initial_capital=capital,
                fee_pct=fee,
                log_callback=lambda msg: self.root.after(0, lambda: self.log(msg))
            )
            
            result = engine.run(
                interval=interval, 
                consensus_threshold=buy_thresh, 
                sell_threshold=sell_thresh,
                sell_only_at_profit=profit_guard,
                stop_loss_pct=stop_loss
            )
            
            if result:
                self.root.after(0, lambda: self.update_results(result))
                self.log(f"SUCCESS: Final Balance ${result.final_value:.2f}")
            else:
                self.log("FAILED: No trade data generated.")
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"CRITICAL ERROR: {str(e)}"))
            messagebox.showerror("Execution Error", str(e))
        finally:
            self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))

    def update_results(self, result):
        m = self.metrics_labels
        
        # Dashboard Values
        m['strat_ret'].config(text=f"{result.total_return_pct:+.2f}%")
        m['bh_ret'].config(text=f"{result.buy_and_hold_return_pct:+.2f}%")
        
        alpha = result.total_return_pct - result.buy_and_hold_return_pct
        m['alpha'].config(text=f"{alpha:+.2f}%")
        
        m['mdd'].config(text=f"{result.max_drawdown_pct:.2f}%")
        m['trades'].config(text=f"{result.trade_count}")
        m['final_val'].config(text=f"${result.final_value:,.2f}")
        
        # Color coding for psychology
        success_color = "#27ae60"
        danger_color = "#e74c3c"
        
        m['strat_ret'].config(foreground=success_color if result.total_return_pct > 0 else danger_color)
        m['alpha'].config(foreground=success_color if alpha > 0 else danger_color)

if __name__ == "__main__":
    root = tk.Tk()
    # Handle DPI awareness for sharp text on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = BacktestUI(root)
    root.mainloop()
