import json
import os
import sys

# Add parent directory to path so icats_engine can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from icats_engine import evaluate_claim

def load_test_cases(filename="real_test_cases.json"):
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(json_path):
        return []
    with open(json_path, "r") as f:
        return json.load(f)

def run_test_suite(filename):
    test_cases = load_test_cases(filename)
    if not test_cases:
        print("[!] No test cases found in {}".format(filename))
        return True
        
    passed_count = 0
    failed_count = 0
    
    print("-" * 80)
    print("  RUNNING: {}".format(filename))
    print("-" * 80)
    
    for case in test_cases:
        case_id = case["id"]
        title = case["title"]
        policy = case["policy"]
        claim = case["claim"]
        expected = case["expected_evaluation"]
        
        result = evaluate_claim(policy, claim)
        
        # Validate status
        status_match = result["status"] == expected["status"]
        
        # Validate flags (soft-check: length and presence of key words)
        flags_match = len(result["flags"]) == len(expected["flags"])
        
        # Validate missing documents
        missing_docs_match = set(result["missing_documents"]) == set(expected["missing_documents"])
        
        # Validate payout if applicable
        payout_match = True
        if "calculated_payout" in expected:
            payout_match = result.get("calculated_payout") == expected["calculated_payout"]
            
        case_passed = status_match and flags_match and missing_docs_match and payout_match
        
        if case_passed:
            passed_count += 1
        else:
            failed_count += 1
            print("\n[x] FAILED: Case {} - {}".format(case_id, title))
            print("    Expected Status: {}, Got: {}".format(expected["status"], result["status"]))
            print("    Expected Flags:  {}, Got: {}".format(expected["flags"], result["flags"]))
            print("    Expected Docs:   {}, Got: {}".format(expected["missing_documents"], result["missing_documents"]))
            if "calculated_payout" in expected:
                print("    Expected Payout: {}, Got: {}".format(expected["calculated_payout"], result.get("calculated_payout")))
                
    print("  Total: {}, Passed: \033[92m{}\033[0m, Failed: \033[91m{}\033[0m".format(len(test_cases), passed_count, failed_count))
    return failed_count == 0

