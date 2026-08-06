import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

# Try loading .env from parent of app/ or app/
load_env_file(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_env_file(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.getenv("JWT_SECRET", "icats_super_secret_signing_key_for_jwt_tokens")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
Testing = os.getenv("Testing", "False").lower() in ("true", "1", "yes")

# Application Info & Versioning
APP_NAME = "ICATS"
APP_VERSION = "1.0.4"
API_VERSION = "v1"

# Presently used tools & technologies (can be updated later)
APP_TOOLS = {
    "Backend": "Python FastAPI 0.100+",
    "Frontend": "Vite React SPA / Vanilla JS views",
    "Database": "MongoDB / File-based JSON database fallback",
    "Engine": "Custom Rule-based Decision Engine",
    "Styling": "Sleek Obsidian CSS variables (Cyber Neon theme)"
}
