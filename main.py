"""
Firestore → Cloud function trigger that provisions client infrastructure.

Steps:
1. Triggered when a document is created in `clients/{clientId}`.
2. Creates a GCP project under the provided folder.
3. Enables required APIs and links billing (optional).
4. Ensures the `meta_ads` dataset exists in the new project.
5. Updates the `clients.json` manifest stored in Cloud Storage.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.cloud import storage
from googleapiclient import discovery
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENTS_BUCKET = os.getenv("CLIENTS_CONFIG_BUCKET", "clients-config")
CLIENTS_FILENAME = os.getenv("CLIENTS_CONFIG_FILENAME", "clients.json")
CLIENT_FOLDER_ID = os.getenv("CLIENT_FOLDER_ID", "555317256759")
BILLING_ACCOUNT_ID = os.getenv("BILLING_ACCOUNT_ID")
DATASET_ID = os.getenv("DATASET_ID", "meta_ads")
REQUIRED_APIS = [
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
]


def create_client_infra(event: Dict[str, Any], context) -> None:
    """Entry point for Firestore triggers (CREATE on clients collection)."""
    value = event.get("value", {})
    fields = value.get("fields")

    if not fields:
        logger.warning("No fields in Firestore event, skipping")
        return

    client = _decode_firestore_fields(fields)

    project_id = client.get("project_id")
    slug = client.get("slug")

    if not project_id or not slug:
        logger.warning("Client missing project_id or slug, skipping: %s", client)
        return

    crm = discovery.build("cloudresourcemanager", "v3", cache_discovery=False)
    serviceusage = discovery.build("serviceusage", "v1", cache_discovery=False)

    logger.info("Provisioning project %s for client %s", project_id, slug)
    ensure_project(crm, project_id, client.get("name") or project_id)
    enable_apis(serviceusage, project_id, REQUIRED_APIS)
    link_billing(project_id)
    ensure_bigquery_dataset(project_id, DATASET_ID)
    update_clients_manifest(client)

    logger.info("Client %s provisioning complete", slug)


def ensure_project(crm, project_id: str, display_name: str) -> None:
    """Create the project if it does not exist."""
    try:
        crm.projects().get(name=f"projects/{project_id}").execute()
        logger.info("Project %s already exists", project_id)
        return
    except HttpError as err:
        if err.resp.status != 404:
            raise

    body = {
        "projectId": project_id,
        "displayName": display_name[:30],
        "parent": {
            "type": "folder",
            "id": CLIENT_FOLDER_ID,
        },
    }

    operation = crm.projects().create(body=body).execute()
    wait_for_operation(crm, operation["name"], "Project creation")
    logger.info("Project %s created under folder %s", project_id, CLIENT_FOLDER_ID)


def wait_for_operation(crm, operation_name: str, description: str, timeout: int = 600) -> None:
    """Poll Cloud Resource Manager operations until completion."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        op = crm.operations().get(name=operation_name).execute()
        if op.get("done"):
            if "error" in op:
                raise RuntimeError(f"{description} failed: {op['error']}")
            return
        time.sleep(5)
    raise TimeoutError(f"{description} did not finish before timeout")


def enable_apis(serviceusage, project_id: str, apis: List[str]) -> None:
    """Enable required APIs; ignore if already enabled."""
    for api in apis:
        name = f"projects/{project_id}/services/{api}"
        try:
            serviceusage.services().enable(name=name, body={}).execute()
            logger.info("Enabled API %s", api)
        except HttpError as err:
            if err.resp.status == 409:
                logger.info("API %s already enabled", api)
                continue
            raise


def link_billing(project_id: str) -> None:
    """Attach a billing account if BILLING_ACCOUNT_ID is provided."""
    if not BILLING_ACCOUNT_ID:
        logger.info("Skipping billing linkage, BILLING_ACCOUNT_ID not set")
        return

    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    name = f"projects/{project_id}"
    body = {"billingAccountName": f"billingAccounts/{BILLING_ACCOUNT_ID}"}

    billing.projects().updateBillingInfo(name=name, body=body).execute()
    logger.info("Billing account %s linked to %s", BILLING_ACCOUNT_ID, project_id)


def ensure_bigquery_dataset(project_id: str, dataset_id: str) -> None:
    """Create the dataset if it does not exist."""
    client = bigquery.Client(project=project_id)
    dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
    dataset_ref.location = "US"

    try:
        client.get_dataset(dataset_ref)
        logger.info("Dataset %s already exists in %s", dataset_id, project_id)
    except Exception:
        client.create_dataset(dataset_ref, exists_ok=True)
        logger.info("Dataset %s created in %s", dataset_id, project_id)


def update_clients_manifest(client: Dict[str, Any]) -> None:
    """Ensure clients.json is updated with the latest client entry."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLIENTS_BUCKET)
    blob = bucket.blob(CLIENTS_FILENAME)

    entries: List[Dict[str, Any]]

    if blob.exists():
        entries = json.loads(blob.download_as_text())
    else:
        entries = []

    filtered = [row for row in entries if row.get("slug") != client.get("slug")]
    filtered.append(
        {
            "slug": client.get("slug") or "",
            "project_id": client.get("project_id") or "",
            "google_ads_customer_id": client.get("google_ads_customer_id") or "",
            "business_id": client.get("business_id") or "",
        }
    )

    blob.upload_from_string(json.dumps(filtered, indent=2), content_type="application/json")
    logger.info("clients.json updated with slug %s", client.get("slug"))


def _decode_firestore_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Firestore event representation into a flat dict."""
    decoded = {}
    for key, value in fields.items():
        decoded[key] = _decode_value(value)
    return decoded


def _decode_value(value: Dict[str, Any]) -> Any:
    if "stringValue" in value:
        return value["stringValue"]
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "booleanValue" in value:
        return value["booleanValue"]
    if "arrayValue" in value:
        return [_decode_value(v) for v in value["arrayValue"].get("values", [])]
    if "mapValue" in value:
        return _decode_firestore_fields(value["mapValue"].get("fields", {}))
    if "timestampValue" in value:
        return value["timestampValue"]
    if "nullValue" in value:
        return None
    return None

