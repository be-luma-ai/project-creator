# scripts/main.py

from fastapi import FastAPI
import os
import uvicorn
import sys
import pathlib

# Agrega el root del proyecto al sys.path para que funcionen los imports
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

# Importa la función main desde run_pipeline.py
from scripts.run_pipeline import run_pipeline as pipeline_main 


app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/run-pipeline")
def run_pipeline():
    """
    Execute the Meta Ads pipeline.
    This endpoint runs synchronously and may take several minutes.
    Cloud Run timeout should be set to at least 60 minutes for large datasets.
    """
    import logging
    logger = logging.getLogger("meta_ads_pipeline")
    
    logger.info("🔥 [run_pipeline] started")
    try:
        pipeline_main()
        logger.info("✅ [run_pipeline] completed successfully")
        return {
            "status": "success",
            "message": "✅ Pipeline executed successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error in run_pipeline: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/test-token")
def test_token():
    """Test if the Meta access token is working"""
    try:
        from scripts.utilities.load_credentials import load_meta_access_token
        from scripts.utilities.meta_ads_api import call_meta_api
        from facebook_business.api import FacebookAdsApi
        
        # Load token
        access_token = load_meta_access_token()
        print(f"🔑 Token loaded: {access_token[:20]}...")
        
        # Initialize Facebook API (required before calling call_meta_api)
        FacebookAdsApi.init(access_token=access_token)
        
        # Test with a simple API call
        result = call_meta_api(
            object_id="me",
            edge="",
            fields=["id", "name"]
        )
        
        return {
            "status": "✅ Token working",
            "token_preview": f"{access_token[:20]}...",
            "api_result": result
        }
    except Exception as e:
        print(f"❌ Token test error: {e}")
        return {"error": str(e)}

@app.get("/test-creative-structure")
def test_creative_structure():
    """Test endpoint to show the new creative performance structure"""
    import pandas as pd
    from scripts.modules.settings.ad_creatives import extract_creative_format, extract_destination_urls
    
    # Sample creative data for testing
    sample_creative = {
        "id": "123456789",
        "title": "Test Ad Creative",
        "body": "This is a test creative for video ads",
        "call_to_action_type": "LEARN_MORE",
        "video_id": "987654321",
        "link_url": "https://example.com/landing-page",
        "object_url": "https://example.com/product",
        "object_type": "video"
    }
    
    # Extract format and URLs
    creative_format = extract_creative_format(sample_creative)
    urls = extract_destination_urls(sample_creative)
    
    # Sample performance data
    sample_data = {
        "ad_id": "111222333",
        "creative_id": sample_creative["id"],
        "creative_format": creative_format,
        "primary_url": urls["primary_url"],
        "link_url": urls["link_url"],
        "object_url": urls["object_url"],
        "creative_title": sample_creative["title"],
        "creative_body": sample_creative["body"],
        "call_to_action_type": sample_creative["call_to_action_type"],
        "video_id": sample_creative["video_id"],
        "date": "2025-01-01",
        "spend": 100.50,
        "impressions": 10000,
        "clicks": 150,
        "ctr": 1.5,
        "cpm": 10.05,
        "cpc": 0.67,
        "purchase": 5,
        "cpa": 20.10
    }
    
    return {
        "message": "✅ Creative performance structure test",
        "sample_data": sample_data,
        "available_fields": [
            "ad_id", "creative_id", "creative_format", "primary_url", "link_url", 
            "object_url", "template_url", "instagram_url", "creative_title", 
            "creative_body", "call_to_action_type", "object_type", "video_id", 
            "image_url", "date", "spend", "impressions", "clicks", "ctr", 
            "cpm", "cpc", "cpa", "purchase", "likes", "comments", "shares"
        ],
        "creative_formats_detected": ["video", "image", "carousel", "slideshow", "unknown"],
        "url_types": ["primary_url", "link_url", "object_url", "template_url", "instagram_url"]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("scripts.main:app", host="0.0.0.0", port=port)