# Financial ML Pipeline - User Stories

## Epic 1: News Sentiment Analysis with FinBERT

### US-ML-001: Real-time News Fetching for Selected Ticker
**Priority**: High  
**Story Points**: 5

**As a** data scientist  
**I want** to fetch today's financial news for a selected ticker  
**So that** I can analyze market sentiment in real-time

**Acceptance Criteria:**
- [ ] System fetches news from multiple sources (NewsAPI, Alpha Vantage, Finnhub)
- [ ] News is filtered by ticker symbol
- [ ] Only today's news (last 24 hours) is retrieved
- [ ] News includes: headline, description, source, published timestamp, URL
- [ ] API rate limits are respected with exponential backoff
- [ ] Failed API calls are logged and retried

**Technical Notes:**
- Use `newsapi`, `alpha_vantage`, `finnhub-python` libraries
- Store API keys in environment variables
- Implement caching to avoid duplicate API calls

---

### US-ML-002: FinBERT Sentiment Classification
**Priority**: High  
**Story Points**: 8

**As a** ML engineer  
**I want** to classify news sentiment using pre-trained FinBERT  
**So that** I can quantify market sentiment for each ticker

**Acceptance Criteria:**
- [ ] FinBERT model (`ProsusAI/finbert`) is loaded and cached
- [ ] Each news headline + description is classified as positive/negative/neutral
- [ ] Sentiment scores (confidence) are extracted (0-1 range)
- [ ] Batch processing is implemented for efficiency (batch size: 16-32)
- [ ] GPU acceleration is used if available
- [ ] Processing time is logged for performance monitoring

**Technical Notes:**
- Use `transformers` library: `AutoTokenizer`, `AutoModelForSequenceClassification`
- Model: `ProsusAI/finbert` or `yiyanghkust/finbert-tone`
- Max sequence length: 512 tokens
- Return both label and probability distribution

**Implementation Example:**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

def classify_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    # Returns: {label: 'positive', score: 0.87}
```

---

### US-ML-003: Sentiment Data Deduplication & Timestamping
**Priority**: High  
**Story Points**: 5

**As a** data engineer  
**I want** to prevent duplicate news entries and ensure proper timestamping  
**So that** my dataset remains clean and time-series analysis is accurate

**Acceptance Criteria:**
- [ ] Unique constraint on (ticker, headline_hash, published_timestamp)
- [ ] Duplicate news articles are detected and skipped
- [ ] All timestamps are stored in UTC
- [ ] Timestamps are indexed for fast time-range queries
- [ ] Data retention policy: keep last 90 days of news
- [ ] Old data is archived, not deleted

**Technical Notes:**
- Use SHA-256 hash of headline for deduplication
- PostgreSQL/TimescaleDB for time-series optimization
- Create composite index: `(ticker, published_timestamp DESC)`

**Database Schema:**
```sql
CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    headline_hash VARCHAR(64) NOT NULL,
    description TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sentiment_label VARCHAR(10) NOT NULL, -- positive/negative/neutral
    sentiment_score FLOAT NOT NULL,
    sentiment_distribution JSONB, -- {positive: 0.1, negative: 0.05, neutral: 0.85}
    UNIQUE(ticker, headline_hash, published_at)
);

CREATE INDEX idx_ticker_time ON news_sentiment(ticker, published_at DESC);
```

---

### US-ML-004: Sentiment Feature Engineering
**Priority**: High  
**Story Points**: 8

**As a** ML engineer  
**I want** to create aggregated sentiment features at multiple time windows  
**So that** I can capture both recent and historical sentiment trends

**Acceptance Criteria:**
- [ ] Sentiment aggregated over: 1h, 4h, 24h, 7d, 30d windows
- [ ] Features include: mean, weighted mean (time-decay), std, min, max
- [ ] Sentiment velocity (rate of change) calculated
- [ ] News volume (count) per time window included
- [ ] Features are computed efficiently using rolling windows
- [ ] Missing data is handled (forward-fill with decay)

**Feature List:**
```python
sentiment_features = {
    # Aggregated sentiment scores
    'sentiment_1h_mean': float,
    'sentiment_4h_mean': float,
    'sentiment_24h_mean': float,
    'sentiment_7d_mean': float,
    'sentiment_30d_mean': float,
    
    # Time-decay weighted (recent news weighted more)
    'sentiment_1h_weighted': float,
    'sentiment_24h_weighted': float,
    
    # Volatility
    'sentiment_1h_std': float,
    'sentiment_24h_std': float,
    
    # Velocity (rate of change)
    'sentiment_velocity_1h': float,  # (current - 1h_ago) / 1h
    'sentiment_velocity_24h': float,
    
    # Volume
    'news_count_1h': int,
    'news_count_24h': int,
    
    # Extremes
    'sentiment_24h_min': float,
    'sentiment_24h_max': float,
}
```

**Time-Decay Formula:**
```python
import numpy as np

