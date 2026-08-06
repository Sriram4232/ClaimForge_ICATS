import json
import os
from typing import List, Dict, Any, Optional
from app.core.database import MONGO_AVAILABLE, users_col, JSON_DB_PATH

def get_all_users() -> List[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return list(users_col.find({}, {"_id": 0}))
    else:
        if not os.path.exists(JSON_DB_PATH):
            return []
        with open(JSON_DB_PATH, "r") as f:
            return json.load(f).get("users", [])

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return users_col.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}}, {"_id": 0})
    else:
        users = get_all_users()
        return next((u for u in users if u["email"].lower() == email.lower()), None)
