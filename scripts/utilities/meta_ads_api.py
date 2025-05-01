import time
import json
import logging
import requests
from typing import List, Dict, Any
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

logger = logging.getLogger(__name__)

def call_meta_api(
    object_id: str,
    method: str = "GET",
    edge: str = "",
    fields: List[str] = [],
    params: Dict[str, Any] = {},
    max_retries: int = 3,
    sleep_seconds: int = 5
) -> List[Dict[str, Any]]:
    """
    Generic Meta Graph API caller with pagination and retry logic.

    Args:
        object_id (str): Object ID (e.g., 'act_123456' or business ID).
        method (str): HTTP method ("GET", "POST", etc.)
        edge (str): Edge to call on the object (e.g., "campaigns", "ads").
        fields (list): Fields to request.
        params (dict): Extra query params.
        max_retries (int): Retry attempts.
        sleep_seconds (int): Wait time between retries.

    Returns:
        list[dict]: API response data.
    """
    results = []
    attempt = 0

    # Serialize time_range if it's a dict
    if "time_range" in params and isinstance(params["time_range"], dict):
        params["time_range"] = json.dumps(params["time_range"])

    query = {"fields": ",".join(fields), **params}
    path = f"{object_id}/{edge}" if edge else object_id

    # Get access token from session
    api = FacebookAdsApi.get_default_api()
    access_token = api._session.access_token
    base_url = f"https://graph.facebook.com/v22.0/{path}"

    while attempt < max_retries:
        try:
            logger.info(f"📡 Calling Meta API: {base_url} (Attempt {attempt+1})")

            response = requests.get(base_url, params={**query, "access_token": access_token})
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("data", []))

            # Handle pagination
            while "paging" in data and "next" in data["paging"]:
                next_url = data["paging"]["next"]
                logger.info(f"➡️ Following next page: {next_url}")
                response = requests.get(next_url)
                response.raise_for_status()
                data = response.json()
                results.extend(data.get("data", []))

            logger.info(f"✅ Retrieved {len(results)} records from /{path}")
            return results

        except FacebookRequestError as e:
            logger.warning(f"⚠️ Meta API error on /{path}: {e.api_error_message()}")
            if e.api_transient or e.api_error_code() in [80004, 17]:
                logger.warning(f"⏳ Rate limit hit. Retrying in {sleep_seconds} sec...")
                time.sleep(sleep_seconds)
                attempt += 1
            else:
                logger.error(f"❌ Fatal Meta API error on /{path}: {e}")
                break
        except requests.exceptions.RequestException as e:
            logger.warning(f"🌐 Request error: {e}")
            attempt += 1
            time.sleep(sleep_seconds)
        except Exception as e:
            logger.error(f"❌ Unexpected error on /{path}: {e}")
            break

    return []