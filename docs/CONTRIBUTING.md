# Contributing to FinAdvice

Thank you for your interest in contributing to FinAdvice! This document provides guidelines and instructions for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We expect:

- **Respectful Communication**: Be kind and constructive in all interactions
- **Collaborative Spirit**: Help others learn and grow
- **Quality Focus**: Strive for excellence in code and documentation
- **Open Mindedness**: Be receptive to feedback and new ideas

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of algorithmic trading concepts
- Familiarity with pandas, numpy, and scikit-learn

### Setting Up Your Development Environment

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/finAdvice.git
cd finAdvice

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/finAdvice.git

# 4. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
cd algotrade_datascience
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 6. Verify installation
python test_pipeline.py
```

---

## 🔄 Development Workflow

### Branch Naming Convention

Use descriptive branch names following this pattern:

```
<type>/<short-description>

Examples:
- feature/add-rsi-indicator
- bugfix/fix-data-validation
- docs/update-readme
- refactor/optimize-data-fetcher
```

**Types:**
- `feature/` - New features or enhancements
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### Workflow Steps

```bash
# 1. Update your local main branch
git checkout main
git pull upstream main

# 2. Create a new branch
git checkout -b feature/your-feature-name

# 3. Make your changes
# ... edit files ...

# 4. Run tests
pytest tests/
python data_quality_checker.py

# 5. Commit your changes
git add .
git commit -m "feat: add RSI indicator calculation"

# 6. Push to your fork
git push origin feature/your-feature-name

# 7. Create a Pull Request on GitHub
```

---

## 📝 Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

#### General Guidelines

- **Line Length**: Maximum 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Use single quotes for strings unless double quotes avoid escaping
- **Imports**: Group in order: standard library, third-party, local

#### Example

```python
"""
Module for calculating technical indicators.

This module provides functions for computing various technical
indicators used in algorithmic trading.
"""

import logging
from typing import List, Dict, Optional, Union
from datetime import datetime

import pandas as pd
import numpy as np
import yfinance as yf

from config import TIMEFRAMES, QUALITY_THRESHOLDS


class IndicatorCalculator:
    """
    Calculate technical indicators for financial data.
    
    Attributes:
        data (pd.DataFrame): OHLCV data
        window_sizes (List[int]): Rolling window sizes to use
        
    Example:
        >>> calculator = IndicatorCalculator(data)
        >>> rsi = calculator.calculate_rsi(period=14)
    """
    
    def __init__(self, data: pd.DataFrame, window_sizes: Optional[List[int]] = None):
        """
        Initialize the indicator calculator.
        
        Args:
            data: DataFrame with OHLCV columns
            window_sizes: List of window sizes for rolling calculations
            
        Raises:
            ValueError: If data is missing required columns
        """
        self.data = data
        self.window_sizes = window_sizes or [5, 10, 20, 50, 100, 200]
        self._validate_data()
    
    def _validate_data(self) -> None:
        """Validate that required columns are present."""
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            period: Lookback period for RSI calculation
            
        Returns:
            Series containing RSI values (0-100)
            
        Example:
            >>> rsi = calculator.calculate_rsi(period=14)
            >>> print(rsi.tail())
        """
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
```

### Type Hints

Always use type hints for function parameters and return values:

```python
def fetch_data(ticker: str, interval: str, period: str) -> pd.DataFrame:
    """Fetch OHLCV data for a ticker."""
    pass

def validate_tickers(tickers: List[str]) -> Dict[str, bool]:
    """Validate a list of ticker symbols."""
    pass
```

### Docstrings

Use **Google-style docstrings**:

```python
def calculate_moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    Calculate simple moving average.
    
    Args:
        data: Price series to calculate MA on
        window: Number of periods for the moving average
        
    Returns:
        Series containing moving average values
        
    Raises:
        ValueError: If window is less than 1
        
    Example:
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> ma = calculate_moving_average(prices, window=3)
    """
    if window < 1:
        raise ValueError("Window must be at least 1")
    return data.rolling(window=window).mean()
