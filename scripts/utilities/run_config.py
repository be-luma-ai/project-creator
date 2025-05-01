# utilities/run_config.py

from datetime import datetime, timedelta
from typing import Dict, Union

def get_run_config(days_back: int = 90) -> Dict[str, Union[str, int, datetime]]:
    """
    Generates a configuration dictionary with relevant dates for the extraction run.

    Args:
        days_back (int): Number of days back from today to set the 'since_date'. Default is 5.

    Returns:
        Dict[str, Union[str, int, datetime]]: A dictionary with:
            - run_time: current UTC datetime (datetime object)
            - since_date: start date in '%Y-%m-%d' format (for API time range)
            - yesterday: date of yesterday in '%Y%m%d' format (for table suffixes)
            - yesterday_iso: date of yesterday in '%Y-%m-%d' format (for API time range)
            - days_back: number of days back used in this run
    """
    run_time = datetime.utcnow()
    since_date = (run_time - timedelta(days=days_back)).strftime('%Y-%m-%d')
    yesterday_iso = (run_time - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday = (run_time - timedelta(days=1)).strftime('%Y%m%d')

    return {
        "run_time": run_time,
        "since_date": since_date,
        "yesterday": yesterday,
        "yesterday_iso": yesterday_iso,
        "days_back": days_back
    }