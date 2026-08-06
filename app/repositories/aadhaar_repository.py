import json
import os
from typing import Dict, Any, Optional
from app.core.database import MONGO_AVAILABLE, aadhaar_col, JSON_DB_PATH

def get_aadhaar_profile(aadhaar_num: str) -> Optional[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return aadhaar_col.find_one({"aadhaar": aadhaar_num}, {"_id": 0})
    else:
        if not os.path.exists(JSON_DB_PATH):
            return None
        with open(JSON_DB_PATH, "r") as f:
            profiles = json.load(f).get("aadhaar", [])
        return next((p for p in profiles if p["aadhaar"] == aadhaar_num), None)
