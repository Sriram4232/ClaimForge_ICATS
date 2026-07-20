import json
import os
import sys
import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from icats_engine import evaluate_claim

def regenerate_real_cases():
    # We will define the 5 core cases matching the new schema
    from server import load_db
    # Temporarily bypass MongoDB to get the clean mock_initial list
    import server
    server.MONGO_AVAILABLE = False
    
    # If claims_db.json exists, we can delete it temporarily to get clean mock_initial,
    # or just read the mock_initial variable directly via reflection if needed.
    # Actually, server.py has mock_initial defined in load_db. We can just load it.
    # Let's inspect server.py's load_db and extract the mock cases.
    raw_cases = server.load_db()
    
    real_cases = []
    for case in raw_cases:
        # Keep only the first 5 cases (CASE-001 to CASE-005)
        if case["id"] not in ["CASE-001", "CASE-002", "CASE-003", "CASE-004", "CASE-005"]:
            continue
            
        policy = case["policy"]
        claim = case["claim"]
        
        # Run evaluate_claim to get expected evaluation
        eval_res = evaluate_claim(policy, claim)
        
        real_cases.append({
            "id": case["id"],
            "title": f"Core Case {case['id']}",
            "source_citation": "Standard ICATS Mock Database Case",
            "policy": policy,
            "claim": claim,
            "expected_evaluation": {
                "status": eval_res["status"],
                "flags": eval_res["flags"],
                "missing_documents": eval_res["missing_documents"],
                "calculated_payout": eval_res["calculated_payout"]
            }
        })
        
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_test_cases.json")
    with open(output_path, "w") as f:
        json.dump(real_cases, f, indent=2)
    print(f"[+] Regenerated {len(real_cases)} core cases in real_test_cases.json")


