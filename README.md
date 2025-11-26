# 项目概述

该项目提供了一个统一的 REST API 网关服务，用于调度和管理不同的视频服务，目前包括基于 `yt-dlp` 库的视频下载和元数据检索服务，以及一个用于上传视频到 Bilibili 的服务。所有服务都使用 FastAPI 构建，旨在在 Docker 容器中运行。

## 构建和运行

### 使用 Docker（推荐）

运行该服务最直接的方法是使用 Docker 和 Docker Compose。

1.  **构建并运行服务：**
    ```bash
    docker-compose up -d --build
    ```
    此命令将构建 Docker 镜像并在后台启动服务。API 网关将在 `http://localhost:9000` 上可访问。

2.  **停止服务：**
    ```bash
    docker-compose down
    ```

### 本地运行

您也可以直接在您的机器上运行该服务。

1.  **安装依赖项：**
    ```bash
    pip install -r src/requirements.txt
    ```

2.  **运行服务：**
    ```bash
    uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 9000
    ```
    对于开发，您可以使用 `--reload` 标志在代码更改时自动重新启动服务器：
    ```bash
    uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 9000 --reload
    ```

## API 用法

API 网关启动后，您可以通过以下路径访问不同的服务：

### YouTube 视频服务

*   **获取视频信息**
    -   **端点：** `POST /api/v1/youtube/info`
    -   **请求体：**
        ```json
        {
          "url": "VIDEO_URL"
        }
        ```

*   **下载视频**
    -   **端点：** `POST /api/v1/youtube/download`
    -   **请求体：**
        ```json
        {
          "url": "VIDEO_URL",
          "subtitles": ["en", "es"]
        }
        ```
        `subtitles` 字段是可选的。

### Bilibili 上传服务

*   **上传视频到 Bilibili**
    -   **端点：** `POST /api/v1/bilibili/upload`
    -   **请求体：**
        ```json
        {
          "pages": [
            {
              "path": "/path/to/video1.mp4",
              "title": "Part 1",
              "description": "Description for part 1"
            }
          ],
          "tid": 1,
          "title": "My Awesome Video",
          "tags": ["tag1", "tag2"],
          "desc": "Full description of the video",
          "cover": "/path/to/cover.jpg",
          "no_reprint": true,
          "source": "Original"
        }
        ```

## 测试

该项目包括一套测试，以验证 API 的功能。

1.  **确保服务正在运行。**
2.  **运行测试：**
    ```bash
    python tests/test_api.py
    ```

## 开发约定

*   项目采用模块化结构，API 网关位于 `src/api_gateway/main.py`。
*   各个服务（如 `youtube` 和 `bilibili`）的代码分别位于 `src/youtube/router.py` 和 `src/bilibili/router.py` 中，并作为 `APIRouter` 注册到 API 网关。
*   `src/youtube/ydl_opts.json` 文件可用于自定义 `yt-dlp` 的行为。
*   Cookie 文件可用于需要登录的站点。Cookie 文件的路径通过 `COOKIE_FILE_PATH` 环境变量指定。
