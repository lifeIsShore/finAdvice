"""
Weekly Report Job
Triggered by the scheduler every week.
"""

import logging
import subprocess
import os

logger = logging.getLogger("Orchestration.Weekly")

def run_weekly_job():
    """
    Executes the weekly report generation.
    """
    logger.info("Triggering weekly report generation...")
    
    # Assuming generate_complete_report.py is a script that can be run
    # We'll use subprocess to run it as a separate process to avoid import conflicts if any
    try:
        # Get the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "generate_complete_report.py")
        script_path = os.path.abspath(script_path)
        
        logger.info(f"Running script: {script_path}")
        result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
        
        logger.info("Weekly report generated successfully.")
        logger.debug(f"Output: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate weekly report: {e.stderr}")
        raise

if __name__ == "__main__":
    # Allow running this job independently for testing
    logging.basicConfig(level=logging.INFO)
    run_weekly_job()
