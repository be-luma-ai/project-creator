# modules/settings/campaigns.py

import pandas as pd
import json
import logging
from typing import List, Dict

from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

CAMPAIGN_FIELDS = [
    "id", "name", "created_time", "start_time", "updated_time", "effective_status",
    "objective", "bid_strategy", "promoted_object", "configured_status", 
    "smart_promotion_type", "primary_attribution", "status", "stop_time"
]

def get_campaigns_df(ad_accounts: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Fetch all campaigns from a list of Meta Ad Accounts using the generic API wrapper.

    Args:
        ad_accounts (List[Dict[str, str]]): A list of ad account dictionaries with keys:
            - account_id
            - account_name
            - currency

    Returns:
        pd.DataFrame: A DataFrame with campaign metadata for all ad accounts.
    """
    campaign_list = []

    logger.info(f"📊 Retrieving campaigns from {len(ad_accounts)} ad accounts...")

    for acc in ad_accounts:
        acc_id = acc["account_id"]
        acc_name = acc["account_name"]
        currency = acc["currency"]

        try:
            campaigns = call_meta_api(
                object_id=acc_id,
                edge="campaigns",
                fields=CAMPAIGN_FIELDS
            )

            logger.info(f"✅ {len(campaigns)} campaigns fetched from account {acc_id} - {acc_name}")

            for c in campaigns:
                campaign_list.append({
                    "account_id": acc_id,
                    "account_name": acc_name,
                    "currency": currency,
                    "campaign_id": c.get("id"),
                    "campaign_name": c.get("name", ""),
                    "created_time": c.get("created_time"),
                    "start_time": c.get("start_time"),
                    "updated_time": c.get("updated_time"),
                    "effective_status": c.get("effective_status", ""),
                    "objective": c.get("objective", ""),
                    "bid_strategy": c.get("bid_strategy", ""),
                    "promoted_object": json.dumps(c.get("promoted_object", {})) if c.get("promoted_object") else "{}",
                    "configured_status": c.get("configured_status", ""),
                    "smart_promotion_type": c.get("smart_promotion_type", ""),
                    "primary_attribution": c.get("primary_attribution", ""),
                    "status": c.get("status", ""),
                    "stop_time": c.get("stop_time"),
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch campaigns for account {acc_id}: {e}", exc_info=True)

    df = pd.DataFrame(campaign_list)

    if not df.empty:
        for col in ["created_time", "start_time", "updated_time", "stop_time"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        logger.info(f"📈 Total campaigns processed: {len(df)}")
    else:
        logger.warning("⚠️ No campaigns found for the provided ad accounts.")

    return df