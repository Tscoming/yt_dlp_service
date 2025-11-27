# Project Overview

This document provides an overview of the `yt_dlp_service` project, including its folder structure, key components, and setup instructions.

## Folder Structure

```
/home/ubuntu/workspaces/yt/yt_dlp_service/
├───.env.example
├───.gitignore
├───docker-compose.yaml
├───Dockerfile
├───LICENSE
├───README.md
├───.git/...
├───docs/
│   └───v_voucher.md
├───downloads/
│   ├───jNQXAC9IVRw/...
│   └───test_video_123/...
├───scripts/
│   ├───run_client.sh
│   └───setenv.sh
├───src/
│   ├───requirements.txt
│   ├───api_gateway/
│   │   ├───main.py
│   │   └───__pycache__/
│   ├───bilibili/
│   │   ├───__init__.py
│   │   ├───config.py
│   │   ├───README.md
│   │   ├───router.py
│   │   ├───uploader.py
│   │   └───__pycache__/
│   ├───common/
│   │   ├───router.py
│   │   └───__pycache__/
│   └───youtube/
│       ├───__init__.py
│       ├───client.py
│       ├───router.py
│       ├───ydl_opts.json
│       └───__pycache__/
└───tests/
    ├───api_tests.http
    └───test_api.py
```

## Setup Instructions

To set up the project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd yt_dlp_service
    ```
2.  **Set up environment variables:**
    Copy `.env.example` to `.env` and fill in the necessary values.
    ```bash
    cp .env.example .env
    # Edit .env file
    ```
3.  **Build and run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    Alternatively, you can set up a virtual environment and install dependencies manually:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r src/requirements.txt
    ```
    Then run the `main.py` from `src/api_gateway`.

## Key Components

-   **`src/api_gateway/main.py`**: The main entry point for the API gateway.
-   **`src/bilibili/`**: Contains modules for Bilibili integration, including routing and uploading functionalities.
-   **`src/youtube/`**: Contains modules for YouTube integration, including client and routing functionalities.
-   **`src/common/`**: Shared utilities and common routers.
-   **`tests/`**: Contains API tests.
-   **`docker-compose.yaml`**: Defines the services, networks, and volumes for the Dockerized application.
-   **`Dockerfile`**: Specifies how the Docker image for the application is built.
