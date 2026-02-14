# FinAdvice AI - Improvements & Feature Roadmap

**Last Updated**: February 12, 2026  
**Status**: Active Development (Phase 2 - Enhanced Features)

---

## 📑 Table of Contents

1. [Immediate Improvements](#immediate-improvements)
2. [Code Quality & Production-Ready](#code-quality--production-ready)
3. [Future Feature Roadmap](#future-feature-roadmap)
4. [Architecture Recommendations](#architecture-recommendations)
5. [Implementation Timeline](#implementation-timeline)

---

# IMMEDIATE IMPROVEMENTS

## 🔒 Section 1: Security & Input Validation

### 1.1 Ticker Validation Layer

**Current Issue**: No validation on ticker input - could cause injection vulnerabilities or unexpected behavior.

**Location**: `dashboard_app.py` and `algotrade_datascience/core/data_fetcher.py`

**Implementation**:

Create new file: `algotrade_datascience/utils/validators.py`

```python
"""
Input validators for API endpoints
Ensures all user inputs are sanitized and safe
"""
import re
from typing import Tuple

class TickerValidator:
    """Validates ticker symbols against known patterns"""
    
    # Pattern: 1-5 uppercase letters, optionally followed by -CURRENCY
    # Examples: AAPL, BTC-USD, SAP, ETH-EUR
    TICKER_PATTERN = r'^[A-Z]{1,5}(-[A-Z]{3})?$'
    
    # Blacklist of suspicious patterns
    BLACKLIST_PATTERNS = [
        r'\.\.\/|\.\.\\',  # Path traversal
        r'[;&|`$()]',      # Shell metacharacters
        r'--',             # SQL injection
    ]
    
    MAX_TICKER_LENGTH = 10
    MIN_TICKER_LENGTH = 1
    
    @classmethod
    def validate(cls, ticker: str) -> Tuple[bool, str]:
        """
        Validate ticker format
        
        Args:
            ticker: User-provided ticker string
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check length
        if not ticker or len(ticker) > cls.MAX_TICKER_LENGTH:
            return False, f"Ticker must be 1-{cls.MAX_TICKER_LENGTH} characters"
        
        # Check for blacklist patterns
        for pattern in cls.BLACKLIST_PATTERNS:
            if re.search(pattern, ticker):
                return False, "Ticker contains invalid characters"
        
        # Check valid format
        if not re.match(cls.TICKER_PATTERN, ticker):
            return False, f"Invalid ticker format. Use pattern: ABC or BTC-USD"
        
        return True, ""


class HorizonValidator:
    """Validates prediction horizon"""
    
    MIN_HORIZON = 1
    MAX_HORIZON = 365
    
    @classmethod
    def validate(cls, horizon: int) -> Tuple[bool, str]:
        if not isinstance(horizon, int):
            return False, "Horizon must be integer"
        
        if horizon < cls.MIN_HORIZON or horizon > cls.MAX_HORIZON:
            return False, f"Horizon must be between {cls.MIN_HORIZON}-{cls.MAX_HORIZON}"
        
        return True, ""


class RiskModeValidator:
    """Validates risk mode parameter"""
    
    VALID_MODES = {'conservative', 'aggressive', 'balanced'}
    
    @classmethod
    def validate(cls, mode: str) -> Tuple[bool, str]:
        if mode.lower() not in cls.VALID_MODES:
            return False, f"Risk mode must be one of: {', '.join(cls.VALID_MODES)}"
        
        return True, ""
```

**Update in dashboard_app.py**:

```python
from algotrade_datascience.utils.validators import (
    TickerValidator, HorizonValidator, RiskModeValidator
)

@app.route("/api/run_ml", methods=["POST"])
def run_ml():
    data = request.json
    ticker = data.get("ticker", "").upper()
    horizon = data.get("horizon", 60)
    risk = data.get("risk", "conservative").lower()
    
    # VALIDATE ALL INPUTS
    is_valid, msg = TickerValidator.validate(ticker)
    if not is_valid:
        return jsonify({"status": "error", "output": msg}), 400
    
    is_valid, msg = HorizonValidator.validate(horizon)
    if not is_valid:
        return jsonify({"status": "error", "output": msg}), 400
    
    is_valid, msg = RiskModeValidator.validate(risk)
    if not is_valid:
        return jsonify({"status": "error", "output": msg}), 400
    
    # NOW SAFE TO RUN
    try:
        cmd = ["python", "algotrade_datascience/decision_making_ml.py", 
               "--ticker", ticker, "--horizon", str(horizon), "--risk", risk]
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              timeout=600)  # 10 minute timeout
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "output": "Prediction timed out"}), 408
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500
```

---

### 1.2 API Rate Limiting

**Current Issue**: No rate limiting - users can spam endpoints.

**Installation**: `pip install Flask-Limiter`

**Implementation in dashboard_app.py**:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/run_pipeline", methods=["POST"])
@limiter.limit("10 per hour")  # Heavy operation
def run_pipeline():
    """Data sync - expensive, limit heavily"""
    ...

@app.route("/api/run_ml", methods=["POST"])
@limiter.limit("20 per hour")  # ML prediction
def run_ml():
    """ML prediction - moderately expensive"""
    ...

@app.route("/api/sentiment/<ticker>")
@limiter.limit("30 per hour")  # Sentiment fetch
def get_sentiment(ticker):
    """Sentiment - lighter operation"""
    ...

@app.route("/api/tickers")
@limiter.limit("60 per hour")  # List operation
def get_tickers():
    """List tickers - very light"""
    ...
```

---

### 1.3 CORS Security Fix

**Current Issue**: CORS allows requests from ANY domain.

**Fix in dashboard_app.py**:

```python
from flask import Flask, request
import os

# Load from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",")
DEBUG = os.getenv("DEBUG", "False") == "True"

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    
    # Only allow listed origins
    if origin in ALLOWED_ORIGINS or DEBUG:
        response.headers['Access-Control-Allow-Origin'] = origin
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    return response
```

**Create `.env.example`**:

```env
# Environment Configuration
DEBUG=False
FLASK_PORT=5000
ALLOWED_ORIGINS=http://localhost:5000,https://yourdomain.com

# API Keys (if using paid APIs)
NEWSAPI_KEY=your_key_here
FINNHUB_KEY=your_key_here

# Data Storage
DATA_PATH=./data

# Model Settings
MAX_PREDICTION_TIMEOUT=600  # seconds
CACHE_TTL=300  # seconds
```

---

## 🔍 Section 2: Structured Logging & Monitoring

**Current Issue**: Random print statements scattered throughout; hard to debug.

**Implementation**: Create `algotrade_datascience/utils/logger.py`

```python
"""
Centralized logging configuration
Provides structured logging across the entire application
"""
import logging
import json
from datetime import datetime
from pathlib import Path

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(name: str):
    """
    Get or create a logger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Starting process", extra={"ticker": "AAPL"})
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:  # Already configured
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console Handler (Pretty format for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File Handler (JSON format for production parsing)
    log_file = Path("logs/finadvice.log")
    log_file.parent.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

**Usage throughout codebase**:

```python
from algotrade_datascience.utils.logger import get_logger

logger = get_logger(__name__)

# Instead of: print("Starting ML pipeline...")
logger.info("Starting ML pipeline", extra={"ticker": "AAPL", "horizon": 60})

# Instead of: print(f"Error: {e}")
logger.error("Failed to fetch data", exc_info=True, extra={"ticker": "AAPL"})

# Success tracking
logger.info("Prediction completed", extra={
    "ticker": "AAPL",
    "status": "success",
    "model_winner": "XGBoost",
    "confidence": 75.3
})
```

---

## ✅ Section 3: Unit Testing Framework

**Current Issue**: `/tests` folder is empty - no coverage.

**Create test structure**:

```
tests/
├── __init__.py
├── conftest.py                      # Pytest configuration
├── unit/
│   ├── __init__.py
│   ├── test_validators.py
│   ├── test_data_fetcher.py
│   ├── test_sentiment_analysis.py
│   └── test_ml_pipeline.py
├── integration/
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   └── test_full_pipeline.py
└── fixtures/
    ├── sample_ticker_data.csv
    ├── sample_news.json
    └── sample_predictions.json
```

**Create tests/conftest.py**:

```python
"""
Pytest configuration and shared fixtures
"""
import pytest
import json
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_ticker_data():
    """Sample OHLCV data for testing"""
    return pd.DataFrame({
        'Date': pd.date_range('2025-01-01', periods=100),
        'Open': [150 + i*0.5 for i in range(100)],
        'High': [152 + i*0.5 for i in range(100)],
        'Low': [148 + i*0.5 for i in range(100)],
        'Close': [151 + i*0.5 for i in range(100)],
        'Volume': [1000000 + i*10000 for i in range(100)],
    })

@pytest.fixture
def sample_news():
    """Sample news articles for sentiment testing"""
    return [
        {
            'title': 'Apple Stock Soars on Record Earnings',
            'publisher': 'Reuters',
            'link': 'https://example.com/1',
            'publish_time': '2025-02-01 10:00:00'
        },
        {
            'title': 'Tech Stocks Face Headwinds Amid Rate Hikes',
            'publisher': 'Bloomberg',
            'link': 'https://example.com/2',
            'publish_time': '2025-02-01 09:00:00'
        }
    ]

@pytest.fixture
def app_client():
    """Flask test client"""
    from dashboard_app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

**Create tests/unit/test_validators.py**:

```python
"""
Unit tests for input validators
"""
import pytest
from algotrade_datascience.utils.validators import (
    TickerValidator, HorizonValidator, RiskModeValidator
)

class TestTickerValidator:
    def test_valid_stock_ticker(self):
        is_valid, msg = TickerValidator.validate("AAPL")
        assert is_valid is True
        assert msg == ""
    
    def test_valid_crypto_ticker(self):
        is_valid, msg = TickerValidator.validate("BTC-USD")
        assert is_valid is True
    
    def test_invalid_length(self):
        is_valid, msg = TickerValidator.validate("A" * 15)
        assert is_valid is False
        assert "characters" in msg
    
    def test_invalid_characters(self):
        is_valid, msg = TickerValidator.validate("APP;LE")
        assert is_valid is False
    
    def test_path_traversal_attempt(self):
        is_valid, msg = TickerValidator.validate("../../../etc/passwd")
        assert is_valid is False

class TestHorizonValidator:
    def test_valid_horizon(self):
        is_valid, msg = HorizonValidator.validate(60)
        assert is_valid is True
    
    def test_horizon_too_small(self):
        is_valid, msg = HorizonValidator.validate(0)
        assert is_valid is False
    
    def test_horizon_too_large(self):
        is_valid, msg = HorizonValidator.validate(1000)
        assert is_valid is False

class TestRiskModeValidator:
    @pytest.mark.parametrize("mode", ["conservative", "aggressive", "balanced"])
    def test_valid_modes(self, mode):
        is_valid, msg = RiskModeValidator.validate(mode)
        assert is_valid is True
    
    def test_invalid_mode(self):
        is_valid, msg = RiskModeValidator.validate("ultra_aggressive")
        assert is_valid is False
```

**Create tests/integration/test_api_endpoints.py**:

```python
"""
Integration tests for Flask API endpoints
"""
import pytest
import json

class TestAPIEndpoints:
    def test_get_tickers(self, app_client):
        """Test /api/tickers returns list"""
        response = app_client.get('/api/tickers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_run_ml_with_invalid_ticker(self, app_client):
        """Test /api/run_ml rejects invalid ticker"""
        response = app_client.post('/api/run_ml', 
            json={"ticker": "INVALID;;;", "horizon": 60, "risk": "conservative"}
        )
        assert response.status_code == 400
    
    def test_run_ml_with_valid_inputs(self, app_client):
        """Test /api/run_ml accepts valid inputs"""
        response = app_client.post('/api/run_ml',
            json={"ticker": "AAPL", "horizon": 60, "risk": "conservative"}
        )
        # Should succeed or timeout gracefully
        assert response.status_code in [200, 408]
```

**Run tests**:

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=algotrade_datascience tests/

# Run specific test file
pytest tests/unit/test_validators.py -v
```

---

## 📊 Section 4: Error Handling & User Feedback

**Current Issue**: API returns confusing errors; frontend doesn't show error states.

**Create unified error response format**:

```python
# algotrade_datascience/utils/errors.py
class APIError(Exception):
    """Base API error"""
    def __init__(self, message, code=500, user_message=None):
        self.message = message
        self.code = code
        self.user_message = user_message or message
        super().__init__(self.message)

class ValidationError(APIError):
    def __init__(self, message):
        super().__init__(message, 400, message)

class NotFoundError(APIError):
    def __init__(self, resource):
        super().__init__(f"{resource} not found", 404, f"Could not find {resource}")

class TimeoutError(APIError):
    def __init__(self):
        super().__init__("Operation timed out", 408, 
                        "Prediction took too long. Please try again.")

class ExternalServiceError(APIError):
    def __init__(self, service):
        super().__init__(f"{service} failed", 503,
                        f"Unable to reach {service}. Please try again later.")
```

**Consistent response format in dashboard_app.py**:

```python
@app.errorhandler(APIError)
def handle_api_error(error):
    """Return consistent error response"""
    response = {
        "status": "error",
        "code": error.code,
        "message": error.user_message,
        "debug": error.message if DEBUG else None
    }
    return jsonify(response), error.code

# Example usage
@app.route("/api/run_ml", methods=["POST"])
@limiter.limit("20 per hour")
def run_ml():
    data = request.json or {}
    ticker = data.get("ticker", "").upper()
    
    # Validate
    is_valid, msg = TickerValidator.validate(ticker)
    if not is_valid:
        raise ValidationError(msg)
    
    try:
        result = subprocess.run(cmd, timeout=600)
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.TimeoutExpired:
        raise TimeoutError()
    except Exception as e:
        logger.error("ML pipeline failed", exc_info=True)
        raise APIError(str(e), 500, "Prediction failed. Please check logs.")
```

**Update frontend to show errors** (in `frontend/js/script.js`):

```javascript
async function runML() {
    showLoading("Running prediction...");
    
    try {
        const response = await fetch('/api/run_ml', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker: currentTicker,
                horizon: parseInt(document.getElementById('param-horizon').value),
                risk: document.getElementById('param-risk').value
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Show error to user
            showError(data.message || "Prediction failed");
            addToConsole(`❌ Error: ${data.message}`);
            return;
        }
        
        addToConsole(`✅ Success: ${data.output}`);
        await loadResults();
        
    } catch (error) {
        showError("Network error: " + error.message);
        addToConsole(`❌ Network Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;
    document.body.insertBefore(errorDiv, document.body.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => errorDiv.remove(), 5000);
}
```

**Add CSS for error display** (in `frontend/css/style.css`):

```css
.error-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(239, 68, 68, 0.95);
    color: white;
    padding: 16px 20px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
    backdrop-filter: blur(10px);
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

---

# CODE QUALITY & PRODUCTION-READY

## 🧹 Section 5: Code Organization & Configuration

### 5.1 Environment-Based Configuration

**Create `algotrade_datascience/config/settings.py`**:

```python
"""
Environment-aware configuration
Load from .env file and fallback to defaults
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_file)

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # API
    MAX_TIMEOUT = int(os.getenv("MAX_PREDICTION_TIMEOUT", 600))
    CACHE_TTL = int(os.getenv("CACHE_TTL", 300))
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True") == "True"
    
    # ML
    RANDOM_STATE = 42
    TEST_SIZE = 0.2
    VALIDATION_SIZE = 0.1
    
    # Sentiment Analysis
    SENTIMENT_MODEL = "ProsusAI/finbert"
    NEWS_CACHE_HOURS = 24
    
    # External APIs
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", None)
    FINNHUB_KEY = os.getenv("FINNHUB_KEY", None)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    RATE_LIMIT_ENABLED = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    RATE_LIMIT_ENABLED = False


# Load config based on environment
def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Make available globally
config = get_config()
```

**Update dashboard_app.py**:

```python
from algotrade_datascience.config.settings import config

app = Flask(__name__, 
            static_folder='frontend',
            static_url_path='',
            template_folder='frontend')

app.config['DEBUG'] = config.DEBUG
app.config['TESTING'] = config.TESTING

# Use config throughout app
if config.RATE_LIMIT_ENABLED:
    limiter = Limiter(...)  # Apply rate limiting
```

---

### 5.2 Directory Structure Reorganization

**Proposed new structure**:

```
finAdvice/
├── algotrade_datascience/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # NEW: Environment config
│   │   └── constants.py             # NEW: Magic numbers
│   ├── core/                        # Data fetching
│   ├── features/                    # Feature engineering
│   ├── models/                      # ML models
│   │   ├── baseline_models.py
│   │   ├── sentiment_models.py
│   │   └── ensemble.py              # Model combination logic
│   ├── services/                    # NEW: Business logic
│   │   ├── __init__.py
│   │   ├── prediction_service.py    # Orchestrates prediction pipeline
│   │   ├── sentiment_service.py     # Wraps sentiment analysis
│   │   └── cache_service.py         # NEW: Cache management
│   ├── utils/                       # NEW: Utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── errors.py
│   ├── main_data_pipeline.py
│   ├── decision_making_ml.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── analytics.html
│   ├── css/
│   └── js/
├── tests/                           # NEW: Comprehensive testing
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                            # Documentation
├── logs/                            # NEW: Application logs
├── .env.example
├── .env.production                  # Template for production
├── dashboard_app.py
├── docker-compose.yml               # NEW: Docker setup
├── Dockerfile                       # NEW: Docker setup
├── requirements-dev.txt             # NEW: Dev dependencies
└── README.md
```

---

### 5.3 Update requirements.txt with Versions

**Create updated `requirements.txt`**:

```
# Core Framework
Flask==3.0.0
Werkzeug==3.0.0
python-dotenv==1.0.0

# Data & ML
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.3.2
xgboost==2.0.3

# NLP & Sentiment (for current + future enhancements)
transformers==4.35.2
torch==2.1.1
nltk==3.8.1

# Data Fetching
yfinance==0.2.37
requests==2.31.0
beautifulsoup4==4.12.2

# API Management
Flask-Limiter==3.5.0
Flask-CORS==4.0.0

# Utilities
python-dateutil==2.8.2
schedule==1.2.0

# Production
gunicorn==21.2.0

# Optional: For future dashboard enhancements
# plotly==5.18.0
# dash==2.14.1
```

**Create `requirements-dev.txt`**:

```
-r requirements.txt

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
flake8==6.1.0
black==23.12.0
isort==5.13.2
pylint==3.0.3

# Type Checking
mypy==1.7.1

# Development
ipython==8.18.1
jupyter==1.0.0
```

---

# FUTURE FEATURE ROADMAP

## 🚀 Section 6: Advanced NLP & News Intelligence

### 6.1 Multi-Source News Aggregation & Economic Intelligence

**Feature Overview**: Extend beyond simple news headlines to include:
- Economic reports (Fed statements, inflation data, employment reports)
- Earnings transcripts & interviews
- Analyst reports
- Macroeconomic indicators

**Implementation Plan**:

**Create `algotrade_datascience/features/nlp_engine.py`**:

```python
"""
Advanced NLP Engine for financial news & economic data
Supports multiple data sources and sentiment analysis types
"""
from typing import Dict, List
from datetime import datetime
from enum import Enum
from algotrade_datascience.utils.logger import get_logger

logger = get_logger(__name__)

class NewsSourceType(Enum):
    """Types of news sources"""
    GENERAL_NEWS = "general_news"          # Reuters, Bloomberg, CNBC
    EARNINGS = "earnings"                  # Earnings calls
    ECONOMIC_REPORTS = "economic_reports"  # Fed, BLS, IMF
    INTERVIEWS = "interviews"              # CEO interviews, analyst calls
    REGULATORY = "regulatory"              # SEC filings, regulations
    RESEARCH = "research"                  # Analyst reports, research


class SentimentType(Enum):
    """Types of sentiment analysis"""
    PRICE_SENTIMENT = "price_sentiment"           # Will price go up/down
    VOLATILITY_SENTIMENT = "volatility_sentiment" # Will volatility increase
    CONFIDENCE_SENTIMENT = "confidence_sentiment" # Overall market confidence


class NewsArticle:
    """Structured news article with metadata"""
    
    def __init__(self, 
                 title: str,
                 content: str,
                 publisher: str,
                 publish_time: datetime,
                 source_type: NewsSourceType,
                 tickers: List[str],
                 url: str):
        self.title = title
        self.content = content
        self.publisher = publisher
        self.publish_time = publish_time
        self.source_type = source_type
        self.tickers = tickers
        self.url = url
        self.sentiment_scores = {}  # Will store multiple sentiment types
        self.importance_score = 0.0  # 0-1, based on relevance & recency


class AdvancedNLPEngine:
    """
    Multi-source NLP analysis engine
    
    Usage:
        nlp = AdvancedNLPEngine()
        articles = await nlp.fetch_news_multi_source("AAPL")
        sentiment = nlp.analyze_sentiment(articles)
    """
    
    def __init__(self):
        self.price_sentiment_model = "ProsusAI/finbert"
        self.volatility_model = "yiyanghkust/finbert-fls"  # For volatility
        self.source_weights = {
            NewsSourceType.ECONOMIC_REPORTS: 0.8,   # Very important
            NewsSourceType.EARNINGS: 0.7,
            NewsSourceType.GENERAL_NEWS: 0.4,
            NewsSourceType.RESEARCH: 0.6,
            NewsSourceType.INTERVIEWS: 0.5,
        }
    
    async def fetch_news_multi_source(self, ticker: str) -> List[NewsArticle]:
        """
        Fetch news from multiple sources
        
        Sources:
        1. NewsAPI - General news
        2. Finnhub - Economic calendar, earnings
        3. SEC Edgar - Regulatory filings
        4. Custom: Earnings transcript APIs
        
        Returns:
            List of NewsArticle objects enriched with source type
        """
        logger.info(f"Fetching multi-source news for {ticker}")
        
        articles = []
        
        # Fetch from each source in parallel
        general_news = await self._fetch_newsapi(ticker)
        earnings_calls = await self._fetch_earnings(ticker)
        economic_data = await self._fetch_economic_calendar()
        regulatory_filings = await self._fetch_sec_filings(ticker)
        
        articles.extend(general_news)
        articles.extend(earnings_calls)
        articles.extend(economic_data)
        articles.extend(regulatory_filings)
        
        return sorted(articles, key=lambda x: x.publish_time, reverse=True)
    
    async def _fetch_newsapi(self, ticker: str) -> List[NewsArticle]:
        """Fetch from NewsAPI (general news)"""
        # Implementation here
        pass
    
    async def _fetch_earnings(self, ticker: str) -> List[NewsArticle]:
        """Fetch earnings transcripts from Finnhub/Seeking Alpha"""
        # Implementation here
        pass
    
    async def _fetch_economic_calendar(self) -> List[NewsArticle]:
        """Fetch economic events (Fed, inflation, employment)"""
        # Implementation here
        pass
    
    async def _fetch_sec_filings(self, ticker: str) -> List[NewsArticle]:
        """Fetch SEC filings (10-K, 10-Q, 8-K)"""
        # Implementation here
        pass
    
    def analyze_sentiment(self, articles: List[NewsArticle]) -> Dict:
        """
        Analyze sentiment across multiple dimensions
        
        Returns:
            {
                'price_sentiment': 'Bullish/Bearish/Neutral',
                'price_score': 0.75,  # -1 (bearish) to +1 (bullish)
                'volatility_sentiment': 'High/Normal/Low',
                'confidence': 0.82,
                'key_drivers': ['Fed rate cut', 'Earnings beat'],
                'sentiment_by_source': {
                    'earnings': 0.85,
                    'economic_reports': -0.2,
                    'general_news': 0.3
                }
            }
        """
        pass
    
    def extract_key_drivers(self, articles: List[NewsArticle], 
                           ticker: str) -> List[str]:
        """
        Extract main themes/drivers from news
        Uses NER (Named Entity Recognition) + keyword extraction
        
        Returns:
            ['Fed Rate Cut', 'Strong iPhone Sales', 'Supply Chain Recovery']
        """
        pass
```

---

### 6.2 Economic Calendar Integration

**Create `algotrade_datascience/features/economic_calendar.py`**:

```python
"""
Economic calendar integration
Tracks major economic events and their impact on markets
"""
from datetime import datetime
from typing import List, Dict
from enum import Enum

class EconomicEventType(Enum):
    """Major economic indicators"""
    FED_RATE_DECISION = "fed_rate_decision"
    CPI = "cpi"                              # Consumer Price Index
    UNEMPLOYMENT = "unemployment"             # Jobs report
    GDP = "gdp"
    INFLATION = "inflation"
    RETAIL_SALES = "retail_sales"
    HOUSING_STARTS = "housing_starts"
    EARNINGS_SEASON = "earnings_season"
    FOMC_MEETING = "fomc_meeting"


class EconomicEvent:
    """Represents an economic event with impact prediction"""
    
    def __init__(self,
                 event_type: EconomicEventType,
                 date: datetime,
                 actual: float = None,
                 forecast: float = None,
                 previous: float = None,
                 importance: str = 'Medium'):  # Low, Medium, High
        
        self.event_type = event_type
        self.date = date
        self.actual = actual
        self.forecast = forecast
        self.previous = previous
        self.importance = importance
        self.impact_on_stocks = self._calculate_impact()
    
    def _calculate_impact(self) -> Dict[str, float]:
        """
        Estimate impact on stocks based on actual vs forecast
        
        Returns:
            {
                'direction': -0.5,  # Negative is bearish
                'magnitude': 0.3,   # 0-1, how much will it move
                'volatility': 0.8   # Expected volatility increase
            }
        """
        if not self.actual or not self.forecast:
            return {'direction': 0, 'magnitude': 0.5, 'volatility': 0.5}
        
        # Calculate surprise (actual vs forecast)
        surprise = (self.actual - self.forecast) / self.forecast
        
        return {
            'direction': 1 if surprise > 0 else -1 * abs(surprise),
            'magnitude': min(abs(surprise), 1.0),
            'volatility': 0.5 + abs(surprise)
        }


class EconomicCalendar:
    """
    Tracks upcoming economic events
    Predicts their impact on specific stocks
    """
    
    # Mapping: which stocks are sensitive to which economic events
    STOCK_EVENT_SENSITIVITY = {
        'FED_RATE_DECISION': {
            'affected_sectors': ['Technology', 'Finance'],
            'inverse_correlation': True,  # Rate hike = stock decline
            'impact_multiplier': 2.0
        },
        'CPI': {
            'affected_sectors': ['Consumer', 'Energy'],
            'inverse_correlation': True,
            'impact_multiplier': 1.5
        },
        'UNEMPLOYMENT': {
            'affected_sectors': ['Consumer', 'Finance', 'Retail'],
            'inverse_correlation': False,  # High unemployment = bad
            'impact_multiplier': 1.3
        }
    }
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[EconomicEvent]:
        """Get economic events for next N days"""
        # Fetch from Investing.com API or similar
        pass
    
    def predict_stock_impact(self, ticker: str, 
                            event: EconomicEvent) -> Dict:
        """
        Predict how an economic event will impact a specific stock
        
        Returns:
            {
                'ticker': 'AAPL',
                'event': 'FED_RATE_DECISION',
                'predicted_direction': -0.3,  # Likely to go down
                'expected_volatility': 0.8,
                'reasoning': 'Tech stocks are sensitive to rate hikes'
            }
        """
        pass
```

---

## 💰 Section 7: Hedging Strategies & Correlation Analysis

### 7.1 Hedging Recommendations Engine

**Feature Overview**: Suggest hedging positions based on current holdings.

**Example**:
- If user holds AAPL (tech), recommend buying GLD (gold - inverse correlation)
- If user holds energy stocks, suggest buying bonds
- Calculate optimal hedge ratio

**Create `algotrade_datascience/features/hedging.py`**:

```python
"""
Hedging strategies engine
Recommends hedging positions based on correlation analysis
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

class HedgeType(Enum):
    """Types of hedges"""
    INVERSE_POSITION = "inverse_position"      # Short related asset
    UNCORRELATED = "uncorrelated"              # Buy uncorrelated asset
    SECTOR_HEDGE = "sector_hedge"              # Hedge sector risk
    VOLATILITY_HEDGE = "volatility_hedge"      # Buy VIX options


@dataclass
class HedgeRecommendation:
    """A suggested hedge position"""
    
    primary_asset: str                         # e.g., 'AAPL'
    hedge_asset: str                           # e.g., 'GLD'
    hedge_type: HedgeType
    
    correlation: float                         # -1 to +1 with primary
    recommended_ratio: float                   # % of portfolio to hedge
    
    max_loss_without_hedge: float             # $
    max_loss_with_hedge: float                # $
    
    reasoning: str                            # Why this hedge


class CorrelationMatrix:
    """
    Maintains correlation matrix between major assets
    Used for finding optimal hedges
    
    Note: Will be moved to database later for persistence
    """
    
    def __init__(self):
        # For now, store in memory; will move to DB later
        self.correlation_data = {}
        self.last_updated = None
        self.lookback_periods = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365
        }
    
    def calculate_correlations(self, tickers: List[str], 
                              period: str = '1y') -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for list of tickers
        
        Returns:
            {
                'AAPL': {'GLD': -0.15, 'TSLA': 0.82, 'BND': 0.05},
                'GLD': {'AAPL': -0.15, 'TSLA': -0.10, 'BND': 0.60},
                ...
            }
        """
        pass
    
    def find_uncorrelated_assets(self, ticker: str, 
                                threshold: float = 0.3) -> List[str]:
        """
        Find assets with low correlation to given ticker
        These make good hedges
        """
        pass
    
    def find_inverse_assets(self, ticker: str,
                           threshold: float = -0.5) -> List[str]:
        """
        Find assets that move opposite to given ticker
        Best hedges
        """
        pass


class HedgingEngine:
    """
    Main hedging recommendation engine
    """
    
    # Asset classes and their correlations
    TRADITIONAL_HEDGES = {
        'stocks': {
            'gold': -0.15,              # Slightly inverse
            'bonds': -0.25,             # Somewhat inverse
            'vix': -0.80                # Highly inverse
        },
        'tech': {
            'gold': -0.20,
            'utilities': -0.30,         # Defensive sector
            'bonds': -0.35,
            'commodities': -0.10
        },
        'energy': {
            'tech': -0.40,              # Different sector
            'bonds': -0.05,
            'renewables': -0.60         # Inverse in future
        }
    }
    
    def recommend_hedge(self, ticker: str, 
                       position_size: float = 10000) -> List[HedgeRecommendation]:
        """
        Recommend hedges for a position
        
        Args:
            ticker: Asset to hedge (e.g., 'AAPL')
            position_size: Amount invested ($)
        
        Returns:
            List of hedge recommendations, ranked by effectiveness
        """
        logger.info(f"Generating hedge recommendations for {ticker}")
        
        recommendations = []
        
        # Strategy 1: Find inverse correlation assets
        inverse_assets = self._find_inverse_correlations(ticker)
        for hedge_ticker, correlation in inverse_assets:
            rec = HedgeRecommendation(
                primary_asset=ticker,
                hedge_asset=hedge_ticker,
                hedge_type=HedgeType.INVERSE_POSITION,
                correlation=correlation,
                recommended_ratio=self._calculate_hedge_ratio(correlation),
                max_loss_without_hedge=position_size * 0.2,  # 20% loss
                max_loss_with_hedge=position_size * 0.1,     # 10% loss
                reasoning=f"{hedge_ticker} historically moves opposite to {ticker}"
            )
            recommendations.append(rec)
        
        # Strategy 2: Find uncorrelated assets (diversification)
        uncorrelated = self._find_uncorrelated_assets(ticker)
        for hedge_ticker, correlation in uncorrelated:
            rec = HedgeRecommendation(
                primary_asset=ticker,
                hedge_asset=hedge_ticker,
                hedge_type=HedgeType.UNCORRELATED,
                correlation=correlation,
                recommended_ratio=0.1,  # Small allocation
                max_loss_without_hedge=position_size * 0.2,
                max_loss_with_hedge=position_size * 0.15,
                reasoning=f"{hedge_ticker} is independent of {ticker} movements"
            )
            recommendations.append(rec)
        
        # Strategy 3: Sector hedge
        sector_hedge = self._find_sector_hedge(ticker)
        if sector_hedge:
            rec = HedgeRecommendation(
                primary_asset=ticker,
                hedge_asset=sector_hedge,
                hedge_type=HedgeType.SECTOR_HEDGE,
                correlation=-0.4,
                recommended_ratio=0.2,
                max_loss_without_hedge=position_size * 0.2,
                max_loss_with_hedge=position_size * 0.12,
                reasoning=f"Defensive sector hedge"
            )
            recommendations.append(rec)
        
        # Sort by effectiveness
        return sorted(recommendations, 
                     key=lambda x: abs(x.correlation), 
                     reverse=True)
    
    def _find_inverse_correlations(self, ticker: str) -> List[Tuple[str, float]]:
        """Find assets with negative correlation"""
        pass
    
    def _find_uncorrelated_assets(self, ticker: str) -> List[Tuple[str, float]]:
        """Find assets with ~0 correlation"""
        pass
    
    def _find_sector_hedge(self, ticker: str) -> str:
        """Find defensive sector to hedge with"""
        pass
    
    def _calculate_hedge_ratio(self, correlation: float) -> float:
        """
        Calculate optimal hedge ratio based on correlation
        
        Formula: ratio = -correlation
        If AAPL and GLD have -0.15 correlation, hedge 15% of position
        """
        return abs(correlation)  # Simplified
```

**Integration in frontend** (show in results):

```python
# In decision_making_ml.py, after generating prediction:

hedging_engine = HedgingEngine()
hedge_recommendations = hedging_engine.recommend_hedge(
    ticker=ticker,
    position_size=10000  # Example
)

# Add to decision JSON
decision_data['hedging_strategy'] = {
    'recommendations': [
        {
            'hedge_asset': rec.hedge_asset,
            'correlation': rec.correlation,
            'hedge_ratio': rec.recommended_ratio,
            'reasoning': rec.reasoning
        } for rec in hedge_recommendations
    ]
}
```

---

### 7.2 Correlation Analysis Dashboard

**New API endpoint**:

```python
@app.route("/api/correlation/<ticker>")
def get_correlation_analysis(ticker):
    """Get correlation matrix for selected ticker"""
    try:
        correlations = correlation_service.get_correlations_for_ticker(ticker)
        return jsonify({
            'ticker': ticker,
            'correlations': correlations,
            'updated_at': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Correlation analysis failed", exc_info=True)
        return jsonify({"error": str(e)}), 500
```

**Frontend visualization** (add new panel):

```html
<div class="panel glass correlations">
    <h3><i class="fas fa-link"></i> Stock Correlations</h3>
    <div id="correlation-chart">
        <!-- Interactive correlation heatmap -->
    </div>
    <div class="correlation-details">
        <p><strong>Strongest Correlation:</strong> <span id="strongest">---</span></p>
        <p><strong>Best Hedge:</strong> <span id="best-hedge">---</span></p>
    </div>
</div>
```

---

## 📈 Section 8: Slowly Changing Window & Historical Tracking

### 8.1 Slowly Changing Window (SCD) Architecture

**Feature Overview**: Instead of overwriting data, maintain historical versions.

**Create `algotrade_datascience/features/slowly_changing_dimension.py`**:

```python
"""
Slowly Changing Dimension (SCD) implementation
Tracks how model predictions change over time without overwriting history

This prepares the codebase for database migration later.
Current: JSON files with version tracking
Future: Database with SCD Type 2 pattern
"""
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import json
from algotrade_datascience.utils.logger import get_logger

logger = get_logger(__name__)

class SlowlyChangingWindow:
    """
    SCD Type 2: Maintain full history of predictions
    
    Example:
    Prediction for AAPL on 2025-02-01:
    {
        'version': 1,
        'ticker': 'AAPL',
        'prediction_date': '2025-02-01',
        'buy_target': 180.5,
        'sell_target': 195.0,
        'confidence': 0.75,
        'active': True,
        'created_at': '2025-02-01 10:30:00',
        'updated_at': '2025-02-01 10:30:00'
    }
    
    Next day, new prediction replaces it:
    {
        'version': 2,
        'ticker': 'AAPL',
        'prediction_date': '2025-02-02',
        'buy_target': 182.0,
        'sell_target': 197.0,
        'confidence': 0.82,
        'active': True,
        'created_at': '2025-02-02 10:25:00',
        'updated_at': '2025-02-02 10:25:00',
        'superseded_by': 2
    }
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data/predictions_history")
        self.data_dir.mkdir(exist_ok=True)
    
    def save_prediction_version(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save prediction with version tracking
        
        Returns:
            Prediction with version metadata added
        """
        ticker = prediction['ticker']
        version_file = self.data_dir / f"{ticker}_versions.jsonl"
        
        # Add metadata
        versioned_prediction = {
            **prediction,
            'version': self._get_next_version(ticker),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'active': True
        }
        
        # Append to versioned history (JSONL format - one JSON per line)
        with open(version_file, 'a') as f:
            f.write(json.dumps(versioned_prediction) + '\n')
        
        logger.info(f"Saved prediction v{versioned_prediction['version']} for {ticker}")
        
        return versioned_prediction
    
    def get_prediction_history(self, ticker: str, limit: int = 30) -> List[Dict]:
        """Get last N predictions for ticker"""
        version_file = self.data_dir / f"{ticker}_versions.jsonl"
        
        if not version_file.exists():
            return []
        
        predictions = []
        with open(version_file, 'r') as f:
            for line in f:
                if line.strip():
                    predictions.append(json.loads(line))
        
        # Return last N (most recent first)
        return sorted(predictions, key=lambda x: x['version'], reverse=True)[:limit]
    
    def get_prediction_timeline(self, ticker: str) -> List[Dict]:
        """
        Get prediction timeline - how predictions have changed
        
        Returns:
            [
                {'date': '2025-01-01', 'buy_target': 180, 'confidence': 0.7},
                {'date': '2025-01-02', 'buy_target': 182, 'confidence': 0.75},
                ...
            ]
        """
        history = self.get_prediction_history(ticker, limit=None)
        
        return [
            {
                'date': pred.get('prediction_date', pred.get('created_at')),
                'buy_target': pred.get('buy_target'),
                'sell_target': pred.get('sell_target'),
                'confidence': pred.get('confidence'),
                'model_winner': pred.get('model_winner'),
                'version': pred.get('version')
            }
            for pred in reversed(history)  # Oldest first
        ]
    
    def compare_predictions(self, ticker: str, 
                           version1: int, 
                           version2: int) -> Dict:
        """
        Compare two versions of predictions
        
        Returns:
            {
                'ticker': 'AAPL',
                'version1': {...},
                'version2': {...},
                'changes': {
                    'buy_target_change': 2.5,
                    'confidence_change': 0.05,
                    'model_change': 'XGBoost -> Random Forest'
                }
            }
        """
        pass
    
    def _get_next_version(self, ticker: str) -> int:
        """Get next version number for ticker"""
        version_file = self.data_dir / f"{ticker}_versions.jsonl"
        
        if not version_file.exists():
            return 1
        
        with open(version_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return 1
            
            last_line = json.loads(lines[-1])
            return last_line.get('version', 0) + 1


class PredictionAccuracy:
    """
    Track prediction accuracy over time
    Calculate how often predictions were correct
    
    Note: Requires database later for storing actual vs predicted values
    Current: Simple file-based tracking
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data/accuracy_tracking")
        self.data_dir.mkdir(exist_ok=True)
    
    def record_prediction_outcome(self, ticker: str, 
                                  version: int,
                                  buy_target: float,
                                  sell_target: float,
                                  actual_price: float,
                                  outcome: str):  # 'hit', 'partial', 'miss'
        """
        Record whether a prediction was correct
        
        Example:
            engine.record_outcome('AAPL', 5, 180.5, 195.0, 193.2, 'partial')
            # Predicted 195, actually hit 193.2 = 99% of target
        """
        tracking_file = self.data_dir / f"{ticker}_outcomes.jsonl"
        
        record = {
            'ticker': ticker,
            'version': version,
            'buy_target': buy_target,
            'sell_target': sell_target,
            'actual_price': actual_price,
            'outcome': outcome,
            'accuracy_pct': (actual_price / sell_target) * 100,
            'recorded_at': datetime.now().isoformat()
        }
        
        with open(tracking_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
    
    def get_accuracy_stats(self, ticker: str) -> Dict:
        """
        Calculate accuracy statistics
        
        Returns:
            {
                'ticker': 'AAPL',
                'total_predictions': 30,
                'hit_rate': 0.63,
                'partial_rate': 0.27,
                'miss_rate': 0.10,
                'avg_accuracy': 0.82  # Of partial/hit predictions
            }
        """
        tracking_file = self.data_dir / f"{ticker}_outcomes.jsonl"
        
        if not tracking_file.exists():
            return {}
        
        outcomes = []
        with open(tracking_file, 'r') as f:
            for line in f:
                if line.strip():
                    outcomes.append(json.loads(line))
        
        total = len(outcomes)
        if total == 0:
            return {}
        
        hits = len([o for o in outcomes if o['outcome'] == 'hit'])
        partials = len([o for o in outcomes if o['outcome'] == 'partial'])
        
        return {
            'ticker': ticker,
            'total_predictions': total,
            'hit_rate': hits / total,
            'partial_rate': partials / total,
            'miss_rate': (total - hits - partials) / total,
            'avg_accuracy': sum([o.get('accuracy_pct', 0) 
                               for o in outcomes if o['outcome'] != 'miss']) / max(hits + partials, 1)
        }
```

**API endpoints for historical tracking**:

```python
@app.route("/api/prediction_history/<ticker>")
def get_prediction_history(ticker):
    """Get timeline of predictions for a ticker"""
    try:
        scd = SlowlyChangingWindow()
        timeline = scd.get_prediction_timeline(ticker)
        return jsonify({
            'ticker': ticker,
            'timeline': timeline
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/accuracy_stats/<ticker>")
def get_accuracy_stats(ticker):
    """Get prediction accuracy statistics"""
    try:
        accuracy = PredictionAccuracy()
        stats = accuracy.get_accuracy_stats(ticker)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Frontend: Show prediction evolution**:

```html
<div class="panel glass prediction-history">
    <h3><i class="fas fa-history"></i> Prediction Evolution</h3>
    <canvas id="prediction-timeline"></canvas>
    <p class="info">Shows how buy/sell targets have changed over time</p>
</div>
```

---

# ARCHITECTURE RECOMMENDATIONS

## Section 9: Service Layer Architecture

To support upcoming features cleanly, introduce a **Service Layer**:

**Create `algotrade_datascience/services/prediction_service.py`**:

```python
"""
Prediction Service - Orchestrates entire prediction pipeline
Coordinates: Data fetching -> Feature engineering -> ML -> Hedging -> History tracking
"""
from typing import Dict, Any
from algotrade_datascience.utils.logger import get_logger
from algotrade_datascience.core.data_fetcher import DataFetcher
from algotrade_datascience.features.sentiment_analysis import SentimentProcessor
from algotrade_datascience.features.nlp_engine import AdvancedNLPEngine
from algotrade_datascience.features.hedging import HedgingEngine
from algotrade_datascience.features.slowly_changing_dimension import SlowlyChangingWindow
from algotrade_datascience.baseline_models import BaselineModels

logger = get_logger(__name__)

class PredictionService:
    """
    High-level service that orchestrates prediction pipeline
    
    Usage:
        service = PredictionService()
        result = service.predict(
            ticker="AAPL",
            horizon=60,
            risk="conservative",
            include_hedges=True,
            include_sentiment=True
        )
    """
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.sentiment_processor = SentimentProcessor()
        self.nlp_engine = AdvancedNLPEngine()
        self.hedging_engine = HedgingEngine()
        self.ml_models = BaselineModels()
        self.scd = SlowlyChangingWindow()
    
    async def predict(self, 
                     ticker: str,
                     horizon: int = 60,
                     risk: str = "conservative",
                     include_hedges: bool = True,
                     include_sentiment: bool = True,
                     include_correlations: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive prediction
        
        Args:
            ticker: Asset to predict
            horizon: Days ahead to predict
            risk: 'conservative' or 'aggressive'
            include_hedges: Add hedging recommendations
            include_sentiment: Add sentiment analysis
            include_correlations: Add correlation matrix
        
        Returns:
            Complete prediction with all requested components
        """
        logger.info(f"Starting prediction for {ticker}")
        
        # Step 1: Fetch data
        logger.info("Step 1: Fetching data...")
        data = self.data_fetcher.fetch_ticker_data(ticker)
        
        # Step 2: ML Prediction
        logger.info("Step 2: Running ML models...")
        ml_results = self.ml_models.predict(ticker, data, horizon, risk)
        
        # Step 3: Sentiment Analysis
        sentiment_results = {}
        if include_sentiment:
            logger.info("Step 3a: Basic sentiment...")
            sentiment_results['basic'] = self.sentiment_processor.analyze(ticker)
            
            logger.info("Step 3b: Advanced NLP...")
            nlp_results = await self.nlp_engine.fetch_news_multi_source(ticker)
            sentiment_results['advanced'] = self.nlp_engine.analyze_sentiment(nlp_results)
        
        # Step 4: Hedging
        hedge_results = {}
        if include_hedges:
            logger.info("Step 4: Generating hedges...")
            hedge_results = self.hedging_engine.recommend_hedge(ticker)
        
        # Step 5: Compile results
        prediction = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'ml_prediction': ml_results,
            'sentiment': sentiment_results,
            'hedging': hedge_results,
        }
        
        # Step 6: Save to history (SCD)
        self.scd.save_prediction_version(prediction)
        
        logger.info(f"Prediction complete for {ticker}")
        return prediction
```

---

# IMPLEMENTATION TIMELINE

## Phase 1 (Next 2 Weeks) - Foundation
- [ ] Input validation (Section 1.1)
- [ ] Rate limiting (Section 1.2)
- [ ] Logging system (Section 2)
- [ ] Basic unit tests (Section 3)
- [ ] Error handling (Section 4)
- [ ] Environment config (Section 5.1)
- [ ] Update requirements.txt (Section 5.3)

## Phase 2 (Weeks 3-4) - NLP Enhancement
- [ ] Multi-source news aggregation (Section 6.1)
- [ ] Economic calendar integration (Section 6.2)
- [ ] Advanced sentiment analysis
- [ ] Frontend: Show economic events

## Phase 3 (Weeks 5-6) - Hedging & Correlation
- [ ] Correlation analysis engine (Section 7.1)
- [ ] Hedging recommendations (Section 7.1)
- [ ] Correlation dashboard (Section 7.2)
- [ ] Frontend: Correlation matrix visualization

## Phase 4 (Weeks 7-8) - Historical Tracking
- [ ] Slowly Changing Window implementation (Section 8.1)
- [ ] Prediction accuracy tracking
- [ ] Historical timeline API
- [ ] Frontend: Prediction evolution chart

## Phase 5 (Future) - Database Migration
- [ ] Switch from JSON to SQLite/PostgreSQL
- [ ] Migrate SCD to database
- [ ] Add query optimization
- [ ] Enable advanced analytics

---

## Summary Table

| Feature | Priority | Effort | Impact | Timeline |
|---------|----------|--------|--------|----------|
| Input Validation | Critical | 2h | High | Week 1 |
| Rate Limiting | Critical | 1h | High | Week 1 |
| Logging | High | 3h | Medium | Week 1 |
| Unit Tests | High | 8h | High | Week 2 |
| NLP Engine | Medium | 16h | High | Week 3 |
| Hedging Engine | Medium | 12h | High | Week 5 |
| Correlation Analysis | Medium | 10h | Medium | Week 5 |
| SCD Implementation | Low | 8h | Medium | Week 7 |
| Database Migration | Low | 20h | High | Future |

---

**End of Document**

This roadmap provides:
1. ✅ Immediate fixes (security, logging, testing)
2. ✅ Code quality improvements
3. ✅ Detailed future features with implementation guides
4. ✅ Clear timeline and prioritization
5. ✅ Foundation for database migration (but not doing it now)

Happy building! 🚀