def time_decay_weight(hours_ago, half_life=6):
    """Exponential decay: news from 6 hours ago has 50% weight"""
    return np.exp(-np.log(2) * hours_ago / half_life)
```

---

## Epic 2: Multi-Horizon Prediction Models

### US-ML-005: Dataset Design for Multi-Horizon Prediction
**Priority**: Critical  
**Story Points**: 13

**As a** ML architect  
**I want** to design a unified dataset structure supporting multiple prediction horizons  
**So that** I can train specialized models for different trading strategies

**Acceptance Criteria:**
- [ ] Target variables created for: 1min, 3min, 30min, 1h, 1d, 1w, 1mo horizons
- [ ] Targets include: price change (%), direction (up/down), volatility
- [ ] Features are aligned with prediction horizon (no data leakage)
- [ ] Train/validation/test splits are time-based (no shuffle)
- [ ] Dataset supports both regression and classification tasks
- [ ] Data is normalized/standardized per feature

**Target Variable Design:**
```python
# For each horizon (e.g., 30min):
targets = {
    'price_change_30min': (price_t+30min - price_t) / price_t * 100,  # percentage
    'direction_30min': 1 if price_t+30min > price_t else 0,  # binary
    'high_30min': max(price[t:t+30min]),  # for risk management
    'low_30min': min(price[t:t+30min]),
    'volatility_30min': std(returns[t:t+30min]),
}
```

**Feature Categories by Horizon:**

| Feature Type | 1min | 30min | 1h | 1d | 1w | 1mo |
|--------------|------|-------|----|----|----|----|
| Price/Volume (OHLCV) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Technical Indicators | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Order Book (L2 data) | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| News Sentiment | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Macro Indicators | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Earnings/Fundamentals | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |

**Data Split Strategy:**
```python
# Time-based split (NO SHUFFLE!)
train_end = '2024-12-31'
val_end = '2025-06-30'
test_end = '2026-01-22'

train_data = df[df.index <= train_end]
val_data = df[(df.index > train_end) & (df.index <= val_end)]
test_data = df[df.index > val_end]
```

---

### US-ML-006: Ultra-Short Term Model (1-5 min)
**Priority**: Medium  
**Story Points**: 13

**As a** quantitative trader  
**I want** a model predicting 1-5 minute price movements  
**So that** I can execute high-frequency trading strategies

**Acceptance Criteria:**
- [ ] Model trained on 1-second or 1-minute OHLCV data
- [ ] Features: price momentum, volume spikes, bid-ask spread, order flow
- [ ] Model type: LightGBM or XGBoost (fast inference)
- [ ] Prediction latency < 10ms
- [ ] Backtested with transaction costs (0.1% per trade)
- [ ] Sharpe ratio > 1.5 on validation set

**Key Features:**
- Price returns (1min, 5min)
- Volume ratios (current / moving average)
- RSI (5min, 15min)
- VWAP distance
- Order book imbalance (if available)

**Model Architecture:**
```python
import lightgbm as lgb

params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1
}

