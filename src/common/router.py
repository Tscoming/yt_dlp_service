import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/upload")
async def upload_file(
    video_id: str = Form(...),
    fileName: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Uploads a file to a specific subdirectory within the video download path.
    """
    try:
        download_root = os.environ.get('VIDEO_DOWNLOAD_PATH', 'downloads')
        
        # Sanitize video_id and fileName to prevent path traversal
        if ".." in video_id or "/" in video_id:
            raise HTTPException(status_code=400, detail="Invalid video_id.")
        if ".." in fileName or "/" in fileName:
            raise HTTPException(status_code=400, detail="Invalid fileName.")

        upload_path = os.path.join(download_root, video_id)
        os.makedirs(upload_path, exist_ok=True)

        file_path = os.path.join(upload_path, fileName)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(status_code=200, content={"message": f"File '{fileName}' uploaded successfully to '{upload_path}'."})

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})
    finally:
        if file:
            await file.close()
