"""
News Fetcher
Fetches financial news for specified tickers.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        pass

    def fetch_ticker_news(self, ticker_symbol):
        """
        Fetch news for a specific ticker using yfinance.
        """
        logger.info(f"Fetching news for {ticker_symbol}...")
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        
        if not news:
            logger.warning(f"No news found for {ticker_symbol}")
            return pd.DataFrame()
        
        news_data = []
        for article in news:
            publish_time_raw = article.get("providerPublishTime")
            if publish_time_raw:
                publish_time = datetime.fromtimestamp(publish_time_raw)
            else:
                publish_time = datetime.now()
                
            news_data.append({
                "ticker": ticker_symbol,
                "title": article.get("title"),
                "publisher": article.get("publisher"),
                "link": article.get("link"),
                "publish_time": publish_time,
                "type": article.get("type")
            })
        
        df = pd.DataFrame(news_data)
        # Ensure publish_time is datetime
        df['publish_time'] = pd.to_datetime(df['publish_time'])
        # Sort by time
        df = df.sort_values(by='publish_time', ascending=False)
        
        return df

    def get_daily_sentiment(self, news_with_sentiment):
        """
        Groups sentiment by day and calculates average daily sentiment.
        """
        if news_with_sentiment.empty:
            return pd.DataFrame()
        
        df = news_with_sentiment.copy()
        df['date'] = df['publish_time'].dt.date
        
        daily_sentiment = df.groupby('date').agg({
            'sentiment_score': 'mean',
            'positive': 'mean',
            'negative': 'mean',
            'neutral': 'mean',
            'title': 'count'
        }).rename(columns={'title': 'news_count'})
        
        return daily_sentiment

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    fetcher = NewsFetcher()
    news_df = fetcher.fetch_ticker_news("AAPL")
    print(news_df.head())
