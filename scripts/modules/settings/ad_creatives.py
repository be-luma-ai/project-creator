import json
import logging
from typing import List, Dict, Optional

import pandas as pd

from scripts.utilities.meta_ads_api import call_meta_api
from scripts.utilities.image_storage import process_and_store_creative_images
from scripts.utilities.video_storage import process_and_store_creative_videos

logger = logging.getLogger(__name__)


def extract_creative_format(creative_data: dict) -> str:
    """
    Extract creative format from creative data using the same logic as BigQuery function.

    Args:
        creative_data (dict): Creative data from Meta API

    Returns:
        str: Creative format (CAROUSEL, VIDEO, DYNAMIC/ADVANTAGE+, SINGLE_IMAGE/LINK, etc.)
    """
    # Get object_story_spec
    object_story_spec = creative_data.get("object_story_spec", {})
    if isinstance(object_story_spec, str):
        try:
            object_story_spec = json.loads(object_story_spec)
        except Exception:
            object_story_spec = {}

    # 1. Check for Carousel: child_attachments present and not empty
    child_attachments = object_story_spec.get("child_attachments")
    if child_attachments and child_attachments not in ([], [{}]):
        return "CAROUSEL"

    # 2. Check for Video: video_id or video_data
    video_id = creative_data.get("video_id")
    video_data = object_story_spec.get("video_data")
    if video_id or video_data:
        return "VIDEO"

    # 3. Check for Dynamic/Advantage+: asset_feed_spec with content or product_set_id
    asset_feed_spec = creative_data.get("asset_feed_spec", {})
    if isinstance(asset_feed_spec, str):
        try:
            asset_feed_spec = json.loads(asset_feed_spec)
        except Exception:
            asset_feed_spec = {}

    product_set_id = creative_data.get("product_set_id")
    if (asset_feed_spec and asset_feed_spec not in ({}, [])) or product_set_id:
        return "DYNAMIC/ADVANTAGE+"

    # 4. Check for Single Image/Link: link_data, image_hash or photo_url
    link_data = object_story_spec.get("link_data")
    image_hash = creative_data.get("image_hash")
    photo_data = object_story_spec.get("photo_data", {})
    photo_url = photo_data.get("url") if isinstance(photo_data, dict) else None

    if link_data or image_hash or photo_url:
        return "SINGLE_IMAGE/LINK"

    # 5. Check for Promoted post
    page_id = object_story_spec.get("page_id")
    link_in_link_data = link_data.get("link") if isinstance(link_data, dict) else None
    if page_id and not link_in_link_data:
        return "PROMOTED_POST"

    return "UNKNOWN"


def extract_destination_urls(creative_data: dict) -> dict:
    """
    Extract destination URLs from creative data.

    Args:
        creative_data (dict): Creative data from Meta API

    Returns:
        dict: Dictionary with different URL types
    """
    urls = {
        "primary_url": "",
        "link_url": "",
        "object_url": "",
        "template_url": "",
        "instagram_url": "",
    }

    # Extract from direct fields
    urls["link_url"] = creative_data.get("link_url", "")
    urls["object_url"] = creative_data.get("object_url", "")
    urls["template_url"] = creative_data.get("template_url", "")
    urls["instagram_url"] = creative_data.get("instagram_permalink_url", "")

    # Set primary URL (most important)
    urls["primary_url"] = (
        urls["link_url"]
        or urls["object_url"]
        or urls["template_url"]
        or ""
    )

    return urls


def extract_object_story_data(object_story_spec: dict) -> dict:
    """
    Extract data from object_story_spec nested structure.

    Args:
        object_story_spec (dict): Object story spec data

    Returns:
        dict: Extracted data from object story spec
    """
    if not isinstance(object_story_spec, dict):
        return {}

    data = {
        "page_id": "",
        "instagram_actor_id": "",
        "link_url": "",
        "link_caption": "",
        "link_name": "",
        "link_description": "",
        "link_message": "",
        "link_call_to_action": "",
        "video_id": "",
        "video_title": "",
        "video_message": "",
        "video_call_to_action": "",
        "template_message": "",
        "template_call_to_action": "",
        "template_link": "",
        "photo_url": "",
        "photo_caption": "",
    }

    # page_id / instagram_actor_id
    data["page_id"] = object_story_spec.get("page_id", "")
    data["instagram_actor_id"] = object_story_spec.get("instagram_actor_id", "")

    # link_data
    link_data = object_story_spec.get("link_data", {})
    if isinstance(link_data, dict):
        data["link_url"] = link_data.get("link", "")
        data["link_caption"] = link_data.get("caption", "")
        data["link_name"] = link_data.get("name", "")
        data["link_description"] = link_data.get("description", "")
        data["link_message"] = link_data.get("message", "")
        data["link_call_to_action"] = json.dumps(
            link_data.get("call_to_action", {}), default=str
        )

    # video_data
    video_data = object_story_spec.get("video_data", {})
    if isinstance(video_data, dict):
        data["video_id"] = video_data.get("video_id", "")
        data["video_title"] = video_data.get("title", "")
        data["video_message"] = video_data.get("message", "")
        data["video_call_to_action"] = json.dumps(
            video_data.get("call_to_action", {}), default=str
        )

    # template_data
    template_data = object_story_spec.get("template_data", {})
    if isinstance(template_data, dict):
        data["template_message"] = template_data.get("message", "")
        data["template_call_to_action"] = json.dumps(
            template_data.get("call_to_action", {}), default=str
        )
        data["template_link"] = template_data.get("link", "")

    # photo_data
    photo_data = object_story_spec.get("photo_data", {})
    if isinstance(photo_data, dict):
        data["photo_url"] = photo_data.get("url", "")
        data["photo_caption"] = photo_data.get("caption", "")

    return data


