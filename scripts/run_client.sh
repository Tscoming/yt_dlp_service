
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
