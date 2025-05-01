# modules/settings/accounts.py

import pandas as pd
import logging
from typing import List

from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

AD_ACCOUNT_FIELDS = ["id", "name", "currency", "account_status", "business_country_code"]

def get_ad_accounts_df(business_id: str) -> pd.DataFrame:
    """
    Fetch all ad accounts associated with a Meta Business Manager using a generic API wrapper.

    Args:
        business_id (str): The Meta Business ID (e.g., '123456789').

    Returns:
        pd.DataFrame: A DataFrame containing ad account metadata.
    """
    logger.info(f"🔍 Retrieving ad accounts for Business ID: {business_id}")

    try:
        accounts = call_meta_api(
            object_id=business_id,
            edge="owned_ad_accounts",
            fields=AD_ACCOUNT_FIELDS
        )

        df = pd.DataFrame([{
            "account_id": acc["id"],
            "account_name": acc["name"],
            "currency": acc["currency"],
            "account_status": acc.get("account_status", ""),
            "business_country_code": acc.get("business_country_code", "")
        } for acc in accounts])

        logger.info(f"✅ {len(df)} ad accounts retrieved for Business ID: {business_id}")
        return df

    except Exception as e:
        logger.error(f"❌ Failed to fetch ad accounts for Business ID {business_id}: {e}", exc_info=True)
        return pd.DataFrame()