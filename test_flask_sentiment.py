import sys
sys.path.append('algotrade_datascience')

from core.news_fetcher import NewsFetcher
from features.sentiment_analysis import SentimentProcessor
import pandas as pd
from flask import Flask, jsonify

app = Flask(__name__)

news_fetcher = NewsFetcher()
sentiment_processor = None

def get_sentiment_processor():
    global sentiment_processor
    if sentiment_processor is None:
        sentiment_processor = SentimentProcessor()
    return sentiment_processor

@app.route("/test/<ticker>")
def test_sentiment(ticker):
    print(f"TEST: Fetching for {ticker}", flush=True)
    df = news_fetcher.fetch_ticker_news(ticker)
    print(f"TEST: Got {len(df)} items", flush=True)
    
    if df.empty:
        return jsonify([])
    
    df = df.head(2)
    processor = get_sentiment_processor()
    df_with_sentiment = processor.process_news_dataframe(df)
    
    results = []
    for _, row in df_with_sentiment.iterrows():
        item = {
            "title": str(row['title']),
            "publisher": str(row['publisher']),
            "sentiment": str(row['sentiment']),
            "score": float(row['sentiment_score'])
        }
        results.append(item)
        print(f"TEST: {item}", flush=True)
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=False, port=5001, use_reloader=False)
