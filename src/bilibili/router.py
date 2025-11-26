import os
import uuid
import shutil
import json
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Optional

from .uploader import upload_video_to_bilibili
from . import config

router = APIRouter()

# --- New API Models ---
class PageMetadata(BaseModel):
    title: str
    description: Optional[str] = ""

class UploadMetadata(BaseModel):
    pages: List[PageMetadata]
    tid: int
    title: str
    tags: List[str]
    desc: Optional[str] = ""
    cover: Optional[str] = None # For providing a cover via URL
    no_reprint: bool = True
    source: Optional[str] = ""


# --- Original Models (kept for reference) ---
class VideoPage(BaseModel):
    path: str
    title: str
    description: Optional[str] = ""

class UploadRequest(BaseModel):
    pages: List[VideoPage]
    tid: int
    title: str
    tags: List[str]
    desc: Optional[str] = ""
    cover: Optional[str] = None
    no_reprint: bool = True
    source: Optional[str] = ""

@router.post("/upload")
async def upload_video(
    files: List[UploadFile] = File(..., description="List of video files to upload."),
    metadata_json: str = Form(..., description="A JSON string with metadata for the upload (see UploadMetadata model)."),
    cover_file: Optional[UploadFile] = File(None, description="Optional cover image file. If provided, it overrides the 'cover' URL in metadata_json.")
):
    """
    Receives video files, metadata, and an optional cover image to upload to Bilibili.

    This endpoint uses `multipart/form-data`. You must provide:
    - One or more `files` parts, each containing a video file.
    - One `metadata_json` form field containing a JSON string for video metadata.
    - Optionally, one `cover_file` part for the video cover image.

    The order of files in the `files` part must match the order of pages in the `metadata_json`.

    Example with `curl`:
    ```
    curl -X POST "http://localhost:9000/bilibili/upload" \
    -F "files=@/path/to/your/video1.mp4" \
    -F "cover_file=@/path/to/your/cover.jpg" \
    -F 'metadata_json={
        "tid": 17,
        "title": "My Awesome Video",
        "tags": ["tag1", "tag2"],
        "pages": [
            {"title": "Part 1", "description": "First part of the video."}
        ]
    }'
    ```
    """
    if not all([config.SESSDATA, config.BILI_JCT]):
        raise HTTPException(status_code=500, detail="Bilibili credentials not configured.")

    try:
        metadata = UploadMetadata.parse_raw(metadata_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata_json format: {e}")
    
    if metadata.cover and cover_file:
        raise HTTPException(status_code=400, detail="Provide cover as a URL in metadata_json OR as a file in cover_file, but not both.")

    if len(files) != len(metadata.pages):
        raise HTTPException(
            status_code=400,
            detail=f"Number of files ({len(files)}) does not match number of pages in metadata ({len(metadata.pages)})."
        )

    temp_file_paths = []
    pages_data_with_paths = []
    container_download_path = "downloads"
    container_cover_path = metadata.cover  # Default to URL from metadata

    os.makedirs(container_download_path, exist_ok=True)

    try:
        # Handle cover file upload
        if cover_file:
            if not cover_file.filename:
                raise HTTPException(status_code=400, detail="Cover file has no filename.")
            
            _, extension = os.path.splitext(cover_file.filename)
            unique_filename = f"cover-{uuid.uuid4()}{extension}"
            temp_path = os.path.join(container_download_path, unique_filename)

            try:
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(cover_file.file, buffer)
            finally:
                await cover_file.close()
            
            temp_file_paths.append(temp_path)
            container_cover_path = temp_path

        # Handle video files upload
        for i, file in enumerate(files):
            if not file.filename:
                raise HTTPException(status_code=400, detail=f"File at index {i} has no filename.")

            _, extension = os.path.splitext(file.filename)
            unique_filename = f"{uuid.uuid4()}{extension}"
            temp_path = os.path.join(container_download_path, unique_filename)

            try:
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            finally:
                await file.close()

            temp_file_paths.append(temp_path)

            page_meta = metadata.pages[i]
            pages_data_with_paths.append({
                "path": temp_path,
                "title": page_meta.title,
                "description": page_meta.description
            })

        # Call the uploader with the final paths
        result = await upload_video_to_bilibili(
            pages_data=pages_data_with_paths,
            tid=metadata.tid,
            title=metadata.title,
            tags=metadata.tags,
            desc=metadata.desc,
            cover=container_cover_path,
            no_reprint=metadata.no_reprint,
            source=metadata.source,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during upload: {e}")
    finally:
        # Clean up all saved temp files
        for path in temp_file_paths:
            if os.path.exists(path):
                os.remove(path)