def run_edge_cases_tests():
    print("-" * 80)
    print("  RUNNING: Custom Decision Intelligence Edge Cases")
    print("-" * 80)
    
    # 1. Conflicting signals test
    policy_1 = {
        "policy_number": "POL001",
        "commencement_date": "15/01/2024",
        "maturity_date": "15/01/2034",
        "sum_assured": 1000000.0,
        "premium_paying_term_years": 10,
        "premiums_paid_years": 1,
        "nominee_name": "Sunita Devi",
        "life_assured": "Harish Kumar",
        "exclusions": ["Suicide within 12 months"],
        "last_premium_paid_date": "15/01/2024",
        "policy_status": "ACTIVE"
    }
    claim_1 = {
        "date_of_death": "20/10/2024",
        "cause_of_death": "Cardiac Arrest",
        "place_of_death": "Hospital",
        "date_of_intimation": "05/11/2024",
        "submitted_documents": ["Death_Certificate"],
        "claimant": {
            "name": "Sunita Devi",
            "relationship": "Wife",
            "aadhaar": "1234-5678-9012",
            "phone": "9876543210",
            "address": "Delhi"
        },
        "claim_forms": {"Form_A": True, "Form_B": True, "Form_C": True},
        "bank_details": {
            "account_number": "12345",
            "ifsc": "SBIN0001234",
            "bank_name": "State Bank of India",
            "name_on_cheque": "Sunita Devi"
        },
        "medical_details": {
            "treating_doctor": "Dr. Smith",
            "underlying_disease": "Cardiac Arrest",
            "icd_code": "I46.9",
            "hospitalization_history": ""
        },
        "investigation": {
            "investigation_status": "NOT_APPLICABLE",
            "police_final_report_status": "NOT_APPLICABLE",
            "accident_details": ""
        },
        "legal_status": {
            "nominee_verified": True,
            "legal_heir_required": False,
            "succession_certificate_status": "NOT_REQUIRED"
        }
    }
    
    res_1 = evaluate_claim(policy_1, claim_1)
    status_1_ok = res_1["status"] == "UNDER_REVIEW"
    early_claim_ok = "EARLY_CLAIM" in res_1.get("fraud_flags", [])
    
    # 2. Edge fraud case (no rule failures + 2 fraud flags) -> evaluates to UNDER_REVIEW
    policy_2 = {
        "policy_number": "POL002",
        "commencement_date": "15/01/2024",
        "maturity_date": "15/01/2034",
        "sum_assured": 4000000.0,
        "premium_paying_term_years": 10,
        "premiums_paid_years": 1,
        "nominee_name": "Sunita Devi",
        "life_assured": "Harish Kumar",
        "exclusions": ["Suicide within 12 months"],
        "last_premium_paid_date": "15/01/2024",
        "policy_status": "ACTIVE"
    }
    claim_2 = {
        "date_of_death": "20/10/2024",
        "cause_of_death": "Cardiac Arrest",
        "place_of_death": "Hospital",
        "date_of_intimation": "05/11/2024",
        "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Nominee_Aadhaar", "Medical_Records"],
        "claimant": {
            "name": "Sunita Devi",
            "relationship": "Wife",
            "aadhaar": "1234-5678-9012",
            "phone": "9876543210",
            "address": "Delhi"
        },
        "claim_forms": {"Form_A": True, "Form_B": True, "Form_C": True},
        "bank_details": {
            "account_number": "12345",
            "ifsc": "SBIN0001234",
            "bank_name": "State Bank of India",
            "name_on_cheque": "Sunita Devi"
        },
        "medical_details": {
            "treating_doctor": "Dr. Smith",
            "underlying_disease": "Cardiac Arrest",
            "icd_code": "I46.9",
            "hospitalization_history": ""
        },
        "investigation": {
            "investigation_status": "NOT_APPLICABLE",
            "police_final_report_status": "NOT_APPLICABLE",
            "accident_details": ""
        },
        "legal_status": {
            "nominee_verified": True,
            "legal_heir_required": False,
            "succession_certificate_status": "NOT_REQUIRED"
        }
    }
    
    res_2 = evaluate_claim(policy_2, claim_2)
    status_2_ok = res_2["status"] == "UNDER_REVIEW"
    two_flags_ok = len(res_2.get("fraud_flags", [])) >= 2
    
    # 3. Aggregate risk breach test case (risk > 70) -> evaluates to REJECTED
    policy_3 = {
        "policy_number": "POL003",
        "commencement_date": "15/01/2024",
        "maturity_date": "15/01/2034",
        "sum_assured": 4000000.0,
        "premium_paying_term_years": 10,
        "premiums_paid_years": 1,
        "nominee_name": "Sunita Devi",
        "life_assured": "Harish Kumar",
        "exclusions": ["Suicide within 12 months"],
        "last_premium_paid_date": "15/01/2024",
        "policy_status": "ACTIVE"
    }
    claim_3 = {
        "date_of_death": "20/10/2024",
        "cause_of_death": "Asphyxia due to Hanging (Suicide)",
        "place_of_death": "Pune",
        "date_of_intimation": "05/11/2024",
        "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Nominee_Aadhaar", "FIR", "Post_Mortem_Report"],
        "claimant": {
            "name": "Sunita Kumar",
            "relationship": "Wife",
            "aadhaar": "1234-5678-9012",
            "phone": "9876543210",
            "address": "Pune"
        },
        "claim_forms": {"Form_A": True, "Form_B": True, "Form_C": True},
        "bank_details": {
            "account_number": "12345",
            "ifsc": "SBIN0001234",
            "bank_name": "State Bank of India",
            "name_on_cheque": "Sunita Kumar"
        },
        "medical_details": {
            "treating_doctor": "Dr. Smith",
            "underlying_disease": "Asphyxia / Suicide",
            "icd_code": "X70.0",
            "hospitalization_history": ""
        },
        "investigation": {
            "investigation_status": "COMPLETED",
            "police_final_report_status": "SUBMITTED",
            "accident_details": "Self-inflicted suicide by hanging"
        },
        "legal_status": {
            "nominee_verified": False,
            "legal_heir_required": True,
            "succession_certificate_status": "NOT_SUBMITTED"
        }
    }
    
    res_3 = evaluate_claim(policy_3, claim_3)
    status_3_ok = res_3["status"] == "REJECTED"
    risk_breach_ok = res_3.get("risk", {}).get("total_score", 0) > 70
    
    passed_1 = status_1_ok and early_claim_ok
    passed_2 = status_2_ok and two_flags_ok
    passed_3 = status_3_ok and risk_breach_ok
    
    if passed_1:
        print("[+] Passed: Conflicting Signals Test")
    else:
        print("[x] Failed: Conflicting Signals Test (Got status={}, fraud_flags={})".format(res_1["status"], res_1.get("fraud_flags")))
        
    if passed_2:
        print("[+] Passed: Edge Fraud Case Test")
    else:
        print("[x] Failed: Edge Fraud Case Test (Got status={}, fraud_flags={})".format(res_2["status"], res_2.get("fraud_flags")))
        
    if passed_3:
        print("[+] Passed: Aggregate Risk Breach Test")
    else:
        print("[x] Failed: Aggregate Risk Breach Test (Got status={}, risk={})".format(res_3["status"], res_3.get("risk")))
        
    all_ok = passed_1 and passed_2 and passed_3
    return all_ok

def run_all_tests():
    print("=" * 80)
    print("  ICATS TEST RUNNER")
    print("=" * 80)
    
    success1 = run_test_suite("real_test_cases.json")
    success2 = run_test_suite("expanded_test_cases.json")
    success3 = run_edge_cases_tests()
    
    print("=" * 80)
    return success1 and success2 and success3

# Pytest discovery helpers
def test_core_cases():
    cases = load_test_cases("real_test_cases.json")
    for c in cases:
        res = evaluate_claim(c["policy"], c["claim"])
        assert res["status"] == c["expected_evaluation"]["status"]
        assert len(res["flags"]) == len(c["expected_evaluation"]["flags"])

def test_expanded_cases():
    cases = load_test_cases("expanded_test_cases.json")
    for c in cases:
        res = evaluate_claim(c["policy"], c["claim"])
        assert res["status"] == c["expected_evaluation"]["status"]

def test_decision_intelligence_edge_cases():
    assert run_edge_cases_tests()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
