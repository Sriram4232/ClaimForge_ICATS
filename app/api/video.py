import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.core.database import BASE_DIR

router = APIRouter(tags=["Videos"])

def resolve_video_file(role: str) -> str:
    role_map = {
        "claimant": "Claimant_bg",
        "bank_employee": "Banker_bg",
        "banker": "Banker_bg",
        "insurer": "Insurer_bg",
        "guest": "Claimant_bg"
    }
    
    base_name = role_map.get(role.lower(), "Claimant_bg")
    
    for ext in [".mp4", ".webm", ".mov", ".avi", ".mkv"]:
        path = os.path.join(BASE_DIR, "assets", "videos", base_name + ext)
        if os.path.exists(path):
            return path
        path = os.path.join(BASE_DIR, "assets", "videos", base_name.lower() + ext)
        if os.path.exists(path):
            return path
    return ""

@router.get("/api/bg-video/{role}")
def get_bg_video(role: str):
    path = resolve_video_file(role)
    if path:
        ext = os.path.splitext(path)[1]
        return FileResponse(path, media_type=f"video/{ext[1:]}")
    raise HTTPException(status_code=404, detail="Background video file not found.")

@router.get("/api/video/background")
def get_video_background(role: str = Query("guest")):
    path = resolve_video_file(role)
    if path:
        ext = os.path.splitext(path)[1]
        return FileResponse(path, media_type=f"video/{ext[1:]}")
    raise HTTPException(status_code=404, detail="Background video file not found.")
