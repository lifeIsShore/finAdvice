# Pipeline Orchestration

This folder contains the orchestration logic for the AlgoTrade Data Science project. It is designed to handle tasks that need to run at specific intervals (hourly, daily, weekly, etc.).

## Structure

- `scheduler.py`: The main entry point that schedules and runs jobs.
- `jobs/`: Contains individual job definitions.
    - `hourly_data_job.py`: Logic for fetching data every hour.
    - `weekly_report_job.py`: Logic for generating comprehensive reports every week.

## Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scheduler**:
   From the project root directory:
   ```bash
   python -m algotrade_datascience.orchestration.scheduler
   ```
   Or if you are in the root and have the package installed:
   ```bash
   python algotrade_datascience/orchestration/scheduler.py
   ```

## Adding New Jobs

1. Create a new Python file in the `jobs/` directory.
2. Define a function (e.g., `run_new_job()`) that contains the logic.
3. Register the job in `scheduler.py` using `schedule.every()...do()`.
