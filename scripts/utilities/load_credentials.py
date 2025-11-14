import json
import logging
from typing import Dict, List, Any
from google.cloud import secretmanager
from google.cloud import storage
logger = logging.getLogger(__name__)

# 📌 1. Meta access token desde Secret Manager
def load_meta_access_token() -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/497033857194/secrets/meta-access-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token_raw = response.payload.data.decode("utf-8")
        token = json.loads(token_raw)["ACCESS_TOKEN"]
        logger.info("🔑 Meta access token loaded from Secret Manager.")
        return token
    except Exception as e:
        logger.error(f"❌ Failed to load Meta access token: {e}")
        raise RuntimeError(f"❌ Failed to load Meta access token: {e}")

# 👥 2. Clients config desde Cloud Storage
def load_clients_config() -> List[Dict[str, Any]]:
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket("clients-config")
        blob = bucket.blob("clients.json")
        content = blob.download_as_text()
        clients = json.loads(content)
        logger.info(f"👥 Loaded {len(clients)} clients from GCS.")
        return clients
    except Exception as e:
        logger.error(f"❌ Failed to load client config: {e}")
        raise RuntimeError(f"❌ Failed to load client config: {e}")

# 🔐 3. Service account centralizada para BigQuery desde Secret Manager
def load_bigquery_service_account() -> Dict[str, Any]:
    """
    Load the central BigQuery admin service account from Secret Manager.
    This SA has cross-project permissions to write to BigQuery in all client projects.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/497033857194/secrets/big-query-admin-sa/versions/latest"
        response = client.access_secret_version(request={"name": name})
        sa = json.loads(response.payload.data.decode("utf-8"))
        logger.info("🔐 Loaded BigQuery admin service account from Secret Manager.")
        return sa
    except Exception as e:
        logger.error(f"❌ Failed to load BigQuery service account: {e}")
        raise RuntimeError(f"❌ Failed to load BigQuery service account: {e}")

# 🔐 4. Service account centralizada para Cloud Storage desde Secret Manager
def load_cloud_storage_service_account() -> Dict[str, Any]:
    """
    Load the central Cloud Storage manager service account from Secret Manager.
    This SA has permissions to write to Cloud Storage buckets in all client projects.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/497033857194/secrets/cloud-storage-manager-sa/versions/latest"
        response = client.access_secret_version(request={"name": name})
        sa = json.loads(response.payload.data.decode("utf-8"))
        logger.info("🔐 Loaded Cloud Storage manager service account from Secret Manager.")
        return sa
    except Exception as e:
        logger.error(f"❌ Failed to load Cloud Storage service account: {e}")
        raise RuntimeError(f"❌ Failed to load Cloud Storage service account: {e}")


