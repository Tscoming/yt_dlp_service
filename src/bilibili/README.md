# Bilibili 视频上传服务

这是一个基于 FastAPI 的 REST API 服务，用于将视频上传到 Bilibili。

## 设置

1.  **安装依赖:**

    确保您已安装根目录 `requirements.txt` 中列出的所有依赖项。
    ```bash
    pip3 install -r ../requirements.txt
    ```

2.  **配置凭证:**

    将 `bilibili/.env.example` 文件复制为 `bilibili/.env`：
    ```bash
    cp .env.example .env
    ```
    然后，编辑 `.env` 文件并填入您的 Bilibili 凭证 (`SESSDATA`, `BILI_JCT`, `BUVID3`)。

    **如何获取 Bilibili 凭证:**
    - 登录 [bilibili.com](https://www.bilibili.com/)。
    - 打开浏览器的开发者工具 (通常按 F12)。
    - 转到 `Application` (应用) -> `Cookies` -> `https://www.bilibili.com`。
    - 在 Cookie 列表中找到 `SESSDATA`, `bili_jct` 和 `buvid3`，并复制它们的值。

## 如何运行服务

使用 `uvicorn` 在项目根目录中运行服务：

```bash
uvicorn bilibili.main:app --host 0.0.0.0 --port 8001
```

服务将在 `http://0.0.0.0:8001` 上可用。

## API 端点

### `POST /upload`

在后台任务中上传一个或多个视频片段。

**请求体 (JSON):**

```json
{
  "pages": [
    {
      "path": "/path/to/your/video1.mp4",
      "title": "视频片段1的标题",
      "description": "这是第一个视频片段的简介。"
    }
  ],
  "tid": 130,
  "title": "视频的总标题",
  "tags": ["标签1", "标签2"],
  "desc": "视频的完整描述。",
  "cover": "/path/to/your/cover_image.jpg",
  "no_reprint": true,
  "source": ""
}
```

-   `pages`: 一个视频片段对象的列表。
    -   `path`: (必须) 视频文件的绝对路径。
    -   `title`: (必须) 该片段的标题。
    -   `description`: (可选) 该片段的简介。
-   `tid`: (必须) Bilibili 分区 ID (例如, 130 代表“音乐综合”)。
-   `title`: (必须) 视频的总标题。
-   `tags`: (必须) 标签列表。
-   `desc`: (可选) 视频的描述。
-   `cover`: (可选) 封面的绝对路径。如果未提供，Bilibili 将使用视频的第一帧。
-   `no_reprint`: (可选) 是否禁止转载 (默认为 `true`)。
-   `source`: (可选) 如果是转载视频，请在此处填写来源。

**响应:**

```json
{
  "message": "Upload task accepted and running in the background."
}
```

上传过程将在后台进行。您可以在运行 `uvicorn` 的终端中查看上传进度和日志。
