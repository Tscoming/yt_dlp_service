import asyncio
import os
from bilibili_api import video_uploader, Credential
from . import config

async def upload(data: dict):
    """
    接收一个字典参数，根据其中的 video_id 查找文件并上传到Bilibili。
    """
    video_id = data.get("video_id")
    if not video_id:
        return {"status": "error", "message": "video_id is required"}

    # 1. 获取文件路径
    download_path = os.getenv("VIDEO_DOWNLOAD_PATH", "downloads")
    video_dir = os.path.join(download_path, video_id)

    if not os.path.isdir(video_dir):
        return {"status": "error", "message": f"Video directory not found: {video_dir}"}

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

    if not video_files:
        return {"status": "error", "message": f"No video files found in {video_dir}"}
    
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

    # 从配置中获取凭证
    credential = Credential(
        sessdata=config.SESSDATA,
        bili_jct=config.BILI_JCT,
        buvid3=config.BUVID3
    )

    # 打印凭证信息用于调试
    print(f"Using Bilibili Credential: SESSDATA={credential.sessdata}, BILI_JCT={credential.bili_jct}, BUVID3={credential.buvid3}")

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

    # 创建 VideoUploaderPage 列表
    pages = [
        video_uploader.VideoUploaderPage(
            path=page['path'],
            title=page['title'],
            description=page.get('description', '')
        ) for page in pages_data
    ]

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
            upload_result = event_data.get("data")

    # 开始上传
    print("Starting Bilibili upload...")
    await uploader.start()
    print("Bilibili upload finished.")

    final_response = {
        "status": "success", 
        "message": "Bilibili upload finished.",
        "video_id": video_id
    }
    if upload_result:
        result_dict = upload_result
        if isinstance(upload_result, tuple) and len(upload_result) > 0:
            result_dict = upload_result[0]
        
        if isinstance(result_dict, dict):
            final_response.update(result_dict)

    return final_response


