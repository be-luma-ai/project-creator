import logging
import pandas as pd
from typing import List, Dict
from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

def get_recommendations_ad_accounts_df(business_id: str, access_token: str) -> pd.DataFrame:
    """
    Fetches recommendation data for all ad accounts under a given Meta Business ID.

    Args:
        business_id (str): Meta Business ID.
        access_token (str): Meta Graph API access token.

    Returns:
        pd.DataFrame: DataFrame with ad account-level recommendations.
    """
    all_recommendations: List[Dict] = []

    try:
        ad_accounts_data = call_meta_api(
            object_type="business",
            object_id=business_id,
            method="owned_ad_accounts",
            fields=["id", "name"],
            params={"access_token": access_token}
        )
        ad_accounts = ad_accounts_data.get("data", [])
        logger.info(f"🔍 Found {len(ad_accounts)} ad accounts for Business ID {business_id}.")
    except Exception as e:
        logger.error(f"❌ Failed to fetch ad accounts for Business ID {business_id}: {e}", exc_info=True)
        return pd.DataFrame()

    for account in ad_accounts:
        ad_account_id = account.get("id")
        account_name = account.get("name")

        try:
            recommendations_obj = call_meta_api(
                object_type="ad_account",
                object_id=ad_account_id,
                fields=["recommendations"],
                params={"access_token": access_token}
            )

            recommendation_groups = recommendations_obj.get("recommendations", {}).get("data", [])
            if not isinstance(recommendation_groups, list):
                logger.warning(f"⚠️ Unexpected format for 'recommendations' in ad account {ad_account_id}")
                continue

            for group in recommendation_groups:
                rec_list = group.get("recommendations", [])
                if not isinstance(rec_list, list):
                    continue

                for rec in rec_list:
                    all_recommendations.append({
                        "object_type": "Ad Account",
                        "object_id": ad_account_id,
                        "account_name": account_name,
                        "recommendation_signature": rec.get("recommendation_signature", ""),
                        "type": rec.get("type", ""),
                        "object_ids": ",".join(rec.get("object_ids", [])) if "object_ids" in rec else "",
                        "title": rec.get("title", ""),
                        "message": rec.get("message", ""),
                        "code": rec.get("code", ""),
                        "importance": rec.get("importance", ""),
                        "confidence": rec.get("confidence", ""),
                        "blame_field": rec.get("blame_field", "")
                    })

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch recommendations for ad account {ad_account_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_recommendations)
    logger.info(f"📊 Total ad account recommendations retrieved: {len(df)}")
    return df