import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

from services.media_transfer import MediaTransferService

app = FastAPI(
    title="Media Video Dump",
    description="A service for managing media and video files",
    version="0.1.0",
)

# 定义下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# 挂载下载目录为静态文件服务
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# 创建 MediaTransferService 实例
media_service = MediaTransferService(DOWNLOAD_DIR)


class DownloadRequest(BaseModel):
    """
    example url:
    video_url = 'https://www.youtube.com/watch?v=oJx9DpXtmAE'
    video_url = 'https://www.tiktok.com/@hakata4k.official/video/7468249703516261650'
    video_url = 'https://cn.pornhub.com/view_video.php?viewkey=6571c740e2b69'
    video_url = 'https://www.facebook.com/watch?v=2973003642996553'
    video_url = 'https://www.instagram.com/p/DF9Z3YsMLiu/'
    """

    url: str
    format_id: Optional[str] = None
    resolution: Optional[str] = None
    proxy: Optional[str] = None


class GetVideoResolutionsRequest(BaseModel):
    url: str
    proxy: Optional[str] = None


@app.post("/resolution_list")
async def get_video_resolution_list(request: GetVideoResolutionsRequest):
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
async def download_video(request: DownloadRequest):
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


@app.get("/health")
def read_health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
