import json
import logging
from typing import Dict, List, Any
from google.cloud import secretmanager, storage

logger = logging.getLogger(__name__)

# 📌 1. Meta access token desde Secret Manager
def load_meta_access_token() -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/be-luma-infra/secrets/meta-access-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token = response.payload.data.decode("utf-8")
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

# 🔐 3. Service account JSON por cliente desde Secret Manager
def load_service_account_json(slug: str) -> Dict[str, Any]:
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/be-luma-infra/secrets/client-{slug}-sa/versions/latest"
        response = client.access_secret_version(request={"name": name})
        sa = json.loads(response.payload.data.decode("utf-8"))
        logger.info(f"🔐 Loaded service account for client: {slug}")
        return sa
    except Exception as e:
        logger.error(f"❌ Failed to load service account for {slug}: {e}")
        raise RuntimeError(f"❌ Failed to load service account for {slug}: {e}")