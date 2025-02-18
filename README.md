# Media Video Dump

一个用于下载和管理媒体文件的服务。

## 功能特点

- 支持多个平台的视频下载
- 支持选择视频质量和格式
- RESTful API 接口
- Docker 容器化部署

## Docker 部署说明

### 前置条件

- Docker
- Docker Compose
- ffmpeg

### 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/ImChrisChen/media-video-dump.git
cd media-video-dump
```

2. 使用 Docker Compose 启动服务：
```bash
docker-compose up -d
```

服务将在 http://localhost:8000 启动，你可以通过以下地址访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 目录结构

- `/app/downloads`: 容器内的下载目录，通过 volume 映射到宿主机的 `./downloads` 目录

### 环境变量

- `TZ`: 时区设置，默认为 `Asia/Shanghai`

### 自定义配置

如需修改端口或下载目录，可以编辑 `docker-compose.yml` 文件：

```yaml
services:
  media-video-dump:
    ports:
      - "自定义端口:8000"
    volumes:
      - ./自定义下载目录:/app/downloads
```

## 开发环境

如果你想在本地开发，需要：

1. Python 3.12+
2. Poetry 包管理器

安装依赖：
```bash
poetry install
```

启动服务：
```bash
poetry run uvicorn media_video_dump.main:app --reload
```