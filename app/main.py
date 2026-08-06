import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import BASE_DIR
from app.core.config import HOST, PORT

# Import API routers
from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.agents import router as agents_router
from app.api.video import router as video_router

app = FastAPI(title="ICATS - Insurance Claim Assistance & Tracking System API (MVC)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup views static directories
VIEWS_DIR = os.path.join(BASE_DIR, "views")
ASSETS_DIR = os.path.join(VIEWS_DIR, "assets")

# Mount static assets
app.mount("/static/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Register APIRouters
app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(agents_router)
app.include_router(video_router)

@app.get("/")
def read_index():
    return FileResponse(os.path.join(VIEWS_DIR, "index.html"))

@app.get("/app.js")
def read_js():
    return FileResponse(os.path.join(VIEWS_DIR, "app.js"))

@app.get("/style.css")
def read_css():
    return FileResponse(os.path.join(VIEWS_DIR, "style.css"))

@app.get("/api/config")
def get_config():
    from app.core import config
    return {
        "app_name": config.APP_NAME,
        "app_version": config.APP_VERSION,
        "api_version": config.API_VERSION,
        "tools": config.APP_TOOLS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
