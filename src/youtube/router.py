import os, json, zipfile, uuid
from urllib.parse import urlparse, parse_qs
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
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
    
def cleanup_zip_file(zip_path: str):
    """Removes the temporary zip file."""
    if zip_path and os.path.exists(zip_path):
        os.remove(zip_path)

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

class MyLogger:
    def debug(self, msg):
        # For compatibility with yt-dlp, we filter out some messages
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        print(msg, flush=True)

    def warning(self, msg):
        print(f"WARNING: {msg}", flush=True)

    def error(self, msg):
        print(f"ERROR: {msg}", flush=True)

def my_progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total_bytes:
            percentage = d['downloaded_bytes'] / total_bytes * 100
            print(f"Downloading: {d['filename']} - {percentage:.2f}% of {total_bytes / 1024 / 1024:.2f}MB at {d.get('speed', 'N/A')}B/s, ETA: {d.get('eta', 'N/A')}s", flush=True)
    elif d['status'] == 'finished':
        print(f"Finished downloading {d['filename']}", flush=True)
    elif d['status'] == 'error':
        print(f"Error downloading {d['filename']}", flush=True)

@router.post("/download")
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Downloads files, then zips and returns all non-mp4 files,
    leaving the original files in the download directory.
    """
    zip_path = None
    try:
        print(f"Starting download for URL: {request.url}", flush=True)
        download_root = os.environ.get('VIDEO_DOWNLOAD_PATH', 'downloads')
        parsed_url = urlparse(request.url)
        video_id = parse_qs(parsed_url.query).get('v')
        if not video_id:
            video_id = parsed_url.path.lstrip('/')
            if not video_id:
                print("Could not extract video_id from URL.", flush=True)
                return JSONResponse(status_code=400, content={"error": "Could not extract video_id from URL."})
        
        if isinstance(video_id, list): video_id = video_id[0]

        download_path = os.path.join(download_root, video_id)
        os.makedirs(download_path, exist_ok=True)
        print(f"Download path set to: {download_path}", flush=True)

        ydl_opts = load_base_ydl_opts()
        ydl_opts['outtmpl'] = f'{download_path}/%(title)s.%(ext)s'
        ydl_opts['logger'] = MyLogger()
        ydl_opts['progress_hooks'] = [my_progress_hook]
        
        if request.subtitles is not None:
            if request.subtitles:
                print(f"Subtitles requested for languages: {request.subtitles}", flush=True)
                ydl_opts['writesubtitles'] = True
                ydl_opts['subtitleslangs'] = request.subtitles
                if 'allsubtitles' in ydl_opts:
                    del ydl_opts['allsubtitles']
            else:
                print("No subtitles requested.", flush=True)
                ydl_opts['writesubtitles'] = False
                if 'allsubtitles' in ydl_opts:
                    del ydl_opts['allsubtitles']

        cookie_path = os.environ.get('COOKIE_FILE_PATH')
        if cookie_path and os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
            print("Using cookies from file.", flush=True)
            ydl_opts['cookiefile'] = cookie_path
        
        print("Starting yt-dlp download...", flush=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_title = info.get('title', 'video')
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
        print("yt-dlp download finished.", flush=True)

        downloaded_files = os.listdir(download_path)
        print(f"Downloaded files: {downloaded_files}", flush=True)
        
        zip_filename = f"{safe_title}_subtitles.zip"
        zip_path = os.path.join("/tmp", zip_filename)
        
        files_to_zip = [f for f in downloaded_files if not f.endswith('.mp4')]

        if not files_to_zip:
            print("No non-mp4 files found to zip.", flush=True)
            return JSONResponse(status_code=404, content={"error": "No non-mp4 files found to zip."})

        print(f"Zipping files: {files_to_zip}", flush=True)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_zip:
                file_path = os.path.join(download_path, file)
                zipf.write(file_path, arcname=file)
        print(f"Zip file created at: {zip_path}", flush=True)
        
        background_tasks.add_task(cleanup_zip_file, zip_path)
        
        return FileResponse(path=zip_path, media_type='application/zip', filename=zip_filename)

    except yt_dlp.utils.DownloadError as e:
        if zip_path: cleanup_zip_file(zip_path)
        return JSONResponse(status_code=500, content={"error": f"yt-dlp download error: {str(e)}"})
    except Exception as e:
        if zip_path: cleanup_zip_file(zip_path)
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})