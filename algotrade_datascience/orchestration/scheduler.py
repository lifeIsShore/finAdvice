"""
Pipeline Orchestration Scheduler
Handles different data pipelines running at various intervals.
"""

import schedule
import time
import logging
import sys
from datetime import datetime
from algotrade_datascience.orchestration.jobs.hourly_data_job import run_hourly_job
from algotrade_datascience.orchestration.jobs.weekly_report_job import run_weekly_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Orchestration")

def job_wrapper(job_func, name):
    """Wrapper to catch errors in jobs and log them"""
    logger.info(f"Starting job: {name}")
    try:
        start_time = time.time()
        job_func()
        duration = time.time() - start_time
        logger.info(f"Finished job: {name} (Duration: {duration:.2f}s)")
    except Exception as e:
        logger.error(f"Job failed: {name} - Error: {e}", exc_info=True)

def main():
    logger.info("Starting Pipeline Orchestration Scheduler...")
    
    # Schedule Hourly Data Pipeline
    schedule.every().hour.at(":00").do(job_wrapper, run_hourly_job, "Hourly Data Pipeline")
    
    # Schedule Weekly Report/Cleanup
    schedule.every().monday.at("00:00").do(job_wrapper, run_weekly_job, "Weekly Report Job")
    
    # Example for frequent testing (comment out in production)
    # schedule.every(5).minutes.do(job_wrapper, run_hourly_job, "Frequent Test Job")

    logger.info(f"Jobs scheduled. Waiting for next run...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        sys.exit(0)
