import unittest
import os
import json
import sys
from fastapi.testclient import TestClient

# Mock environment before imports
os.environ["Testing"] = "True"

# Add app parent (workspace root) and app directory to import path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_parent = os.path.dirname(app_dir)
if app_parent not in sys.path:
    sys.path.insert(0, app_parent)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.utils.icats_engine import evaluate_claim, verify_name_match, parse_date
from app.main import app
from app.core.database import MOCK_USERS
from app.repositories.claim_repository import get_all_claims, save_claim
from app.repositories.aadhaar_repository import get_aadhaar_profile

class TestIcatsMvcArchitecture(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
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

    # ================= 1. SECURITY & AUTHENTICATION TESTS =================

    def test_positive_authentication(self):
        # Correct credentials return JWT token
        res = self.client.post("/api/auth/login", json={
            "email": "nominee@icats.in",
            "password": "nominee"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token", data)
        self.assertEqual(data["role"], "claimant")

    def test_negative_authentication(self):
        # Invalid password fails
        res = self.client.post("/api/auth/login", json={
            "email": "nominee@icats.in",
            "password": "wrongpassword"
        })
        self.assertEqual(res.status_code, 401)
        
        # Non-existent user fails
        res = self.client.post("/api/auth/login", json={
            "email": "unknown@domain.com",
            "password": "somepassword"
        })
        self.assertEqual(res.status_code, 401)

    def test_endpoint_security_no_token(self):
        # Requesting claims without token fails
        res = self.client.get("/api/claims")
        self.assertEqual(res.status_code, 401)

    def test_role_based_access_control_restricted(self):
        # Log in as Claimant
        login_res = self.client.post("/api/auth/login", json={
            "email": "nominee@icats.in",
            "password": "nominee"
        })
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to call bank employee endpoint (verify Aadhaar)
        res = self.client.post("/api/claims/verify-aadhaar", json={"case_id": "CASE-001"}, headers=headers)
        self.assertEqual(res.status_code, 403)

        # Attempt to call insurer endpoint (make claim decision)
        res = self.client.post("/api/claims/decision", json={
            "case_id": "CASE-001",
            "status": "APPROVED",
            "comment": "Nice",
            "by": "hacked"
        }, headers=headers)
        self.assertEqual(res.status_code, 403)

    # ================= 2. DATABASE MIGRATION TESTS =================

    def test_mock_aadhaar_db_migration(self):
        # Verify that mock Aadhaar values are stored and queryable in MongoDB
        profile_match = get_aadhaar_profile("1234-5678-9012")
        self.assertIsNotNone(profile_match)
        self.assertEqual(profile_match["name"], "Sunita Devi")
        self.assertEqual(profile_match["status"], "ACTIVE")

        profile_inactive = get_aadhaar_profile("3000-0000-0001")
        self.assertIsNotNone(profile_inactive)
        self.assertEqual(profile_inactive["status"], "INACTIVE")

    # ================= 3. DISBURSAL CLEARANCE 0.00 INR BUG FIX TESTS =================

    def test_approved_claim_payout_correct(self):
        # Set CKD parameters to trigger early-claim non-disclosure zero-out
        self.claim["cause_of_death"] = "Chronic Kidney Disease (CKD) / Renal Failure"
        self.claim["medical_details"]["underlying_disease"] = "Chronic Kidney Disease"
        self.claim["medical_details"]["icd_code"] = "N18.9"
        
        # Under normal rules engine execution, it is rejected and payout is set to 0.00 due to non-disclosure.
        res_normal = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res_normal["payout"]["amount"], 0.0)
        self.assertEqual(res_normal["status"], "REJECTED")

        # However, if the Assessor has bypassed warnings and marked the claim APPROVED,
        # evaluate_claim should preserve the payout instead of zeroing it out.
        res_approved = evaluate_claim(self.policy, self.claim, status="APPROVED")
        self.assertEqual(res_approved["payout"]["amount"], 2500000.0)
        self.assertEqual(res_approved["status"], "APPROVED")

    # ================= 4. BASE RULES ENGINE CONFORMITY TESTS =================

    def test_name_matching_levenshtein(self):
        match, score = verify_name_match("Sunita Devi", "Sunita Devi")
        self.assertTrue(match)
        self.assertEqual(score, 1.0)
        
        match, score = verify_name_match("Sunita Devi", "Suneeta Devi")
        self.assertTrue(match)
        self.assertGreaterEqual(score, 0.80)
        
        match, score = verify_name_match("Ramesh Kumar", "Kumar Ramesh")
        self.assertTrue(match)
        self.assertEqual(score, 1.0)

        match, score = verify_name_match("Sunita Devi", "Sunita Sharma")
        self.assertFalse(match)
        self.assertLess(score, 0.90)

    def test_section_113_paid_up_math(self):
        self.policy["policy_status"] = "ACTIVE"
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["payout"]["amount"], 2500000.0)

        self.policy["policy_status"] = "LAPSED"
        self.policy["premiums_paid_years"] = 3
        self.policy["premium_paying_term_years"] = 15
        res = evaluate_claim(self.policy, self.claim)
        expected_payout = (3 / 15) * 2500000.0
        self.assertEqual(res["payout"]["amount"], expected_payout)

        self.policy["premiums_paid_years"] = 2
        res = evaluate_claim(self.policy, self.claim)
        self.assertEqual(res["payout"]["amount"], 0.0)

    # ================= 5. PASSWORD SECURITY TESTS =================
    def test_password_security_hashing(self):
        from app.utils.security import hash_password, verify_password
        pwd = "securepassword123"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(verify_password(hashed, pwd))
        self.assertFalse(verify_password(hashed, "wrongpwd"))

    # ================= 6. MONGO TEMPLATE TESTS =================
    def test_mongo_template_crud_operations(self):
        from app.core.database import mongo_template
        # Create
        test_doc = {"id": "TEST-099", "status": "DRAFT", "detail": "MongoTemplate test"}
        mongo_template.save("claims", {"id": "TEST-099"}, test_doc)
        
        # Read
        retrieved = mongo_template.find_one("claims", {"id": "TEST-099"})
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["detail"], "MongoTemplate test")
        
        # Count
        count = mongo_template.count("claims", {"id": "TEST-099"})
        self.assertEqual(count, 1)

        # Delete
        mongo_template.delete_many("claims", {"id": "TEST-099"})
        deleted = mongo_template.find_one("claims", {"id": "TEST-099"})
        self.assertIsNone(deleted)

    # ================= 7. NEGATIVE AADHAAR KYC CONDITIONS =================
    def test_aadhaar_kyc_mismatch_negative(self):
        # 1234-5678-0009 is hardcoded as biometric mismatch in our repository mock-to-db logic
        profile = get_aadhaar_profile("1234-5678-0009")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["biometric_status"], "MISMATCH")
        
        # 2000-0000-0009 is seeded directly in the db as biometric mismatch
        profile_seeded = get_aadhaar_profile("2000-0000-0009")
        self.assertIsNotNone(profile_seeded)
        self.assertEqual(profile_seeded["biometric_status"], "MISMATCH")

    def test_aadhaar_kyc_inactive_negative(self):
        profile = get_aadhaar_profile("1234-5678-0001")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["status"], "INACTIVE")

    def test_aadhaar_kyc_name_mismatch_negative(self):
        profile = get_aadhaar_profile("1234-5678-0005")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "John Doe")

    def test_aadhaar_kyc_timeout_negative(self):
        profile = get_aadhaar_profile("1234-5678-0006")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["biometric_status"], "TIMEOUT")

    # ================= 8. NEGATIVE LIFE CYCLE TRANSITIONS =================
    def test_invalid_claim_state_transition_negative(self):
        login_res = self.client.post("/api/auth/login", json={
            "email": "assessor@lic.co.in",
            "password": "assessor"
        })
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Transition from DRAFT directly to APPROVED is forbidden (SUBMITTED -> UNDER_REVIEW -> APPROVED is valid)
        # Attempt to transition CASE-002 from QUERY_RAISED to APPROVED (forbidden, next states are RESUBMITTED)
        res = self.client.post("/api/claims/decision", json={
            "case_id": "CASE-002",
            "status": "APPROVED",
            "comment": "Illegal approval direct bypass",
            "by": "assessor"
        }, headers=headers)
        self.assertEqual(res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
