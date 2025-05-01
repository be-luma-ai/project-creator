import pandas as pd
import json
import logging
from typing import List, Dict

from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

AD_FIELDS = [
    "id", "name", "account_id", "campaign_id", "adset_id",
    "created_time", "updated_time", "ad_active_time", "ad_review_feedback",
    "ad_schedule_start_time", "ad_schedule_end_time", "bid_amount", "configured_status",
    "conversion_domain", "effective_status", "issues_info", "preview_shareable_link",
    "status", "creative", "creative_asset_groups_spec"
]

def get_ads_df(ad_accounts: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Fetch ads from a list of ad accounts using the Meta Ads API.

    Args:
        ad_accounts (List[Dict[str, str]]): List of ad account metadata dicts.

    Returns:
        pd.DataFrame: DataFrame with ad metadata.
    """
    ads_list = []

    logger.info(f"📊 Retrieving ads from {len(ad_accounts)} ad accounts...")

    for acc in ad_accounts:
        acc_id = acc["account_id"]
        acc_name = acc["account_name"]
        currency = acc["currency"]

        try:
            ads = call_meta_api(
                object_id=acc_id,
                edge="ads",
                fields=AD_FIELDS
            )

            logger.info(f"✅ {len(ads)} ads retrieved from account {acc_id} - {acc_name}")

            for ad in ads:
                ads_list.append({
                    "ad_id": ad.get("id"),
                    "name": ad.get("name", ""),
                    "account_id": acc_id,
                    "account_name": acc_name,
                    "currency": currency,
                    "campaign_id": ad.get("campaign_id", ""),
                    "adset_id": ad.get("adset_id", ""),
                    "created_time": ad.get("created_time", ""),
                    "updated_time": ad.get("updated_time", ""),
                    "ad_active_time": ad.get("ad_active_time", ""),
                    "ad_schedule_start_time": ad.get("ad_schedule_start_time", ""),
                    "ad_schedule_end_time": ad.get("ad_schedule_end_time", ""),
                    "configured_status": ad.get("configured_status", ""),
                    "effective_status": ad.get("effective_status", ""),
                    "status": ad.get("status", ""),
                    "bid_amount": float(ad.get("bid_amount", 0)) if ad.get("bid_amount") else None,
                    "conversion_domain": ad.get("conversion_domain", ""),
                    "preview_shareable_link": ad.get("preview_shareable_link", ""),
                    "creative": json.dumps(ad.get("creative", {}), default=str),
                    "creative_asset_groups_spec": json.dumps(ad.get("creative_asset_groups_spec", {}), default=str),
                    "ad_review_feedback": json.dumps(ad.get("ad_review_feedback", {}), default=str),
                    "issues_info": json.dumps(ad.get("issues_info", {}), default=str),
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch ads for account {acc_id}: {e}", exc_info=True)

    df = pd.DataFrame(ads_list)

    if not df.empty:
        for col in ["created_time", "updated_time", "ad_active_time", "ad_schedule_start_time", "ad_schedule_end_time"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        logger.info(f"📈 Total ads processed: {len(df)}")
    else:
        logger.warning("⚠️ No ads found for the provided ad accounts.")

    return df