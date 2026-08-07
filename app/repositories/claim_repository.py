from typing import List, Dict, Any, Optional
from app.core.database import mongo_template

def get_all_claims() -> List[Dict[str, Any]]:
    """
    Retrieves all claims from the database collection using MongoTemplate.
    """
    return mongo_template.find("claims")

def get_claim_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a claim by its unique ID using MongoTemplate.
    """
    return mongo_template.find_one("claims", {"id": case_id})

def save_claim(claim_data: Dict[str, Any]):
    """
    Saves or updates a single claim record using MongoTemplate.
    """
    mongo_template.save("claims", {"id": claim_data["id"]}, claim_data, upsert=True)

def save_claims(claims: List[Dict[str, Any]]):
    """
    Deletes all claims and inserts a fresh set using MongoTemplate.
    """
    mongo_template.delete_many("claims", {})
    if claims:
        mongo_template.insert_many("claims", claims)
