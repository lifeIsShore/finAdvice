import os
import sys
import subprocess
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request

# Use absolute path based on this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Add algotrade_datascience to path so internal imports work
sys.path.append(os.path.join(BASE_DIR, "algotrade_datascience"))

from algotrade_datascience.core.data_storage import DataStorage
from algotrade_datascience.core.news_fetcher import NewsFetcher
from algotrade_datascience.features.sentiment_analysis import SentimentProcessor

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Add CORS headers to allow local HTML development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Paths
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DECISIONS_DIR = os.path.join(BASE_DIR, "data", "decisions")

# Initialize storage for fetching metadata/tickers
storage = DataStorage(base_dir=BASE_DIR)
news_fetcher = NewsFetcher()
sentiment_processor = None # Lazy load

def get_sentiment_processor():
    global sentiment_processor
    if sentiment_processor is None:
        sentiment_processor = SentimentProcessor()
    return sentiment_processor

print(f"SERVER: Starting in {BASE_DIR}")
print(f"SERVER: Decisions directory: {DECISIONS_DIR}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tickers")
def get_tickers():
    try:
        # Show tickers that have either raw data or decision files
        tickers = set()
        
        # Check decisions
        if os.path.exists(DECISIONS_DIR):
            try:
                for f in os.listdir(DECISIONS_DIR):
                    if f.endswith("_premium_decision.json"):
                        tickers.add(f.replace("_premium_decision.json", ""))
            except Exception as e:
                print(f"Warning: Error reading DECISIONS_DIR: {e}")
        
        # Check raw data folders if they contain at least one CSV
        if os.path.exists(RAW_DATA_DIR):
            try:
                for d in os.listdir(RAW_DATA_DIR):
                    path = os.path.join(RAW_DATA_DIR, d)
                    if os.path.isdir(path):
                        # Verify it has data
                        if any(fname.endswith('.csv') for fname in os.listdir(path)):
                            tickers.add(d)
            except Exception as e:
                print(f"Warning: Error reading RAW_DATA_DIR: {e}")

        res = sorted(list(tickers))
        print(f"API: Found {len(res)} tickers: {res}")
        return jsonify(res)
    except Exception as e:
        print(f"API Error in get_tickers: {e}")
        # Return empty list instead of 500 to keep UI alive
        return jsonify([])

@app.route("/api/run_pipeline", methods=["POST"])
def run_pipeline():
    data = request.json
    ticker = data.get("ticker", "AAPL")
    try:
        cmd = ["python", "algotrade_datascience/main_data_pipeline.py", "--mode", "manual", "--tickers", ticker]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "output": (e.stdout or "") + (e.stderr or "")}), 500

@app.route("/api/run_ml", methods=["POST"])
def run_ml():
    data = request.json
    ticker = data.get("ticker", "AAPL")
    horizon = data.get("horizon", 60)
    risk = data.get("risk", "conservative")
    try:
        # Pass horizon and risk to script
        cmd = ["python", "algotrade_datascience/decision_making_ml.py", "--ticker", ticker, "--horizon", str(horizon), "--risk", risk]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        error_msg = (e.stdout or "") + (e.stderr or "")
        print(f"ML Script Error: {error_msg}", flush=True)
        return jsonify({"status": "error", "output": error_msg}), 500
    except Exception as e:
        print(f"Unexpected Error in run_ml: {str(e)}", flush=True)
        return jsonify({"status": "error", "output": str(e)}), 500

@app.route("/api/history/<ticker>")
def get_history(ticker):
    try:
        # Load 1d data for chart
        df = storage.load_ticker_data(ticker, "1d")
        if df is None or df.empty:
            return jsonify({"error": "No data found"}), 404
        
        # Return last 100 points for chart
        df = df.tail(100)
        # Convert to records
        if 'Date' in df.columns:
            df['Date'] = df['Date'].astype(str)
        else:
            df = df.reset_index()
            df['Date'] = df['Date'].astype(str)
            
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/test")
def test_endpoint():
    return jsonify({"message": "Server is running UPDATED code - v2", "timestamp": "2026-02-01 02:39"})

