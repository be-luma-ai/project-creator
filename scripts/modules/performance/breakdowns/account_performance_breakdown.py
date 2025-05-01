import logging
import pandas as pd
from facebook_business.adobjects.adaccount import AdAccount
from utilities.actions_extractor import extract_action_value

logger = logging.getLogger(__name__)

AD_INSIGHTS_FIELDS = [
    "date_start", "ad_id", "adset_id", "campaign_id", "spend", "impressions", "reach", "clicks",
    "unique_clicks", "unique_inline_link_clicks", "actions", "action_values",
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking", "relevance_score"
]


def get_ad_performance_with_breakdowns(ad_accounts, run_config, breakdown_config: dict) -> dict:
    """
    Extracts ad-level performance data for each breakdown combination specified in a JSON config.

    Args:
        ad_accounts (list[dict]): Metadata of ad accounts (with 'account_id').
        run_config (dict): Includes 'since_date' and 'yesterday'.
        breakdown_config (dict): Dict like {"ad": [["gender"], ["age", "gender"]]}

    Returns:
        dict: Mapping from breakdown name (e.g., "ad_performance_gender") to DataFrame.
    """
    result = {}

    since_date = run_config["since_date"]
    until_date = run_config["yesterday"]

    ad_breakdowns = breakdown_config.get("ad", [])

    logger.info(f"🧩 Running {len(ad_breakdowns)} breakdown combinations at ad level...")

    for breakdown_list in ad_breakdowns:
        breakdowns_str = "_".join(breakdown_list)  # e.g. "gender" or "age_gender"
        table_key = f"ad_performance_{breakdowns_str}"
        logger.info(f"📊 Extracting insights with breakdowns: {breakdown_list}")

        all_data = []

        for acc in ad_accounts:
            ad_account_id = acc["account_id"]

            try:
                account = AdAccount(ad_account_id)
                insights = account.get_insights(
                    fields=AD_INSIGHTS_FIELDS,
                    params={
                        "level": "ad",
                        "time_increment": 1,
                        "time_range": {"since": since_date, "until": until_date},
                        "breakdowns": breakdown_list
                    }
                )

                for row in insights:
                    base = {
                        "account_id": ad_account_id,
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
                        "likes": extract_action_value(row.get("actions"), "like"),
                        "comments": extract_action_value(row.get("actions"), "comment"),
                        "shares": extract_action_value(row.get("actions"), "post_share"),
                        "link_clicks": extract_action_value(row.get("actions"), "link_click"),
                        "landing_page_views": extract_action_value(row.get("actions"), "landing_page_view"),
                        "content_views": extract_action_value(row.get("actions"), "view_content"),
                        "add_to_cart": extract_action_value(row.get("actions"), "add_to_cart"),
                        "initiate_checkout": extract_action_value(row.get("actions"), "initiate_checkout"),
                        "purchase": extract_action_value(row.get("actions"), "purchase"),
                        "purchase_value": float(extract_action_value(row.get("action_values"), "purchase")),
                        "quality_ranking": row.get("quality_ranking", ""),
                        "engagement_rate_ranking": row.get("engagement_rate_ranking", ""),
                        "conversion_rate_ranking": row.get("conversion_rate_ranking", ""),
                        "relevance_score": row.get("relevance_score", ""),
                    }

                    # 🧩 Add breakdown fields dynamically
                    for b in breakdown_list:
                        base[b] = row.get(b, "")

                    all_data.append(base)

            except Exception as e:
                logger.warning(f"⚠️ Error fetching insights for account {ad_account_id} with breakdowns {breakdown_list}: {e}")

        df = pd.DataFrame(all_data)
        logger.info(f"📥 Loaded {len(df)} rows for breakdowns: {breakdowns_str}")
        result[table_key] = df

    return result