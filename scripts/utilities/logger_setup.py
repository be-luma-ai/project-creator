import logging
import sys
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = "meta_ads_pipeline.log") -> logging.Logger:
    """
    Configures and returns a logger instance with both console and file output.

    Args:
        name (str): Logger name (usually __name__).
        log_file (Optional[str]): File path to write logs. Default is 'meta_ads_pipeline.log'.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger  # Prevent duplicate handlers

    logger.setLevel(logging.INFO)
    logger.propagate = False  # Avoid duplicate logs from root logger

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger