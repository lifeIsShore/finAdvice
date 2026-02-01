"""
US-01: Asset Universe Selection
Handles ticker input, validation, and top S&P 500 selection
"""

import logging
from typing import List, Optional
import yfinance as yf
from config import TOP_SP500_TICKERS, CRYPTO_SUFFIX

logger = logging.getLogger(__name__)


class TickerSelector:
    """
    Handles ticker selection and validation
    Supports manual input and automatic top S&P 500 selection
    """
    
    def __init__(self):
        self.tickers: List[str] = []
        self.invalid_tickers: List[str] = []
        self.validated_tickers: List[str] = []
    
    def set_manual_tickers(self, tickers: List[str]) -> None:
        """
        Set tickers manually
        
        Args:
            tickers: List of ticker symbols (e.g., ['AAPL', 'TSLA', 'BTC-USD'])
        """
        if not isinstance(tickers, list):
            raise TypeError("Tickers must be provided as a list")
        
        if not tickers:
            raise ValueError("Ticker list cannot be empty")
        
        # Clean and uppercase tickers
        self.tickers = [ticker.strip().upper() for ticker in tickers]
        logger.info(f"Manual tickers set: {self.tickers}")
    
    def set_top_sp500(self, count: int = 10) -> None:
        """
        Automatically select top N S&P 500 companies by market cap
        
        Args:
            count: Number of top companies to select (default: 10)
        """
        if count <= 0:
            raise ValueError("Count must be positive")
        
        # Use predefined list (in production, this could fetch from API)
        self.tickers = TOP_SP500_TICKERS[:count]
        logger.info(f"Top {count} S&P 500 tickers selected: {self.tickers}")
    
    def validate_tickers(self) -> bool:
        """
        Validate all tickers by checking if they exist in yfinance
        
        Returns:
            True if all tickers are valid, False otherwise
        """
        if not self.tickers:
            logger.error("No tickers to validate")
            return False
        
        self.validated_tickers = []
        self.invalid_tickers = []
        
        for ticker in self.tickers:
            try:
                # Attempt to fetch minimal data to validate ticker
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Check if we got valid data
                if info and ('symbol' in info or 'shortName' in info or 'longName' in info):
                    self.validated_tickers.append(ticker)
                    logger.info(f"[OK] Valid ticker: {ticker}")
                else:
                    self.invalid_tickers.append(ticker)
                    logger.warning(f"[FAIL] Invalid ticker: {ticker} (no data returned)")
                    
            except Exception as e:
                self.invalid_tickers.append(ticker)
                logger.warning(f"[FAIL] Invalid ticker: {ticker} (error: {str(e)})")
        
        # Report validation results
        total = len(self.tickers)
        valid_count = len(self.validated_tickers)
        
        logger.info(f"Validation complete: {valid_count}/{total} tickers valid")
        
        if self.invalid_tickers:
            logger.warning(f"Invalid tickers found: {self.invalid_tickers}")
        
        return len(self.invalid_tickers) == 0
    
    def get_validated_tickers(self) -> List[str]:
        """
        Get list of validated tickers
        
        Returns:
            List of valid ticker symbols
        """
        return self.validated_tickers
    
    def get_validation_report(self) -> dict:
        """
        Get detailed validation report
        
        Returns:
            Dictionary with validation statistics
        """
        return {
            'total_tickers': len(self.tickers),
            'valid_tickers': len(self.validated_tickers),
            'invalid_tickers': len(self.invalid_tickers),
            'validated_list': self.validated_tickers,
            'invalid_list': self.invalid_tickers,
            'success_rate': len(self.validated_tickers) / len(self.tickers) if self.tickers else 0
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test 1: Manual ticker selection
    print("=" * 60)
    print("TEST 1: Manual Ticker Selection")
    print("=" * 60)
    selector = TickerSelector()
    selector.set_manual_tickers(['AAPL', 'TSLA', 'INVALID_TICKER', 'BTC-USD'])
    selector.validate_tickers()
    print(f"\nValidation Report: {selector.get_validation_report()}")
    
    # Test 2: Top S&P 500 selection
    print("\n" + "=" * 60)
    print("TEST 2: Top 5 S&P 500 Tickers")
    print("=" * 60)
    selector2 = TickerSelector()
    selector2.set_top_sp500(5)
    selector2.validate_tickers()
    print(f"\nValidation Report: {selector2.get_validation_report()}")
