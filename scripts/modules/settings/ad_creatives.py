import pandas as pd
import json
import logging
from typing import List, Dict

from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

CREATIVE_FIELDS = [
    "id", "name", "actor_id", "adlabels", "body", "call_to_action_type",
    "image_url", "image_hash", "object_story_id", "object_url", "status",
    "thumbnail_url", "title", "url_tags", "video_id", "product_data", "product_set_id"
]

def get_creatives_df(ad_accounts: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Fetch ad creatives from a list of ad accounts.

    Args:
        ad_accounts (List[Dict[str, str]]): List of ad account dicts with metadata.

    Returns:
        pd.DataFrame: DataFrame with creative metadata.
    """
    creative_list = []

    logger.info(f"🎨 Retrieving ad creatives from {len(ad_accounts)} ad accounts...")

    for acc in ad_accounts:
        ad_account_id = acc["account_id"]
        account_name = acc["account_name"]
        currency = acc["currency"]

        try:
            creatives = call_meta_api(
                object_id=ad_account_id,
                edge="adcreatives",
                fields=CREATIVE_FIELDS
            )

            logger.info(f"✅ {len(creatives)} creatives fetched from account {ad_account_id} - {account_name}")

            for creative in creatives:
                creative_list.append({
                    "creative_id": creative.get("id"),
                    "name": creative.get("name", ""),
                    "account_id": ad_account_id,
                    "account_name": account_name,
                    "currency": currency,
                    "actor_id": creative.get("actor_id", ""),
                    "adlabels": json.dumps(creative.get("adlabels", {}), default=str),
                    "body": creative.get("body", ""),
                    "call_to_action_type": creative.get("call_to_action_type", ""),
                    "image_url": creative.get("image_url", ""),
                    "image_hash": creative.get("image_hash", ""),
                    "object_story_id": creative.get("object_story_id", ""),
                    "object_url": creative.get("object_url", ""),
                    "status": creative.get("status", ""),
                    "thumbnail_url": creative.get("thumbnail_url", ""),
                    "title": creative.get("title", ""),
                    "url_tags": creative.get("url_tags", ""),
                    "video_id": creative.get("video_id", ""),
                    "product_data": json.dumps(creative.get("product_data", {}), default=str),
                    "product_set_id": creative.get("product_set_id", "")
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch creatives for account {ad_account_id}: {e}", exc_info=True)

    df = pd.DataFrame(creative_list)

    if not df.empty:
        logger.info(f"📈 Total creatives processed: {len(df)}")
    else:
        logger.warning("⚠️ No creatives found for any of the provided ad accounts.")

    return df