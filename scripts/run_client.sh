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
 

# Example for Bilibili upload 
 
curl -X POST "http://localhost:9000/api/v1/bilibili/upload" \
-F "files=@/mnt/d/temp/youtube-download/file_upload/Me at the zoo.mp4" \
-F "cover_file=@/mnt/d/temp/youtube-download/file_upload/Me at the zoo.jpg" \
-F 'metadata_json={
    "tid": 17,
    "title": "我的B站首秀 - 动物园趣事",
    "tags": ["生活", "Vlog", "动物园"],
    "desc": "大家好，这是我在动物园拍摄的一些有趣片段，希望大家喜欢！",
    "pages": [
        {"title": "我的第一个B站视频 - Part 1", "description": "这是我上传的第一个B站视频片段描述。"}
    ]
}'


RESPONSE:
{"status":"success","message":"Bilibili upload finished.","aid":115614714759223,"bvid":"BV1bGUhBxEWh"}



curl -X POST "http://localhost:9000/api/v1/common/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "video_id=test_video_123" \
  -F "fileName=my_uploaded_file.txt" \
  -F "file=@test_upload.txt"
