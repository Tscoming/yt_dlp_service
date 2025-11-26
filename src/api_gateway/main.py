from fastapi import FastAPI
from src.youtube.router import router as youtube_router
from src.bilibili.router import router as bilibili_router

app = FastAPI(title="Video Service API Gateway")

app.include_router(youtube_router, prefix="/api/v1/youtube", tags=["YouTube"])
app.include_router(bilibili_router, prefix="/api/v1/bilibili", tags=["Bilibili"])

@app.get("/")
def read_root():
    return {"message": "API Gateway is running."}
