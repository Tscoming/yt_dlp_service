import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock, call

# Adjust the path to import from the src directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from bilibili.robust_uploader import (
    RobustVideoUploader,
    EnhancedVideoMetaValidator,
    ResilientChunkUploader,
)
from bilibili_api import Credential
from bilibili_api.exceptions import ApiException

class TestRobustVideoUploader(unittest.TestCase):

    def setUp(self):
        """同步设置，准备测试数据。"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 模拟凭证
        self.mock_credential = MagicMock(spec=Credential)
        
        # 创建一个假的视频文件
        self.test_video_path = "fake_video_for_test.mp4"
        with open(self.test_video_path, "wb") as f:
            f.write(os.urandom(1024)) # 1KB fake video

        # 准备合法的元数据
        self.valid_meta = {
            "tid": 17,
            "title": "A Valid Test Video",
            "tags": ["test"],
            "desc": "Valid description.",
            "cover": None,
        }

    def tearDown(self):
        """清理测试文件和事件循环。"""
        if os.path.exists(self.test_video_path):
            os.remove(self.test_video_path)
        self.loop.close()

    def run_async(self, coro):
        """工具函数，用于同步运行异步代码。"""
        return self.loop.run_until_complete(coro)

    @patch('bilibili.robust_uploader.EnhancedVideoMetaValidator.validate', return_value=False)
    @patch('builtins.print')
    def test_upload_with_invalid_meta_fails(self, mock_print, mock_validate):
        """测试当元数据验证失败时，上传流程是否被中止。"""
        uploader = RobustVideoUploader(self.mock_credential)
        
        result = self.run_async(uploader.upload([self.test_video_path], self.valid_meta))
        
        # 断言
        self.assertIsNone(result)
        mock_validate.assert_called_once()
        mock_print.assert_any_call("元数据验证失败:")

    @patch('bilibili.robust_uploader.video_uploader.VideoUploader')
    def test_successful_upload_flow(self, MockVideoUploader):
        """测试一个理想的、成功的上传流程。"""
        # 模拟bilibili-api的上传器
        mock_uploader_instance = MockVideoUploader.return_value
        mock_uploader_instance.start = AsyncMock()
        
        # 存储事件处理函数
        events = {}

        def on_side_effect(event_name):
            def decorator(func):
                events[event_name] = func
                return func
            return decorator

        mock_uploader_instance.on.side_effect = on_side_effect

        async def start_side_effect():
            # 模拟上传成功事件
            if "__ALL__" in events:
                await events["__ALL__"]({
                    "name": "COMPLETE",
                    "data": ({"bvid": "BV123456", "aid": 123456},)
                })
        
        mock_uploader_instance.start.side_effect = start_side_effect

        uploader = RobustVideoUploader(self.mock_credential)
        
        result = self.run_async(uploader.upload([self.test_video_path], self.valid_meta))

        # 断言
        self.assertIsNotNone(result)
        self.assertEqual(result['bvid'], 'BV123456')
        MockVideoUploader.assert_called_once()
        mock_uploader_instance.start.assert_called_once()


    @patch('bilibili.robust_uploader.video_uploader.VideoUploader')
    @patch('asyncio.sleep', new_callable=AsyncMock)
    def test_resilient_uploader_retries_on_failure(self, mock_sleep, MockVideoUploader):
        """测试ResilientChunkUploader在上传失败时是否会重试。"""
        
        mock_uploader_instance = MockVideoUploader.return_value
        mock_uploader_instance.start = AsyncMock()
        
        events = {}
        def on_side_effect(event_name):
            def decorator(func):
                events[event_name] = func
                return func
            return decorator
        mock_uploader_instance.on.side_effect = on_side_effect

        async def start_side_effect():
            if mock_uploader_instance.start.call_count == 1:
                if "__ALL__" in events:
                    await events["__ALL__"]({"name": "FAILED", "data": "Simulated failure"})
                raise ApiException("Simulated upload failure")
            else:
                if "__ALL__" in events:
                    await events["__ALL__"]({
                        "name": "COMPLETE",
                        "data": ({"bvid": "BV123456", "aid": 123456},)
                    })
        
        mock_uploader_instance.start.side_effect = start_side_effect

        from bilibili_api import video_uploader
        page = video_uploader.VideoUploaderPage(path=self.test_video_path, title="t", description="d")
        
        resilient_uploader = ResilientChunkUploader([page], self.valid_meta, self.mock_credential, max_retries=2, retry_delay=1)

        result = self.run_async(resilient_uploader.upload(line="test-line"))

        self.assertIsNotNone(result)
        self.assertEqual(result['bvid'], 'BV123456')
        self.assertEqual(mock_uploader_instance.start.call_count, 2)
        mock_sleep.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()