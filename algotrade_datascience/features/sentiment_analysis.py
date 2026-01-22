"""
Sentiment Analysis using FinBERT
Processes financial news and returns sentiment scores.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SentimentProcessor:
    def __init__(self, model_name="ProsusAI/finbert"):
        """
        Initialize FinBERT model and tokenizer.
        """
        logger.info(f"Loading FinBERT model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.labels = ["positive", "negative", "neutral"]
        
        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        logger.info(f"Model loaded on {self.device}")

    def analyze_sentiment(self, texts):
        """
        Analyze sentiment for a list of texts.
        Returns a list of dictionaries with scores.
        """
        if not texts:
            return []

        # Tokenize
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Convert to list of dictionaries
        results = []
        for i in range(len(texts)):
            scores = predictions[i].cpu().numpy()
            results.append({
                "sentiment": self.labels[np.argmax(scores)],
                "positive": float(scores[0]),
                "negative": float(scores[1]),
                "neutral": float(scores[2]),
                "sentiment_score": float(scores[0] - scores[1]) # Aggregate score
            })
        
        return results

    def process_news_dataframe(self, news_df):
        """
        Processes a dataframe of news (must have 'title' column).
        Adds sentiment columns.
        """
        if news_df.empty:
            return news_df
        
        logger.info(f"Analyzing sentiment for {len(news_df)} headlines...")
        titles = news_df['title'].tolist()
        sentiments = self.analyze_sentiment(titles)
        
        sentiment_df = pd.DataFrame(sentiments)
        return pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    processor = SentimentProcessor()
    test_news = [
        "Apple reports record breaking Q3 earnings, stock surges.",
        "Concerns over slowing iPhone sales in China weigh on Apple's outlook.",
        "Market remains flat as investors await Fed decision."
    ]
    results = processor.analyze_sentiment(test_news)
    for text, res in zip(test_news, results):
        print(f"Text: {text}")
        print(f"Result: {res}\n")
