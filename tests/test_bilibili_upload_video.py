from bilibili_api import sync, video_uploader, Credential
import os

async def main():
    allowed_video_exts = ['.mp4', '.flv', '.avi', '.mkv', '.mov']
    allowed_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    credential = Credential(sessdata="c5609078%2C1780486566%2C813ad%2Ac2CjAbRxiC7jvl4DgPp-h22MquwZbsFZGzVOGpCOFFVWLFQUFDFbgYs5snCo854TOU-esSVlVzaW9Cc0tlMGRrTGw4MzM2d1kwSFBraGtEZFNpYlpUWHFTbmNuUVZ5NW5XWnJSZ0pzbVJHUUxXRVFSVDA5ODFkTU44STllZEdCVXBjMjVTb3lCWXNnIIEC", 
                            bili_jct="e67354950836d37da19d605fd9ed4b80", 
                            buvid3="")
    video_files = []
    cover_file = None
    download_path = "../downloads"
    data = {
        "video_id":  "jNQXAC9IVRw",
        "tid": 21,
        "title": "无法被击中的芬兰战斗机",
        "tags": ["空战","二战","芬兰","飞行骑士","战斗机","击落","苏联","传奇","战术","空战英雄"],
        "desc": "本视频讲述了1944年6月30日，芬兰“飞行骑士”Ilmari Juutilainen 的传奇空战经历。视频详细展示了他如何熟练地与苏联 P-39 交战并将其击落，随后加入中队追击逃跑的敌机。面对由 Yak-9 带领、La-5 护航的数百架 Pe-2 轰炸机编队，Juutilainen 和他的中队冲入混战，击落多架敌机。尽管燃料不足，他们仍冒险迎战由 Pe-2、IL-2 和 La-5 组成的新威胁。在与 La-5 的最终对抗中，Juutilainen 利用巧妙的能量陷阱再次获胜。最终，他和中队在燃料耗尽前安全返回，奇迹般地无一损失，Juutilainen 单日取得 6 次胜利，且座机未受任何敌火损伤。",
        "pages": [
            {
            "title": "无法被击中的芬兰战斗机",
            "description": "本视频讲述了1944年6月30日，芬兰“飞行骑士”Ilmari Juutilainen 的传奇空战经历。视频详细展示了他如何熟练地与苏联 P-39 交战并将其击落，随后加入中队追击逃跑的敌机。面对由 Yak-9 带领、La-5 护航的数百架 Pe-2 轰炸机编队，Juutilainen 和他的中队冲入混战，击落多架敌机。尽管燃料不足，他们仍冒险迎战由 Pe-2、IL-2 和 La-5 组成的新威胁。在与 La-5 的最终对抗中，Juutilainen 利用巧妙的能量陷阱再次获胜。最终，他和中队在燃料耗尽前安全返回，奇迹般地无一损失，Juutilainen 单日取得 6 次胜利，且座机未受任何敌火损伤。"
            }
        ]
        }
    video_dir = os.path.join(download_path, data["video_id"])

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

    videoPages = []
    for video_file in video_files:
        if not os.path.exists(video_file):
            print(f"视频文件 {video_file} 不存在，跳过上传。")
            continue
        else:
            print(f"视频文件 {video_file} 存在，开始上传。")
            pageItem = video_uploader.VideoUploaderPage(
                path=video_file,
                title=data.get("title", "Untitled"),
                description=data.get("desc", ""),
            )
            videoPages.append(pageItem)


    if os.path.exists(cover_file):
        print(f"封面文件 {cover_file} 存在，开始上传。")

        vu_meta = video_uploader.VideoMeta(
            tid=data.get("tid", 17),
            title=data.get("title", "Untitled"),
            tags=data.get("tags", []),
            desc=data.get("desc", ""),
            cover=cover_file,
            no_reprint=True,
        )
    else:
        print(f"封面文件 {cover_file} 不存在，使用默认封面。")
        cover_file = None   
 
    uploader = video_uploader.VideoUploader(
        videoPages, vu_meta, credential, line=video_uploader.Lines.BLDSA
    )   

    @uploader.on("__ALL__")
    async def ev(data):
        print(data)

    await uploader.start()


sync(main())