model_1min = lgb.train(params, train_data, num_boost_round=1000)
```

---

### US-ML-007: Short Term Model (15min - 1h)
**Priority**: High  
**Story Points**: 13

**As a** day trader  
**I want** a model predicting 15-60 minute price movements  
**So that** I can make informed intraday trading decisions

**Acceptance Criteria:**
- [ ] Model trained on 5-minute or 15-minute bars
- [ ] Features: technical indicators, volume profile, sentiment (1h window)
- [ ] Model type: Ensemble (LightGBM + LSTM)
- [ ] Directional accuracy > 55% on validation set
- [ ] Includes confidence scores for predictions
- [ ] Backtested with realistic slippage

**Key Features:**
- All features from 1-5min model
- **+ News sentiment (1h, 4h aggregates)**
- MACD, Bollinger Bands
- ATR (Average True Range)
- Market regime (trending/ranging)

---

### US-ML-008: Medium Term Model (1 day - 1 week)
**Priority**: High  
**Story Points**: 13

**As a** swing trader  
**I want** a model predicting daily/weekly price movements  
**So that** I can hold positions for days to weeks

**Acceptance Criteria:**
- [ ] Model trained on daily OHLCV data
- [ ] Features: technical indicators, sentiment (24h, 7d), macro indicators
- [ ] Model type: LSTM or Transformer (captures long-term dependencies)
- [ ] Prediction includes price target and confidence interval
- [ ] Backtested over 3+ years of data
- [ ] Risk-adjusted returns (Sortino ratio) > 1.0

**Key Features:**
- All features from previous models (aggregated to daily)
- **+ News sentiment (24h, 7d, 30d aggregates)**
- **+ Sentiment velocity and volatility**
- Moving averages (20, 50, 200 day)
- Sector performance
- VIX (volatility index)
- Economic calendar events

---

### US-ML-009: Long Term Model (1 month+)
**Priority**: Medium  
**Story Points**: 21

**As a** portfolio manager  
**I want** a model predicting monthly price movements using cascaded predictions  
**So that** I can make strategic allocation decisions

**Acceptance Criteria:**
- [ ] Model uses outputs from all shorter-term models as features
- [ ] Additional features: fundamentals (P/E, EPS growth), analyst ratings
- [ ] Model type: Ensemble (Gradient Boosting + Neural Network)
- [ ] Predictions include uncertainty quantification
- [ ] Backtested with portfolio-level metrics (max drawdown, Calmar ratio)
- [ ] Explainability: SHAP values for feature importance

**Cascading Architecture:**
```python
# Inputs to 1-month model:
features_1mo = {
    # Predictions from shorter models
    'pred_1min_avg_last_day': float,
    'pred_30min_avg_last_week': float,
    'pred_1h_avg_last_week': float,
    'pred_1d_avg_last_month': float,
    'pred_1w_last_4_weeks': list,
    
    # Confidence/uncertainty from shorter models
    'pred_1d_std_last_month': float,
    'pred_1w_std_last_month': float,
    
    # Traditional features
    'sentiment_30d_mean': float,
    'sentiment_30d_trend': float,
    'pe_ratio': float,
    'eps_growth_yoy': float,
    'analyst_rating_avg': float,
    # ... etc
}
```

**Why This Works:**
- Shorter models capture high-frequency patterns
- Aggregating their predictions smooths noise
- Longer model focuses on strategic trends
- Reduces overfitting to short-term volatility

---

## Epic 3: Model Training & Evaluation Pipeline

### US-ML-010: Automated Training Pipeline
**Priority**: High  
**Story Points**: 13

**As a** ML engineer  
**I want** an automated pipeline for training all models  
**So that** I can retrain models regularly with new data

**Acceptance Criteria:**
- [ ] Pipeline orchestrated with Airflow or Prefect
- [ ] Daily retraining for 1min-1h models
- [ ] Weekly retraining for 1d-1w models
- [ ] Monthly retraining for 1mo model
- [ ] Hyperparameter tuning with Optuna
- [ ] Model versioning with MLflow
- [ ] Automated A/B testing (new model vs. production model)
- [ ] Rollback mechanism if new model underperforms

---

### US-ML-011: Backtesting Framework
**Priority**: Critical  
**Story Points**: 13

**As a** quantitative analyst  
**I want** a comprehensive backtesting framework  
**So that** I can evaluate model performance realistically

**Acceptance Criteria:**
- [ ] Walk-forward validation (expanding window)
- [ ] Transaction costs included (commission + slippage)
- [ ] Position sizing based on Kelly Criterion
- [ ] Risk management: stop-loss, take-profit, max drawdown limits
- [ ] Performance metrics: Sharpe, Sortino, Calmar, max drawdown, win rate
- [ ] Comparison against buy-and-hold baseline
- [ ] Visualization: equity curve, drawdown chart, monthly returns heatmap

---

### US-ML-012: Model Monitoring & Drift Detection
**Priority**: High  
**Story Points**: 8

**As a** ML engineer  
**I want** to monitor model performance in production  
**So that** I can detect and respond to model degradation

**Acceptance Criteria:**
- [ ] Real-time tracking of prediction accuracy
- [ ] Feature distribution monitoring (detect data drift)
- [ ] Prediction distribution monitoring (detect concept drift)
- [ ] Alerts when performance drops below threshold
- [ ] Dashboard showing model health metrics
- [ ] Automatic retraining triggered on drift detection

---

## Epic 4: Infrastructure & Deployment

### US-ML-013: Feature Store Implementation
**Priority**: High  
**Story Points**: 13

**As a** ML engineer  
**I want** a centralized feature store  
**So that** features are computed once and reused across models

**Acceptance Criteria:**
- [ ] Feature store using Feast or custom solution
- [ ] Features computed in batch (daily) and streaming (real-time)
- [ ] Point-in-time correct joins (no data leakage)
- [ ] Feature versioning and lineage tracking
- [ ] Low-latency feature serving (<50ms)

**Technology Stack:**
- **Batch**: Apache Spark or Pandas
- **Streaming**: Apache Kafka + Flink
- **Storage**: Redis (online), Parquet/Delta Lake (offline)
- **Orchestration**: Feast or Tecton

---

### US-ML-014: Model Serving API
**Priority**: High  
**Story Points**: 8

**As a** application developer  
**I want** a REST API for model predictions  
**So that** I can integrate ML models into the trading application

**Acceptance Criteria:**
- [ ] FastAPI endpoint: `POST /predict/{ticker}/{horizon}`
- [ ] Input: ticker symbol, horizon (1min, 30min, 1d, etc.)
- [ ] Output: prediction, confidence, feature importance
- [ ] Response time: <100ms (p95)
- [ ] Rate limiting: 1000 requests/min per user
- [ ] Authentication with API keys
- [ ] Logging all predictions for audit

**API Example:**
```python
# Request
POST /predict/AAPL/1d
{
    "features": {...}  # Optional: override features
}