```

### Error Handling

Use specific exceptions and provide helpful error messages:

```python
# Good
try:
    data = yf.download(ticker, period=period, interval=interval)
    if data.empty:
        raise ValueError(f"No data returned for ticker {ticker}")
except Exception as e:
    logging.error(f"Failed to fetch data for {ticker}: {str(e)}")
    raise

# Avoid bare except
try:
    risky_operation()
except:  # Bad - too broad
    pass
```

### Logging

Use the logging module instead of print statements:

```python
import logging

logging.info(f"Fetching data for {ticker}")
logging.warning(f"Missing data detected: {missing_count} rows")
logging.error(f"Failed to validate ticker {ticker}: {error}")
logging.debug(f"Intermediate calculation result: {value}")
```

---

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── test_ticker_selector.py
├── test_data_fetcher.py
├── test_data_storage.py
├── test_indicators.py
└── fixtures/
    └── sample_data.csv
```

### Writing Tests

Use **pytest** for all tests:

```python
import pytest
import pandas as pd
from ticker_selector import TickerSelector


class TestTickerSelector:
    """Test suite for TickerSelector class."""
    
    @pytest.fixture
    def selector(self):
        """Create a TickerSelector instance for testing."""
        return TickerSelector()
    
    def test_validate_valid_ticker(self, selector):
        """Test validation of a valid ticker."""
        result = selector.validate_ticker('AAPL')
        assert result is True
    
    def test_validate_invalid_ticker(self, selector):
        """Test validation of an invalid ticker."""
        result = selector.validate_ticker('INVALID123')
        assert result is False
    
    def test_get_sp500_tickers(self, selector):
        """Test fetching S&P 500 tickers."""
        tickers = selector.get_sp500_tickers(count=10)
        assert len(tickers) == 10
        assert all(isinstance(t, str) for t in tickers)
    
    @pytest.mark.parametrize("ticker,expected", [
        ('AAPL', True),
        ('MSFT', True),
        ('BTC-USD', True),
        ('INVALID', False),
    ])
    def test_validate_multiple_tickers(self, selector, ticker, expected):
        """Test validation of multiple ticker formats."""
        result = selector.validate_ticker(ticker)
        assert result == expected
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=algotrade_datascience --cov-report=html

# Run specific test file
pytest tests/test_ticker_selector.py

# Run specific test
pytest tests/test_ticker_selector.py::TestTickerSelector::test_validate_valid_ticker

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

### Test Coverage

Aim for **>80% code coverage** for all new features:

```bash
pytest --cov=algotrade_datascience --cov-report=term-missing
```

---

## 📚 Documentation

### Code Documentation

- **All modules** must have module-level docstrings
- **All classes** must have class-level docstrings
- **All public functions** must have docstrings with Args, Returns, Raises
- **Complex logic** should have inline comments

### Documentation Files

When adding new features, update:

1. **README.md** - If it affects usage
2. **IMPLEMENTATION_SUMMARY.md** - For technical details
3. **API.md** - For new public APIs
4. **CHANGELOG.md** - For all changes

### Markdown Style

- Use ATX-style headers (`#` not underlines)
- Include code blocks with language specification
- Add table of contents for long documents
- Use relative links for internal references

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No unnecessary files included
- [ ] Commit messages are clear and descriptive

### PR Title Format

```
<type>: <short description>

Examples:
feat: add RSI indicator calculation
fix: correct OHLC validation logic
docs: update installation instructions
refactor: optimize data fetching performance
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Related Issue
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD will run tests and linting
2. **Code Review**: At least one maintainer will review
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, a maintainer will merge

---

## 🐛 Issue Reporting

### Bug Reports

Use this template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. With parameters '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Package versions: [run `pip freeze`]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information.
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How you think it should work.

**Alternatives Considered**
Other approaches you've thought about.

**Additional Context**
Any other relevant information.
```

---

## 🏆 Recognition

Contributors will be recognized in:

- **README.md** - Contributors section
- **CHANGELOG.md** - Release notes
- **GitHub Contributors** - Automatic recognition

---

## 📞 Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for sensitive issues

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to FinAdvice! 🚀**
