from fastapi import APIRouter, HTTPException, Body, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from bilibili_api import video_zone
import asyncio

from .uploader import upload
from . import auth

router = APIRouter()

# --- API Models ---
class PageMetadata(BaseModel):
    title: str
    description: Optional[str] = ""

class BilibiliUploadRequest(BaseModel):
    video_id: str
    tid: int
    title: str
    tags: List[str]
    desc: str
    pages: List[PageMetadata]
    source: Optional[str] = ""
    no_reprint: Optional[int] = 1

@router.get("/zones")
def get_zones(format: str = Query("json", description="Output format: 'json' or 'text'")):
    """
    Retrieves a list of all Bilibili video zones.
    If format is 'json' (default), returns a JSON array of {name, tid}.
    If format is 'text', returns a comma-separated string of {name}({tid}).
    """
    if format not in ["json", "text"]:
        raise HTTPException(status_code=400, detail="Invalid format parameter. Must be 'json' or 'text'.")

    try:
        zone_list = video_zone.get_zone_list()
        # Transform the list to the desired format, excluding entries where tid is 0 or doesn't exist.
        formatted_zones = [
            {"name": zone.get("name"), "tid": zone.get("tid")}
            for zone in zone_list
            if zone.get("tid")  # Ensures tid exists and is not 0
        ]

        if format == "json":
            return formatted_zones
        elif format == "text":
            return ", ".join([f"{zone['name']}({zone['tid']})" for zone in formatted_zones])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching zones: {e}")


@router.post("/login")
async def login():
    """
    Initiates the Bilibili QR code login process.
    The QR code will be displayed in the console where the service is running.
    This process runs in the background.
    """
    print("Received request to start Bilibili login process...")
    # Run the login process in the background so it doesn't block the API
    asyncio.create_task(auth.login_and_save_credential())
    return {"message": "Bilibili login process started. Please check the server console to scan the QR code."}

@router.post("/refresh")
async def refresh():
    """
    Attempts to refresh the Bilibili credentials using the stored refresh token.
    """
    print("Received request to refresh Bilibili credential...")
    credential = await auth.refresh_credential()
    if credential:
        return {"status": "success", "message": "Credential refreshed successfully."}
    else:
        raise HTTPException(status_code=400, detail="Failed to refresh credential. A new login may be required.")

@router.post("/upload")
async def upload_from_id(request: BilibiliUploadRequest, background_tasks: BackgroundTasks):
    """
    Receives metadata including a `video_id`, finds the corresponding
    downloaded files, and uploads them to Bilibili.

    The video and cover files are expected to be present in the directory
    `{VIDEO_DOWNLOAD_PATH}/{video_id}`.
    
    This endpoint returns immediately and the upload is processed in the background.
    """
    try:
        # Add the upload task to run in the background
        background_tasks.add_task(upload, request.dict())
        
        return {
            "message": "Upload task accepted and is running in the background.",
            "video_id": request.video_id
        }
    except Exception as e:
        # Catch any unexpected errors during task submission
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while queueing the upload task: {e}")

