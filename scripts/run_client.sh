rm -f ./downloads/*
python src/youtube/client.py https://www.youtube.com/watch?v=jNQXAC9IVRw ./downloads  --api_host 127.0.0.1 --api_port 9000


curl -X POST \
    http://127.0.0.1:9000/api/v1/youtube/info \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }'


curl -X POST \
    http://127.0.0.1:9000/api/v1/youtube/download \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }' -o file.zip
 

# Example for Bilibili upload
 curl -X POST "http://0.0.0.0:9000/api/v1/bilibili/upload" -H "Content-Type: application/json" -d '{
  "pages": [
    {
      "path": "/mnt/d/temp/youtube-download/file_upload/Me at the zoo.mp4",
      "title": "我的第一个B站视频",
      "description": "这是我上传的第一个B站视频片段描述。"
    }
  ],
  "tid": 130,
  "title": "我的B站首秀 - 动物园趣事",
  "tags": ["生活", "Vlog", "动物园"],
  "desc": "大家好，这是我在动物园拍摄的一些有趣片段，希望大家喜欢！",
  "cover": "/mnt/d/temp/youtube-download/file_upload/Me at the zoo.jpg",
  "no_reprint": true,
  "source": ""
}'

RESPONSE:
{"status":"success","message":"Bilibili upload finished.","aid":115614714759223,"bvid":"BV1bGUhBxEWh"}