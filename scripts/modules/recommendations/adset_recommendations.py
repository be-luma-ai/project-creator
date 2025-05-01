import logging
import pandas as pd
from typing import List, Dict
from utilities.meta_ads_api import call_meta_api

logger = logging.getLogger(__name__)

def get_recommendations_adsets_df(business_id: str, access_token: str) -> pd.DataFrame:
    """
    Fetches recommendation data for all ad sets under a given Meta Business ID.

    Args:
        business_id (str): Meta Business ID.
        access_token (str): Meta Graph API access token.

    Returns:
        pd.DataFrame: DataFrame with ad set-level recommendations.
    """
    if not isinstance(business_id, str):
        logger.error(f"❌ Invalid business_id (not a string): {business_id}")
        return pd.DataFrame()

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
        logger.error(f"❌ Failed to fetch ad accounts: {e}", exc_info=True)
        return pd.DataFrame()

    for account in ad_accounts:
        ad_account_id = account["id"]

        try:
            adsets_data = call_meta_api(
                object_type="ad_account",
                object_id=ad_account_id,
                method="adsets",
                fields=["id", "name", "campaign_id"],
                params={"access_token": access_token}
            )
            adsets = adsets_data.get("data", [])
            logger.info(f"📦 {len(adsets)} ad sets found for account {ad_account_id}.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch ad sets for account {ad_account_id}: {e}", exc_info=True)
            continue

        for adset in adsets:
            adset_id = adset.get("id")
            campaign_id = adset.get("campaign_id", "")

            try:
                rec_data = call_meta_api(
                    object_type="adset",
                    object_id=adset_id,
                    fields=["recommendations"],
                    params={"access_token": access_token}
                )

                recommendations = rec_data.get("recommendations", {}).get("data", [])
                if not isinstance(recommendations, list):
                    continue

                for rec in recommendations:
                    all_recommendations.append({
                        "object_type": "Ad Set",
                        "object_id": adset_id,
                        "ad_account_id": ad_account_id,
                        "campaign_id": campaign_id,
                        "recommendation_signature": rec.get("recommendation_signature", ""),
                        "type": rec.get("type", ""),
                        "object_ids": ",".join(rec.get("object_ids", [])) if rec.get("object_ids") else "",
                        "title": rec.get("title", ""),
                        "message": rec.get("message", ""),
                        "code": rec.get("code", ""),
                        "importance": rec.get("importance", ""),
                        "confidence": rec.get("confidence", ""),
                        "blame_field": rec.get("blame_field", "")
                    })

            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch recommendations for ad set {adset_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_recommendations)
    logger.info(f"📊 Total ad set recommendations retrieved: {len(df)}")
    return df