from typing import List, Dict, Any, Optional
from app.core.database import mongo_template

def get_all_users() -> List[Dict[str, Any]]:
    """
    Retrieves all users from the user directory collection using MongoTemplate.
    """
    return mongo_template.find("users")

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a user by their unique email address using MongoTemplate regex query.
    """
    return mongo_template.find_one("users", {"email": {"$regex": f"^{email}$", "$options": "i"}})
