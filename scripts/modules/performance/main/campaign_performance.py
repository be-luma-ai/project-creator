import pandas as pd
import logging
from typing import List, Dict, Any

from utilities.meta_ads_api import call_meta_api
from utilities.actions_extractor import extract_action_value

logger = logging.getLogger(__name__)

CAMPAIGN_INSIGHTS_FIELDS = [
    "date_start", "campaign_id", "spend", "impressions", "reach", "clicks",
    "unique_clicks", "unique_inline_link_clicks", "actions", "action_values", "campaign_name"
]

def get_campaign_performance_df(ad_accounts: List[Dict[str, Any]], run_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract campaign-level performance metrics from a list of Meta ad accounts.

    Args:
        ad_accounts (List[Dict]): List of ad accounts with keys "account_id" and "currency".
        run_config (Dict): Contains time range settings like 'since_date' and 'yesterday_iso'.

    Returns:
        pd.DataFrame: Combined performance data for all campaigns across accounts.
    """
    logger.info(f"📊 Fetching campaign performance data for {len(ad_accounts)} ad accounts...")

    all_data = []
    time_range = {
        "since": run_config["since_date"],
        "until": run_config["yesterday_iso"]
    }

    for account in ad_accounts:
        account_id = account["account_id"]
        currency = account["currency"]

        try:
            insights = call_meta_api(
            object_id=account_id,
            edge="insights",  # 🔥 esto es clave
            method="GET",
            params={
                "level": "campaign",
                "time_increment": 1,
                "time_range": time_range
            },
            fields=CAMPAIGN_INSIGHTS_FIELDS
            )

            logger.info(f"✅ Insights retrieved from account {account_id}")

            for row in insights:
                # Parse date to extract week, month, and year
                date_start = row.get("date_start", "")
                if date_start:
                    date_obj = pd.to_datetime(date_start)  # Convert the date string to a datetime object
                    week = date_obj.isocalendar()[1]  # Week number
                    month = date_obj.month  # Month number
                    year = date_obj.year  # Year number
                else:
                    week, month, year = None, None, None

                all_data.append({
                    "account_id": account_id,
                    "currency": currency,
                    "campaign_id": row.get("campaign_id", ""),
                    "campaign_name": row.get("campaign_name", ""),  # Add campaign name here
                    "date": date_start,
                    "week": week,
                    "month": month,
                    "year": year,
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
                    "purchase_value": float(extract_action_value(row.get("action_values"), "purchase"))
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch campaign insights for account {account_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_data)
    logger.info(f"📈 Total campaign performance records loaded: {len(df)}")
    return df