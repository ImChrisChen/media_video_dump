import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
from services.media_transfer import MediaTransferService
import schemas

app = FastAPI(
    title="Media Video Dump",
    description="A service for managing media and video files",
    version="0.1.0",
)

# 定义下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# 确保下载目录存在
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 挂载下载目录为静态文件服务
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# 创建 MediaTransferService 实例
media_service = MediaTransferService(DOWNLOAD_DIR)


@app.post("/resolution_list")
async def get_video_resolution_list(request: schemas.GetVideoResolutionsRequest):
    """获取视频可用的分辨率列表"""
    try:
        resolutions = media_service.get_resolution_list(
            request.url, proxy=request.proxy
        )
        return {
            "status": "success",
            "message": "Get video resolutions list successfully",
            "data": resolutions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download_video(request: schemas.DownloadRequest):
    """下载指定格式或分辨率的视频"""
    try:
        result = media_service.download(
            request.url,
            resolution=request.resolution,
            proxy=request.proxy,
        )
        return {
            "status": "success",
            "message": "Video downloaded successfully",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
curl --location 'http://localhost:8000/video_list' \
--header 'Content-Type: application/json' \
--data '{
    "url": "https://missav.ws/dm23/ja/siro",
    "proxy": "socks5://127.0.0.1:7890"
}'
"""
@app.post("/video_list")
async def get_video_list(request: schemas.GetVideoListRequest):
    """获取网址中的视频列表"""
    try:
        video_list = media_service.get_video_list(request.url, proxy=request.proxy)
        return {
            "status": "success",
            "message": "Get video list successfully",
            "data": video_list,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def read_health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
