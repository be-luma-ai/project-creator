# modules/performance/main/ad_performance.py

import logging
import pandas as pd
from typing import List, Dict, Any

from utilities.meta_ads_api import call_meta_api
from utilities.actions_extractor import extract_action_value

logger = logging.getLogger(__name__)

AD_INSIGHTS_FIELDS = [
    "date_start", "ad_id", "adset_id", "campaign_id", "spend", "impressions", "reach", "clicks",
    "unique_clicks", "unique_inline_link_clicks", "actions", "action_values",
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking", "relevance_score"
]

def get_ad_performance_df(ad_accounts: List[Dict[str, Any]], run_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Extracts daily performance metrics at the ad level using Meta's Marketing API.

    Args:
        ad_accounts (List[Dict]): List of ad account metadata.
        run_config (Dict): Configuration with 'since_date' and 'yesterday_iso'.

    Returns:
        pd.DataFrame: Combined ad performance data.
    """
    logger.info(f"📊 Fetching ad performance for {len(ad_accounts)} ad accounts...")

    all_data = []
    time_range = {
        "since": run_config["since_date"],
        "until": run_config["yesterday_iso"]
    }

    for acc in ad_accounts:
        account_id = acc["account_id"]

        try:
            insights = call_meta_api(
            object_id=account_id,
            edge="insights",  # 🔥 esto es clave
            method="GET",
            params={
                "level": "ad",
                "time_increment": 1,
                "time_range": time_range
            },
            fields=AD_INSIGHTS_FIELDS
            )
        

            logger.info(f"✅ Insights retrieved from account {account_id}")

            for row in insights:
                all_data.append({
                    "account_id": account_id,
                    "ad_id": row.get("ad_id", ""),
                    "adset_id": row.get("adset_id", ""),
                    "campaign_id": row.get("campaign_id", ""),
                    "date": row.get("date_start", ""),
                    "spend": float(row.get("spend", 0)),
                    "impressions": int(row.get("impressions", 0)),
                    "reach": int(row.get("reach", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "unique_clicks": int(row.get("unique_clicks", 0)),
                    "unique_inline_link_clicks": int(row.get("unique_inline_link_clicks", 0)),

                    # Engagement
                    "likes": extract_action_value(row.get("actions"), "like"),
                    "comments": extract_action_value(row.get("actions"), "comment"),
                    "shares": extract_action_value(row.get("actions"), "post_share"),

                    # Funnel
                    "link_clicks": extract_action_value(row.get("actions"), "link_click"),
                    "landing_page_views": extract_action_value(row.get("actions"), "landing_page_view"),
                    "content_views": extract_action_value(row.get("actions"), "view_content"),
                    "add_to_cart": extract_action_value(row.get("actions"), "add_to_cart"),
                    "initiate_checkout": extract_action_value(row.get("actions"), "initiate_checkout"),
                    "purchase": extract_action_value(row.get("actions"), "purchase"),
                    "purchase_value": float(extract_action_value(row.get("action_values"), "purchase")),

                    # Rankings
                    "quality_ranking": row.get("quality_ranking", ""),
                    "engagement_rate_ranking": row.get("engagement_rate_ranking", ""),
                    "conversion_rate_ranking": row.get("conversion_rate_ranking", ""),
                    "relevance_score": row.get("relevance_score", "")
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch ad insights for account {account_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_data)
    logger.info(f"📈 Total ad performance rows loaded: {len(df)}")
    return df