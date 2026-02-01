import sys
sys.path.append('algotrade_datascience')

from core.news_fetcher import NewsFetcher
from features.sentiment_analysis import SentimentProcessor
import pandas as pd

print("Testing News Sentiment Flow...")
print("=" * 50)

# Test 1: NewsFetcher
print("\n1. Testing NewsFetcher...")
fetcher = NewsFetcher()
df = fetcher.fetch_ticker_news('AAPL')
print(f"   Found {len(df)} news items")
if not df.empty:
    print(f"   Columns: {df.columns.tolist()}")
    print(f"   First title: {df.iloc[0]['title']}")
    print(f"   First publisher: {df.iloc[0]['publisher']}")

# Test 2: SentimentProcessor
print("\n2. Testing SentimentProcessor...")
processor = SentimentProcessor()
df_with_sentiment = processor.process_news_dataframe(df.head(2))
print(f"   Processed {len(df_with_sentiment)} items")
print(f"   Columns after sentiment: {df_with_sentiment.columns.tolist()}")

# Test 3: Serialization
print("\n3. Testing JSON Serialization...")
for idx, row in df_with_sentiment.iterrows():
    item = {
        "title": str(row.get('title', '')),
        "publisher": str(row.get('publisher', '')),
        "link": str(row.get('link', '')),
        "publish_time": row.get('publish_time').strftime("%Y-%m-%d %H:%M") if pd.notna(row.get('publish_time')) else '',
        "sentiment": str(row.get('sentiment', 'neutral')),
        "sentiment_score": float(row.get('sentiment_score', 0))
    }
    print(f"   Item: {item['title'][:40]}... | Sentiment: {item['sentiment']} ({item['sentiment_score']:.2f})")
    break

print("\n" + "=" * 50)
print("Test Complete!")
