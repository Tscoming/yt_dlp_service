
curl -X POST http://localhost:9000/api/v1/bilibili/login

# 测试上传bilibili视频完成后的webhook回调
curl -X POST https://n8n.homelabtech.cn/webhook-test/b2d8a919-323e-46ea-9d39-80c1d75ca680 \
  -H "Content-Type: application/json" \
  -d '{"msg": "hello n8n 1"}'

rm -f ./downloads/*
python src/youtube/client.py https://www.youtube.com/watch?v=jNQXAC9IVRw ./downloads  --api_host 127.0.0.1 --api_port 9000


https://www.youtube.com/watch?v=QyD0liioY8E

curl -X POST \
    http://127.0.0.1:9000/api/v1/youtube/info \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }'


curl -X POST \
    http://127.0.0.1:9000/api/v1/youtube/download \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }' -o file.zip
 



# class VideoMeta:
#     """
#     视频源数据
#     """

#     tid: int  # 分区 ID。可以使用 channel 模块进行查询。
#     title: str  # 视频标题
#     desc: str  # 视频简介。
#     cover: Picture  # 封面 URL
#     tags: Union[List[str], str]  # 视频标签。使用英文半角逗号分隔的标签组。
#     topic_id: Optional[int] = None  # 可选，话题 ID。
#     mission_id: Optional[int] = None  # 可选，任务 ID。
#     original: bool = True  # 可选，是否为原创视频。
#     source: Optional[str] = None  # 可选，视频来源。
#     recreate: Optional[bool] = False  # 可选，是否允许重新上传。
#     no_reprint: Optional[bool] = False  # 可选，是否禁止转载。
#     open_elec: Optional[bool] = False  # 可选，是否展示充电信息。
#     up_selection_reply: Optional[bool] = False  # 可选，是否开启评论精选。
#     up_close_danmu: Optional[bool] = False  # 可选，是否关闭弹幕。
#     up_close_reply: Optional[bool] = False  # 可选，是否关闭评论。
#     lossless_music: Optional[bool] = False  # 可选，是否启用无损音乐。
#     dolby: Optional[bool] = False  # 可选，是否启用杜比音效。
#     subtitle: Optional[dict] = None  # 可选，字幕设置。
#     dynamic: Optional[str] = None  # 可选，动态信息。
#     neutral_mark: Optional[str] = None  # 可选，创作者声明。
#     delay_time: Optional[Union[int, datetime]] = None  # 可选，定时发布时间戳（秒）。
#     porder: Optional[VideoPorderMeta] = None  # 可选，商业相关参数。
# Example for Bilibili upload (new JSON-based API)
curl -X POST \
    http://localhost:9000/api/v1/bilibili/upload \
    -H 'Content-Type: application/json' \
    -d '{
  "video_id":  "jNQXAC9IVRw",
  "tid": 232,
  "title": "上传测试",
  "tags": ["测试", "上传", "脚本"],
  "desc": "这是上传测试视频",
  "original": false,
  "source": "TestSource",
  "pages": [
    {
      "title": "上传测试 - 第1页",
      "description": "这是上传测试视频的第一页。"
    }
  ]
}'


RESPONSE:
{"status":"success","message":"Bilibili upload finished.","aid":115614714759223,"bvid":"BV1bGUhBxEWh"}


# 上传文件到服务器示例
curl -X POST "http://localhost:9000/api/v1/common/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "video_id=test_video_123" \
  -F "fileName=my_uploaded_file.txt" \
  -F "file=@test_upload.txt"
