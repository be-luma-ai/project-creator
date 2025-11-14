# utilities/run_config.py

import os
from datetime import datetime, timedelta
from typing import Dict, Union

def get_run_config(days_back: int = 7) -> Dict[str, Union[str, int, datetime, bool]]:
    """
    Generates a configuration dictionary with relevant dates for the extraction run.

    Args:
        days_back (int): Number of days back from today to set the 'since_date'. Default is 30.

    Returns:
        Dict[str, Union[str, int, datetime, bool]]: A dictionary with:
            - run_time: current UTC datetime (datetime object)
            - since_date: start date in '%Y-%m-%d' format (for API time range)
            - yesterday: date of yesterday in '%Y%m%d' format (for table suffixes)
            - yesterday_iso: date of yesterday in '%Y-%m-%d' format (for API time range)
            - days_back: number of days back used in this run
            - image_bucket_name: GCS bucket name for storing images (from env var, optional)
            - download_images: Whether to download and store images (from env var, default False)
            - download_videos: Whether to download and store videos (from env var, default False)
            - extract_ads: Whether to extract ads data (from env var, default True)
            - extract_ad_creatives: Whether to extract ad creatives data (from env var, default True)
            - extract_ad_performance: Whether to extract ad performance data (from env var, default True)
            
    Note:
        When both download_images and download_videos are enabled, the pipeline will
        automatically find 1 creative with image and 1 creative with video per client.
    """
    run_time = datetime.utcnow()
    since_date = (run_time - timedelta(days=days_back)).strftime('%Y-%m-%d')
    yesterday_iso = (run_time - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday = (run_time - timedelta(days=1)).strftime('%Y%m%d')

    # Storage configuration (optional)
    image_bucket_name = os.getenv("META_ADS_IMAGE_BUCKET", None)
    download_images = os.getenv("META_ADS_DOWNLOAD_IMAGES", "false").lower() == "true"
    download_videos = os.getenv("META_ADS_DOWNLOAD_VIDEOS", "false").lower() == "true"
    
    # Data extraction flags (optional, default all True)
    extract_ads = os.getenv("META_ADS_EXTRACT_ADS", "true").lower() == "true"
    extract_ad_creatives = os.getenv("META_ADS_EXTRACT_AD_CREATIVES", "true").lower() == "true"
    extract_ad_performance = os.getenv("META_ADS_EXTRACT_AD_PERFORMANCE", "true").lower() == "true"

    return {
        "run_time": run_time,
        "since_date": since_date,
        "yesterday": yesterday,
        "yesterday_iso": yesterday_iso,
        "days_back": days_back,
        "image_bucket_name": image_bucket_name,
        "download_images": download_images,
        "download_videos": download_videos,
        "extract_ads": extract_ads,
        "extract_ad_creatives": extract_ad_creatives,
        "extract_ad_performance": extract_ad_performance
    }