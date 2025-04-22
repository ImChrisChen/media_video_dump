FROM python:3.12-slim

WORKDIR /app

# 安装 poetry
RUN pip install poetry

# 安装 ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml poetry.lock ./
COPY media_video_dump ./media_video_dump
COPY README.md ./

# 安装依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["poetry", "run", "uvicorn", "media_video_dump.main:app", "--host", "0.0.0.0", "--port", "8000"]
