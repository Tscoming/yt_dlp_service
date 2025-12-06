
import asyncio
import os
import time
from typing import List, Dict, Any, Optional

from bilibili_api import video_uploader, Credential
from bilibili_api.exceptions import ApiException
from bilibili_api.utils.picture import Picture
class EnhancedVideoMetaValidator:
    """
    对Bilibili视频元数据进行增强验证。
    """
    def __init__(self, meta: Dict[str, Any]):
        self.meta = meta
        self.errors = []

    def validate(self) -> bool:
        """
        执行所有验证检查。
        :return: 如果所有检查都通过，则返回 True，否则返回 False。
        """
        self._validate_title()
        self._validate_tid()
        self._validate_tags()
        self._validate_desc()
        self._validate_cover()
        
        return not self.errors

    def _validate_title(self):
        title = self.meta.get("title")
        if not title:
            self.errors.append("视频标题不能为空。")
        elif len(title) > 80:
            self.errors.append(f"视频标题过长（{len(title)} > 80个字符）。")

    def _validate_tid(self):
        tid = self.meta.get("tid")
        if tid is None:
            self.errors.append("分区ID (tid) 不能为空。")
        elif not isinstance(tid, int) or tid <= 0:
            self.errors.append("分区ID (tid) 必须为正整数。")

    def _validate_tags(self):
        tags = self.meta.get("tags")
        if not tags:
            self.errors.append("至少需要包含一个标签。")
        elif not isinstance(tags, list):
            self.errors.append("标签必须是一个列表。")
        elif len(tags) > 10:
            self.errors.append(f"标签数量过多（{len(tags)} > 10个）。")
        if tags:
            for tag in tags:
                if len(tag) > 20:
                    self.errors.append(f"标签 '{tag[:10]}...' 过长（{len(tag)} > 20个字符）。")

    def _validate_desc(self):
        desc = self.meta.get("desc", "")
        if len(desc) > 2000:
            self.errors.append(f"视频简介过长（{len(desc)} > 2000个字符）。")

    def _validate_cover(self):
        cover = self.meta.get("cover")
        if cover and not isinstance(cover, str):
            self.errors.append("封面路径必须是一个字符串。")
        elif cover and not os.path.exists(cover):
            self.errors.append(f"封面文件不存在: {cover}")

class EnhancedLineSelector:
    """
    根据网络状况和文件大小选择最佳上传线路。
    注意：这是一个概念性实现，实际测速逻辑需要更复杂的实现。
    """
    def __init__(self, lines: Optional[List[str]] = None):
        # 默认线路来自 bilibili-api 库的观察
        self.lines = lines or ["upos-fs-gcs-bse.bilibili.com", "upos-fs-gcs-ali.bilibili.com"]
        self.best_line = None

    async def select_best_line(self) -> str:
        """
        模拟选择最佳线路。在实际应用中，这里应包含测速逻辑。
        为简单起见，我们只选择列表中的第一个。
        """
        # 这是一个模拟实现。真正的实现需要向每个线路发送测试数据包并测量时间。
        print("模拟线路选择... 默认选择第一条线路。")
        self.best_line = self.lines[0]
        return self.best_line


