import time
import json
import logging
import requests
from typing import List, Dict, Any
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.business import Business

logger = logging.getLogger(__name__)

def call_meta_api(
    object_id: str,
    method: str = "GET",
    edge: str = "",
    fields: List[str] = [],
    params: Dict[str, Any] = {},
    max_retries: int = 5,
    sleep_seconds: int = 2,
    base_delay: int = 1
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

    # Get access token from session, or load it if not initialized
    api = FacebookAdsApi.get_default_api()
    if api is None or not hasattr(api, '_session') or api._session is None:
        # API not initialized, load token directly
        from scripts.utilities.load_credentials import load_meta_access_token
        access_token = load_meta_access_token()
        # Initialize for future calls
        FacebookAdsApi.init(access_token=access_token)
    else:
        access_token = api._session.access_token
    
    base_url = f"https://graph.facebook.com/v23.0/{path}"

    while attempt < max_retries:
        try:
            logger.info(f"📡 Calling Meta API: {base_url} (Attempt {attempt+1})")

            response = requests.get(base_url, params={**query, "access_token": access_token})
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("data", []))
            
            # Check if we have a limit and already reached it
            limit_value = params.get("limit") if isinstance(params, dict) else None
            if limit_value and len(results) >= limit_value:
                logger.info(f"✅ Reached limit of {limit_value} records, stopping pagination")
                results = results[:limit_value]
                return results

            # Handle pagination - with error handling to preserve already fetched data
            while "paging" in data and "next" in data["paging"]:
                # Check limit before fetching next page
                if limit_value and len(results) >= limit_value:
                    logger.info(f"✅ Reached limit of {limit_value} records, stopping pagination")
                    results = results[:limit_value]
                    break
                    
                next_url = data["paging"]["next"]
                logger.info(f"➡️ Following next page: {next_url}")
                try:
                    response = requests.get(next_url)
                    response.raise_for_status()
                    data = response.json()
                    results.extend(data.get("data", []))
                    logger.info(f"✅ Retrieved {len(data.get('data', []))} records from next page (Total: {len(results)})")
                    
                    # Check limit after fetching
                    if limit_value and len(results) >= limit_value:
                        logger.info(f"✅ Reached limit of {limit_value} records, stopping pagination")
                        results = results[:limit_value]
                        break
                except Exception as page_error:
                    logger.warning(f"⚠️ Error during pagination, but preserving {len(results)} already fetched records: {page_error}")
                    # Break pagination loop but keep the results we already have
                    break

            logger.info(f"✅ Retrieved {len(results)} records from /{path}")
            return results

        except FacebookRequestError as e:
            error_code = e.api_error_code()
            error_message = e.api_error_message()
            logger.warning(f"⚠️ Meta API error on /{path}: {error_message} (Code: {error_code})")
            
            # Rate limiting errors - use exponential backoff
            if error_code in [80004, 17, 4, 32]:
                delay = base_delay * (2 ** attempt) + sleep_seconds
                logger.warning(f"⏳ Rate limit hit. Waiting {delay} seconds before retry {attempt+1}/{max_retries}...")
                time.sleep(delay)
                attempt += 1
            elif e.api_transient:
                # Transient errors - shorter delay
                delay = sleep_seconds + (attempt * 2)
                logger.warning(f"⏳ Transient error. Waiting {delay} seconds before retry {attempt+1}/{max_retries}...")
                time.sleep(delay)
                attempt += 1
            else:
                logger.error(f"❌ Fatal Meta API error on /{path}: {e}")
                break
        except requests.exceptions.RequestException as e:
            logger.warning(f"🌐 Request error: {e}")
            if attempt < max_retries - 1:
                delay = sleep_seconds + (attempt * 2)
                logger.warning(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
                attempt += 1
            else:
                logger.error(f"❌ Max retries reached for /{path}")
                break
        except Exception as e:
            logger.error(f"❌ Unexpected error on /{path}: {e}")
            break

    return []

def call_meta_api_business(object_id: str, edge: str, fields: List[str], params: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
    """
    Call Meta API using facebook-business library for better authentication.
    Specifically for Business Manager endpoints like owned_ad_accounts.
    """
    try:
        logger.info(f"📡 Calling Meta API with facebook-business: {object_id}/{edge}")
        
        # Initialize Facebook API if not already done
        from facebook_business.api import FacebookAdsApi
        if not FacebookAdsApi.get_default_api():
            # Get access token from the current session or load it
            from scripts.utilities.load_credentials import load_meta_access_token
            access_token = load_meta_access_token()
            FacebookAdsApi.init(access_token=access_token)
        
        # Use Business object for owned_ad_accounts
        if edge == "owned_ad_accounts":
            business = Business(object_id)
            cursor = business.get_owned_ad_accounts(fields=fields, params=params)
            
            # Convert cursor to list
            data = []
            for account in cursor:
                if hasattr(account, 'export_all_data'):
                    data.append(account.export_all_data())
                else:
                    data.append(account)
            
            logger.info(f"📊 Retrieved {len(data)} accounts from Business API")
            return data
        else:
            # Fallback to regular call_meta_api for other endpoints
            return call_meta_api(object_id, "GET", edge, fields, params)
            
    except Exception as e:
        logger.error(f"❌ Error in call_meta_api_business: {e}")
        return []