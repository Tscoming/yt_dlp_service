from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional

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

