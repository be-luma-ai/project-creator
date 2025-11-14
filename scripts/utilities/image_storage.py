# scripts/utilities/image_storage.py

import logging
import requests
import os
import io
from typing import Optional, Dict, List
from urllib.parse import urlparse
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

logger = logging.getLogger(__name__)


def download_image(url: str, timeout: int = 30) -> Optional[bytes]:
    """
    Download an image from a URL.
    
    Args:
        url (str): Image URL to download
        timeout (int): Request timeout in seconds
        
    Returns:
        bytes: Image data, or None if download fails
    """
    if not url or not url.startswith(('http://', 'https://')):
        return None
    
    try:
        logger.debug(f"📥 Downloading image from: {url}")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"⚠️ URL does not point to an image: {content_type}")
            return None
        
        image_data = response.content
        logger.debug(f"✅ Downloaded {len(image_data)} bytes")
        return image_data
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Failed to download image from {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Unexpected error downloading image from {url}: {e}")
        return None


def get_image_extension_from_url(url: str) -> str:
    """
    Extract file extension from URL, defaulting to .jpg if not found.
    
    Args:
        url (str): Image URL
        
    Returns:
        str: File extension (e.g., '.jpg', '.png')
    """
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    
    # Default to jpg if no extension found
    if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return '.jpg'
    
    return ext


def compress_image(image_data: bytes, max_size: tuple = (1920, 1920), quality: int = 75) -> Optional[bytes]:
    """
    Compress an image using PIL/Pillow.
    
    Args:
        image_data (bytes): Original image data
        max_size (tuple): Maximum dimensions (width, height). Default (1920, 1920) for AI analysis.
        quality (int): JPEG quality (1-100). Lower = smaller file. Default 75, 60-70 for AI.
        
    Returns:
        bytes: Compressed image data, or None if compression fails
    """
    try:
        from PIL import Image
        
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        original_format = image.format
        original_size = len(image_data)
        
        # Convert RGBA to RGB if needed (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if image is larger than max_size
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes with compression
        output = io.BytesIO()
        
        # Use JPEG format for better compression (convert PNG/GIF to JPEG)
        # Quality: 60-70 is good for AI analysis (smaller file, sufficient quality)
        image.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        compressed_size = len(compressed_data)
        
        compression_ratio = (1 - compressed_size/original_size) * 100
        logger.debug(f"   Image compressed: {original_size/(1024):.1f} KB -> {compressed_size/(1024):.1f} KB ({compression_ratio:.1f}% reduction)")
        
        return compressed_data
        
    except ImportError:
        logger.warning("⚠️ PIL/Pillow not installed. Install with: pip install Pillow")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Image compression failed: {e}")
        return None


def upload_image_to_gcs(
    image_data: bytes,
    bucket_name: str,
    blob_path: str,
    content_type: Optional[str] = None,
    credentials: Optional[Dict] = None,
    project_id: Optional[str] = None
) -> Optional[str]:
    """
    Upload an image to Cloud Storage.
    
    Args:
        image_data (bytes): Image binary data
        bucket_name (str): GCS bucket name
        blob_path (str): Path within the bucket (e.g., 'meta-ads-images/gama/123456/image.jpg')
        content_type (str): MIME type (e.g., 'image/jpeg'). Auto-detected if None.
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
            if blob_path.endswith('.png'):
                content_type = 'image/png'
            elif blob_path.endswith('.gif'):
                content_type = 'image/gif'
            elif blob_path.endswith('.webp'):
                content_type = 'image/webp'
            else:
                content_type = 'image/jpeg'
        
        blob.upload_from_string(image_data, content_type=content_type)
        
        gcs_url = f"gs://{bucket_name}/{blob_path}"
        logger.info(f"✅ Uploaded image to {gcs_url}")
        return gcs_url
        
    except GoogleCloudError as e:
        logger.error(f"❌ GCS error uploading image to {blob_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error uploading image to {blob_path}: {e}")
        return None


def process_and_store_creative_images(
    creative_id: str,
    creative_data: Dict,
    client_slug: str,
    bucket_name: str,
    date_suffix: str,
    download_images: bool = True,
    credentials: Optional[Dict] = None,
    project_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Download and store image_url for a creative.
    
    Args:
        creative_id (str): Creative ID
        creative_data (dict): Creative data from Meta API
        client_slug (str): Client slug (e.g., 'gama')
        bucket_name (str): GCS bucket name
        date_suffix (str): Date suffix for organization (e.g., '20251001')
        download_images (bool): Whether to actually download and upload images
        credentials (dict, optional): Service account credentials for Cloud Storage
        project_id (str, optional): GCP project ID where the bucket is located
        
    Returns:
        dict: Mapping with 'cloud_storage_url' to GCS URL (or original URL if download failed)
    """
    stored_urls = {}
    
    # Only process image_url
    image_url = creative_data.get("image_url", "")
    
    if not image_url:
        # No image_url available, return empty dict
        return stored_urls
    
    if not download_images:
        # Just return the original URL
        stored_urls['cloud_storage_url'] = image_url
        return stored_urls
    
    # Download image
    logger.info(f"📥 Downloading image for creative {creative_id}...")
    image_data = download_image(image_url)
    if not image_data:
        logger.warning(f"⚠️ Failed to download image for creative {creative_id}, using original URL")
        # Fallback to original URL if download fails
        stored_urls['cloud_storage_url'] = image_url
        return stored_urls
    
    original_size = len(image_data)
    logger.info(f"✅ Downloaded {original_size} bytes ({original_size/(1024):.1f} KB) for creative {creative_id}")
    
    # Compress image for AI analysis
    logger.info(f"🗜️ Compressing image...")
    compressed_data = compress_image(
        image_data,
        max_size=(1920, 1920),  # Max 1920x1920 (sufficient for AI)
        quality=65  # Quality 65: good balance for AI analysis
    )
    
    if compressed_data:
        compressed_size = len(compressed_data)
        compression_ratio = (1 - compressed_size/original_size) * 100
        logger.info(f"✅ Image compressed: {original_size/(1024):.1f} KB -> {compressed_size/(1024):.1f} KB ({compression_ratio:.1f}% reduction)")
        final_image_data = compressed_data
        ext = '.jpg'  # Compressed images are saved as JPEG
    else:
        logger.warning(f"⚠️ Compression failed, using original image")
        final_image_data = image_data
        ext = get_image_extension_from_url(image_url)
    
    # Build GCS path: directly in bucket root: {creative_id}_image{ext}
    # Each client has its own bucket, so no need for client_slug in path
    blob_path = f"{creative_id}_image{ext}"
    
    # Upload to GCS
    logger.info(f"📤 Uploading image to GCS: {blob_path} (project: {project_id})...")
    gcs_url = upload_image_to_gcs(final_image_data, bucket_name, blob_path, credentials=credentials, project_id=project_id)
    
    if gcs_url:
        stored_urls['cloud_storage_url'] = gcs_url
    else:
        # Fallback to original URL if upload fails
        stored_urls['cloud_storage_url'] = image_url
    
    return stored_urls

