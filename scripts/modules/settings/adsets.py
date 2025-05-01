import pandas as pd
import json
import logging
from typing import List, Dict

from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

ADSET_FIELDS = [
    "id", "name", "campaign_id", "created_time", "end_time", "updated_time", "effective_status",
    "attribution_spec", "bid_adjustments", "bid_amount", "bid_info", "bid_strategy",
    "destination_type", "issues_info", "learning_stage_info",
    "optimization_goal", "optimization_sub_event", "promoted_object", "targeting",
    "targeting_optimization_types", "asset_feed_id", "is_dynamic_creative"
]

def get_adsets_df(ad_accounts: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Fetch ad sets from a list of ad accounts using the Meta Ads API.

    Args:
        ad_accounts (List[Dict[str, str]]): A list of ad account metadata dictionaries.

    Returns:
        pd.DataFrame: A DataFrame containing ad set metadata.
    """
    adset_list = []

    logger.info(f"📊 Retrieving ad sets from {len(ad_accounts)} ad accounts...")

    for acc in ad_accounts:
        acc_id = acc["account_id"]
        acc_name = acc["account_name"]
        currency = acc["currency"]

        try:
            adsets = call_meta_api(
                object_id=acc_id,
                edge="adsets",
                fields=ADSET_FIELDS
            )

            logger.info(f"✅ {len(adsets)} ad sets retrieved from account {acc_id} - {acc_name}")

            for adset in adsets:
                adset_list.append({
                    "account_id": acc_id,
                    "account_name": acc_name,
                    "currency": currency,
                    "campaign_id": adset.get("campaign_id", ""),
                    "adset_id": adset.get("id"),
                    "adset_name": adset.get("name", ""),
                    "created_time": adset.get("created_time", ""),
                    "end_time": adset.get("end_time", ""),
                    "updated_time": adset.get("updated_time", ""),
                    "effective_status": adset.get("effective_status", ""),
                    "bid_adjustments": json.dumps(adset.get("bid_adjustments", {}), default=str),
                    "bid_amount": float(adset.get("bid_amount", 0)) if adset.get("bid_amount") else None,
                    "bid_info": json.dumps(adset.get("bid_info", {}), default=str),
                    "bid_strategy": adset.get("bid_strategy", ""),
                    "optimization_goal": adset.get("optimization_goal", ""),
                    "optimization_sub_event": adset.get("optimization_sub_event", ""),
                    "attribution_spec": json.dumps(adset.get("attribution_spec", {}), default=str),
                    "destination_type": adset.get("destination_type", ""),
                    "issues_info": json.dumps(adset.get("issues_info", {}), default=str),
                    "learning_stage_info": json.dumps(adset.get("learning_stage_info", {}), default=str),
                    "promoted_object": json.dumps(adset.get("promoted_object", {})) if adset.get("promoted_object") else "{}",
                    "targeting": json.dumps(adset.get("targeting", {}), default=str),
                    "targeting_optimization_types": json.dumps(adset.get("targeting_optimization_types", {}), default=str),
                    "asset_feed_id": adset.get("asset_feed_id", ""),
                    "is_dynamic_creative": adset.get("is_dynamic_creative", False)
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch ad sets for account {acc_id}: {e}", exc_info=True)

    df = pd.DataFrame(adset_list)

    if not df.empty:
        for col in ["created_time", "end_time", "updated_time"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        logger.info(f"📈 Total ad sets processed: {len(df)}")
    else:
        logger.warning("⚠️ No ad sets found for the provided ad accounts.")

    return df