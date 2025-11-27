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
 

# Example for Bilibili upload (new JSON-based API)
curl -X POST \
    http://localhost:9000/api/v1/bilibili/upload \
    -H 'Content-Type: application/json' \
    -d '{
  "video_id":  "QyD0liioY8E",
  "tid": 17,
  "title": "鹰狮战斗机 - 随时保持战斗准备状态",
  "tags": [
    "生活",
    "Vlog",
    "动物园"
  ],
  "desc": "作战效果的关键在于在需要时让战斗机升空。这就是为什么鹰狮战斗机的设计确保了持续的最大可用性。当没有跑道可用时，鹰狮战斗机部队可以从小型机场甚至高速公路上运作。例如，鹰狮战斗机可以在仅16×800米的公路跑道上运作。在本片中，您将了解更多关于鹰狮战斗机始终保持战斗准备状态的原因。

访问鹰狮战斗机主页：https://saab.com/gripen/

在Facebook上关注萨博：https://www.facebook.com/saabtechnologies/

在Twitter上关注萨博：https://twitter.com/Saab

在Instagram上关注萨博：https://www.instagram.com/saab/

在LinkedIn上关注萨博：https://www.linkedin.com/company/saab",
  "pages": [
    {
      "title": "我的第一个B站视频 - Part 1",
      "description": "这是我上传的第一个B站视频片段描述。"
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
