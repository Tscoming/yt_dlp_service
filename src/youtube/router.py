import os, shutil, zipfile, uuid, json
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import yt_dlp

router = APIRouter()

class URLRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    subtitles: Optional[List[str]] = None

class VideoFormat(BaseModel):
    format_id: Optional[str] = None
    ext: Optional[str] = None
    resolution: Optional[str] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    url: Optional[str] = None

class SubtitleInfo(BaseModel):
    lang_code: str
    name: str
    ext: str

class VideoInfo(BaseModel):
    video_id: str = Field(..., description="The unique identifier for the video.")
    title: str = Field(..., description="The title of the video.")
    description: Optional[str] = Field(None, description="The description of the video.")
    uploader: Optional[str] = Field(None, description="The uploader or channel name.")
    upload_date: Optional[str] = Field(None, description="The video upload date (YYYYMMDD).")
    duration: Optional[int] = Field(None, description="The duration of the video in seconds.")
    thumbnail: Optional[str] = Field(None, description="URL of the video thumbnail image.")
    tags: Optional[List[str]] = Field([], description="A list of tags associated with the video.")
    view_count: Optional[int] = Field(None, description="Number of views.")
    like_count: Optional[int] = Field(None, description="Number of likes.")
    formats: Optional[List[VideoFormat]] = Field([], description="List of available video formats.")
    subtitles: Optional[Dict[str, SubtitleInfo]] = Field({}, description="Available subtitles by language code.")
    original_url: str = Field(..., description="The original URL provided.")
    
def cleanup_files(temp_dir: str, zip_path: str):
    """Removes the temporary directory and the zip file."""
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    if zip_path and os.path.exists(zip_path): os.remove(zip_path)

def safe_get(data, key, default=None):
    """Safely get a value from a nested dictionary."""
    return data.get(key, default)

def load_base_ydl_opts():
    """Loads the base yt-dlp options from the JSON config file."""
    try:
        # Construct the path to the JSON file relative to the current script
        dir_path = os.path.dirname(os.path.realpath(__file__))
        opts_path = os.path.join(dir_path, 'ydl_opts.json')
        with open(opts_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_video_info(url: str) -> dict:
    """Extracts video information using yt-dlp."""
    ydl_opts = load_base_ydl_opts()
    ydl_opts.update({'listsubtitles': True})
    
    cookie_path = os.environ.get('COOKIE_FILE_PATH')
    if cookie_path and os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.sanitize_info(info)

@router.post("/info", response_model=VideoInfo)
def get_info(request: URLRequest):
    """Retrieves metadata for a given video URL."""
    try:
        info = get_video_info(request.url)
        subtitles_info = {}
        if info.get('subtitles'):
            for lang, subs in info['subtitles'].items():
                if subs:
                    sub_data = subs[-1]
                    subtitles_info[lang] = SubtitleInfo(lang_code=lang, name=sub_data.get('name', lang), ext=sub_data.get('ext'))

        standardized_info = VideoInfo(
            video_id=safe_get(info, 'id'),
            title=safe_get(info, 'title'),
            description=safe_get(info, 'description'),
            uploader=safe_get(info, 'uploader'),
            upload_date=safe_get(info, 'upload_date'),
            duration=safe_get(info, 'duration'),
            thumbnail=safe_get(info, 'thumbnail'),
            tags=safe_get(info, 'tags', []),
            view_count=safe_get(info, 'view_count'),
            like_count=safe_get(info, 'like_count'),
            formats=[VideoFormat(**f) for f in safe_get(info, 'formats', [])],
            subtitles=subtitles_info,
            original_url=safe_get(info, 'webpage_url', request.url)
        )
        return standardized_info
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"An error occurred: {str(e)}"})

@router.post("/download")
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Downloads a video and specified subtitles from the given URL,
    packages them into a zip file, and returns it.
    """
    request_id = str(uuid.uuid4())
    temp_dir = f"/tmp/{request_id}"
    os.makedirs(temp_dir, exist_ok=True)
    zip_path = None  # Initialize zip_path
    
    ydl_opts = load_base_ydl_opts()
    ydl_opts['outtmpl'] = f'{temp_dir}/%(title)s.%(ext)s'

    # Handle subtitle selection
    if request.subtitles is not None:
        if request.subtitles:  # If the list is not empty
            ydl_opts['subtitleslangs'] = request.subtitles
            ydl_opts['writesubtitles'] = True
            if 'allsubtitles' in ydl_opts:
                del ydl_opts['allsubtitles']
        else:  # If the list is empty, explicitly disable subtitles
            ydl_opts['writesubtitles'] = False
            if 'allsubtitles' in ydl_opts:
                del ydl_opts['allsubtitles']
    # If request.subtitles is None, the settings from ydl_opts.json are used by default.



    cookie_path = os.environ.get('COOKIE_FILE_PATH')
    if cookie_path and os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_title = info.get('title', 'video')
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
        zip_filename = f"{safe_title}.zip"
        zip_path = os.path.join("/tmp", zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files: zipf.write(os.path.join(root, file), arcname=file)

        background_tasks.add_task(cleanup_files, temp_dir, zip_path)

        return FileResponse(path=zip_path, media_type='application/zip', filename=zip_filename)

    except yt_dlp.utils.DownloadError as e:
        cleanup_files(temp_dir, zip_path)
        return JSONResponse(status_code=500, content={"error": f"yt-dlp download error: {str(e)}"})
    except Exception as e:
        cleanup_files(temp_dir, zip_path)
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})