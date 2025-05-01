# modules/change_history/activities.py

import pandas as pd
import logging
from typing import List, Dict, Any
from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

ACTIVITY_FIELDS = [
    "actor_name", "event_time", "event_type", "translated_event_type",
    "object_name", "object_id", "object_type"
]

def get_activities_df(ad_accounts: List[Dict[str, Any]], since_date: str) -> pd.DataFrame:
    """
    Fetches change history activities from Meta Ads for a list of ad accounts.

    Args:
        ad_accounts (List[Dict]): List of ad account metadata.
        since_date (str): Start date (YYYY-MM-DD) for activity history.

    Returns:
        pd.DataFrame: DataFrame with activities across all accounts.
    """
    logger.info(f"📊 Fetching activities since {since_date} for {len(ad_accounts)} ad accounts...")
    all_activities = []

    for acc in ad_accounts:
        account_id = acc["account_id"]
        account_name = acc.get("account_name", "")
        currency = acc.get("currency", "")

        try:
            activities = call_meta_api(
                object_type="ad_account",
                object_id=account_id,
                method="get_activities",
                fields=ACTIVITY_FIELDS,
                params={"since": since_date}
            )

            logger.info(f"✅ {len(activities)} activities retrieved from account {account_id}")

            for activity in activities:
                activity.update({
                    "account_id": account_id,
                    "account_name": account_name,
                    "currency": currency
                })
                all_activities.append(activity)

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch activities for account {account_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_activities)

    if not df.empty:
        df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce").dt.date
        logger.info(f"📈 Total activities loaded: {len(df)}")
    else:
        logger.info("📭 No activities found across all accounts.")

    return df