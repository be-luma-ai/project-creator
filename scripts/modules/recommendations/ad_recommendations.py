# modules/recommendations/ad_recommendations.py

import requests
import pandas as pd
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def get_recommendations_ads_df(business_id: str, access_token: str) -> pd.DataFrame:
    """
    Fetches ad-level recommendations for all ads under the given Meta Business ID.

    Args:
        business_id (str): Meta Business ID.
        access_token (str): Meta Graph API access token.

    Returns:
        pd.DataFrame: DataFrame containing ad-level recommendations.
    """
    if not isinstance(business_id, str):
        logger.error(f"❌ Invalid business_id: {business_id}")
        return pd.DataFrame()

    all_recommendations: List[Dict] = []

    # 🔹 Step 1: Get all ad accounts
    accounts_url = f"https://graph.facebook.com/v22.0/{business_id}/owned_ad_accounts"
    accounts_params = {
        "fields": "id,name",
        "access_token": access_token
    }

    try:
        acc_resp = requests.get(accounts_url, params=accounts_params)
        acc_resp.raise_for_status()
        ad_accounts = acc_resp.json().get("data", [])
        logger.info(f"🔍 Found {len(ad_accounts)} ad accounts for Business ID {business_id}")
    except Exception as e:
        logger.error(f"❌ Failed to fetch ad accounts: {e}", exc_info=True)
        return pd.DataFrame()

    # 🔁 Step 2: For each ad account, fetch its ads and their recommendations
    for account in ad_accounts:
        ad_account_id = account.get("id")
        ads_url = f"https://graph.facebook.com/v22.0/{ad_account_id}/ads"
        ads_params = {
            "fields": "id,name,adset_id",
            "access_token": access_token
        }

        try:
            ads_resp = requests.get(ads_url, params=ads_params)
            ads_resp.raise_for_status()
            ads = ads_resp.json().get("data", [])
            logger.info(f"📦 {len(ads)} ads found for ad account {ad_account_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch ads for account {ad_account_id}: {e}", exc_info=True)
            continue

        for ad in ads:
            ad_id = ad.get("id")
            adset_id = ad.get("adset_id", "")
            rec_url = f"https://graph.facebook.com/v22.0/{ad_id}"
            rec_params = {
                "fields": "recommendations",
                "access_token": access_token
            }

            try:
                rec_resp = requests.get(rec_url, params=rec_params)
                rec_resp.raise_for_status()
                rec_data = rec_resp.json()
                recommendations = rec_data.get("recommendations", [])

                if isinstance(recommendations, list):
                    for rec in recommendations:
                        all_recommendations.append({
                            "object_type": "Ad",
                            "object_id": ad_id,
                            "ad_account_id": ad_account_id,
                            "adset_id": adset_id,
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
                logger.warning(f"⚠️ Failed to fetch recommendations for ad {ad_id}: {e}", exc_info=True)

    df = pd.DataFrame(all_recommendations)
    logger.info(f"📊 Total ad-level recommendations retrieved: {len(df)}")

    return df