import datetime
from fastapi import APIRouter, HTTPException, Query
from app.repositories.claim_repository import get_all_claims, save_claim
from app.utils.icats_engine import evaluate_claim

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.post("/simulate")
def simulate_agents(case_id: str = Query("CASE-002")):
    # Simulation doesn't enforce strict security to facilitate end-to-end demo scripts
    db_claims = get_all_claims()
    claim = next((c for c in db_claims if c["id"] == case_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail="Simulated Case not found.")
        
    logs = []
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    logs.append(f"[{now_str}] [Claimant Agent] Autopilot triggered for Case ID: {case_id}")
    logs.append(f"[{now_str}] [Claimant Agent] Reading dossier details for insured: {claim['policy']['life_assured']}")
    logs.append(f"[{now_str}] [Claimant Agent] Verifying Forms A and B compliance checklist...")
    logs.append(f"[{now_str}] [Claimant Agent] Submitting claim dossier to Insurer Portal.")
    
    claim["status"] = "SUBMITTED"
    claim["state_history"] = [{
        "from": "INIT",
        "to": "SUBMITTED",
        "at": now_str,
        "by": "claimant_agent",
        "comment": "Autopilot Initial Intake Submission"
    }]
    
    logs.append(f"[{now_str}] [Insurer Agent] Running icats_engine compliance audits...")
    eval_res = evaluate_claim(claim["policy"], claim["claim"])
    
    if eval_res["status"] in ["QUERY_RAISED", "MISSING_MANDATORY_DOCUMENTS", "FLAGGED_DISCREPANCY"]:
        logs.append(f"[{now_str}] [Insurer Agent] Compliance Check Failed: {eval_res['explainability']['summary']}.")
        logs.append(f"[{now_str}] [Insurer Agent] Flagged Missing Documents: {eval_res['missing_documents']}")
        logs.append(f"[{now_str}] [Insurer Agent] Transitioning claim status to QUERY_RAISED.")
        
        claim["status"] = "QUERY_RAISED"
        claim["state_history"].append({
            "from": "SUBMITTED",
            "to": "QUERY_RAISED",
            "at": now_str,
            "by": "insurer_agent",
            "comment": f"Auto Query: {eval_res['explainability']['summary']}"
        })
        
        logs.append(f"[{now_str}] [Bank Agent] Scanning branch query queue. Found Case: {case_id} (Status: QUERY_RAISED).")
        logs.append(f"[{now_str}] [Bank Agent] Calling Simulated Municipal/Police Portal API to fetch missing documents...")
        
        if "submitted_documents" not in claim["claim"]:
            claim["claim"]["submitted_documents"] = []
            
        if "accident" in claim["claim"]["cause_of_death"].lower():
            if "FIR" not in claim["claim"]["submitted_documents"]:
                claim["claim"]["submitted_documents"].append("FIR")
                logs.append(f"[{now_str}] [Bank Agent] Retreived certified FIR (Sec 174 CrPC). Saved to assets/bank_employee/.")
            if "Post_Mortem_Report" not in claim["claim"]["submitted_documents"]:
                claim["claim"]["submitted_documents"].append("Post_Mortem_Report")
                logs.append(f"[{now_str}] [Bank Agent] Retreived certified Post-Mortem Report. Saved to assets/bank_employee/.")
            claim["claim"]["claim_forms"]["Form_C"] = True
            claim["claim"]["investigation"]["police_final_report_status"] = "SUBMITTED"
        else:
            claim["claim"]["legal_status"]["nominee_verified"] = True
            if "Nominee_Aadhaar" not in claim["claim"]["submitted_documents"]:
                claim["claim"]["submitted_documents"].append("Nominee_Aadhaar")
            logs.append(f"[{now_str}] [Bank Agent] Verified nominee identity biometric. Generated name mismatch affidavit.")
            
        logs.append(f"[{now_str}] [Bank Agent] Resubmitting verified dossier back to underwriter queue.")
        claim["status"] = "RESUBMITTED"
        claim["state_history"].append({
            "from": "QUERY_RAISED",
            "to": "RESUBMITTED",
            "at": now_str,
            "by": "bank_agent",
            "comment": "Uploaded missing reports and verified biometric KYC details."
        })
        
        logs.append(f"[{now_str}] [Insurer Agent] Scanning resubmissions. Found Case: {case_id}.")
        logs.append(f"[{now_str}] [Insurer Agent] Claim transitioned to UNDER_REVIEW for final audit.")
        claim["status"] = "UNDER_REVIEW"
        claim["state_history"].append({
            "from": "QUERY_RAISED", # Wait, in original server.py it transitions from "RESUBMITTED" to "UNDER_REVIEW"
            "to": "UNDER_REVIEW",
            "at": now_str,
            "by": "insurer_agent",
            "comment": "Triage evaluation start"
        })
        # Wait, the state history transition from in original server.py was from "RESUBMITTED" to "UNDER_REVIEW".
        # Let's match original server.py exactly:
        # `claim["state_history"].append({"from": "RESUBMITTED", "to": "UNDER_REVIEW", ...})`
        # Let's fix this in the code below to match it 100%.
        claim["state_history"][-1]["to"] = "RESUBMITTED" # wait, the previous was QUERY_RAISED -> RESUBMITTED.
        # So we append a new one:
        claim["state_history"].append({
            "from": "RESUBMITTED",
            "to": "UNDER_REVIEW",
            "at": now_str,
            "by": "insurer_agent",
            "comment": "Triage evaluation start"
        })
        
        claim["status"] = "UNDER_REVIEW"
        
        final_eval = evaluate_claim(claim["policy"], claim["claim"])
        logs.append(f"[{now_str}] [Insurer Agent] Running final icats_engine calculations...")
        logs.append(f"[{now_str}] [Insurer Agent] Rules check passed. Payout eligibility: {final_eval['payout']['type']} ({final_eval['payout']['amount']:.2f} INR).")
        
        if final_eval["status"] in ["READY", "LAPSED_PAID_UP"]:
            claim["status"] = "APPROVED"
            claim["state_history"].append({
                "from": "UNDER_REVIEW",
                "to": "APPROVED",
                "at": now_str,
                "by": "insurer_agent",
                "comment": "Auto-approved. Cleared for bank disbursal payout."
            })
            logs.append(f"[{now_str}] [Insurer Agent] Claim APPROVED. Disbursal Clearance Certificate issued.")
        else:
            claim["status"] = "REJECTED"
            claim["state_history"].append({
                "from": "UNDER_REVIEW",
                "to": "REJECTED",
                "at": now_str,
                "by": "insurer_agent",
                "comment": f"Auto-rejected: {final_eval['explainability']['summary']}"
            })
            logs.append(f"[{now_str}] [Insurer Agent] Claim REJECTED: {final_eval['explainability']['summary']}.")
    else:
        logs.append(f"[{now_str}] [Insurer Agent] Checks passed immediately. Payout: {eval_res['payout']['amount']:.2f} INR.")
        claim["status"] = "APPROVED"
        claim["state_history"].append({
            "from": "SUBMITTED",
            "to": "APPROVED",
            "at": now_str,
            "by": "insurer_agent",
            "comment": "Auto-approved. Direct intake clearance successful."
        })
        logs.append(f"[{now_str}] [Insurer Agent] Claim APPROVED. Disbursal Clearance Certificate issued.")

    save_claim(claim)
    return {"logs": logs}
