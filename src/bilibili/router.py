from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from bilibili_api import video_zone

from .uploader import upload
from . import config

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
def get_zones():
    """
    Retrieves a list of all Bilibili video zones, formatted as {name, tid}.
    """
    try:
        zone_list = video_zone.get_zone_list()
        # Transform the list to the desired format, excluding entries where tid is 0 or doesn't exist.
        formatted_zones = [
            {"name": zone.get("name"), "tid": zone.get("tid")} 
            for zone in zone_list 
            if zone.get("tid")  # Ensures tid exists and is not 0
        ]
        return formatted_zones
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching zones: {e}")

@router.post("/upload")
async def upload_from_id(request: BilibiliUploadRequest):
    """
    Receives metadata including a `video_id`, finds the corresponding
    downloaded files, and uploads them to Bilibili.

    The video and cover files are expected to be present in the directory
    `{VIDEO_DOWNLOAD_PATH}/{video_id}`.
    """
    if not all([config.SESSDATA, config.BILI_JCT]):
        raise HTTPException(status_code=500, detail="Bilibili SESSDATA and BILI_JCT credentials must be configured on the server.")

    try:
        # The uploader function now expects a dictionary.
        result = await upload(request.dict())
        
        if result.get("status") == "error":
            # Pass through errors from the uploader as HTTPExceptions
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error during upload."))
            
        return result
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