class ResilientChunkUploader:
    """
    支持断点续传和重试的大文件分块上传器。
    此类将包装 bilibili_api 的内部上传逻辑以增加韧性。
    """
    def __init__(self, pages: List[video_uploader.VideoUploaderPage], meta: Dict[str, Any], credential: Credential, max_retries: int = 3, retry_delay: int = 5):
        self.pages = pages
        self.meta = meta
        self.credential = credential
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.uploader = None

    async def upload(self, line: str):
        """
        执行分块上传，并在失败时重试。
        """
        for attempt in range(self.max_retries):
            try:
                # 注意: bilibili-api的VideoUploader不直接暴露线路切换，
                # 但其内部有线路选择逻辑。这里的 'line' 参数是概念性的。
                # 实际的韧性将通过捕获异常和重试来实现。
                print(f"开始上传文件: {[page.path for page in self.pages]} (尝试 {attempt + 1}/{self.max_retries})")
                
                #  bilibili-api VideoUploader 封装了大部分复杂性
                uploader_meta = video_uploader.VideoMeta(
                    tid=self.meta.get("tid"),
                    title=self.meta.get("title"),
                    tags=self.meta.get("tags"),
                    desc=self.meta.get("desc"),
                    cover=self.meta.get("cover") if self.meta.get("cover") else Picture()
                )
                self.uploader = video_uploader.VideoUploader(self.pages, uploader_meta, self.credential)

                upload_result = None
                @self.uploader.on("__ALL__")
                async def on_event(event_data):
                    nonlocal upload_result
                    print(f"上传事件: {event_data}")
                    if event_data.get("name") in ["PREUPLOAD_FAILED", "FAILED"]:
                        raise ApiException(f"上传失败: {event_data.get('data')}")
                    elif event_data.get("name") == "COMPLETE":
                        raw_result = event_data.get("data")
                        upload_result = raw_result[0] if isinstance(raw_result, tuple) and raw_result else raw_result
                
                await self.uploader.start()
                print(f"文件上传成功: {[page.path for page in self.pages]}")
                return upload_result

            except ApiException as e:
                print(f"上传 '{[page.path for page in self.pages]}' 失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    print(f"将在 {self.retry_delay} 秒后重试...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    print(f"达到最大重试次数，上传失败: {[page.path for page in self.pages]}")
                    raise e
            except Exception as e:
                print(f"上传过程中发生意外错误 (尝试 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise e

class RobustVideoUploader:
    """
    一个健壮的Bilibili视频上传器，整合了元数据验证、线路选择和弹性上传。
    """
    def __init__(self, credential: Credential):
        self.credential = credential

    async def upload(self, video_paths: List[str], meta: Dict[str, Any]):
        """
        执行完整的、健壮的上传流程。
        :param video_paths: 视频文件路径列表。
        :param meta: 包含tid, title, tags, desc, cover的字典。
        """
        # 1. 验证元数据
        print("步骤 1: 验证视频元数据...")
        validator = EnhancedVideoMetaValidator(meta)
        if not validator.validate():
            print("元数据验证失败:")
            for error in validator.errors:
                print(f"- {error}")
            return None
        print("元数据验证通过。")

        # 2. 线路选择 (概念性)
        print("\n步骤 2: 选择上传线路...")
        line_selector = EnhancedLineSelector()
        best_line = await line_selector.select_best_line()
        print(f"选择的最佳线路: {best_line}")

        # 3. 创建视频页面和分块上传器
        print("\n步骤 3: 准备上传任务...")
        pages = []
        for video_path in video_paths:
            pages.append(video_uploader.VideoUploaderPage(
                path=video_path,
                title=meta.get("title", os.path.basename(video_path)),
                description=meta.get("desc", "")
            ))
        
        chunk_uploader = ResilientChunkUploader(pages, meta, self.credential)

        # 4. 执行上传
        print("\n步骤 4: 开始上传...")
        try:
            return await chunk_uploader.upload(line=best_line)

        except Exception as e:
            print(f"视频上传最终失败: {e}")
            return None

if __name__ == '__main__':
    # 这是一个示例，用于演示如何使用 RobustVideoUploader
    # 需要设置环境变量 BILIBILI_SESSDATA, BILIBILI_BILI_JCT, BILIBILI_BUVID3
    
    async def main():
        # 准备凭证
        try:
            credential = Credential(
                sessdata=os.getenv("BILIBILI_SESSDATA"),
                bili_jct=os.getenv("BILIBILI_BILI_JCT"),
                buvid3=os.getenv("BILIBILI_BUVID3"),
            )
            await credential.check_valid()
            print("凭证验证通过。")
        except (ApiException, KeyError) as e:
            print(f"凭证无效或未设置，请检查环境变量: {e}")
            return

        # 准备视频文件和元数据
        # 创建一个假的视频文件用于测试
        test_video_path = "test_video_123.mp4"
        if not os.path.exists(test_video_path):
            print(f"创建假的视频文件: {test_video_path}")
            with open(test_video_path, "wb") as f:
                f.write(os.urandom(1024 * 1024 * 2)) # 2MB

        video_meta = {
            "tid": 17, # 分区ID, 17为单机游戏
            "title": f"一个健壮的测试视频上传 {int(time.time())}",
            "tags": ["测试", "API上传", "自动化"],
            "desc": "这是一个通过 RobustVideoUploader 上传的测试视频。",
            "cover": None, # "path/to/your/cover.jpg"
        }

        # 初始化并开始上传
        uploader = RobustVideoUploader(credential)
        result = await uploader.upload([test_video_path], video_meta)

        if result:
            print("\n上传成功！结果:")
            print(result)
        else:
            print("\n上传失败。")

    asyncio.run(main())