@app.route("/api/sentiment/<ticker>")
def get_sentiment(ticker):
    try:
        # Try to load cached news first (24 hour cache)
        df = storage.load_news_data(ticker, max_age_hours=24)
        cache_used = False
        
        if df is None or df.empty:
            # Fallback to real-time fetch
            print(f"DEBUG: No cached news for {ticker}, fetching real-time...", flush=True)
            df = news_fetcher.fetch_ticker_news(ticker)
            print(f"DEBUG: NewsFetcher returned {len(df)} items", flush=True)
            
            if df.empty:
                return jsonify([])
            
            # Take up to 10 articles (or all if fewer available)
            df = df.head(10)
            print(f"DEBUG: Using {len(df)} articles after limiting to 10", flush=True)
            
            # Cache the fetched news for future use
            storage.save_news_data(ticker, df)
        else:
            cache_used = True
            print(f"DEBUG: Using cached news for {ticker} ({len(df)} items)", flush=True)
        
        print(f"DEBUG: Processing {len(df)} items for sentiment...", flush=True)
        processor = get_sentiment_processor()
        
        # Check if sentiment already exists in cached data
        if 'sentiment' not in df.columns:
            df_with_sentiment = processor.process_news_dataframe(df)
        else:
            df_with_sentiment = df
        
        print(f"DEBUG: After sentiment: {len(df_with_sentiment)} items", flush=True)
        
        results = []
        for _, row in df_with_sentiment.iterrows():
            results.append({
                "title": str(row['title']),
                "publisher": str(row['publisher']),
                "link": str(row['link']),
                "publish_time": row['publish_time'].strftime("%Y-%m-%d %H:%M"),
                "sentiment": str(row['sentiment']),
                "sentiment_score": float(row['sentiment_score']),
                "cached": cache_used
            })
        print(f"DEBUG: Returning {len(results)} items (cached: {cache_used})", flush=True)
        return jsonify(results)
    except Exception as e:
        import traceback
        print(f"Sentiment API Error: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify([])

@app.route("/api/results/<ticker>")
def get_results(ticker):
    try:
        path = os.path.join(DECISIONS_DIR, f"{ticker}_premium_decision.json")
        if not os.path.exists(path):
            return jsonify({"error": "No results found"}), 404
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/model_metrics/<ticker>")
def get_model_metrics(ticker):
    try:
        # We can either read the separate baseline JSON or the decision JSON which now includes it
        # Let's read the decision JSON as it is the single source of truth for the UI
        path = os.path.join(DECISIONS_DIR, f"{ticker}_premium_decision.json")
        if not os.path.exists(path):
             return jsonify({"error": "No model metrics found"}), 404
             
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Try to get consensus if model_competition is missing/empty
        competition = data.get("model_competition", {})
        if not competition:
            # Fallback to new consensus format
            # New format: data['consensus'] is a dict where keys are intervals '1h', '4h', etc.
            competition = data.get("consensus", {})
            
        return jsonify(competition)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/model_diagnostics/<ticker>")
def get_model_diagnostics(ticker):
    """Serve consensus data for analytics page"""
    try:
        # Load the main decision file which contains consensus data
        path = os.path.join(DECISIONS_DIR, f"{ticker}_premium_decision.json")
        if not os.path.exists(path):
            return jsonify({"error": "No data found"}), 404
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Return the 'consensus' part which has data for all intervals
        return jsonify(data.get("consensus", {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analytics/<ticker>")
def analytics_page(ticker):
    """Serve the analytics page"""
    return render_template("analytics.html", ticker=ticker)

@app.route("/api/kill_server", methods=["POST"])
def kill_server():
    """Allows the UI to request a server restart (useful for dev)"""
    def _shutdown():
        import time
        time.sleep(1)
        os._exit(0)
    
    import threading
    threading.Thread(target=_shutdown).start()
    return jsonify({"status": "shutting_down"})

if __name__ == "__main__":
    app.run(debug=False, port=5000, use_reloader=False)
