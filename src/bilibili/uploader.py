import asyncio
import os
import re
from bilibili_api import video, video_uploader, Credential
from bilibili_api.exceptions import ApiException
from . import config

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

async def _upload_subtitles(credential, video_dir: str, bvid: str):
    """
    Finds and uploads SRT subtitles for the given BVID. It polls the video status
    to ensure it's ready before proceeding.
    """
    print(f"Video upload complete. BVID: {bvid}. Now processing subtitles.")
    
    # 1. Find .srt files
    srt_files = [f for f in os.listdir(video_dir) if f.endswith('.srt')]
    if not srt_files:
        print("No .srt subtitle files found, skipping subtitle upload.")
        return

    print(f"Found subtitle files: {srt_files}")

    try:
        # 2. Poll for video readiness before fetching pages.
        video_obj = video.Video(bvid=bvid, credential=credential)
        is_video_ready = False
        max_retries = 5
        retry_delay = 15

        print("Polling video status to ensure it's ready for subtitle upload...")
        for i in range(max_retries):
            try:
                info = await video_obj.get_info()
                # The 'state' field indicates the video's status.
                # Positive values (e.g., 1) mean it's visible/passed review.
                # Negative values or 0 mean it's in review, private, deleted, etc.
                video_state = info.get('state', 0)
                print(f"Polling attempt {i+1}/{max_retries}: Video state is '{video_state}'. Full info: {info}")
                
                if video_state >= 0:
                    print("Video is ready.")
                    is_video_ready = True
                    break
                else:
                    print(f"Video not ready yet (state: {video_state}). Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

            except ApiException as e:
                if e.code == -404:
                    print(f"Polling attempt {i+1}/{max_retries}: Video not found yet (API returned 404). Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"An unexpected API error occurred while polling: {e}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            except Exception as e:
                print(f"An unexpected error occurred while polling: {e}. Aborting subtitle upload.")
                return

        if not is_video_ready:
            print(f"Video did not become ready after {max_retries} attempts. Aborting subtitle upload.")
            return

        # 3. Get video pages and upload subtitles
        pages = await video_obj.get_pages()
        if not pages:
            print("Could not retrieve video pages (CIDs), aborting subtitle upload.")
            return
        
        first_part_cid = pages[0]['cid']
        print(f"Targeting first video part with CID: {first_part_cid}")
        if len(pages) > 1:
            print("Warning: Multiple video parts detected. Subtitles will be applied to the first part only.")

        for srt_filename in srt_files:
            # Correctly extract language code, e.g., from 'my_video.en.srt' -> 'en'
            base_name = os.path.splitext(srt_filename)[0]
            lang = base_name.split('.')[-1]
            srt_path = os.path.join(video_dir, srt_filename)
            
            print(f"Processing subtitle for lang '{lang}' from file '{srt_path}'...")
            
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                
                subtitle_body = parse_srt_to_bilibili_body(srt_content)
                if not subtitle_body:
                    print(f"Warning: Subtitle file '{srt_path}' is empty or invalid. Skipping.")
                    continue
                
                subtitle_data = {
                    "font_size": 0.4,
                    "font_color": "#FFFFFF",
                    "background_alpha": 0.5,
                    "background_color": "#000000",
                    "Stroke": "none",
                    "body": subtitle_body
                }
                
                await video_obj.submit_subtitle(
                    cid=first_part_cid,
                    lan=lang,
                    data=subtitle_data,
                    submit=True,
                    sign=True
                )
                print(f"Successfully submitted subtitle '{lang}' for CID {first_part_cid}.")
            except Exception as e:
                print(f"Error submitting subtitle from file '{srt_path}': {e}")

    except Exception as e:
        print(f"An error occurred during subtitle processing for BVID {bvid}: {e}")


async def upload(data: dict):
    print("Starting Bilibili upload process...")
    video_id = data.get("video_id")
    if not video_id:
        return {"status": "error", "message": "video_id is required"}
    print(f"Processing video with ID: {video_id}")

    # 1. 获取文件路径
    download_path = os.getenv("VIDEO_DOWNLOAD_PATH", "downloads")
    video_dir = os.path.join(download_path, video_id)
    print(f"Video directory set to: {video_dir}")

    if not os.path.isdir(video_dir):
        return {"status": "error", "message": f"Video directory not found: {video_dir}"}
    print(f"Video directory '{video_dir}' found.")

    # 2. 遍历文件，区分视频和封面
    video_files = []
    cover_file = None
    allowed_video_exts = ['.mp4', '.flv', '.avi', '.mkv', '.mov']
    allowed_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    for f in sorted(os.listdir(video_dir)):
        ext = os.path.splitext(f)[1].lower()
        full_path = os.path.join(video_dir, f)
        if ext in allowed_video_exts:
            video_files.append(full_path)
        elif not cover_file and ext in allowed_image_exts:
            cover_file = full_path
    print(f"Found video files: {video_files}")
    print(f"Found cover file: {cover_file}")

    if not video_files:
        return {"status": "error", "message": f"No video files found in {video_dir}"}
    print(f"Video files to upload: {len(video_files)}")
    
    # 3. 组装上传参数
    pages_meta = data.get("pages", [])
    if len(pages_meta) != len(video_files):
        return {
            "status": "error",
            "message": f"Mismatch between page metadata count ({len(pages_meta)}) and found video files count ({len(video_files)})"
        }

    pages_data = []
    for i, video_path in enumerate(video_files):
        page_meta = pages_meta[i]
        pages_data.append({
            "path": video_path,
            "title": page_meta.get("title", f"Part {i+1}"),
            "description": page_meta.get("description", "")
        })
    print(f"Prepared {len(pages_data)} pages for upload.")

    # 从配置中获取凭证
    credential = Credential(
        sessdata=config.SESSDATA,
        bili_jct=config.BILI_JCT,
        buvid3=config.BUVID3
    )

    # 打印凭证信息用于调试
    print(f"Using Bilibili Credential: SESSDATA={credential.sessdata}, BILI_JCT={credential.bili_jct}, BUVID3={credential.buvid3}")

    print("Building VideoMeta object...")
    # 构建 VideoMeta 对象
    vu_meta = video_uploader.VideoMeta(
        source=data.get("source", ""),
        tid=data.get("tid", 17), # 默认为17 生活区
        title=data.get("title", "Untitled"),
        tags=data.get("tags", []),
        desc=data.get("desc", ""),
        cover=cover_file,
        no_reprint=data.get("no_reprint", 1) # 默认开启禁止转载
    )

    print("Creating VideoUploaderPage list...")
    # 创建 VideoUploaderPage 列表
    pages = [
        video_uploader.VideoUploaderPage(
            path=page['path'],
            title=page['title'],
            description=page.get('description', '')
        ) for page in pages_data
    ]

    print("Initializing VideoUploader...")
    # 初始化上传器
    uploader = video_uploader.VideoUploader(
        pages, vu_meta, credential
    )

    upload_result = None

    # 定义事件处理器
    @uploader.on("__ALL__")
    async def ev(event_data):
        nonlocal upload_result
        print(f"Bilibili Upload Event: {event_data}")
        if event_data.get("name") == "COMPLETE":
            # The result from a successful upload can be a tuple or dict
            raw_result = event_data.get("data")
            if isinstance(raw_result, tuple) and len(raw_result) > 0:
                upload_result = raw_result[0] 
            else:
                upload_result = raw_result

    # 开始上传
    print("Starting Bilibili upload...")
    await uploader.start()
    print("Bilibili upload finished.")

    final_response = {
        "status": "success",
        "message": "Bilibili upload finished.",
        "video_id": video_id
    }
    if upload_result and isinstance(upload_result, dict):
        final_response.update(upload_result)
        # --- SUBTITLE UPLOAD ---
        print("Checking for BVID to initiate subtitle upload...")
        bvid = upload_result.get("bvid")
        if bvid:
            await _upload_subtitles(credential, video_dir, bvid)
        else:
            print("Upload complete, but no BVID received. Cannot upload subtitles.")

    return final_response


