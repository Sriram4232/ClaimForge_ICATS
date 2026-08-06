import os
import io
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Dict, Any

from app.api.schemas import EvaluateRequest, VerifyAadhaarRequest, SubmitClaimRequest, DecisionRequest
from app.core.database import BASE_DIR, MONGO_AVAILABLE, grid_fs
from app.repositories.claim_repository import get_claim_by_id, save_claim
from app.services.auth_service import get_current_user, RoleChecker
from app.services.claim_service import get_claims_service, submit_claim_service, post_decision_service
from app.services.aadhaar_service import verify_aadhaar_kyc_service
from app.utils.icats_engine import evaluate_claim

router = APIRouter(prefix="/api/claims", tags=["Claims"])

VIEWS_DIR = os.path.join(BASE_DIR, "views")
ASSETS_DIR = os.path.join(VIEWS_DIR, "assets")

# Ensure subfolders exist
for role in ["claimant", "bank_employee", "insurer"]:
    os.makedirs(os.path.join(ASSETS_DIR, role), exist_ok=True)

@router.get("")
def get_claims(current_user: dict = Depends(get_current_user)):
    return get_claims_service(current_user)

@router.post("/evaluate")
def evaluate(req: EvaluateRequest, current_user: dict = Depends(get_current_user)):
    policy_dict = req.policy.dict()
    claim_dict = req.claim.dict()
    return evaluate_claim(policy_dict, claim_dict)

@router.post("/verify-aadhaar")
def verify_aadhaar_endpoint(
    req: VerifyAadhaarRequest,
    current_user: dict = Depends(RoleChecker(["bank_employee", "insurer"]))
):
    return verify_aadhaar_kyc_service(req.case_id)

@router.post("/submit")
def submit(req: SubmitClaimRequest, current_user: dict = Depends(RoleChecker(["claimant"]))):
    return submit_claim_service(req, current_user)

@router.post("/decision")
def post_decision(
    req: DecisionRequest,
    current_user: dict = Depends(RoleChecker(["insurer", "bank_employee"]))
):
    return post_decision_service(req, current_user)

@router.post("/upload")
def upload_file(
    case_id: str = Form(...),
    document_type: str = Form(...),
    role: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if role not in ["claimant", "bank_employee", "insurer"]:
        raise HTTPException(status_code=400, detail="Invalid uploading role context.")
        
    filename = f"{case_id}_{document_type}_{file.filename}"
    file_bytes = file.file.read()
    sha = hashlib.sha256(file_bytes).hexdigest()
    
    url = f"/api/claims/file/{role}/{filename}"
    
    if MONGO_AVAILABLE and grid_fs is not None:
        existing = grid_fs.find_one({"filename": filename})
        if existing:
            grid_fs.delete(existing._id)
        grid_fs.put(
            file_bytes,
            filename=filename,
            metadata={"case_id": case_id, "document_type": document_type, "role": role},
            content_type=file.content_type
        )
    else:
        role_dir = os.path.join(ASSETS_DIR, role)
        os.makedirs(role_dir, exist_ok=True)
        filepath = os.path.join(role_dir, filename)
        with open(filepath, "wb") as buffer:
            buffer.write(file_bytes)
        url = f"/static/assets/{role}/{filename}"
        
    # Update claim record
    claim = get_claim_by_id(case_id)
    if claim:
        if "submitted_documents" not in claim["claim"]:
            claim["claim"]["submitted_documents"] = []
            
        doc_key = document_type
        if doc_key not in claim["claim"]["submitted_documents"]:
            claim["claim"]["submitted_documents"].append(doc_key)
            
        if claim["status"] == "QUERY_RAISED" and role == "bank_employee":
            if "FIR" in claim["claim"]["submitted_documents"] and "Post_Mortem_Report" in claim["claim"]["submitted_documents"]:
                claim["claim"]["claim_forms"]["Form_C"] = True
                claim["claim"]["investigation"]["police_final_report_status"] = "SUBMITTED"
            
        save_claim(claim)
        
    return {"filename": filename, "sha256": sha, "url": url}

@router.get("/file/{role}/{filename}")
def get_claim_file(role: str, filename: str, current_user: dict = Depends(get_current_user)):
    if MONGO_AVAILABLE and grid_fs is not None:
        grid_out = grid_fs.find_one({"filename": filename})
        if grid_out:
            return StreamingResponse(
                io.BytesIO(grid_out.read()),
                media_type=grid_out.content_type or "application/octet-stream",
                headers={"Content-Disposition": f"inline; filename={filename}"}
            )
            
    filepath = os.path.join(ASSETS_DIR, role, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
        
    raise HTTPException(status_code=404, detail="Requested dossier file not found.")