# Response
{
    "ticker": "AAPL",
    "horizon": "1d",
    "prediction": {
        "price_change_pct": 2.3,
        "direction": "up",
        "confidence": 0.72
    },
    "feature_importance": {
        "sentiment_24h_mean": 0.25,
        "rsi_14d": 0.18,
        ...
    },
    "timestamp": "2026-01-22T16:30:00Z",
    "model_version": "v1.2.3"
}
```

---

## Epic 5: Data Quality & Governance

### US-ML-015: Data Quality Monitoring
**Priority**: High  
**Story Points**: 8

**As a** data engineer  
**I want** automated data quality checks  
**So that** bad data doesn't corrupt model training

**Acceptance Criteria:**
- [ ] Schema validation (Great Expectations)
- [ ] Null value detection and handling
- [ ] Outlier detection (z-score > 3)
- [ ] Data freshness checks (alert if data > 1 hour old)
- [ ] Duplicate detection
- [ ] Automated data profiling reports

---

## Summary & Recommendations

### **Recommended Implementation Order:**

**Phase 1: Foundation (Weeks 1-2)**
1. US-ML-001: News fetching
2. US-ML-002: FinBERT sentiment
3. US-ML-003: Deduplication
4. US-ML-005: Dataset design

**Phase 2: Core Models (Weeks 3-6)**
5. US-ML-007: Short-term model (1h) - **Start here for quick wins**
6. US-ML-008: Medium-term model (1d)
7. US-ML-004: Sentiment feature engineering
8. US-ML-011: Backtesting framework

**Phase 3: Advanced Models (Weeks 7-10)**
9. US-ML-006: Ultra-short model (1min)
10. US-ML-009: Long-term cascading model
11. US-ML-010: Training pipeline
12. US-ML-012: Model monitoring

**Phase 4: Production (Weeks 11-12)**
13. US-ML-013: Feature store
14. US-ML-014: Model serving API
15. US-ML-015: Data quality

### **Technology Stack Recommendation:**

```yaml
Data Collection:
  - News: newsapi, finnhub, alpha_vantage
  - Market Data: yfinance, alpaca-trade-api

ML Framework:
  - Sentiment: transformers (FinBERT)
  - Tabular Models: LightGBM, XGBoost, CatBoost
  - Time Series: LSTM (PyTorch), Prophet
  - Ensemble: scikit-learn, Optuna

Infrastructure:
  - Database: PostgreSQL + TimescaleDB
  - Feature Store: Feast
  - Orchestration: Apache Airflow
  - Experiment Tracking: MLflow, Weights & Biases
  - Model Serving: FastAPI + Docker
  - Monitoring: Prometheus + Grafana

Deployment:
  - Containerization: Docker
  - Cloud: AWS (SageMaker) or GCP (Vertex AI)
  - CI/CD: GitHub Actions
```

---

**Next Steps:**
Would you like me to start implementing any of these user stories? I recommend starting with **US-ML-001, US-ML-002, and US-ML-003** to get the sentiment analysis pipeline working first, then move to **US-ML-005** for dataset design.

Let me know which direction you'd like to go! 🚀
