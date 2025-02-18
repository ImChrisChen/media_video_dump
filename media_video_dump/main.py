import json
from math import inf
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
import yt_dlp
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class MediaTransferService:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.log_file = os.path.join(download_dir, 'download_history.jsonl')
        os.makedirs(self.download_dir, exist_ok=True)

    def _log_download(self, info: Dict[str, Any], url: str):
        """记录下载历史"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "title": info.get('title'),
            "format": info.get('format'),
            "formats": info.get('formats'),
            "format_id": info.get('format_id'),
            "resolution": info.get('resolution'),
            "filesize": info.get('filesize'),
            "duration": info.get('duration'),
            "view_count": info.get('view_count'),
            "webpage_url": info.get('webpage_url'),
            "extractor": info.get('extractor'),
            "download_path": os.path.join(self.download_dir, f"{info.get('title')}.{info.get('ext')}")
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """获取视频可用的格式列表"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print('info:', info)
                formats = []

                for f in info['formats']:
                    print('f:', f)
                    # temp1.formats.filter(item => item.ext === 'mp4').filter(item => item.format_note).map(item => item.format_note)
                    # 提取有用的格式信息
                    if f.get('ext') == 'mp4' and f.get('format_note'):
                        format_info = {
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext'),
                            'resolution': f.get('resolution', 'unknown'),
                            'filesize': f.get('filesize', 'unknown'),
                            'format_note': f.get('format_note', ''),
                            'fps': f.get('fps'),
                        }
                    formats.append(format_info)

                return formats
        except Exception as e:
            raise Exception(f"Failed to get formats: {str(e)}")

    def download(self, url: str, output_path: str = None, format_id: Optional[str] = None, max_filename_length: int = 150) -> Dict[str, Any]:
        """下载视频，可以指定格式ID"""
        if output_path is None:
            output_path = os.path.join(self.download_dir, '%(upload_date).100s_%(id)s_%(resolution)s_%(title)s.%(ext)s')

        # 设置 yt-dlp 选项
        ydl_opts = {
            'outtmpl': output_path,  # 输出文件名模板
            'noplaylist': True,  # 如果 URL 是播放列表，只下载单个视频
            'overwrites': True,  # 允许覆盖已存在的文件
        }

        # 如果指定了格式ID，添加到选项/api/pc/billing_portal中
        if format_id:
            ydl_opts['format'] = format_id
        else:
            # ydl_opts['format'] = 'bv[ext=mp4]+ba[ext=m4a]'  # 默认下载最佳质量
            ydl_opts['format'] = 'bv[ext=mp4]'  # 默认下载最佳质量
            # ydl_opts['format'] = 'best'  # 默认下载最佳质量

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=True)
                # 记录下载历史
                self._log_download(info, url)

                # 获取实际下载的文件路径
                video_title = info['title']
                video_ext = info['ext']
                # 添加文件名长度限制处理
                if len(video_title) > max_filename_length:
                    video_title = video_title[:max_filename_length]
                downloaded_file = os.path.join(self.download_dir, f"{info.get('upload_date')}_{info.get('id')}_{info.get('resolution')}_{video_title}.{video_ext}")

                return {
                    "title": video_title,
                    "file_path": downloaded_file,
                    "format": info.get('format'),
                    "format_id": info.get('format_id'),
                    "resolution": info.get('resolution'),
                    "filesize": info.get('filesize'),
                    "duration": info.get('duration'),
                    "view_count": info.get('view_count'),
                    "webpage_url": info.get('webpage_url')
                }
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")


app = FastAPI(
    title="Media Video Dump",
    description="A service for managing media and video files",
    version="0.1.0"
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
    video_url = 'https://www.youtube.com/watch?v=oJx9DpXtmAE&list=PLI5YfMzCfRtZ4bHJJDl_IJejxMwZFiBwz'
    video_url = 'https://www.tiktok.com/@hakata4k.official/video/7468249703516261650'
    video_url = 'https://cn.pornhub.com/view_video.php?viewkey=6571c740e2b69'
    video_url = 'https://www.facebook.com/watch?v=2973003642996553'
    video_url = 'https://www.instagram.com/p/DF9Z3YsMLiu/'
    """
    url: str
    format_id: Optional[str] = None


class GetVideoResolutionsRequest(BaseModel):
    url: str


@app.post("/video_resolutions")
async def get_video_resolutions(request: GetVideoResolutionsRequest):
    """获取视频可用的分辨率列表"""
    try:
        formats = media_service.get_available_formats(request.url)
        return {
            "status": "success",
            "message": "Available formats retrieved successfully",
            "data": formats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download_video(request: DownloadRequest):
    """下载指定格式的视频"""
    try:
        # 添加文件名长度限制处理
        result = media_service.download(request.url, format_id=request.format_id, max_filename_length=100)
        return {
            "status": "success",
            "message": "Video downloaded successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def read_health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
