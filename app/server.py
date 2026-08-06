import os
import sys

# Ensure parent directory is in path so 'app' package resolves correctly
app_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_parent not in sys.path:
    sys.path.insert(0, app_parent)

from app.main import app
from app.core.database import MOCK_USERS
from app.repositories.claim_repository import get_all_claims, save_claims

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
