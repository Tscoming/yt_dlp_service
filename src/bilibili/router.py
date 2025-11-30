from fastapi import APIRouter, HTTPException, Body, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from bilibili_api import video_zone
import asyncio
import os
from fastapi import Request

from .uploader import upload_video, upload_subtitles, call_webhook
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

async def post_upload_tasks(credential, video_dir: str, bvid: str, upload_data: dict):
    """
    Background tasks after video upload: wait for ready, upload subtitles, call webhook.
    """
    print(f"Starting post-upload tasks for BVID {bvid}...", flush=True)
    
    is_ready = await upload_subtitles(credential, video_dir, bvid)
    
    if is_ready:
        print(f"Video {bvid} is ready. Calling webhook.", flush=True)
        await call_webhook(upload_data)
    else:
        print(f"Video {bvid} did not become ready. Webhook will not be called.", flush=True)

@router.get("/zones")
def get_zones(format: str = Query("json", description="Output format: 'json' or 'text'")):
    """
    Retrieves a list of all Bilibili video zones.
    If format is 'json' (default), returns a JSON array of {name, tid}.
    If format is 'text', returns a comma-separated string of {name}({tid}).
    """
    print(f"\n========== STARTING GET_ZONES with format: {format} ==========\n", flush=True)
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
            print(f"\n========== GET_ZONES COMPLETED SUCCESSFULLY for format: {format} ==========\n", flush=True)
            return formatted_zones
        elif format == "text":
            print(f"\n========== GET_ZONES COMPLETED SUCCESSFULLY for format: {format} ==========\n", flush=True)
            return ", ".join([f"{zone['name']}({zone['tid']})" for zone in formatted_zones])

    except Exception as e:
        print(f"\n========== GET_ZONES FAILED with error: {e} ==========\n", flush=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching zones: {e}")


@router.post("/login")
async def login():
    """
    Initiates the Bilibili QR code login process.
    The QR code will be displayed in the console where the service is running.
    This process runs in the background.
    """
    print("\n========== STARTING BILIBILI LOGIN ==========\n", flush=True)
    print("Received request to start Bilibili login process...")
    # Run the login process in the background so it doesn't block the API
    asyncio.create_task(auth.login_and_save_credential())
    print("\n========== BILIBILI LOGIN PROCESS STARTED ==========\n", flush=True)
    return {"message": "Bilibili login process started. Please check the server console to scan the QR code."}

@router.post("/refresh")
async def refresh():
    """
    Attempts to refresh the Bilibili credentials using the stored refresh token.
    """
    print("\n========== STARTING BILIBILI REFRESH ==========\n", flush=True)
    print("Received request to refresh Bilibili credential...")
    credential = await auth.refresh_credential()
    if credential:
        print("\n========== BILIBILI REFRESH COMPLETED SUCCESSFULLY ==========\n", flush=True)
        return {"status": "success", "message": "Credential refreshed successfully."}
    else:
        print("\n========== BILIBILI REFRESH FAILED ==========\n", flush=True)
        raise HTTPException(status_code=400, detail="Failed to refresh credential. A new login may be required.")

@router.post("/upload")
async def upload_from_id(
    request: Request, 
    payload: BilibiliUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Receives metadata including a `video_id`, finds the corresponding
    downloaded files, and uploads them to Bilibili.
    
    Step 1: Upload video file. This is a synchronous operation.
    Step 2: If video upload is successful, the API returns a response.
    Step 3: Subtitle uploading and other post-processing tasks are run asynchronously in the background.
    """
    video_id = payload.video_id
    data = payload.dict()

    chat_id = request.headers.get("chat_id", 0 )
    
    print(f"\n========== STARTING BILIBILI UPLOAD for video_id: {video_id} ==========\n", flush=True)

    download_path = os.getenv("VIDEO_DOWNLOAD_PATH", "downloads")
    video_dir = os.path.join(download_path, video_id)
    print(f"Video directory set to: {video_dir}", flush=True)

    if not os.path.isdir(video_dir):
        print(f"Error: Video directory not found: {video_dir}", flush=True)
        raise HTTPException(status_code=404, detail=f"Video directory not found: {video_dir}")

    try:
        credential = await auth.get_credential()
        print("Successfully got Bilibili credential.", flush=True)
    except Exception as e:
        print(f"Failed to get Bilibili credential: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Bilibili credential: {e}")

    try:
        # Step 1: Upload video (synchronous)
        upload_result = await upload_video(credential, video_dir, data)

        if upload_result and isinstance(upload_result, dict):
            final_response = {"status": "success", 
                              "message": "Bilibili video upload finished. Begin finds and uploads SRT subtitles... ...", 
                              "video_id": video_id,
                              "chat_id": chat_id
                              }
            final_response.update(upload_result)
            bvid = upload_result.get("bvid")

            if bvid:
                # Step 2 & 3: Run post-processing in the background
                print(f"BVID {bvid} received. Creating background task for post-processing.", flush=True)
                background_tasks.add_task(post_upload_tasks, credential, video_dir, bvid, final_response)
            else:
                print("Upload complete, but no BVID received. Cannot start post-processing.", flush=True)
            
            print(f"\n========== BILIBILI UPLOAD for video_id: {video_id} COMPLETED ==========\n", flush=True)
            return final_response
        else:
            print("Bilibili upload failed. Check logs for details.", flush=True)
            raise HTTPException(status_code=500, detail="Bilibili upload failed. Check logs for details.")

    except Exception as e:
        print(f"\n========== BILIBILI UPLOAD FAILED for video_id: {video_id} with error: {e} ==========\n", flush=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during the upload process: {e}")


