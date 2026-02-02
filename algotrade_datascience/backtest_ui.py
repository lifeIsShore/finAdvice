"""
FinAdvice ML Backtester - GUI Pro
Integrated strategy testing with dynamic position scaling and confidence boosts.
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

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        # Calculate position to avoid covering the widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2d2d2d", foreground="#ffffff", 
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", "9", "normal"), padx=10, pady=5)
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class BacktestUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FinAdvice ML | Backtest Master Pro")
        self.root.geometry("1150x850")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="#2c3e50")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 12, "bold"), foreground="#34495e")
        self.style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        self.style.configure("Cancel.TButton", font=("Segoe UI", 11, "bold"), padding=12, foreground="white", background="#e74c3c")
        
        # State
        self.engine = None
        
        # Main Container
        self.main_frame = ttk.Frame(self.root, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header Section
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        ttk.Label(header_frame, text="Institutional Strategy Lab", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="v3.1 (Async Cancel Support)", font=("Segoe UI", 10, "italic"), foreground="#7f8c8d").pack(side=tk.LEFT, padx=20, pady=(12, 0))
        
        # Main Workspace: 2-Column Layout
        workspace = ttk.Frame(self.main_frame)
        workspace.pack(fill=tk.BOTH, expand=True)
        
        left_col = ttk.Frame(workspace)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        right_col = ttk.Frame(workspace)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        
        # --- 1. CORE CONFIGURATION ---
        core_frame = ttk.LabelFrame(left_col, text=" 1. Market & Timing ", padding="15")
        core_frame.pack(fill=tk.X, pady=(0, 15))
        
        grid = ttk.Frame(core_frame)
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        # Row 0: Ticker & Interval
        ttk.Label(grid, text="Ticker:").grid(row=0, column=0, sticky="w", pady=5)
        self.ticker_var = tk.StringVar(value="BTC-USD")
        e_ticker = ttk.Entry(grid, textvariable=self.ticker_var)
        e_ticker.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 15))
        ToolTip(e_ticker, (
            "SEARCH SYMBOL\n"
            "Tell the bot which asset to analyze.\n\n"
            "Example: 'AAPL' for Apple, 'BTC-USD' for Bitcoin.\n"
            "Tip: We use Yahoo Finance symbols."
        ))
        
        ttk.Label(grid, text="Interval:").grid(row=0, column=2, sticky="w", pady=5)
        self.interval_var = tk.StringVar(value="1d")
        cb_interval = ttk.Combobox(grid, textvariable=self.interval_var, values=["1h", "4h", "1d", "1wk"])
        cb_interval.grid(row=0, column=3, sticky="ew", pady=5, padx=5)
        ToolTip(cb_interval, (
            "REFRESH SPEED\n"
            "How often should the AI check the price?\n\n"
            "1h = Hourly (Fast/Scalping)\n"
            "1d = Daily (Recommended for beginners)\n"
            "1wk = Weekly (Long-term investing)"
        ))
        
        # Row 1: Start Date & Initial Capital
        ttk.Label(grid, text="Start:").grid(row=1, column=0, sticky="w", pady=5)
        self.start_date_var = tk.StringVar(value="2024-01-01")
        e_start = ttk.Entry(grid, textvariable=self.start_date_var)
        e_start.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 15))
        ToolTip(e_start, (
            "TIME TRAVEL\n"
            "When should the simulation start?\n\n"
            "Example: 2023-01-01 to see how the bot\n"
            "would have handled the last year."
        ))
        
        ttk.Label(grid, text="Capital ($):").grid(row=1, column=2, sticky="w", pady=5)
        self.capital_var = tk.DoubleVar(value=10000.0)
        e_cap = ttk.Entry(grid, textvariable=self.capital_var)
        e_cap.grid(row=1, column=3, sticky="ew", pady=5, padx=5)
        ToolTip(e_cap, (
            "STARTING STACK\n"
            "How much paper money do you want to start with?\n\n"
            "Note: This is just for the test, it doesn't\n"
            "use your real money!"
        ))

        # --- 2. ADVANCED STRATEGY & SCALING ---
        adv_frame = ttk.LabelFrame(left_col, text=" 2. Advanced Strategy & Scaling ", padding="15")
        adv_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Thresholds
        thresh_row = ttk.Frame(adv_frame)
        thresh_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(thresh_row, text="Buy Thresh (%):").pack(side=tk.LEFT)
        self.buy_thresh_var = tk.DoubleVar(value=50.0)
        e_buy = ttk.Entry(thresh_row, textvariable=self.buy_thresh_var, width=8)
        e_buy.pack(side=tk.LEFT, padx=(5, 20))
        ToolTip(e_buy, (
            "BUY THRESHOLD\n"
            "This is the AI's 'Confidence Gate'.\n\n"
            "Example: If set to 50, the bot ONLY buys when the AI is 50% sure.\n"
            "Set to 80 for 'Safe/Sniping' mode.\n"
            "Set to 30 for 'Aggressive' mode."
        ))
        
        ttk.Label(thresh_row, text="Sell Thresh (%):").pack(side=tk.LEFT)
        self.sell_thresh_var = tk.DoubleVar(value=0.0)
        e_sell = ttk.Entry(thresh_row, textvariable=self.sell_thresh_var, width=8)
        e_sell.pack(side=tk.LEFT, padx=5)
        ToolTip(e_sell, (
            "SELL THRESHOLD\n"
            "When should the bot panic and exit?\n\n"
            "Example: 0 means 'Sell the moment AI is no longer bullish'.\n"
            "Example: -50 means 'Hold until the AI is screaming that a CRASH is coming'."
        ))
        
        # Position Scaling (Pyramiding)
        scaling_label = ttk.Label(adv_frame, text="Position Scaling (Pyramiding)", style="SubHeader.TLabel")
        scaling_label.pack(anchor="w", pady=(10, 5))
        
        scaling_row = ttk.Frame(adv_frame)
        scaling_row.pack(fill=tk.X)
        
        ttk.Label(scaling_row, text="Base Buy Size (%):").grid(row=0, column=0, sticky="w", pady=5)
        self.pos_size_var = tk.DoubleVar(value=100.0)
        e_psize = ttk.Entry(scaling_row, textvariable=self.pos_size_var, width=8)
        e_psize.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        ToolTip(e_psize, (
            "BASE BUY SIZE\n"
            "How much of your wallet to use for the FIRST buy.\n\n"
            "Example: If set to 25%, the bot buys 1/4 of your cash.\n"
            "This allows the bot to 'Buy more' later if things look good (Pyramiding)!\n"
            "Set to 100% to go 'All-In' on the first signal."
        ))
        
        ttk.Label(scaling_row, text="Confidence Boost (>%):").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.boost_thresh_var = tk.DoubleVar(value=80.0)
        e_bthresh = ttk.Entry(scaling_row, textvariable=self.boost_thresh_var, width=8)
        e_bthresh.grid(row=0, column=3, sticky="w", pady=5, padx=5)
        ToolTip(e_bthresh, (
            "CONFIDENCE BOOST\n"
            "The 'Super Signal' Level.\n\n"
            "Example: If set to 80, the bot treats any AI score above 80 as a 'Gold Mine'.\n"
            "It will then add the 'Boost Size' extra cash on top of the normal buy."
        ))
        
        ttk.Label(scaling_row, text="Boost Size (+%):").grid(row=0, column=4, sticky="w", pady=5, padx=(20, 0))
        self.boost_size_var = tk.DoubleVar(value=0.0)
        e_bsize = ttk.Entry(scaling_row, textvariable=self.boost_size_var, width=8)
        e_bsize.grid(row=0, column=5, sticky="w", pady=5, padx=5)
        ToolTip(e_bsize, (
            "EXTRA BOOST AMOUNT\n"
            "How much EXTRA to buy during a Gold Mine signal.\n\n"
            "Example: If Base is 20% and Boost is 30%,\n"
            "the bot will buy 50% total when confidence is very high."
        ))

        # Protection Toggles
        protect_row = ttk.Frame(adv_frame)
        protect_row.pack(fill=tk.X, pady=10)
        
        self.profit_guard_var = tk.BooleanVar(value=False)
        chk_profit = ttk.Checkbutton(protect_row, text="Profit Guard (No loss selling)", variable=self.profit_guard_var)
        chk_profit.pack(side=tk.LEFT, padx=(0, 20))
        ToolTip(chk_profit, (
            "PROFIT GUARD\n"
            "The 'Diamond Hands' mode.\n\n"
            "If on: The bot will REFUSE to sell if the price is lower\n"
            "than what you paid. It only sells for a win!"
        ))
        
        self.sl_enabled_var = tk.BooleanVar(value=False)
        chk_sl = ttk.Checkbutton(protect_row, text="Stop Loss (%)", variable=self.sl_enabled_var)
        chk_sl.pack(side=tk.LEFT)
        self.sl_val_var = tk.DoubleVar(value=5.0)
        e_sl = ttk.Entry(protect_row, textvariable=self.sl_val_var, width=6)
        e_sl.pack(side=tk.LEFT, padx=10)
        ToolTip(chk_sl, (
            "STOP LOSS\n"
            "Your 'Escape Hatch'.\n\n"
            "If the trade goes wrong by X%, we sell everything\n"
            "immediately to save the rest of your money."
        ))

        # --- Button Area ---
        btn_frame = ttk.Frame(left_col)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.run_btn = ttk.Button(btn_frame, text="EXECUTE BACKTEST", style="Action.TButton", command=self.start_backtest_thread)
        self.run_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(btn_frame, text="CANCEL", style="Cancel.TButton", command=self.request_cancel, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # --- 3. METRICS DASHBOARD ---
        metrics_frame = ttk.LabelFrame(right_col, text=" Real-time Intelligence ", padding="20")
        metrics_frame.pack(fill=tk.Y, expand=True)
        
        self.metrics_labels = {}
        metrics_list = [
            ("Strategy Return", "strat_ret", "Total % profit generated by the AI."),
            ("Buy & Hold", "bh_ret", "What you would earn if you just bought once and did nothing."),
            ("Alpha (The Edge)", "alpha", "Your performance MINUS index performance. Positive is skill!"),
            ("Max Drawdown", "mdd", "The deepest hole your portfolio fell into. Risk indicator."),
            ("Total Trades", "trades", "Number of transactions. High count eats profits via fees."),
            ("Final Account", "final_val", "The final worth of your cash + tokens.")
        ]
        
        for label, key, tip in metrics_list:
            lbl_container = ttk.Frame(metrics_frame)
            lbl_container.pack(fill=tk.X, pady=12)
            l = ttk.Label(lbl_container, text=label, font=("Segoe UI", 9, "bold"), foreground="#7f8c8d")
            l.pack(anchor="w")
            ToolTip(l, tip)
            
            self.metrics_labels[key] = ttk.Label(lbl_container, text="--", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
            self.metrics_labels[key].pack(anchor="w")
            
        # --- 4. EXECUTION CONSOLE ---
        log_container = ttk.LabelFrame(self.main_frame, text=" Simulation Terminal ", padding="10")
        log_container.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        self.log_area = scrolledtext.ScrolledText(log_container, height=12, font=("Consolas", 10), background="#1e1e1e", foreground="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Init state
        self.log("Terminal Ready. AI Engine Synchronized.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def request_cancel(self):
        if self.engine:
            self.engine.stop_requested = True
            self.cancel_btn.config(state=tk.DISABLED, text="Stopping...")
            self.log("[UI] Shutdown request sent to engine...")

    def start_backtest_thread(self):
        self.run_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL, text="CANCEL")
        self.log_area.delete('1.0', tk.END)
        for key in self.metrics_labels:
            self.metrics_labels[key].config(text="--", foreground="#2c3e50")
            
        self.log("Initializing Walk-Forward Analysis...")
        thread = threading.Thread(target=self.run_backtest, daemon=True)
        thread.start()

    def run_backtest(self):
        try:
            # Gather UI Inputs
            ticker = self.ticker_var.get()
            start_date = self.start_date_var.get()
            capital = self.capital_var.get()
            interval = self.interval_var.get()
            buy_thresh = self.buy_thresh_var.get()
            sell_thresh = self.sell_thresh_var.get()
            
            # Advanced Scaling
            pos_size = self.pos_size_var.get()
            boost_thresh = self.boost_thresh_var.get()
            boost_size = self.boost_size_var.get()
            
            # Logic flags
            profit_guard = self.profit_guard_var.get()
            stop_loss = self.sl_val_var.get() if self.sl_enabled_var.get() else None
            
            self.engine = BacktestEngine(
                ticker=ticker,
                start_date=start_date,
                initial_capital=capital,
                log_callback=lambda msg: self.root.after(0, lambda: self.log(msg))
            )
            
            result = self.engine.run(
                interval=interval, 
                consensus_threshold=buy_thresh, 
                sell_threshold=sell_thresh,
                sell_only_at_profit=profit_guard,
                stop_loss_pct=stop_loss,
                pos_size_pct=pos_size,
                boost_threshold=boost_thresh,
                boost_size_pct=boost_size
            )
            
            if result:
                self.root.after(0, lambda: self.update_results(result))
                self.log(f"SIMULATION SUCCESS: Terminal Balance ${result.final_value:.2f}")
            elif self.engine.stop_requested:
                self.log("SIMULATION ABORTED: Results discarded.")
            else:
                self.log("FAILURE: System could not generate trade data.")
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"SYSTEM FAULT: {str(e)}"))
            messagebox.showerror("Execution Fault", str(e))
        finally:
            self.root.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.run_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED, text="CANCEL")
        self.engine = None

    def update_results(self, result):
        m = self.metrics_labels
        
        # Display Results
        m['strat_ret'].config(text=f"{result.total_return_pct:+.2f}%")
        m['bh_ret'].config(text=f"{result.buy_and_hold_return_pct:+.2f}%")
        
        alpha = result.total_return_pct - result.buy_and_hold_return_pct
        m['alpha'].config(text=f"{alpha:+.2f}%")
        
        m['mdd'].config(text=f"{result.max_drawdown_pct:.2f}%")
        m['trades'].config(text=f"{result.trade_count}")
        m['final_val'].config(text=f"${result.final_value:,.2f}")
        
        # Signal Colors
        success = "#27ae60"; danger = "#e74c3c"
        m['strat_ret'].config(foreground=success if result.total_return_pct > 0 else danger)
        m['alpha'].config(foreground=success if alpha > 0 else danger)

if __name__ == "__main__":
    root = tk.Tk()
    # High DPI Scaling for Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = BacktestUI(root)
    root.mainloop()
