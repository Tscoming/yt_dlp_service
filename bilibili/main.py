from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

from .uploader import upload_video_to_bilibili
from . import config

app = FastAPI()

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

@app.post("/upload")
async def upload_video(request: UploadRequest):
    """
    接收视频信息并将其上传到Bilibili。
    这是一个同步端点，它将等待上传完成后再返回结果。
    """
    if not all([config.SESSDATA, config.BILI_JCT]):
        raise HTTPException(status_code=500, detail="Bilibili credentials not configured in environment (SESSDATA or BILI_JCT missing).")

    try:
        result = await upload_video_to_bilibili(
            pages_data=[page.dict() for page in request.pages],
            tid=request.tid,
            title=request.title,
            tags=request.tags,
            desc=request.desc,
            cover=request.cover,
            no_reprint=request.no_reprint,
            source=request.source,
        )
        return result
    except Exception as e:
        # 捕获上传过程中可能发生的任何异常
        raise HTTPException(status_code=500, detail=f"An error occurred during Bilibili upload: {e}")

@app.get("/")
def read_root():
    return {"message": "Bilibili Uploader API is running."}