CREATIVE_FIELDS = [
    # Identificación básica
    "id",
    "name",
    "account_id",
    "actor_id",
    "status",
    "adlabels",

    # Copy / tipo / producto
    "body",
    "call_to_action_type",
    "object_type",
    "product_set_id",
    "url_tags",

    # Imagen / video
    "image_hash",
    "image_url",
    "thumbnail_url",
    "video_id",

    # URLs directas
    "link_url",
    "object_url",
    "template_url",
    "instagram_permalink_url",

    # Story / asset spec
    "object_story_spec",
    "effective_object_story_id",
    "effective_instagram_media_id",
    "template_url_spec",
    "asset_feed_spec",
]


def get_creatives_df(
    ad_accounts: List[Dict[str, str]],
    client_slug: Optional[str] = None,
    bucket_name: Optional[str] = None,
    date_suffix: Optional[str] = None,
    download_images: bool = False,
    download_videos: bool = False,
    gcs_credentials: Optional[Dict] = None,
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    access_token: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch ad creatives from a list of ad accounts.

    Args:
        ad_accounts (List[Dict[str, str]]): List of ad account dicts with metadata.
        client_slug (str, optional): Client slug for organizing images in GCS.
        bucket_name (str, optional): GCS bucket name for storing images.
        date_suffix (str, optional): Date suffix for organizing images (e.g., '20251001').
        download_images (bool): Whether to download and store images in Cloud Storage.
        gcs_credentials (dict, optional): Service account credentials for Cloud Storage.
        limit (int, optional): Limit the number of creatives to fetch (for testing).
        project_id (str, optional): GCP project ID where the bucket is located.

    Returns:
        pd.DataFrame: DataFrame with creative metadata.
    """
    creative_list = []
    # Track how many creatives we've processed (for limiting search when download_images is enabled)
    processed_count = 0
    # Track how many images and videos we've successfully stored
    images_stored = 0
    videos_stored = 0
    # Maximum search limit: if download_images is enabled, search up to 10x the limit to find creatives with images
    max_search_limit = (limit * 10) if (limit and download_images) else None
    
    # When both download_images and download_videos are enabled, we want 1 of each
    target_images = 1 if download_images else 0
    target_videos = 1 if download_videos else 0
    need_images = target_images > 0
    need_videos = target_videos > 0

    logger.info("🎨 Retrieving ad creatives from %d ad accounts...", len(ad_accounts))
    if limit:
        logger.info("📊 Global limit: %d creatives total (across all ad accounts)", limit)
        if download_images:
            logger.info("🔍 Will search up to %d creatives to find ones with image_url", max_search_limit)
    if need_images and need_videos:
        logger.info("🎯 Goal: Find 1 creative with image and 1 creative with video")

    for idx, acc in enumerate(ad_accounts):
        # Check if we've found what we need (1 image + 1 video)
        if need_images and need_videos:
            if images_stored >= target_images and videos_stored >= target_videos:
                logger.info("✅ Found required creatives: %d image(s) and %d video(s), stopping", images_stored, videos_stored)
                break
        elif need_images:
            if images_stored >= target_images:
                logger.info("✅ Found required creatives: %d image(s), stopping", images_stored)
                break
        elif need_videos:
            if videos_stored >= target_videos:
                logger.info("✅ Found required creatives: %d video(s), stopping", videos_stored)
                break
        
        # Check if we've reached the global limit
        if limit and len(creative_list) >= limit:
            logger.info("✅ Reached global limit of %d creatives, stopping", limit)
            break
        
        # Check if we've exceeded max search limit (when looking for creatives with images)
        if max_search_limit and processed_count >= max_search_limit:
            logger.warning("⚠️ Reached max search limit of %d creatives, stopping search", max_search_limit)
            break
        
        ad_account_id = acc["account_id"]
        account_name = acc["account_name"]
        currency = acc["currency"]
        
        logger.info(f"📥 Processing ad account {idx+1}/{len(ad_accounts)}: {account_name} ({ad_account_id})")
        
        # Add delay between ad accounts to avoid rate limiting (except for the first one)
        if idx > 0:
            import time
            delay = 2  # 2 seconds between ad accounts
            logger.info(f"⏳ Waiting {delay} seconds before next ad account...")
            time.sleep(delay)

        try:
            api_params = {}
            # Calculate how many more creatives we need to fetch
            # If download_images is enabled, fetch more to find ones with images
            if limit:
                if download_images:
                    # Fetch more to increase chances of finding creatives with images
                    remaining = max(limit - len(creative_list), 10)  # Fetch at least 10 at a time
                    if max_search_limit:
                        remaining = min(remaining, max_search_limit - processed_count)
                    api_params["limit"] = remaining
                else:
                    remaining = limit - len(creative_list)
                    if remaining > 0:
                        api_params["limit"] = remaining
                    else:
                        # Already reached limit, skip this account
                        logger.info("⏭️ Skipping account %s: global limit already reached", account_name)
                        continue
            elif max_search_limit:
                # No limit specified, but we have max_search_limit for image search
                remaining = max_search_limit - processed_count
                if remaining > 0:
                    api_params["limit"] = min(remaining, 50)  # Fetch up to 50 at a time
            
            creatives = call_meta_api(
                object_id=ad_account_id,
                edge="adcreatives",
                fields=CREATIVE_FIELDS,
                params=api_params
            )

            logger.info(
                "✅ %d creatives fetched from account %s - %s",
                len(creatives),
                ad_account_id,
                account_name,
            )

            for creative in creatives:
                # Check if we've found what we need (1 image + 1 video)
                if need_images and need_videos:
                    if images_stored >= target_images and videos_stored >= target_videos:
                        logger.info("✅ Found required creatives: %d image(s) and %d video(s), stopping", images_stored, videos_stored)
                        break
                elif need_images:
                    if images_stored >= target_images:
                        logger.info("✅ Found required creatives: %d image(s), stopping", images_stored)
                        break
                elif need_videos:
                    if videos_stored >= target_videos:
                        logger.info("✅ Found required creatives: %d video(s), stopping", videos_stored)
                        break
                
                # Check if we've reached the global limit before processing this creative
                if limit and len(creative_list) >= limit:
                    logger.info("✅ Reached global limit of %d creatives, stopping processing", limit)
                    break

                # Check max search limit
                if max_search_limit and processed_count >= max_search_limit:
                    logger.warning("⚠️ Reached max search limit, stopping search")
                    break

                processed_count += 1
                
                # Normalizar object_story_spec (puede venir como string)
                object_story_spec_raw = creative.get("object_story_spec", {})
                if isinstance(object_story_spec_raw, str):
                    try:
                        object_story_spec = json.loads(object_story_spec_raw)
                    except Exception:
                        object_story_spec = {}
                else:
                    object_story_spec = object_story_spec_raw

                # Helpers
                creative_format = extract_creative_format(creative)
                urls = extract_destination_urls(creative)
                object_story_data = extract_object_story_data(object_story_spec)
                
                # Check if we should process this creative
                # Strategy: Find 1 image first, then find 1 video
                image_url = creative.get("image_url", "")
                
                # Get video_id to check if creative has video
                # Priority: object_story_spec.video_data.video_id (this one works!) first, then top-level video_id
                video_id = ""
                video_data = object_story_spec.get("video_data", {})
                if isinstance(video_data, dict):
                    video_id = video_data.get("video_id", "")
                # Fallback to top-level video_id if not found in object_story_spec
                if not video_id:
                    video_id = creative.get("video_id", "")
                
                has_image = bool(image_url)
                has_video = bool(video_id)
                
                # Determine if we should process this creative
                # Priority: Find images first, then videos
                should_process = False
                if need_images and need_videos:
                    # Both needed: prioritize images first, then videos
                    if images_stored < target_images and has_image:
                        should_process = True  # Need image, found one
                    elif images_stored >= target_images and videos_stored < target_videos and has_video:
                        should_process = True  # Have image, need video, found one
                    # Skip if: already have image and this is an image, or already have video and this is a video
                elif need_images:
                    # Only need images
                    should_process = has_image and images_stored < target_images
                elif need_videos:
                    # Only need videos
                    should_process = has_video and videos_stored < target_videos
                else:
                    # Neither enabled: process all
                    should_process = True
                
                if not should_process:
                    logger.debug(f"⏭️ Skipping creative {creative.get('id')}: doesn't match current needs (images: {images_stored}/{target_images}, videos: {videos_stored}/{target_videos})")
                    continue
                
                # Process and store image or video in Cloud Storage
                # When both are enabled, process image if available, then video if available
                cloud_storage_url = ""
                
                # Try image first (if enabled, available, and we still need images)
                if download_images and has_image and images_stored < target_images and client_slug and bucket_name and date_suffix:
                    stored_urls = process_and_store_creative_images(
                        creative_id=creative.get("id", ""),
                        creative_data=creative,
                        client_slug=client_slug,
                        bucket_name=bucket_name,
                        date_suffix=date_suffix,
                        download_images=True,
                        credentials=gcs_credentials,
                        project_id=project_id
                    )
                    # Get the GCS URL if image was stored
                    cloud_storage_url = stored_urls.get("cloud_storage_url", "")
                    if cloud_storage_url:
                        images_stored += 1
                        logger.info(f"✅ Image stored ({images_stored}/{target_images})")
                
                # If no image was stored and we need videos, try video (if enabled and available)
                if not cloud_storage_url and download_videos and has_video and videos_stored < target_videos and bucket_name:
                    stored_urls = process_and_store_creative_videos(
                        creative_id=creative.get("id", ""),
                        creative_data=creative,
                        bucket_name=bucket_name,
                        download_videos=True,
                        credentials=gcs_credentials,
                        project_id=project_id,
                        access_token=access_token
                    )
                    # Get the GCS URL if video was stored
                    cloud_storage_url = stored_urls.get("cloud_storage_url", "")
                    if cloud_storage_url:
                        videos_stored += 1
                        logger.info(f"✅ Video stored ({videos_stored}/{target_videos})")

                creative_list.append(
                    {
                        "creative_id": creative.get("id"),
                        "name": creative.get("name", ""),
                        "account_id": creative.get("account_id", ad_account_id),
                        "account_name": account_name,
                        "currency": currency,

                        "actor_id": creative.get("actor_id", ""),
                        "status": creative.get("status", ""),
                        "adlabels": json.dumps(
                            creative.get("adlabels", {}), default=str
                        ),

                        "body": creative.get("body", ""),
                        "call_to_action_type": creative.get(
                            "call_to_action_type", ""
                        ),
                        "object_type": creative.get("object_type", ""),

                        "image_hash": creative.get("image_hash", ""),
                        "image_url": creative.get("image_url", ""),  # Original URL from Meta
                        "thumbnail_url": creative.get("thumbnail_url", ""),
                        "video_id_raw": creative.get("video_id", ""),
                        "cloud_storage_url": cloud_storage_url,  # GCS URL for image or video (if downloaded)

                        "url_tags": creative.get("url_tags", ""),
                        "product_set_id": creative.get("product_set_id", ""),

                        "effective_object_story_id": creative.get(
                            "effective_object_story_id", ""
                        ),
                        "effective_instagram_media_id": creative.get(
                            "effective_instagram_media_id", ""
                        ),

                        "template_url_spec": json.dumps(
                            creative.get("template_url_spec", {}), default=str
                        ),
                        "asset_feed_spec": json.dumps(
                            creative.get("asset_feed_spec", {}), default=str
                        ),

                        # Formato y URLs (helpers)
                        "creative_format": creative_format,
                        "primary_url": urls["primary_url"],
                        "link_url": urls["link_url"],
                        "object_url": urls["object_url"],
                        "template_url": urls["template_url"],
                        "instagram_url": urls["instagram_url"],

                        # Datos derivados de object_story_spec
                        "page_id": object_story_data["page_id"],
                        "instagram_actor_id": object_story_data["instagram_actor_id"],
                        "link_url_from_spec": object_story_data["link_url"],
                        "link_caption": object_story_data["link_caption"],
                        "link_name": object_story_data["link_name"],
                        "link_description": object_story_data["link_description"],
                        "link_message": object_story_data["link_message"],
                        "link_call_to_action": object_story_data[
                            "link_call_to_action"
                        ],
                        "video_id": object_story_data["video_id"],
                        "video_title": object_story_data["video_title"],
                        "video_message": object_story_data["video_message"],
                        "video_call_to_action": object_story_data[
                            "video_call_to_action"
                        ],
                        "template_message": object_story_data["template_message"],
                        "template_call_to_action": object_story_data[
                            "template_call_to_action"
                        ],
                        "template_link": object_story_data["template_link"],
                        "photo_url": object_story_data["photo_url"],
                        "photo_caption": object_story_data["photo_caption"],

                        # Raw JSON para debugging
                        "object_story_spec": json.dumps(
                            object_story_spec, default=str
                        ),
                    }
                )

        except Exception as e:
            logger.warning(
                "⚠️ Failed to fetch creatives for account %s: %s",
                ad_account_id,
                e,
                exc_info=True,
            )

    df = pd.DataFrame(creative_list)

    if not df.empty:
        logger.info("📈 Total creatives processed: %d", len(df))
    else:
        logger.warning(
            "⚠️ No creatives found for any of the provided ad accounts."
        )

    return df