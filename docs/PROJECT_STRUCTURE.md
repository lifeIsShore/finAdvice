# Project Structure

This document provides a complete overview of the FinAdvice project directory structure.

---

## Complete Directory Tree

```markdown
finAdvice/
│
├── README.md                                    # Project overview and quick start
├── LICENSE                                      # MIT License
├── .gitignore                                   # Git ignore rules
├── dashboard_app.py                             # Main Flask API & Server
├── start_ui.bat                                 # Shortcut to open local UI
├── PROJECT_STABILITY_RULES.md                   # Development stability rules
│
├── docs/                                        # Documentation
│   ├── ARCHITECTURE.md                          # System architecture and design
│   ├── API.md                                   # API documentation
│   ├── CONTRIBUTING.md                          # Contribution guidelines
│   ├── CHANGELOG.md                             # Version history and changes
│   ├── INDEX.md                                 # Documentation entry point
│   ├── PROJECT_STRUCTURE.md                     # This file
│   └── user-stories.json                        # Complete user stories
│
├── frontend/                                    # New Decoupled Frontend
│   ├── index.html                               # Main Dashboard UI
│   ├── analytics.html                           # Model Diagnostics UI
│   ├── css/                                     # Stylesheets
│   ├── js/                                      # Frontend Logic
│   └── assets/                                  # Static media (bg.png, etc.)
│
├── algotrade_datascience/                       # Main application directory
│   ├── core/                                    # Data fetching & storage
│   ├── features/                                # Feature engineering
│   ├── modeling/                                # ML modeling
│   ├── orchestration/                           # Pipeline orchestration
│   ├── visualization/                           # Plotting utilities
│   ├── utils/                                   # General utilities
│   ├── requirements.txt                         # Dependencies
│   ├── config.py                                # System configuration
│   ├── consensus_engine.py                      # Multi-timeframe logic
│   ├── baseline_models.py                       # ML comparison logic
│   └── decision_making_ml.py                    # Core prediction brain
│
├── data/                                        # Persistent data storage
│   ├── raw/                                     # Historical price data
│   ├── decisions/                               # ML prediction results
│   ├── model_diagnostics/                       # Detailed model stats
│   ├── news/                                    # Cached sentiment data
│   └── metadata.json                            # Data fetch logs
│
├── archive/                                     # Historical & unused files
│
└── tests/                                       # Test suite
```

---

## Directory Descriptions

### Root Level
- **`dashboard_app.py`**: The central Flask server that provides the API and serves the frontend.
- **`start_ui.bat`**: A simple windows batch script to open the dashboard.
- **`user-stories.json`**: Documentation of the features and requirements driving the project.

### `frontend/` (The UI Layer)
Decoupled HTML/CSS/JS application that communicates with the Flask API.
- **`index.html`**: The main command center and price dashboard.
- **`analytics.html`**: Specialized view for deep model performance metrics.
- **`js/script.js`**: Core logic for real-time updates and consensus visualization.
- **`js/analytics.js`**: specialized logic for rendering complex diagnostic charts.
- **`css/style.css`**: Design system including glassmorphism and enhanced tooltips.

### `algotrade_datascience/` (The Core Engine)
Python-based data science pipeline.
- **`core/`**: Market data ingestion and CSV persistence.
- **`features/`**: Signal engineering (Momentum, Volatility, Volume).
- **`modeling/`**: Machine learning model training and evaluation.
- **`consensus_engine.py`**: Aggregates multi-interval predictions.

### `data/` (Knowledge Base)
- **`raw/`**: Historical price data sorted by ticker.
- **`decisions/`**: Daily ML predictions and buy/sell targets.
- **`model_diagnostics/`**: Detailed ROC, Confusion Matrix, and SHAP data.
- **`news_cache/`**: Stored sentiment results from the News API.

---

**Last Updated**: February 2026  
**Version**: 2.0.0 (Decoupled Architecture)
