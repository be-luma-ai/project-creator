# core/bigquery_uploader.py

import pandas as pd
import logging
from typing import Literal
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

logger = logging.getLogger(__name__)

def upload_multiple_dataframes(
    bq_client: bigquery.Client,
    dataset_id: str,
    dataframes: dict,
    table_suffix: str,
    write_mode: Literal["WRITE_TRUNCATE", "WRITE_APPEND", "WRITE_EMPTY"] = "WRITE_TRUNCATE"
) -> None:
    """
    Uploads multiple DataFrames to BigQuery with table suffix.
    
    The BigQuery client determines the target project (from service account project_id).
    Data is uploaded to: {project_id}.{dataset_id}.{table_id}_{table_suffix}

    Args:
        bq_client (bigquery.Client): BigQuery client instance (authenticated with client's service account).
        dataset_id (str): BigQuery dataset name (e.g., 'meta_ads').
        dataframes (dict): Table name -> DataFrame mapping.
        table_suffix (str): Suffix to append to each table name (e.g., '20250325').
        write_mode (Literal): Write mode for BigQuery.
    """
    project_id = bq_client.project
    logger.info(f"🚀 Starting upload of {len(dataframes)} tables to BigQuery project: {project_id}")

    for table_id, df in dataframes.items():
        full_table_id = f"{table_id}_{table_suffix}"

        if df is None:
            logger.warning(f"⚠️ Skipping '{full_table_id}': DataFrame is None.")
            continue
        if df.empty:
            logger.warning(f"📭 Skipping '{full_table_id}': DataFrame is empty.")
            continue

        _upload_single_table(bq_client, dataset_id, full_table_id, df, write_mode)

    logger.info("📦 BigQuery upload process completed.")


def _upload_single_table(
    client: bigquery.Client,
    dataset_id: str,
    table_id: str,
    df: pd.DataFrame,
    write_mode: Literal["WRITE_TRUNCATE", "WRITE_APPEND", "WRITE_EMPTY"]
) -> None:
    """
    Uploads a single pandas DataFrame to a BigQuery table.

    Args:
        client (bigquery.Client): Authenticated BigQuery client.
        dataset_id (str): Name of the dataset where the table is located.
        table_id (str): Name of the destination table.
        df (pd.DataFrame): The DataFrame to upload.
        write_mode (Literal): Specifies the write behavior:
            - "WRITE_TRUNCATE": Overwrites the table.
            - "WRITE_APPEND": Appends to the existing table.
            - "WRITE_EMPTY": Fails if the table already exists.

    Raises:
        GoogleCloudError: If the upload fails due to a BigQuery error.
    """
    table_ref = client.dataset(dataset_id).table(table_id)
    job_config = bigquery.LoadJobConfig(write_disposition=write_mode)

    try:
        num_rows = len(df)
        project_id = client.project
        logger.info(f"⏫ Uploading {num_rows} rows to {project_id}.{dataset_id}.{table_id}...")
        load_job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        load_job.result()  # Wait until job is complete
        logger.info(f"✅ Upload successful: {project_id}.{dataset_id}.{table_id} ({num_rows} rows)")
    except GoogleCloudError as e:
        logger.error(f"❌ Failed to upload {dataset_id}.{table_id}: {e}", exc_info=True)
        raise