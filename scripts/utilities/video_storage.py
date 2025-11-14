# scripts/utilities/video_storage.py

import logging
import requests
import os
import subprocess
import tempfile
from typing import Optional, Dict
from urllib.parse import urlparse
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

logger = logging.getLogger(__name__)


def get_video_url_from_meta(video_id: str, access_token: str) -> Optional[str]:
    """
    Get video source URL from Meta API using video_id.
    
    Args:
        video_id (str): Video ID from Meta API
        access_token (str): Meta API access token
        
    Returns:
        str: Video source URL, or None if fetch fails
    """
    if not video_id or not access_token:
        return None
    
    try:
        # Use same API version as meta_ads_api.py (v23.0)
        url = f"https://graph.facebook.com/v23.0/{video_id}"
        params = {
            "fields": "source",
            "access_token": access_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        # Check for errors before raising
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            error_code = error_data.get("error", {}).get("code", response.status_code)
            logger.warning(f"⚠️ Failed to get video URL for video_id {video_id}: {error_code} - {error_message}")
            return None
        
        response.raise_for_status()
        data = response.json()
        source_url = data.get("source", "")
        
        if source_url:
            logger.debug(f"✅ Got video URL for video_id {video_id}")
            return source_url
        else:
            logger.warning(f"⚠️ No source URL in response for video_id {video_id}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Failed to get video URL for video_id {video_id}: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Unexpected error getting video URL for video_id {video_id}: {e}")
        return None


def download_video(url: str, timeout: int = 300) -> Optional[bytes]:
    """
    Download a video from a URL.
    
    Args:
        url (str): Video URL to download
        timeout (int): Request timeout in seconds (default 300 for large videos)
        
    Returns:
        bytes: Video data, or None if download fails
    """
    if not url or not url.startswith(('http://', 'https://')):
        return None
    
    try:
        logger.debug(f"📥 Downloading video from: {url}")
        # Meta videos require specific headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.facebook.com/',
            'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a video
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('video/'):
            logger.warning(f"⚠️ URL does not point to a video: {content_type}")
            return None
        
        video_data = response.content
        logger.debug(f"✅ Downloaded {len(video_data)} bytes")
        return video_data
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Failed to download video from {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Unexpected error downloading video from {url}: {e}")
        return None


def get_video_extension_from_url(url: str) -> str:
    """
    Extract file extension from URL, defaulting to .mp4 if not found.
    
    Args:
        url (str): Video URL
        
    Returns:
        str: File extension (e.g., '.mp4', '.mov')
    """
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    
    # Default to mp4 if no extension found
    if not ext or ext not in ['.mp4', '.mov', '.avi', '.webm', '.mkv']:
        return '.mp4'
    
    return ext


def compress_video(video_data: bytes, crf: str = '32', scale: str = '480:-2') -> Optional[bytes]:
    """
    Compress a video using ffmpeg.
    
    Args:
        video_data (bytes): Original video data
        crf (str): CRF value for compression (lower = higher quality). Default '32' for maximum compression.
        scale (str): Scale resolution (e.g., '480:-2'). Default '480:-2' for 480p with height divisible by 2.
        
    Returns:
        bytes: Compressed video data, or None if compression fails
    """
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            temp_input.write(video_data)
            temp_input_path = temp_input.name
        
        temp_output_path = temp_input_path.replace('.mp4', '_compressed.mp4')
        original_size = len(video_data)
        
        # Compress using ffmpeg - Maximum compression for AI analysis
        compress_cmd = [
            'ffmpeg', '-i', temp_input_path,
            '-vf', f'scale={scale}',  # Scale down resolution (480p for AI)
            '-c:v', 'libx264',
            '-crf', crf,  # CRF 32 = maximum compression
            '-preset', 'fast',  # Faster encoding
            '-c:a', 'aac',
            '-b:a', '64k',  # Low audio bitrate (sufficient for AI)
            '-movflags', '+faststart',  # Web optimization
            '-y',  # Overwrite output
            temp_output_path
        ]
        
        logger.debug(f"   Compression settings: CRF={crf}, Scale={scale} (maximum compression for AI)")
        
        result = subprocess.run(
            compress_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0 and os.path.exists(temp_output_path):
            with open(temp_output_path, 'rb') as f:
                compressed_data = f.read()
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size/original_size) * 100
            logger.debug(f"   Video compressed: {original_size/(1024*1024):.2f} MB -> {compressed_size/(1024*1024):.2f} MB ({compression_ratio:.1f}% reduction)")
            
            # Clean up temp files
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
            
            return compressed_data
        else:
            logger.warning(f"⚠️ Compression failed: {result.stderr}")
            # Clean up
            os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
            return None
            
    except FileNotFoundError:
        logger.warning("⚠️ ffmpeg not found. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Video compression error: {e}")
        return None


def upload_video_to_gcs(
    video_data: bytes,
    bucket_name: str,
    blob_path: str,
    content_type: Optional[str] = None,
    credentials: Optional[Dict] = None,
    project_id: Optional[str] = None
) -> Optional[str]:
    """
    Upload a video to Cloud Storage.
    
    Args:
        video_data (bytes): Video binary data
        bucket_name (str): GCS bucket name
        blob_path (str): Path within the bucket (e.g., '123456_video.mp4')
        content_type (str): MIME type (e.g., 'video/mp4'). Auto-detected if None.
        credentials (dict, optional): Service account credentials for Cloud Storage
        project_id (str, optional): GCP project ID where the bucket is located
        
    Returns:
        str: GCS URL (gs://bucket/path) if successful, None otherwise
    """
    try:
        # Create Storage client with credentials and project
        if credentials and project_id:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(credentials)
            storage_client = storage.Client(credentials=creds, project=project_id)
        elif credentials:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(credentials)
            storage_client = storage.Client(credentials=creds)
        else:
            storage_client = storage.Client(project=project_id) if project_id else storage.Client()
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Auto-detect content type from extension if not provided
        if not content_type:
            if blob_path.endswith('.mov'):
                content_type = 'video/quicktime'
            elif blob_path.endswith('.webm'):
                content_type = 'video/webm'
            else:
                content_type = 'video/mp4'
        
        blob.upload_from_string(video_data, content_type=content_type)
        
        gcs_url = f"gs://{bucket_name}/{blob_path}"
        logger.info(f"✅ Uploaded video to {gcs_url}")
        return gcs_url
        
    except GoogleCloudError as e:
        logger.error(f"❌ GCS error uploading video to {blob_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error uploading video to {blob_path}: {e}")
        return None


def process_and_store_creative_videos(
    creative_id: str,
    creative_data: Dict,
    bucket_name: str,
    download_videos: bool = True,
    credentials: Optional[Dict] = None,
    project_id: Optional[str] = None,
    access_token: Optional[str] = None
) -> Dict[str, str]:
    """
    Download and store video for a creative.
    
    Args:
        creative_id (str): Creative ID
        creative_data (dict): Creative data from Meta API
        bucket_name (str): GCS bucket name
        download_videos (bool): Whether to actually download and upload videos
        credentials (dict, optional): Service account credentials for Cloud Storage
        project_id (str, optional): GCP project ID where the bucket is located
        access_token (str, optional): Meta API access token to fetch video URL
        
    Returns:
        dict: Mapping with 'cloud_storage_url' to GCS URL (or empty if download failed)
    """
    stored_urls = {}
    
    # Get video_id from creative data
    # Priority: object_story_spec.video_data.video_id (this one works!) first, then top-level video_id
    video_id = ""
    object_story_spec = creative_data.get("object_story_spec", {})
    if isinstance(object_story_spec, str):
        try:
            import json
            object_story_spec = json.loads(object_story_spec)
        except Exception:
            object_story_spec = {}
    
    # First try object_story_spec.video_data.video_id (this is the one that works!)
    video_data = object_story_spec.get("video_data", {})
    if isinstance(video_data, dict):
        video_id = video_data.get("video_id", "")
    
    # Fallback to top-level video_id if not found in object_story_spec
    if not video_id:
        video_id = creative_data.get("video_id", "")
    
    if not video_id:
        # No video_id available, return empty dict
        return stored_urls
    
    if not download_videos:
        # Just return empty (we don't have the original video URL without fetching from API)
        return stored_urls
    
    if not access_token:
        logger.warning(f"⚠️ Access token required to fetch video URL for creative {creative_id}")
        return stored_urls
    
    # Get video URL from Meta API
    # IMPORTANT: Facebook video URLs expire quickly, so we fetch the URL
    # just before downloading (not cached) to ensure it's fresh
    logger.info(f"📡 Fetching fresh video URL for creative {creative_id} (video_id: {video_id})...")
    video_url = get_video_url_from_meta(video_id, access_token)
    if not video_url:
        logger.warning(f"⚠️ Failed to get video URL for creative {creative_id}, skipping")
        return stored_urls
    
    # Download video immediately after getting URL (URLs expire quickly)
    # Using appropriate headers (User-Agent, Referer) as required by Facebook
    logger.info(f"📥 Downloading video for creative {creative_id} (URL expires quickly, downloading now)...")
    video_data = download_video(video_url)
    if not video_data:
        logger.warning(f"⚠️ Failed to download video for creative {creative_id}")
        return stored_urls
    
    original_size = len(video_data)
    logger.info(f"✅ Downloaded {original_size} bytes ({original_size/(1024*1024):.2f} MB) for creative {creative_id}")
    
    # Compress video for AI analysis
    logger.info(f"🗜️ Compressing video...")
    compressed_data = compress_video(
        video_data,
        crf='32',  # Maximum compression for AI
        scale='480:-2'  # 480p with height divisible by 2
    )
    
    if compressed_data:
        compressed_size = len(compressed_data)
        compression_ratio = (1 - compressed_size/original_size) * 100
        logger.info(f"✅ Video compressed: {original_size/(1024*1024):.2f} MB -> {compressed_size/(1024*1024):.2f} MB ({compression_ratio:.1f}% reduction)")
        final_video_data = compressed_data
        ext = '.mp4'  # Compressed videos are saved as MP4
    else:
        logger.warning(f"⚠️ Compression failed, using original video")
        final_video_data = video_data
        ext = get_video_extension_from_url(video_url)
    
    # Build GCS path: directly in bucket root: {creative_id}_video{ext}
    blob_path = f"{creative_id}_video{ext}"
    
    # Upload to GCS
    logger.info(f"📤 Uploading video to GCS: {blob_path} (project: {project_id})...")
    gcs_url = upload_video_to_gcs(final_video_data, bucket_name, blob_path, credentials=credentials, project_id=project_id)
    
    if gcs_url:
        stored_urls['cloud_storage_url'] = gcs_url
    else:
        logger.warning(f"⚠️ Failed to upload video for creative {creative_id}")
    
    return stored_urls

