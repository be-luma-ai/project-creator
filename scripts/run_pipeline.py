# scripts/run_pipeline.py

import sys
import os
import time
import logging
from google.cloud import bigquery
from google.auth.exceptions import GoogleAuthError
from google.cloud.exceptions import GoogleCloudError

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Internal imports
from scripts.utilities.logger_setup import setup_logger
from scripts.utilities.load_credentials import (
    load_meta_access_token, 
    load_clients_config,
    load_bigquery_service_account,
    load_cloud_storage_service_account
)
from scripts.utilities.run_config import get_run_config
from scripts.utilities.run_for_client import run_for_client
from scripts.utilities.bigquery_uploader import upload_multiple_dataframes

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
        
        # Load central service accounts (once for all clients)
        bq_service_account = load_bigquery_service_account()
        gcs_service_account = load_cloud_storage_service_account()

        # Suffix for table names (usually extraction date)
        table_suffix = run_config["yesterday"]
        dataset_id = "meta_ads"

        # Control variables
        processed, failed = 0, 0

        # Data extraction flags - configurable from run_config (env vars)
        data_flags = {
            "ads": run_config.get("extract_ads", True),
            "ad_creatives": run_config.get("extract_ad_creatives", True),
            "ad_performance": run_config.get("extract_ad_performance", True)
        }
        
        logger.info("📋 Data extraction flags:")
        logger.info(f"   Extract ads: {data_flags['ads']}")
        logger.info(f"   Extract ad creatives: {data_flags['ad_creatives']}")
        logger.info(f"   Extract ad performance: {data_flags['ad_performance']}")

        for i, client in enumerate(clients):
            slug = client.get("slug")
            business_id = client.get("business_id")
            logger.info(f"📥 Processing client: {slug}")

            # Add delay between clients (except for the first one)
            if i > 0:
                logger.info("⏳ Waiting 10 seconds between clients to avoid rate limiting...")
                time.sleep(10)

            # Skip clients with invalid business IDs
            if not business_id or business_id == "123" or not business_id.isdigit():
                logger.warning(f"⚠️ Skipping client {slug}: Invalid business_id '{business_id}'")
                failed += 1
                continue

            try:
                # 🧠 Run extraction
                data = run_for_client(client, access_token, run_config, data_flags, gcs_service_account)

                # Check if we got any data
                if not data or not data.get("project_id"):
                    logger.warning(f"⚠️ No data or project_id for client {slug}, skipping upload")
                    failed += 1
                    continue

                # 🔐 Auth BigQuery client with central service account
                # Use client's project_id explicitly for cross-project access
                client_project_id = data.get("project_id")
                logger.info(f"📊 Uploading to BigQuery project: {client_project_id}")
                
                bq_client = bigquery.Client.from_service_account_info(bq_service_account, project=client_project_id)
                # Prepare all extracted DataFrames for upload
                dataframes_to_upload = {
                    key: df for key, df in data.items()
                    if key not in ["slug", "project_id"] and isinstance(df, (dict, list, tuple, str)) is False
                }

                # Only upload if we have data
                if dataframes_to_upload:
                    # ⬆️ Upload
                    upload_multiple_dataframes(
                        bq_client=bq_client,
                        dataset_id=dataset_id,
                        dataframes=dataframes_to_upload,
                        table_suffix=table_suffix
                    )
                    logger.info(f"✅ Client {slug} processed successfully with {len(dataframes_to_upload)} datasets.\n")
                else:
                    logger.warning(f"⚠️ No data to upload for client {slug}")
                
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


if __name__ == "__main__":
    run_pipeline()

