import asyncio
import os
import re
import httpx
from bilibili_api.exceptions import ApiException
from bilibili_api import video, video_uploader, Credential
from .robust_uploader import RobustVideoUploader
from . import auth

def srt_time_to_seconds(time_str: str) -> float:
    """Converts SRT time format HH:MM:SS,ms to seconds."""
    parts = time_str.replace(',', ':').split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + int(parts[3]) / 1000

def parse_srt_to_bilibili_body(srt_content: str) -> list:
    """Parses SRT content into a list of dictionaries for the Bilibili API."""
    body = []
    # Normalize line endings and then split
    srt_blocks = re.split(r'\r?\n\s*\r?\n', srt_content.strip())
    for block in srt_blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()
        if len(lines) >= 2:
            time_line = lines[1]
            content_lines = lines[2:]
            
            match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
            if match:
                start_time_str, end_time_str = match.groups()
                content = "\n".join(content_lines)
                body.append({
                    "from": srt_time_to_seconds(start_time_str),
                    "to": srt_time_to_seconds(end_time_str),
                    "location": 2,  # Default location
                    "content": content
                })
    return body

async def call_webhook(data: dict):
    """Calls the n8n webhook with the provided data."""
    
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "https://n8n.homelabtech.cn/webhook-test/b2d8a919-323e-46ea-9d39-80c1d75ca680")
    print(f"Calling webhook url: {webhook_url}", flush=True)
    print(f"Calling webhook with data: {data}", flush=True)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data, timeout=30.0)
            response.raise_for_status()
            print(f"Successfully called webhook for video_id: {data.get('video_id')}. Status: {response.status_code}", flush=True)
    except httpx.RequestError as e:
        print(f"Error calling webhook for video_id: {data.get('video_id')}: {e}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred when calling webhook: {e}", flush=True)

async def upload_subtitles(credential, video_dir: str, bvid: str) -> bool:
    """
    Finds and uploads SRT subtitles for the given BVID. It polls the video status
    to ensure it's ready before proceeding. Returns True if the video is ready, False otherwise.
    """
    print(f"Video upload complete. BVID: {bvid}. Now processing subtitles.", flush=True)
    
    # 1. Poll for video readiness
    video_obj = video.Video(bvid=bvid, credential=credential)
    is_video_ready = False
    max_retries = int(os.getenv("CHECK_READY_MAX_RETRIES", 5))
    retry_delay = int(os.getenv("CHECK_READY_RETRY_DELAY", 15))

    print("Polling video status to ensure it's ready for subtitle upload...", flush=True)
    for i in range(max_retries):
        try:
            info = await video_obj.get_info()
            video_state = info.get('state', 0)
            print(f"Polling attempt {i+1}/{max_retries}: Video state is '{video_state}'. Full info: {info}", flush=True)
            
            if video_state >= 0:
                print("Video is ready.", flush=True)
                is_video_ready = True
                break
            else:
                print(f"Video not ready yet (state: {video_state}). Retrying in {retry_delay} seconds...", flush=True)
                await asyncio.sleep(retry_delay)
        except ApiException as e:
            if e.code == -404:
                print(f"Polling attempt {i+1}/{max_retries}: Video not found yet (API returned 404). Retrying in {retry_delay} seconds...", flush=True)
            else:
                print(f"An unexpected API error occurred while polling: {e}. Retrying in {retry_delay} seconds...", flush=True)
            await asyncio.sleep(retry_delay)
        except Exception as e:
            print(f"An unexpected error occurred while polling: {e}. Aborting subtitle upload.", flush=True)
            return False

    if not is_video_ready:
        print(f"Video did not become ready after {max_retries} attempts. Aborting subtitle upload.", flush=True)
        return False

    # 2. Find and upload .srt files
    srt_files = [f for f in os.listdir(video_dir) if f.endswith('.srt')]
    if not srt_files:
        print("No .srt subtitle files found, skipping subtitle upload.", flush=True)
        return True # Video is ready, but no subtitles to upload.

    print(f"Found subtitle files: {srt_files}", flush=True)

    try:
        pages = await video_obj.get_pages()
        if not pages:
            print("Could not retrieve video pages (CIDs), aborting subtitle upload.", flush=True)
            return True # Still return true because video is ready
        
        first_part_cid = pages[0]['cid']
        print(f"Targeting first video part with CID: {first_part_cid}", flush=True)
        if len(pages) > 1:
            print("Warning: Multiple video parts detected. Subtitles will be applied to the first part only.", flush=True)

        cn_subtitle_regex = re.compile(r'zh(-CN|-TW|-HK|-SG|-MO|-Hans)?\.srt$', re.IGNORECASE)
        for srt_filename in srt_files:
            if cn_subtitle_regex.search(srt_filename):
                lang = "zh-CN"
            else:
                base_name, _ = os.path.splitext(srt_filename)
                lang = base_name.split('.')[-1]
            srt_path = os.path.join(video_dir, srt_filename)
            
            print(f"Processing subtitle for lang '{lang}' from file '{srt_path}'...", flush=True)
            
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                
                subtitle_body = parse_srt_to_bilibili_body(srt_content)
                if not subtitle_body:
                    print(f"Warning: Subtitle file '{srt_path}' is empty or invalid. Skipping.", flush=True)
                    continue
                
                subtitle_data = {
                    "font_size": 0.4, "font_color": "#FFFFFF", "background_alpha": 0.5,
                    "background_color": "#000000", "Stroke": "none", "body": subtitle_body
                }
                
                await video_obj.submit_subtitle(cid=first_part_cid, lan=lang, data=subtitle_data, submit=True, sign=True)
                print(f"Successfully submitted subtitle '{lang}' for CID {first_part_cid}.", flush=True)
            except Exception as e:
                print(f"Error submitting subtitle from file '{srt_path}': {e}", flush=True)

    except Exception as e:
        print(f"An error occurred during subtitle processing for BVID {bvid}: {e}", flush=True)

    return True

async def upload_video(credential: Credential, video_dir: str, data: dict):
    """
    Uploads a video to Bilibili using RobustVideoUploader.
    """
    video_files = []
    cover_file = None
    allowed_video_exts = ['.mp4', '.flv', '.avi', '.mkv', '.mov']
    allowed_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    # 获取操作系统中的视频文件路径信息
    for f in sorted(os.listdir(video_dir)):
        ext = os.path.splitext(f)[1].lower()
        full_path = os.path.join(video_dir, f)
        if ext in allowed_video_exts:
            video_files.append(full_path)
        elif not cover_file and ext in allowed_image_exts:
            cover_file = full_path

    print(f"视频文件: {video_files}")
    print(f"封面文件: {cover_file}")

    if not video_files:
        print("没有找到视频文件，跳过上传。")
        return None

    meta = {
        "tid": data.get("tid", 17),
        "title": data.get("title", "Untitled"),
        "tags": data.get("tags", []),
        "desc": data.get("desc", ""),
        "cover": cover_file,
    }

    uploader = RobustVideoUploader(credential)
    return await uploader.upload(video_files, meta)