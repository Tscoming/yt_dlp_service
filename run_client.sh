rm -f ./downloads/*
python client.py https://www.youtube.com/watch?v=jNQXAC9IVRw ./downloads  --api_host 127.0.0.1 --api_port 9000


curl -X POST \
    http://127.0.0.1:9000/api/v1/video/info \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }' -O


curl -X POST \
    http://127.0.0.1:9000/api/v1/video/download \
    -H 'Content-Type: application/json' \
    -d '{ "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw" }' -o file.zip



uvicorn service:app --host 0.0.0.0 --port 9000 
uvicorn service:app --host 0.0.0.0 --port 9000 --reload

ython test_api.py