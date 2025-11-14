# scripts/utilities/run_for_client.py

import logging
import time
from typing import Dict, Any

from facebook_business.api import FacebookAdsApi

from scripts.modules.settings.ads import get_ads_df
from scripts.modules.settings.ad_creatives import get_creatives_df
from scripts.modules.performance.main.ad_performance import get_ad_performance_df
from typing import Optional
from scripts.utilities.meta_ads_api import call_meta_api_business
import pandas as pd

logger = logging.getLogger(__name__)

def api_delay(seconds: int = 2):
    """Add delay between API calls to avoid rate limiting"""
    logger.info(f"⏳ Waiting {seconds} seconds to avoid rate limiting...")
    time.sleep(seconds)

def run_for_client(
    client: Dict[str, Any], 
    access_token: str, 
    run_config: Dict[str, Any], 
    data_flags: Dict[str, bool],
    gcs_service_account: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract Meta Ads data for a single client.
    
    Extracts: ads, ad_creatives (settings), and ad_performance (performance main).

    Args:
        client (dict): Contains 'slug', 'business_id', and 'project_id'.
        access_token (str): Meta Graph API access token.
        run_config (dict): Run configuration including 'since_date'.
        data_flags (dict): Dict of flags to toggle which datasets to extract.
                          Supported: 'ads', 'ad_creatives', 'ad_performance'.
        gcs_service_account (dict, optional): Cloud Storage service account for image uploads.

    Returns:
        dict: Extracted DataFrames and client metadata (includes 'project_id').
    """
    slug = client.get("slug")
    business_id = client.get("business_id")
    project_id = client.get("project_id")

    if not all([slug, business_id, project_id]):
        logger.error("❌ Client configuration is missing 'slug', 'business_id' or 'project_id'.")
        return {}

    try:
        logger.info(f"🔐 Initializing Meta API for client: {slug}")
        FacebookAdsApi.init(access_token=access_token)

        results = {
            "slug": slug,
            "project_id": project_id
        }

        # Fetch ad accounts (needed for ads, ad_creatives, and ad_performance)
        logger.info(f"📂 Fetching ad accounts for business_id: {business_id}")
        accounts = call_meta_api_business(
            object_id=business_id,
            edge="owned_ad_accounts",
            fields=["id", "name", "currency", "account_status", "business_country_code"]
        )
        
        # Convert accounts to DataFrame format
        accounts_data = []
        for acc in accounts:
            accounts_data.append({
                "account_id": acc.get("id", ""),
                "account_name": acc.get("name", ""),
                "currency": acc.get("currency", ""),
                "account_status": acc.get("account_status", ""),
                "business_country_code": acc.get("business_country_code", "")
            })
        
        df_accounts = pd.DataFrame(accounts_data)
        logger.info(f"📊 Retrieved {len(df_accounts)} ad accounts")
        if len(df_accounts) > 5:
            logger.warning(f"⚠️ Client {slug} has {len(df_accounts)} ad accounts - this may take longer and could cause rate limiting")
        ad_account_records = df_accounts.to_dict("records")

        if data_flags.get("ads"):
            api_delay(3)  # Delay before ads
            results["ads"] = get_ads_df(ad_account_records)

        if data_flags.get("ad_creatives"):
            api_delay(3)  # Delay before ad_creatives
            # Get storage config from run_config (optional)
            download_images = run_config.get("download_images", False)
            download_videos = run_config.get("download_videos", False)
            # Use the central Cloud Storage service account
            # Extract base slug (before hyphen) for bucket organization
            # e.g., "bruta-454620" -> "bruta", "gama-454419" -> "gama"
            base_slug = slug.split("-")[0] if "-" in slug else slug
            # Build client-specific bucket name: {project_id}_meta_creatives
            # Each client has its own bucket in its own project
            storage_bucket = f"{project_id}_meta_creatives" if (download_images or download_videos) else None
            gcs_credentials = gcs_service_account if (download_images or download_videos) and storage_bucket else None
            # Get limit from run_config if specified (for testing)
            creatives_limit = run_config.get("creatives_limit", None)
            results["ad_creatives"] = get_creatives_df(
                ad_account_records,
                client_slug=base_slug,
                bucket_name=storage_bucket,
                date_suffix=run_config.get("yesterday"),
                download_images=download_images,
                download_videos=download_videos,
                gcs_credentials=gcs_credentials,
                limit=creatives_limit,
                project_id=project_id,
                access_token=access_token
            )

        if data_flags.get("ad_performance"):
            api_delay(5)  # Delay before ad performance (insights API)
            results["ad_performance"] = get_ad_performance_df(ad_account_records, run_config)

        logger.info(f"✅ Data successfully extracted for client: {slug}")
        return results

    except Exception as e:
        logger.error(f"❌ Error processing client {slug}: {e}", exc_info=True)
        return {
            "slug": slug,
            "project_id": project_id
        }