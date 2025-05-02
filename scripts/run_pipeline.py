# scripts/run_pipeline.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
import logging
from google.cloud import bigquery
from google.auth.exceptions import GoogleAuthError
from google.cloud.exceptions import GoogleCloudError

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Internal imports
from utilities.logger_setup import setup_logger
from utilities.load_credentials import load_meta_access_token, load_clients_config
from utilities.run_config import get_run_config
from utilities.run_for_client import run_for_client
from utilities.bigquery_uploader import upload_multiple_dataframes

# Logger setup
logger = setup_logger("meta_ads_pipeline")


def run_pipeline():
    """
    Main entry point for extracting Meta Ads data and uploading it to BigQuery
    for all configured clients.
    """
    try:
        logger.info("🚀 Starting Meta Ads pipeline...")

        # 🔐 Load credentials and run config
        access_token = load_meta_access_token()
        clients = load_clients_config()
        run_config = get_run_config()

        # Suffix for table names (usually extraction date)
        table_suffix = run_config["yesterday"]
        dataset_id = "meta_ads"

        # Control variables
        processed, failed = 0, 0

        # Define all flags ON (you can toggle specific ones to False if needed)
        data_flags = {
            "account_performance": True,
            "campaign_performance": False,
            "adset_performance": False,
            "ad_performance": False,
            "account_recommendations": False,
            "adset_recommendations": False,
            "ad_recommendations": False,
            "accounts": False,
            "campaigns": False,
            "adsets": False,
            "ads": False,
            "ad_creatives": False,
            "activities": False
        }

        for client in clients:
            slug = client.get("slug")
            logger.info(f"📥 Processing client: {slug}")

            try:
                # 🧠 Run extraction
                data = run_for_client(client, access_token, run_config, data_flags)

                # 🔐 Auth BigQuery client
                bq_client = bigquery.Client.from_service_account_info(data["service_account"])
                # Prepare all extracted DataFrames for upload
                dataframes_to_upload = {
                    key: df for key, df in data.items()
                    if key not in ["slug", "service_account"] and isinstance(df, (dict, list, tuple, str)) is False
                }

                # ⬆️ Upload
                upload_multiple_dataframes(
                    bq_client=bq_client,
                    dataset_id=dataset_id,
                    dataframes=dataframes_to_upload,
                    table_suffix=table_suffix
                )

                logger.info(f"✅ Client {slug} processed successfully.\n")
                processed += 1

            except Exception as e:
                logger.error(f"❌ Error processing client {slug}: {e}", exc_info=True)
                failed += 1

        logger.info("📦 Pipeline execution complete.")
        logger.info(f"✔️ Successfully processed clients: {processed}")
        logger.info(f"❌ Clients with errors: {failed}")
        logger.info(f"📅 Extraction date: {table_suffix}")

    except GoogleAuthError as auth_err:
        logger.critical(f"🔐 Authentication error: {auth_err}", exc_info=True)
    except GoogleCloudError as cloud_err:
        logger.critical(f"☁️ Google Cloud error: {cloud_err}", exc_info=True)
    except Exception as e:
        logger.critical(f"🚨 Unexpected error in pipeline: {e}", exc_info=True)

