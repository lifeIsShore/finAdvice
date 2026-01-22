"""
Hourly Data Job
Triggered by the scheduler every hour.
"""

import logging
from algotrade_datascience.main_data_pipeline import run_pipeline

logger = logging.getLogger("Orchestration.Hourly")

def run_hourly_job():
    """
    Executes the hourly data fetching pipeline.
    """
    logger.info("Triggering hourly data pipeline...")
    
    # In a real scenario, you might want to specify tickers or count
    # For now, we'll use the default 'auto' mode with a few tickers
    results = run_pipeline(mode='auto', count=5)
    
    logger.info(f"Hourly pipeline finished. Status: {results['final']['total_files']} files updated.")

if __name__ == "__main__":
    # Allow running this job independently for testing
    logging.basicConfig(level=logging.INFO)
    run_hourly_job()
