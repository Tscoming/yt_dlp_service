import asyncio
from bilibili_api import video_uploader, Credential
from . import config

async def upload_video_to_bilibili(pages_data, tid, title, tags, desc, cover, no_reprint, source):
    """
    使用bilibili-api-python上传视频，并返回上传结果。
    """
    # 从配置中获取凭证
    credential = Credential(
        sessdata=config.SESSDATA,
        bili_jct=config.BILI_JCT,
        buvid3=config.BUVID3
    )

    # 打印一下凭证信息（仅供调试，注意隐私）
    print(f"Using Bilibili Credential: SESSDATA={credential.sessdata}, BILI_JCT={credential.bili_jct}, BUVID3={credential.buvid3}")

    # 构建 VideoMeta 对象
    vu_meta = video_uploader.VideoMeta(
        source=source,
        tid=tid,
        title=title,
        tags=tags,
        desc=desc,
        cover=cover,
        no_reprint=no_reprint,
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
    async def ev(data):
        nonlocal upload_result
        print(f"Bilibili Upload Event: {data}")
        if data.get("name") == "COMPLETE":
            upload_result = data.get("data")

    # 开始上传
    print("Starting Bilibili upload...")
    await uploader.start()
    print("Bilibili upload finished.")

    final_response = {"status": "success", "message": "Bilibili upload finished."}
    if upload_result:
        # The result from the uploader event data can be a tuple containing the dict
        result_dict = upload_result
        if isinstance(upload_result, tuple) and len(upload_result) > 0:
            result_dict = upload_result[0]
        
        if isinstance(result_dict, dict):
            final_response.update(result_dict)

    return final_response

