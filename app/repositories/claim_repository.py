import json
import os
from typing import List, Dict, Any, Optional
from app.core.database import MONGO_AVAILABLE, claims_col, JSON_DB_PATH

def get_all_claims() -> List[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return list(claims_col.find({}, {"_id": 0}))
    else:
        if not os.path.exists(JSON_DB_PATH):
            return []
        with open(JSON_DB_PATH, "r") as f:
            return json.load(f).get("claims", [])

def get_claim_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return claims_col.find_one({"id": case_id}, {"_id": 0})
    else:
        claims = get_all_claims()
        return next((c for c in claims if c["id"] == case_id), None)

def save_claim(claim_data: Dict[str, Any]):
    if MONGO_AVAILABLE:
        cleaned = claim_data.copy()
        cleaned.pop("_id", None)
        claims_col.replace_one({"id": claim_data["id"]}, cleaned, upsert=True)
    else:
        claims = get_all_claims()
        claims = [c for c in claims if c["id"] != claim_data["id"]]
        claims.append(claim_data)
        
        with open(JSON_DB_PATH, "r") as f:
            data = json.load(f)
        data["claims"] = claims
        with open(JSON_DB_PATH, "w") as f:
            json.dump(data, f, indent=2)

def save_claims(claims: List[Dict[str, Any]]):
    if MONGO_AVAILABLE:
        claims_col.delete_many({})
        if claims:
            cleaned = []
            for c in claims:
                item = c.copy()
                item.pop("_id", None)
                cleaned.append(item)
            claims_col.insert_many(cleaned)
    else:
        with open(JSON_DB_PATH, "r") as f:
            data = json.load(f)
        data["claims"] = claims
        with open(JSON_DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
