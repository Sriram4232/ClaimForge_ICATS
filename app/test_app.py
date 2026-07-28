import unittest
import os
import json
import datetime
from fastapi.testclient import TestClient

# Mock environment before imports to prevent file uploads or standard port conflicts
os.environ["Testing"] = "True"

# Add app parent directory to import path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from icats_engine import evaluate_claim, verify_name_match, parse_date
from server import app, MOCK_USERS, get_all_claims, save_claims

class TestIcatsRulesEngine(unittest.TestCase):
    def setUp(self):
        # Base policy template
        self.policy = {
            "policy_number": "502918273",
            "commencement_date": "15/01/2024",
            "maturity_date": "15/01/2039",
            "sum_assured": 2500000.0,
            "premium_paying_term_years": 15,
            "premiums_paid_years": 1,
            "nominee_name": "Sunita Devi",
            "life_assured": "Harish Kumar",
            "exclusions": ["Suicide within 12 months"],
            "last_premium_paid_date": "15/01/2024",
            "policy_status": "ACTIVE"
        }
        
        # Base claim template
        self.claim = {
            "date_of_death": "20/10/2024",
            "cause_of_death": "Cardiac Arrest",
            "place_of_death": "Resident",
            "date_of_intimation": "05/11/2024",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Nominee_Aadhaar"],
            "claimant": {
                "name": "Sunita Devi",
                "relationship": "Wife",
                "aadhaar": "1234-5678-9012",
                "phone": "9876543210",
                "address": "Delhi"
            },
            "claim_forms": {
                "Form_A": True,
                "Form_B": True,
                "Form_C": True
            },
            "bank_details": {
                "account_number": "1029384756",
                "ifsc": "SBIN0001029",
                "bank_name": "State Bank of India",
                "name_on_cheque": "Sunita Devi"
            },
            "medical_details": {
                "treating_doctor": "Dr. Ashok",
                "underlying_disease": "None",
                "icd_code": "N/A",
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

    def test_name_matching_levenshtein(self):
        # 1. Direct match
        match, score = verify_name_match("Sunita Devi", "Sunita Devi")
        self.assertTrue(match)
        self.assertEqual(score, 1.0)
        
        # 2. Spelling variance matching (above 80% threshold)
        match, score = verify_name_match("Sunita Devi", "Suneeta Devi")
        self.assertTrue(match)
        self.assertGreaterEqual(score, 0.80)
        
        # 3. Swap tokens matching (Ramesh Kumar vs Kumar Ramesh)
        match, score = verify_name_match("Ramesh Kumar", "Kumar Ramesh")
        self.assertTrue(match)
        self.assertEqual(score, 1.0)

        # 4. Big spelling discrepancy (below 90% threshold)
        match, score = verify_name_match("Sunita Devi", "Sunita Sharma")
        self.assertFalse(match)
        self.assertLess(score, 0.90)

    def test_section_113_paid_up_math(self):
        # Case A: Active policy -> full payout
        self.policy["policy_status"] = "ACTIVE"
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["payout"]["amount"], 2500000.0)
        self.assertEqual(res["payout"]["type"], "FULL_CLAIM")
        
        # Case B: Lapsed policy with premiums paid >= 3 years -> Reduced Paid-Up
        self.policy["policy_status"] = "LAPSED"
        self.policy["premiums_paid_years"] = 3
        self.policy["premium_paying_term_years"] = 15
        self.policy["last_premium_paid_date"] = "15/01/2021" # outside grace period
        res = evaluate_claim(self.policy, self.claim)
        expected_payout = (3 / 15) * 2500000.0
        self.assertEqual(res["payout"]["amount"], expected_payout)
        self.assertEqual(res["payout"]["type"], "REDUCED_PAID_UP")
        
        # Case C: Lapsed policy with premiums paid < 3 years -> Forfeited (0 payout)
        self.policy["policy_status"] = "LAPSED"
        self.policy["premiums_paid_years"] = 2
        self.policy["premium_paying_term_years"] = 15
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["payout"]["amount"], 0.0)
        self.assertEqual(res["payout"]["type"], "NO_PAYOUT")

    def test_section_45_early_claim_disclosure(self):
        # Commencement date: 15/01/2024. Death date: 20/10/2024. Days elapsed: ~279 (Early Claim)
        # Undisclosed Chronic Kidney Disease flagged
        self.claim["medical_details"]["underlying_disease"] = "Chronic Kidney Disease"
        self.claim["medical_details"]["icd_code"] = "N18.9"
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["payout"]["amount"], 0.0)
        self.assertEqual(res["status"], "REJECTED")
        self.assertTrue(any("Section 45 material non-disclosure" in line for line in res["explainability"]["decision_path"]))

    def test_accidental_death_checklist(self):
        # Accidental death cause
        self.claim["cause_of_death"] = "Polytrauma from Vehicular crash"
        # Missing FIR / PMR reports
        self.claim["submitted_documents"] = ["Death_Certificate", "Cancelled_Cheque"]
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["status"], "QUERY_RAISED")
        self.assertTrue(any("Accidental death missing mandatory reports" in r["message"] for r in res["rules"]))


class TestIcatsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_login_routes(self):
        # 1. Test valid credentials
        payload = {"email": "nominee@icats.in", "password": "nominee"}
        res = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        user_info = res.json()
        self.assertEqual(user_info["role"], "claimant")
        self.assertEqual(user_info["name"], "Sunita Devi")

        # 2. Test invalid credentials
        payload = {"email": "nominee@icats.in", "password": "wrongpassword"}
        res = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)

    def test_claims_decision_and_state_history(self):
        # Query list to get an active case ID
        res = self.client.get("/api/claims?role=insurer")
        self.assertEqual(res.status_code, 200)
        claims = res.json()
        self.assertGreater(len(claims), 0)
        
        target_case = claims[0]
        case_id = target_case["id"]
        
        # Test transition of status (SUBMITTED -> UNDER_REVIEW)
        # Note: If it's already in UNDER_REVIEW, the transition might be allowed.
        # Let's reset the status of this case to SUBMITTED to guarantee allowed transitions.
        # We can update the status directly in our server's internal collection.
        raw_claims = get_all_claims()
        srv_claim = next((c for c in raw_claims if c["id"] == case_id), None)
        srv_claim["status"] = "SUBMITTED"
        srv_claim["state_history"] = []
        save_claims(raw_claims)
        
        decision_payload = {
            "case_id": case_id,
            "status": "UNDER_REVIEW",
            "comment": "Audit review started.",
            "by": "assessor"
        }
        res = self.client.post("/api/claims/decision", json=decision_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "UNDER_REVIEW")
        
        # Check that state history is updated
        res = self.client.get("/api/claims?role=insurer")
        updated_claim = next((c for c in res.json() if c["id"] == case_id), None)
        self.assertEqual(updated_claim["status"], "UNDER_REVIEW")
        self.assertGreater(len(updated_claim["state_history"]), 0)
        self.assertEqual(updated_claim["state_history"][-1]["to"], "UNDER_REVIEW")

    def test_autopilot_simulation(self):
        res = self.client.post("/api/agents/simulate?case_id=CASE-002")
        self.assertEqual(res.status_code, 200)
        logs = res.json()["logs"]
        self.assertGreater(len(logs), 0)
        self.assertTrue(any("Autopilot resolved" in log or "Claim APPROVED" in log for log in logs))

    def test_aadhaar_api_scenarios(self):
        # Save original claims db to restore later
        original_claims = get_all_claims()
        try:
            # We will use CASE-001 for these tests
            case_id = "CASE-001"
            
            # Helper to set claimant Aadhaar number
            def set_aadhaar(aadhaar_val, nominee_verified=False, claimant_name="Sunita Devi"):
                claims = get_all_claims()
                c = next((item for item in claims if item["id"] == case_id), None)
                c["claim"]["claimant"]["aadhaar"] = aadhaar_val
                c["claim"]["claimant"]["name"] = claimant_name
                c["claim"]["legal_status"]["nominee_verified"] = nominee_verified
                save_claims(claims)

            # 1. Success whitelisted
            set_aadhaar("1234-5678-9012")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json()["success"])
            self.assertIn("Biometric verify successful", res.json()["message"])

            # 2. Invalid format (too short)
            set_aadhaar("123-456-789")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "INVALID_CHECKSUM")

            # 3. Invalid checksum (Verhoeff fail)
            set_aadhaar("9876-5432-1098")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "INVALID_CHECKSUM")

            # 4. Not registered Aadhaar
            set_aadhaar("9876-5432-1096")  # 9876-5432-1096 has a valid Verhoeff checksum but isn't in DB
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "NOT_FOUND")

            # 5. Biometric fingerprint mismatch
            set_aadhaar("2000-0000-0009")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "BIOMETRIC_MISMATCH")

            # 6. Inactive Aadhaar card
            set_aadhaar("3000-0000-0001")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "INACTIVE_STATUS")

            # 7. Aadhaar name mismatch (Registered name 'John Doe' vs Sunita Devi)
            set_aadhaar("4000-0000-0005")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "NAME_MISMATCH")

            # 8. Device communication timeout
            set_aadhaar("5000-0000-0006")
            res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": case_id})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertEqual(res.json()["error_code"], "DEVICE_TIMEOUT")

        finally:
            save_claims(original_claims)

    def test_aadhaar_combinatorial_scenarios(self):
        # We will dynamically run 108 combinatorial test cases covering:
        # 4 claimant names, 3 Aadhaar numbers, 3 policy statuses, 3 causes of death
        names = [
            {"claimant": "Sunita Devi", "match": "exact"},
            {"claimant": "Suneeta Devi", "match": "fuzzy"},
            {"claimant": "Preeti Kumari", "match": "mismatch"},
            {"claimant": "Unknown Name", "match": "mismatch"}
        ]
        
        aadhaars = [
            {"val": "1234-5678-9012", "type": "valid"},
            {"val": "2000-0000-0009", "type": "biometric_mismatch"},
            {"val": "9876-5432-1098", "type": "invalid_checksum"}
        ]
        
        statuses = [
            {"status": "ACTIVE", "premiums_paid": 3, "expected_payout": 2500000.0},
            {"status": "LAPSED", "premiums_paid": 3, "expected_payout": 500000.0}, # (3/15) * 2500000
            {"status": "LAPSED", "premiums_paid": 1, "expected_payout": 0.0} # forfeited
        ]
        
        causes = [
            {"cause": "Cardiac Arrest", "type": "natural_natural"},
            {"cause": "Polytrauma due to Highway Accident", "type": "accidental"},
            {"cause": "Chronic Kidney Disease (CKD) / Renal Failure", "type": "chronic_early"}
        ]
        
        original_claims = get_all_claims()
        try:
            scenario_count = 0
            for name_cfg in names:
                for aadhaar_cfg in aadhaars:
                    for status_cfg in statuses:
                        for cause_cfg in causes:
                            scenario_count += 1
                            
                            # Construct dynamic policy and claim matching templates
                            policy = {
                                "policy_number": "502918273",
                                "commencement_date": "15/01/2024",
                                "maturity_date": "15/01/2039",
                                "sum_assured": 2500000.0,
                                "premium_paying_term_years": 15,
                                "premiums_paid_years": status_cfg["premiums_paid"],
                                "nominee_name": "Sunita Devi",
                                "life_assured": "Harish Kumar",
                                "exclusions": ["Suicide within 12 months"],
                                "last_premium_paid_date": "15/01/2024",
                                "policy_status": status_cfg["status"]
                            }
                            
                            claim = {
                                "date_of_death": "20/10/2024",
                                "cause_of_death": cause_cfg["cause"],
                                "place_of_death": "Hospital",
                                "date_of_intimation": "05/11/2024",
                                "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Nominee_Aadhaar"],
                                "claimant": {
                                    "name": name_cfg["claimant"],
                                    "relationship": "Wife",
                                    "aadhaar": aadhaar_cfg["val"],
                                    "phone": "9876543210",
                                    "address": "Delhi"
                                },
                                "claim_forms": {
                                    "Form_A": True,
                                    "Form_B": True,
                                    "Form_C": True
                                },
                                "bank_details": {
                                    "account_number": "1029384756",
                                    "ifsc": "SBIN0001029",
                                    "bank_name": "State Bank of India",
                                    "name_on_cheque": name_cfg["claimant"]
                                },
                                "medical_details": {
                                    "treating_doctor": "Dr. Ashok",
                                    "underlying_disease": "None",
                                    "icd_code": "N18.9" if "Chronic Kidney Disease" in cause_cfg["cause"] else "N/A",
                                    "hospitalization_history": "Dialysis" if "Chronic Kidney Disease" in cause_cfg["cause"] else ""
                                },
                                "investigation": {
                                    "investigation_status": "PENDING" if "Accident" in cause_cfg["cause"] else "NOT_APPLICABLE",
                                    "police_final_report_status": "NOT_SUBMITTED" if "Accident" in cause_cfg["cause"] else "NOT_APPLICABLE",
                                    "accident_details": "Road accident" if "Accident" in cause_cfg["cause"] else ""
                                },
                                "legal_status": {
                                    "nominee_verified": False,
                                    "legal_heir_required": name_cfg["match"] == "mismatch",
                                    "succession_certificate_status": "NOT_REQUIRED"
                                }
                            }
                            
                            # Run rules engine check
                            result = evaluate_claim(policy, claim)
                            
                            # Assertions based on combinatorial states:
                            # 1. Payout checks
                            expected_payout = status_cfg["expected_payout"]
                            if "Chronic Kidney Disease" in cause_cfg["cause"]:
                                expected_payout = 0.0
                            self.assertEqual(result["payout"]["amount"], expected_payout)
                            
                            # 2. Aadhaar rule verification behavior
                            rule10 = next((r for r in result["rules"] if r["rule_id"] == "RULE_10"), None)
                            self.assertIsNotNone(rule10)
                            
                            if aadhaar_cfg["type"] == "invalid_checksum":
                                self.assertEqual(rule10["result"], "FAILED")
                                self.assertEqual(rule10["impact"], "BLOCKER")
                            elif name_cfg["match"] == "mismatch" and aadhaar_cfg["type"] == "valid":
                                # Name mismatch prevents automatic rule pass if biometric verified is False
                                self.assertEqual(rule10["result"], "FAILED")
                                self.assertEqual(rule10["impact"], "BLOCKER")
                                
            self.assertEqual(scenario_count, 108)
            print(f"[+] Successfully ran {scenario_count} combinatorial scenario test cases.")
            
        finally:
            save_claims(original_claims)

if __name__ == "__main__":
    unittest.main()