def regenerate_expanded_cases():
    base_cases = []
    
    names = [
        {"policy": "Rajesh Kumar", "nominee": "Sunita Devi", "cheque": "Sunita Devi", "match": True},
        {"policy": "Amit Sharma", "nominee": "Ritu Sharma", "cheque": "Ritu A. Sharma", "match": True}, # fuzzy match
        {"policy": "Vikram Singh", "nominee": "Preeti Singh", "cheque": "Preeti Kumari", "match": False}, # spelling discrepancy
        {"policy": "Manoj Pillai", "nominee": "Chitra Devi", "cheque": "Chithra D. Pillai", "match": False}, # spelling discrepancy
        {"policy": "Sanjay Gupta", "nominee": "Karan Gupta", "cheque": "Anil Gupta", "match": False} # complete mismatch
    ]
    
    causes = [
        {"cause": "Cardiac Arrest", "type": "Natural"},
        {"cause": "COVID-19 Complications", "type": "Natural"},
        {"cause": "Polytrauma due to Road Traffic Accident", "type": "Accidental"},
        {"cause": "Accidental Drowning in pool", "type": "Accidental"},
        {"cause": "Asphyxiation due to Hanging (Suicide)", "type": "Suicide"}
    ]
    
    policy_numbers = 100000000
    case_idx = 1
    
    for name_pair in names:
        for cause_info in causes:
            for days_elapsed in [100, 500, 1200]:
                commencement = datetime.date(2022, 1, 1)
                death_date = commencement + datetime.timedelta(days=days_elapsed)
                
                for premiums_paid in [1, 3]:
                    policy_num = str(policy_numbers + case_idx)
                    
                    # Calculate lapsed status
                    years_elapsed = days_elapsed / 365.25
                    is_lapsed = premiums_paid < int(years_elapsed)
                    policy_status = "LAPSED" if is_lapsed else "ACTIVE"
                    
                    # Last premium date
                    last_premium_date = (commencement + datetime.timedelta(days=(premiums_paid-1)*365)).strftime("%d/%m/%Y")
                    
                    policy = {
                        "policy_number": policy_num,
                        "commencement_date": commencement.strftime("%d/%m/%Y"),
                        "maturity_date": (commencement + datetime.timedelta(days=3650)).strftime("%d/%m/%Y"),
                        "sum_assured": 1000000.0,
                        "premium_paying_term_years": 10,
                        "premiums_paid_years": premiums_paid,
                        "nominee_name": name_pair["nominee"],
                        "life_assured": name_pair["policy"],
                        "exclusions": ["Suicide within 12 months"],
                        "last_premium_paid_date": last_premium_date,
                        "policy_status": policy_status
                    }
                    
                    # Claimant Object
                    claimant = {
                        "name": name_pair["cheque"],
                        "relationship": "Wife" if name_pair["match"] else "Relative",
                        "aadhaar": f"1234-5678-{9000 + case_idx}",
                        "phone": "9876543210",
                        "address": "Test Address, India"
                    }
                    
                    # Claim Forms Checklist
                    # If accidental or early natural, simulate checklist presence.
                    # Standard behavior: Claimant downloads and fills Form A, Doctor fills Form B.
                    # Hospital Certificate (Form C) might be missing for accidental deaths/some early claims to test queries.
                    is_accidental = cause_info["type"] == "Accidental"
                    
                    form_c_present = True
                    # Let's say Form C is missing for accidental claims to trigger missing police/form doc check
                    if is_accidental:
                        form_c_present = False
                        
                    claim_forms = {
                        "Form_A": True,
                        "Form_B": True,
                        "Form_C": form_c_present
                    }
                    
                    # Bank Details
                    bank_details = {
                        "account_number": f"98765432{case_idx:02d}",
                        "ifsc": "SBIN0000001",
                        "bank_name": "State Bank of India",
                        "name_on_cheque": name_pair["cheque"]
                    }
                    
                    # Medical Details
                    medical_details = {
                        "hospital_discharge_summary": "Dialysis three times a week since October 2020." if (cause_info["type"] == "Natural" and case_idx % 2 == 0) else "Patient treated.",
                        "treating_doctor": "Dr. Test",
                        "underlying_disease": "Chronic Kidney Disease" if (cause_info["type"] == "Natural" and case_idx % 2 == 0) else cause_info["cause"],
                        "icd_code": "N18.9" if (cause_info["type"] == "Natural" and case_idx % 2 == 0) else "I46.9",
                        "hospitalization_history": "Chronic kidney failure dialysis." if (cause_info["type"] == "Natural" and case_idx % 2 == 0) else ""
                    }
                    
                    # Investigation
                    police_final_report_status = "NOT_APPLICABLE"
                    investigation_status = "NOT_APPLICABLE"
                    if is_accidental:
                        investigation_status = "PENDING"
                        police_final_report_status = "NOT_SUBMITTED"
                        
                    investigation = {
                        "investigation_status": investigation_status,
                        "police_final_report_status": police_final_report_status,
                        "accident_details": "Road crash" if is_accidental else ""
                    }
                    
                    # Legal Status
                    legal_status = {
                        "nominee_verified": name_pair["match"],
                        "legal_heir_required": not name_pair["match"],
                        "succession_certificate_status": "NOT_REQUIRED" if name_pair["match"] else "NOT_SUBMITTED"
                    }
                    
                    # Submitted documents list of strings
                    submitted_docs = ["Death_Certificate", "Cancelled_Cheque"]
                    if not name_pair["match"]:
                        # Nominee name mismatch
                        pass
                    else:
                        submitted_docs.append("Nominee_Aadhaar")
                        
                    if cause_info["type"] == "Natural":
                        submitted_docs.append("Medical_Records")
                        
                    claim = {
                        "date_of_death": death_date.strftime("%d/%m/%Y"),
                        "cause_of_death": cause_info["cause"],
                        "place_of_death": "City Hospital" if cause_info["type"] == "Natural" else "Public Highway",
                        "date_of_intimation": (death_date + datetime.timedelta(days=10)).strftime("%d/%m/%Y"),
                        "submitted_documents": submitted_docs,
                        "claimant": claimant,
                        "claim_forms": claim_forms,
                        "bank_details": bank_details,
                        "medical_details": medical_details,
                        "investigation": investigation,
                        "legal_status": legal_status
                    }
                    
                    # Evaluate using upgraded engine
                    eval_res = evaluate_claim(policy, claim)
                    
                    base_cases.append({
                        "id": f"GEN-CASE-{case_idx:03d}",
                        "title": f"Autogenerated Test Case: {cause_info['type']} Claim - {days_elapsed}d elapsed, {premiums_paid} premiums paid",
                        "source_citation": "Combinatorial Rule Generation",
                        "policy": policy,
                        "claim": claim,
                        "expected_evaluation": {
                            "status": eval_res["status"],
                            "flags": eval_res["flags"],
                            "missing_documents": eval_res["missing_documents"],
                            "calculated_payout": eval_res["calculated_payout"]
                        }
                    })
                    case_idx += 1
                    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expanded_test_cases.json")
    with open(output_path, "w") as f:
        json.dump(base_cases, f, indent=2)
    print(f"[+] Regenerated {len(base_cases)} expanded cases in expanded_test_cases.json")

if __name__ == "__main__":
    regenerate_real_cases()
    regenerate_expanded_cases()
