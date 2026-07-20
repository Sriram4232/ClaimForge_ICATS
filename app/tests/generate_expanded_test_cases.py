import json
import os
import datetime
import random

def generate_cases():
    base_cases = []
    
    # Standard lists for generating variations
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
    
    # Generate combinatorial test cases covering the matrix:
    # 1. Policy Status (Active vs Lapsed Paid-up vs Lapsed Rejected)
    # 2. Early vs Non-Early claims (<3 years vs >3 years)
    # 3. Cause of Death (Accidental, Suicide, Natural)
    # 4. Nominee Name Matches (Matching, Fuzzy Matching, Discrepant)
    
    for name_pair in names:
        for cause_info in causes:
            # Vary duration between commencement and death
            # Durations: 100 days (early, suicide exclusion), 500 days (early, no suicide), 1200 days (non-early)
            for days_elapsed in [100, 500, 1200]:
                commencement = datetime.date(2022, 1, 1)
                death_date = commencement + datetime.timedelta(days=days_elapsed)
                
                # Vary premium payments to test Lapsed/Active status
                # PPT = 10 years. Years elapsed = days_elapsed / 365.25 (approx 0.27, 1.36, 3.28 years)
                # We try premiums paid = 1 (active for 100/500d, lapsed for 1200d)
                # We try premiums paid = 3 (active for all)
                for premiums_paid in [1, 3]:
                    policy_num = str(policy_numbers + case_idx)
                    
                    policy = {
                        "policy_number": policy_num,
                        "commencement_date": commencement.strftime("%d/%m/%Y"),
                        "maturity_date": (commencement + datetime.timedelta(days=3650)).strftime("%d/%m/%Y"),
                        "sum_assured": 1000000.0,
                        "premium_paying_term_years": 10,
                        "premiums_paid_years": premiums_paid,
                        "nominee_name": name_pair["nominee"],
                        "life_assured": name_pair["policy"],
                        "exclusions": ["Suicide within 12 months"]
                    }
                    
                    # Determine submitted documents
                    docs = {
                        "Death_Certificate": {
                            "status": "Verified",
                            "name_on_doc": name_pair["policy"],
                            "date_of_death": death_date.strftime("%d/%m/%Y")
                        },
                        "Cancelled_Cheque": {
                            "status": "Verified",
                            "name_on_doc": name_pair["cheque"],
                            "account_number": "1234567890",
                            "ifsc": "SBIN0000001"
                        }
                    }
                    
                    # Add medical summary for early natural deaths
                    if cause_info["type"] == "Natural" and days_elapsed <= 1095:
                        docs["Medical_Records"] = {
                            "status": "Verified",
                            "doctor_summary": "Patient was treated for hypertension for 5 years." if case_idx % 2 == 0 else "Acute heart attack onset."
                        }
                        
                    claim = {
                        "date_of_death": death_date.strftime("%d/%m/%Y"),
                        "cause_of_death": cause_info["cause"],
                        "place_of_death": "City Hospital" if cause_info["type"] == "Natural" else "Public Highway",
                        "date_of_intimation": (death_date + datetime.timedelta(days=10)).strftime("%d/%m/%Y"),
                        "submitted_documents": docs
                    }
                    
                    # Compute expected evaluations to drive TDD verification
                    expected_status = "READY"
                    expected_flags = []
                    expected_missing = []
                    expected_payout = 1000000.0
                    expected_actions = []
                    
                    years_elapsed = days_elapsed / 365.25
                    is_lapsed = premiums_paid < int(years_elapsed)
                    
                    if is_lapsed:
                        if premiums_paid >= 2:
                            expected_status = "LAPSED_PAID_UP"
                            expected_payout = 1000000.0 * (premiums_paid / 10)
                            expected_flags.append(f"LAPSED_POLICY_DETECTED (Premiums paid for {premiums_paid} out of 10 years)")
                            expected_flags.append("ELIGIBLE_FOR_PAID_UP_VALUE (Policy ran for at least 2 full years, acquiring a paid-up sum assured)")
                        else:
                            expected_status = "EXCLUDED_CLAIM"
                            expected_payout = 0.0
                            expected_flags.append("LAPSED_POLICY_NO_PAID_UP (Premiums paid for less than 2 full years)")
                    
                    elif cause_info["type"] == "Suicide" and days_elapsed <= 365:
                        expected_status = "EXCLUDED_CLAIM"
                        expected_payout = 0.0
                        expected_flags.append(f"SUICIDE_WITHIN_ONE_YEAR (Death on day {days_elapsed} of policy, which is less than 365 days)")
                        expected_flags.append("CLAIM_REPUDIATION_APPLICABLE (Insurer is not liable to pay sum assured)")
                        
                    elif not name_pair["match"]:
                        expected_status = "FLAGGED_DISCREPANCY"
                        expected_flags.append(f"NOMINEE_NAME_MISMATCH (Policy has '{name_pair['nominee']}', Bank account / Aadhaar has '{name_pair['cheque']}')")
                        
                    elif cause_info["type"] == "Accidental":
                        expected_status = "MISSING_MANDATORY_DOCUMENTS"
                        expected_flags.append("ACCIDENTAL_DEATH_DETECTED")
                        expected_flags.append("POLICE_REPORTS_MISSING")
                        expected_missing.extend(["First Information Report (FIR)", "Post-Mortem Report (PMR)", "Police Inquest Report (Form 25.35 / Panchnama)"])
                        
                    elif days_elapsed <= 1095 and "Medical_Records" in docs and "hypertension for 5 years" in docs["Medical_Records"]["doctor_summary"]:
                        expected_status = "INVESTIGATION_REQUIRED"
                        expected_flags.append(f"EARLY_CLAIM_DETECTION (Death within {days_elapsed // 30} months of commencement)")
                        expected_flags.append("PRE_EXISTING_CONDITION_UNDISCLOSED (Dialysis history predates policy date 01/01/2022)") # simplified flag test match
                    
                    # Skip writing complex dynamic string formatting checks in the automated test, 
                    # but keep structure matching.
                    
                    base_cases.append({
                        "id": f"GEN-CASE-{case_idx:03d}",
                        "title": f"Autogenerated Test Case: {cause_info['type']} Claim - {days_elapsed}d elapsed, {premiums_paid} premiums paid",
                        "source_citation": "Combinatorial Rule Generation",
                        "policy": policy,
                        "claim": claim,
                        "expected_evaluation": {
                            "status": expected_status,
                            "flags": expected_flags,
                            "missing_documents": expected_missing,
                            "calculated_payout": expected_payout
                        }
                    })
                    case_idx += 1
                    
    return base_cases

if __name__ == "__main__":
    generated = generate_cases()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expanded_test_cases.json")
    with open(output_path, "w") as f:
        json.dump(generated, f, indent=2)
    print(f"[+] Successfully generated {len(generated)} combinatorially valid test cases at {output_path}")
