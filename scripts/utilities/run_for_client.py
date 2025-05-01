# scripts/utilities/run_for_client.py

import logging
from typing import Dict, Any

from facebook_business.api import FacebookAdsApi

from modules.settings.accounts import get_ad_accounts_df
from modules.settings.campaigns import get_campaigns_df
from modules.settings.adsets import get_adsets_df
from modules.settings.ads import get_ads_df
from modules.settings.ad_creatives import get_creatives_df

from modules.recommendations.account_recommendations import get_recommendations_ad_accounts_df
from modules.recommendations.adset_recommendations import get_recommendations_adsets_df
from modules.recommendations.ad_recommendations import get_recommendations_ads_df

from modules.performance.main.account_performance import get_account_performance_df
from modules.performance.main.campaign_performance import get_campaign_performance_df
from modules.performance.main.adset_performance import get_adset_performance_df
from modules.performance.main.ad_performance import get_ad_performance_df

from modules.change_history.activities import get_activities_df
from utilities.load_credentials import load_service_account_json

logger = logging.getLogger(__name__)

def run_for_client(client: Dict[str, Any], access_token: str, run_config: Dict[str, Any], data_flags: Dict[str, bool]) -> Dict[str, Any]:
    """
    Extract all Meta Ads data for a single client.

    Args:
        client (dict): Contains 'slug', 'business_id', and 'service_account'.
        access_token (str): Meta Graph API access token.
        run_config (dict): Run configuration including 'since_date'.
        data_flags (dict): Dict of flags to toggle which datasets to extract.

    Returns:
        dict: Extracted DataFrames and client metadata.
    """
    slug = client.get("slug")
    service_account = load_service_account_json(client["slug"])    
    business_id = client.get("business_id")

    if not all([slug, service_account, business_id]):
        logger.error("❌ Client configuration is missing 'slug', 'business_id' or 'service_account'.")
        return {}

    try:
        logger.info(f"🔐 Initializing Meta API for client: {slug}")
        FacebookAdsApi.init(access_token=access_token)

        results = {
            "slug": slug,
            "service_account": service_account
        }

        ad_account_records = []

        needs_ad_accounts = any(data_flags.get(f) for f in [
            "accounts", "campaigns", "adsets", "ads", "ad_creatives",
            "account_performance", "campaign_performance", "adset_performance", "ad_performance",
            "activities"
        ])

        if needs_ad_accounts:
            logger.info("📂 Fetching ad accounts...")
            df_accounts = get_ad_accounts_df(business_id)
            ad_account_records = df_accounts.to_dict("records")
            if data_flags.get("accounts"):
                results["accounts"] = df_accounts

        if data_flags.get("campaigns"):
            results["campaigns"] = get_campaigns_df(ad_account_records)

        if data_flags.get("adsets"):
            results["adsets"] = get_adsets_df(ad_account_records)

        if data_flags.get("ads"):
            results["ads"] = get_ads_df(ad_account_records)

        if data_flags.get("ad_creatives"):
            results["ad_creatives"] = get_creatives_df(ad_account_records)

        if data_flags.get("account_recommendations"):
            results["account_recommendations"] = get_recommendations_ad_accounts_df(business_id, access_token)

        if data_flags.get("adset_recommendations"):
            results["adset_recommendations"] = get_recommendations_adsets_df(business_id, access_token)

        if data_flags.get("ad_recommendations"):
            results["ad_recommendations"] = get_recommendations_ads_df(business_id, access_token)

        if data_flags.get("account_performance"):
            results["account_performance"] = get_account_performance_df(ad_account_records, run_config)

        if data_flags.get("campaign_performance"):
            results["campaign_performance"] = get_campaign_performance_df(ad_account_records, run_config)

        if data_flags.get("adset_performance"):
            results["adset_performance"] = get_adset_performance_df(ad_account_records, run_config)

        if data_flags.get("ad_performance"):
            results["ad_performance"] = get_ad_performance_df(ad_account_records, run_config)

        if data_flags.get("activities"):
            results["activities"] = get_activities_df(ad_account_records, run_config["since_date"])

        logger.info(f"✅ Data successfully extracted for client: {slug}")
        return results

    except Exception as e:
        logger.error(f"❌ Error processing client {slug}: {e}", exc_info=True)
        return {
            "slug": slug,
            "service_account": service_account
        }