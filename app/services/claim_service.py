import copy
import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.repositories.claim_repository import get_all_claims, get_claim_by_id, save_claim, save_claims
from app.utils.icats_engine import evaluate_claim

def mask_aadhaar(aadhaar: str) -> str:
    if not aadhaar:
        return ""
    cleaned = aadhaar.replace("-", "").strip()
    if len(cleaned) == 12:
        return f"XXXX-XXXX-{cleaned[-4:]}"
    return "XXXX-XXXX-xxxx"

def mask_claims_for_role(claims: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    copied = copy.deepcopy(claims)
    for c in copied:
        if role != "claimant":
            claimant = c.get("claim", {}).get("claimant", {})
            if claimant and "aadhaar" in claimant:
                claimant["aadhaar"] = mask_aadhaar(claimant["aadhaar"])
    return copied

def get_claims_service(current_user: dict) -> List[Dict[str, Any]]:
    claims = get_all_claims()
    role = current_user.get("role")
    
    # Restrict claims for claimants to their own claims
    if role == "claimant":
        claims = [c for c in claims if c.get("claim", {}).get("claimant", {}).get("name", "").lower() == current_user.get("name", "").lower()]
    
    # Evaluate claims dynamically
    for c in claims:
        eval_res = evaluate_claim(c["policy"], c["claim"], c.get("status"))
        c["evaluation"] = eval_res
        
    return mask_claims_for_role(claims, role)

def submit_claim_service(req: Any, current_user: dict) -> Dict[str, Any]:
    claims = get_all_claims()
    tracking_id = f"CLM-2026-{req.policy.policy_number[-4:]}-{1000 + len(claims)}"
    
    new_claim = {
        "id": req.id,
        "status": "SUBMITTED",
        "trackingId": tracking_id,
        "policy": req.policy.dict(),
        "claim": req.claim.dict(),
        "state_history": [
            {
                "from": "INIT",
                "to": "SUBMITTED",
                "at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "by": "claimant"
            }
        ]
    }
    
    save_claim(new_claim)
    return {"status": "SUBMITTED", "trackingId": tracking_id}

def post_decision_service(req: Any, current_user: dict) -> Dict[str, Any]:
    claim = get_claim_by_id(req.case_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim record not found.")
        
    current_status = claim.get("status", "SUBMITTED").upper()
    next_status = req.status.upper()
    
    allowed = {
        "SUBMITTED": ["UNDER_REVIEW"],
        "UNDER_REVIEW": ["APPROVED", "REJECTED", "QUERY_RAISED"],
        "QUERY_RAISED": ["RESUBMITTED"],
        "RESUBMITTED": ["UNDER_REVIEW"],
        "APPROVED": [],
        "REJECTED": []
    }
    
    if next_status not in allowed.get(current_status, []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid state transition: {current_status} -> {next_status}")
        
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    if "state_history" not in claim:
        claim["state_history"] = []
    claim["state_history"].append({
        "from": current_status,
        "to": next_status,
        "at": now_str,
        "by": req.by,
        "comment": req.comment
    })
    
    claim["status"] = next_status
    save_claim(claim)
    
    return {"status": next_status}
