import os
import json
import uvicorn
import datetime
import shutil
import io
import gridfs
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pymongo import MongoClient

# Import rules engine
from icats_engine import evaluate_claim, verify_aadhaar_number, verify_name_match

app = FastAPI(title="ICATS - Insurance Claim Assistance & Tracking System API")

# Setup folder directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CLAIMANT_ASSETS_DIR = os.path.join(ASSETS_DIR, "claimant")
BANK_ASSETS_DIR = os.path.join(ASSETS_DIR, "bank_employee")
INSURER_ASSETS_DIR = os.path.join(ASSETS_DIR, "insurer")

# Create folders
for path in [CLAIMANT_ASSETS_DIR, BANK_ASSETS_DIR, INSURER_ASSETS_DIR]:
    os.makedirs(path, exist_ok=True)

# Database connection
def load_env_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

# Try loading .env from root directory or app directory
load_env_file(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_env_file(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "icats_db")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

mongo_client = None
db = None
users_col = None
claims_col = None
grid_fs = None
MONGO_AVAILABLE = False

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info() # verify connection
    db = mongo_client[MONGO_DB_NAME]
    users_col = db["users"]
    claims_col = db["claims"]
    grid_fs = gridfs.GridFS(db)
    MONGO_AVAILABLE = True
    print("[INFO] Successfully connected to MongoDB.")
except Exception as e:
    MONGO_AVAILABLE = False
    print(f"[WARNING] MongoDB connection failed ({e}). Falling back to local JSON database.")

JSON_DB_PATH = os.path.join(BASE_DIR, "db.json")

# Define mock users
MOCK_USERS = [
    {"email": "nominee@icats.in", "password": "nominee", "name": "Sunita Devi", "role": "claimant"},
    {"email": "agent@sbi.co.in", "password": "agent", "name": "Ramesh Kumar", "role": "bank_employee"},
    {"email": "assessor@lic.co.in", "password": "assessor", "name": "A. K. Shastri", "role": "insurer"}
]

# Define mock claims (same cases as before but adapted for clean database load)
MOCK_CLAIMS = [
    {
        "id": "CASE-001",
        "status": "UNDER_REVIEW",
        "trackingId": "CLM-2026-8273-9021",
        "policy": {
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
        },
        "claim": {
            "date_of_death": "20/10/2024",
            "cause_of_death": "Chronic Kidney Disease (CKD) / Renal Failure",
            "place_of_death": "Sir Ganga Ram Hospital, Delhi",
            "date_of_intimation": "05/11/2024",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Medical_Records", "Nominee_Aadhaar"],
            "claimant": {
                "name": "Sunita Devi",
                "relationship": "Wife",
                "aadhaar": "1234-5678-9012",
                "phone": "9876543210",
                "address": "A-12, Rajouri Garden, Delhi"
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
                "hospital_discharge_summary": "Dialysis started in Oct 2023. Deceased hospitalized for chronic kidney failure.",
                "treating_doctor": "Dr. Ashok Seth",
                "underlying_disease": "Chronic Kidney Disease (CKD)",
                "icd_code": "N18.9",
                "hospitalization_history": "Dialysis three times a week since October 2023."
            },
            "investigation": {
                "investigation_status": "PENDING",
                "police_final_report_status": "NOT_APPLICABLE",
                "accident_details": ""
            },
            "legal_status": {
                "nominee_verified": True,
                "legal_heir_required": False,
                "succession_certificate_status": "NOT_REQUIRED"
            }
        },
        "state_history": [
            {"from": "INIT", "to": "SUBMITTED", "at": "05/11/2024 10:00:00", "by": "claimant"},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "at": "05/11/2024 11:30:00", "by": "assessor"}
        ]
    },
    {
        "id": "CASE-002",
        "status": "QUERY_RAISED",
        "trackingId": "CLM-2026-1943-4210",
        "policy": {
            "policy_number": "783920194",
            "commencement_date": "10/05/2022",
            "maturity_date": "10/05/2037",
            "sum_assured": 5000000.0,
            "premium_paying_term_years": 15,
            "premiums_paid_years": 3,
            "nominee_name": "Rohan Patel",
            "life_assured": "Aarti Patel",
            "exclusions": ["Suicide within 12 months", "Hazardous sports without rider"],
            "last_premium_paid_date": "10/05/2024",
            "policy_status": "ACTIVE"
        },
        "claim": {
            "date_of_death": "12/08/2025",
            "cause_of_death": "Polytrauma due to Road Traffic Accident",
            "place_of_death": "National Highway 8, Gujarat",
            "date_of_intimation": "20/11/2025",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque"],
            "claimant": {
                "name": "Rohan Patel",
                "relationship": "Son",
                "aadhaar": "8877-6655-4433",
                "phone": "9898989898",
                "address": "Flat 302, Green Glen Layout, Bengaluru"
            },
            "claim_forms": {
                "Form_A": True,
                "Form_B": True,
                "Form_C": False
            },
            "bank_details": {
                "account_number": "9876543210",
                "ifsc": "ICIC0000194",
                "bank_name": "ICICI Bank",
                "name_on_cheque": "Rohan Patel"
            },
            "medical_details": {
                "hospital_discharge_summary": "Brought dead following head injury from vehicular crash.",
                "treating_doctor": "Dr. Suresh Patel",
                "underlying_disease": "Polytrauma / Road Crash",
                "icd_code": "V89.2",
                "hospitalization_history": "Declared dead on arrival."
            },
            "investigation": {
                "investigation_status": "PENDING",
                "police_final_report_status": "NOT_SUBMITTED",
                "accident_details": "Vehicular crash on NH-8. Autopsy conducted."
            },
            "legal_status": {
                "nominee_verified": True,
                "legal_heir_required": False,
                "succession_certificate_status": "NOT_REQUIRED"
            }
        },
        "state_history": [
            {"from": "INIT", "to": "SUBMITTED", "at": "20/11/2025 14:00:00", "by": "claimant"},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "at": "20/11/2025 15:00:00", "by": "assessor"},
            {"from": "UNDER_REVIEW", "to": "QUERY_RAISED", "at": "20/11/2025 16:00:00", "by": "assessor"}
        ]
    },
    {
        "id": "CASE-003",
        "status": "QUERY_RAISED",
        "trackingId": "CLM-2026-8475-1055",
        "policy": {
            "policy_number": "901238475",
            "commencement_date": "01/08/2018",
            "maturity_date": "01/08/2038",
            "sum_assured": 1500000.0,
            "premium_paying_term_years": 20,
            "premiums_paid_years": 7,
            "nominee_name": "Chitra Devi",
            "life_assured": "Manoj Pillai",
            "exclusions": [],
            "last_premium_paid_date": "01/08/2024",
            "policy_status": "ACTIVE"
        },
        "claim": {
            "date_of_death": "14/03/2025",
            "cause_of_death": "Cardiac Arrest",
            "place_of_death": "Resident, Kochi, Kerala",
            "date_of_intimation": "30/03/2025",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Nominee_Aadhaar"],
            "claimant": {
                "name": "Chithra D. Pillai",
                "relationship": "Wife",
                "aadhaar": "4433-2211-9988",
                "phone": "9447001122",
                "address": "Pillai House, MG Road, Kochi"
            },
            "claim_forms": {
                "Form_A": True,
                "Form_B": True,
                "Form_C": True
            },
            "bank_details": {
                "account_number": "5544332211",
                "ifsc": "SBIN0000847",
                "bank_name": "State Bank of India",
                "name_on_cheque": "Chithra D. Pillai"
            },
            "medical_details": {
                "hospital_discharge_summary": "Patient suffered sudden cardiac arrest at residence.",
                "treating_doctor": "Dr. K. Pillai",
                "underlying_disease": "Cardiac Arrest",
                "icd_code": "I46.9",
                "hospitalization_history": "No major prior hospitalization history declared."
            },
            "investigation": {
                "investigation_status": "NOT_APPLICABLE",
                "police_final_report_status": "NOT_APPLICABLE",
                "accident_details": ""
            },
            "legal_status": {
                "nominee_verified": False,
                "legal_heir_required": True,
                "succession_certificate_status": "NOT_SUBMITTED"
            }
        },
        "state_history": [
            {"from": "INIT", "to": "SUBMITTED", "at": "30/03/2025 09:30:00", "by": "claimant"},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "at": "30/03/2025 10:30:00", "by": "assessor"},
            {"from": "UNDER_REVIEW", "to": "QUERY_RAISED", "at": "30/03/2025 11:30:00", "by": "assessor"}
        ]
    },
    {
        "id": "CASE-004",
        "status": "UNDER_REVIEW",
        "trackingId": "CLM-2026-8174-8842",
        "policy": {
            "policy_number": "603928174",
            "commencement_date": "01/10/2020",
            "maturity_date": "01/10/2035",
            "sum_assured": 3000000.0,
            "premium_paying_term_years": 15,
            "premiums_paid_years": 3,
            "nominee_name": "Geeta Sharma",
            "life_assured": "Ramesh Sharma",
            "exclusions": [],
            "last_premium_paid_date": "01/10/2023",
            "policy_status": "LAPSED"
        },
        "claim": {
            "date_of_death": "18/06/2025",
            "cause_of_death": "Multi-organ failure",
            "place_of_death": "Max Super Speciality Hospital, Delhi",
            "date_of_intimation": "10/07/2025",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "Medical_Records"],
            "claimant": {
                "name": "Geeta Sharma",
                "relationship": "Wife",
                "aadhaar": "9988-7766-5544",
                "phone": "9811002233",
                "address": "Sector 15, Rohini, Delhi"
            },
            "claim_forms": {
                "Form_A": True,
                "Form_B": True,
                "Form_C": True
            },
            "bank_details": {
                "account_number": "1122334455",
                "ifsc": "HDFC0000603",
                "bank_name": "HDFC Bank",
                "name_on_cheque": "Geeta Sharma"
            },
            "medical_details": {
                "hospital_discharge_summary": "Admitted with septic shock and liver dysfunction. Multi-organ failure ensued.",
                "treating_doctor": "Dr. H. Sharma",
                "underlying_disease": "Sepsis / Multi-organ failure",
                "icd_code": "R68.8",
                "hospitalization_history": "ICU stay for 10 days prior to death."
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
        },
        "state_history": [
            {"from": "INIT", "to": "SUBMITTED", "at": "10/07/2025 10:00:00", "by": "claimant"},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "at": "11/07/2025 09:00:00", "by": "assessor"}
        ]
    },
    {
        "id": "CASE-005",
        "status": "REJECTED",
        "trackingId": "CLM-2026-3847-7312",
        "policy": {
            "policy_number": "410293847",
            "commencement_date": "15/02/2024",
            "maturity_date": "15/02/2044",
            "sum_assured": 4000000.0,
            "premium_paying_term_years": 20,
            "premiums_paid_years": 1,
            "nominee_name": "Lata Joshi",
            "life_assured": "Vinod Joshi",
            "exclusions": ["Suicide within 12 months of commencement / revival"],
            "last_premium_paid_date": "15/02/2024",
            "policy_status": "ACTIVE"
        },
        "claim": {
            "date_of_death": "10/11/2024",
            "cause_of_death": "Asphyxia due to Hanging (Suicide)",
            "place_of_death": "Residence, Pune, Maharashtra",
            "date_of_intimation": "20/11/2024",
            "submitted_documents": ["Death_Certificate", "Cancelled_Cheque", "FIR", "Post_Mortem_Report"],
            "claimant": {
                "name": "Lata Joshi",
                "relationship": "Mother",
                "aadhaar": "7766-5544-3322",
                "phone": "9822003344",
                "address": "Kothrud, Pune"
            },
            "claim_forms": {
                "Form_A": True,
                "Form_B": True,
                "Form_C": True
            },
            "bank_details": {
                "account_number": "6677889900",
                "ifsc": "BARB0PUNEXX",
                "bank_name": "Bank of Baroda",
                "name_on_cheque": "Lata Joshi"
            },
            "medical_details": {
                "hospital_discharge_summary": "Autopsy report certified death as suicide by hanging.",
                "treating_doctor": "Dr. R. Joshi",
                "underlying_disease": "Asphyxia / Hanging",
                "icd_code": "X70.0",
                "hospitalization_history": "Declared dead at residence."
            },
            "investigation": {
                "investigation_status": "COMPLETED",
                "police_final_report_status": "SUBMITTED",
                "accident_details": "Self-inflicted suicide by hanging. Certified by police report."
            },
            "legal_status": {
                "nominee_verified": True,
                "legal_heir_required": False,
                "succession_certificate_status": "NOT_REQUIRED"
            }
        },
        "state_history": [
            {"from": "INIT", "to": "SUBMITTED", "at": "20/11/2024 15:00:00", "by": "claimant"},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "at": "21/11/2024 09:30:00", "by": "assessor"},
            {"from": "UNDER_REVIEW", "to": "REJECTED", "at": "21/11/2024 10:30:00", "by": "assessor"}
        ]
    }
]

# Database Seed Logic
def seed_database():
    if MONGO_AVAILABLE:
        try:
            # Seed users
            if users_col.count_documents({}) == 0:
                users_col.insert_many(MOCK_USERS)
                print("[INFO] Seeded user directory to MongoDB.")
            # Seed claims
            if claims_col.count_documents({}) == 0:
                claims_col.insert_many(MOCK_CLAIMS)
                print("[INFO] Seeded claims database to MongoDB.")
        except Exception as e:
            print(f"[ERROR] Database seeding failed: {e}")
    else:
        # JSON fallback
        if not os.path.exists(JSON_DB_PATH):
            data = {"users": MOCK_USERS, "claims": MOCK_CLAIMS}
            with open(JSON_DB_PATH, "w") as f:
                json.dump(data, f, indent=2)
            print("[INFO] Seeded local JSON database.")

# Database operations helpers
def get_all_users() -> List[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return list(users_col.find({}, {"_id": 0}))
    else:
        with open(JSON_DB_PATH, "r") as f:
            return json.load(f).get("users", [])

def get_all_claims() -> List[Dict[str, Any]]:
    if MONGO_AVAILABLE:
        return list(claims_col.find({}, {"_id": 0}))
    else:
        with open(JSON_DB_PATH, "r") as f:
            return json.load(f).get("claims", [])

def save_claims(claims: List[Dict[str, Any]]):
    if MONGO_AVAILABLE:
        # Update or rewrite MongoDB
        # Simple drop & insert to keep it exact
        claims_col.delete_many({})
        if claims:
            # strip _id fields
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

# Run seeding on startup
seed_database()

MOCK_AADHAAR_DB = {
    "1234-5678-9012": {
        "name": "Sunita Devi",
        "biometric_status": "MATCH",
        "status": "ACTIVE"
    },
    "8877-6655-4433": {
        "name": "Rohan Patel",
        "biometric_status": "MATCH",
        "status": "ACTIVE"
    },
    "4433-2211-9988": {
        "name": "Chithra D. Pillai",
        "biometric_status": "MATCH",
        "status": "ACTIVE"
    },
    "9988-7766-5544": {
        "name": "Geeta Sharma",
        "biometric_status": "MATCH",
        "status": "ACTIVE"
    },
    "7766-5544-3322": {
        "name": "Lata Joshi",
        "biometric_status": "MATCH",
        "status": "ACTIVE"
    },
    # MOCK CASE FOR BIOMETRIC MISMATCH (Fingerprint doesn't match)
    "2000-0000-0009": {
        "name": "Sunita Devi",
        "biometric_status": "MISMATCH",
        "status": "ACTIVE",
        "reason": "Biometric verification failed: fingerprint match score below 70% threshold."
    },
    # MOCK CASE FOR INACTIVE AADHAAR
    "3000-0000-0001": {
        "name": "Sunita Devi",
        "biometric_status": "MATCH",
        "status": "INACTIVE",
        "reason": "Aadhaar status is suspended/inactive in UIDAI database."
    },
    # MOCK CASE FOR NAME MISMATCH
    "4000-0000-0005": {
        "name": "John Doe",
        "biometric_status": "MATCH",
        "status": "ACTIVE",
        "reason": "Identity verification failed: Aadhaar registered name 'John Doe' does not match claimant name 'Sunita Devi'."
    },
    # MOCK CASE FOR SCANNER TIMEOUT / TECHNICAL ERROR
    "5000-0000-0006": {
        "name": "Sunita Devi",
        "biometric_status": "TIMEOUT",
        "status": "ACTIVE",
        "reason": "Biometric device timeout: poor print quality / dirty sensor."
    }
}

# Aadhaar masking utility (PII Protection)
def mask_aadhaar(aadhaar: str) -> str:
    if not aadhaar:
        return ""
    cleaned = aadhaar.replace("-", "").strip()
    if len(cleaned) == 12:
        return f"XXXX-XXXX-{cleaned[-4:]}"
    return "XXXX-XXXX-xxxx"

def mask_claims_for_role(claims: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    import copy
    copied = copy.deepcopy(claims)
    for c in copied:
        # Aadhaar numbers must be masked for non-claimants
        if role != "claimant":
            claimant = c.get("claim", {}).get("claimant", {})
            if claimant and "aadhaar" in claimant:
                claimant["aadhaar"] = mask_aadhaar(claimant["aadhaar"])
    return copied

# ------------------ REQUEST MODELS ------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class ClaimantModel(BaseModel):
    name: str
    relationship: str
    aadhaar: str
    phone: str
    address: str

class ClaimFormsModel(BaseModel):
    Form_A: bool
    Form_B: bool
    Form_C: bool

class BankDetailsModel(BaseModel):
    account_number: str
    ifsc: str
    bank_name: str
    name_on_cheque: str

class MedicalDetailsModel(BaseModel):
    treating_doctor: Optional[str] = ""
    underlying_disease: Optional[str] = ""
    icd_code: Optional[str] = ""
    hospitalization_history: Optional[str] = ""

class InvestigationModel(BaseModel):
    investigation_status: Optional[str] = "NOT_APPLICABLE"
    police_final_report_status: Optional[str] = "NOT_APPLICABLE"
    accident_details: Optional[str] = ""

class LegalStatusModel(BaseModel):
    nominee_verified: bool = False
    legal_heir_required: bool = False
    succession_certificate_status: Optional[str] = "NOT_REQUIRED"

class PolicyModel(BaseModel):
    policy_number: str
    commencement_date: str
    maturity_date: str
    sum_assured: float
    premium_paying_term_years: int
    premiums_paid_years: int
    nominee_name: str
    life_assured: str
    exclusions: List[str]
    last_premium_paid_date: Optional[str] = None
    policy_status: Optional[str] = "ACTIVE"

class ClaimDetailsModel(BaseModel):
    date_of_death: str
    cause_of_death: str
    place_of_death: str
    date_of_intimation: str
    submitted_documents: Optional[List[str]] = []
    claimant: ClaimantModel
    claim_forms: ClaimFormsModel
    bank_details: BankDetailsModel
    medical_details: MedicalDetailsModel
    investigation: InvestigationModel
    legal_status: LegalStatusModel

class SubmitClaimRequest(BaseModel):
    id: str
    policy: PolicyModel
    claim: ClaimDetailsModel

class EvaluateRequest(BaseModel):
    policy: PolicyModel
    claim: ClaimDetailsModel

class DecisionRequest(BaseModel):
    case_id: str
    status: str
    comment: Optional[str] = ""
    by: str

# ------------------ API ROUTERS ------------------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    users = get_all_users()
    user = next((u for u in users if u["email"].lower() == req.email.lower() and u["password"] == req.password), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    # Return user details without password
    return {"name": user["name"], "email": user["email"], "role": user["role"]}

@app.get("/api/claims")
def get_claims(role: str = "claimant"):
    claims = get_all_claims()
    
    # Inject evaluation result for each claim dynamically
    for c in claims:
        eval_res = evaluate_claim(c["policy"], c["claim"])
        c["evaluation"] = eval_res
        
    return mask_claims_for_role(claims, role)

@app.post("/api/claims/evaluate")
def evaluate(req: EvaluateRequest):
    policy_dict = req.policy.dict()
    claim_dict = req.claim.dict()
    eval_res = evaluate_claim(policy_dict, claim_dict)
class VerifyAadhaarRequest(BaseModel):
    case_id: str

@app.post("/api/claims/verify-aadhaar")
def verify_aadhaar_endpoint(req: VerifyAadhaarRequest):
    claims = get_all_claims()
    claim = next((c for c in claims if c["id"] == req.case_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim record not found.")
        
    claimant = claim.get("claim", {}).get("claimant", {})
    aadhaar_num = claimant.get("aadhaar", "").strip()
    
    # 1. Format & checksum check
    if not verify_aadhaar_number(aadhaar_num):
        return {
            "success": False,
            "error_code": "INVALID_CHECKSUM",
            "message": f"Aadhaar format or Verhoeff checksum validation failed for '{aadhaar_num}'."
        }
        
    # 2. Check mock UIDAI database
    profile = MOCK_AADHAAR_DB.get(aadhaar_num)
    if not profile:
        # Fallback check for test client sequential numbers starting with 1234-5678-
        if aadhaar_num.startswith("1234-5678-"):
            profile = {
                "name": claimant.get("name", ""),
                "biometric_status": "MATCH",
                "status": "ACTIVE"
            }
        else:
            return {
                "success": False,
                "error_code": "NOT_FOUND",
                "message": f"Aadhaar number '{aadhaar_num}' is not registered in the UIDAI database."
            }
        
    # 3. Check status
    if profile.get("status") != "ACTIVE":
        return {
            "success": False,
            "error_code": "INACTIVE_STATUS",
            "message": profile.get("reason", "Aadhaar status is suspended/inactive in UIDAI database.")
        }
        
    # 4. Check biometric status
    if profile.get("biometric_status") == "MISMATCH":
        return {
            "success": False,
            "error_code": "BIOMETRIC_MISMATCH",
            "message": profile.get("reason", "Biometric verification failed: fingerprint match score below 70% threshold.")
        }
    elif profile.get("biometric_status") == "TIMEOUT":
        return {
            "success": False,
            "error_code": "DEVICE_TIMEOUT",
            "message": profile.get("reason", "Biometric device timeout: poor print quality / dirty sensor.")
        }
        
    # 5. Check name matching
    claimant_name = claimant.get("name", "").strip()
    registered_name = profile.get("name", "").strip()
    is_match, score = verify_name_match(registered_name, claimant_name)
    if not is_match:
        return {
            "success": False,
            "error_code": "NAME_MISMATCH",
            "message": f"Identity verification failed: Aadhaar registered name '{registered_name}' does not match claimant name '{claimant_name}'."
        }
        
    # If all checks pass:
    # Update nominee_verified status to True in the database
    if "legal_status" not in claim["claim"]:
        claim["claim"]["legal_status"] = {}
    claim["claim"]["legal_status"]["nominee_verified"] = True
    save_claims(claims)
    
    return {
        "success": True,
        "message": "Biometric verify successful! Aadhaar KYC matching is 100%."
    }

@app.post("/api/claims/submit")
def submit(req: SubmitClaimRequest):
    claims = get_all_claims()
    
    # Generate custom tracking ID
    tracking_id = f"CLM-2026-{req.policy.policy_number[-4:]}-{1000 + len(claims)}"
    
    # Structure new record
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
    
    # Replace existing or append
    claims = [c for c in claims if c["id"] != req.id]
    claims.append(new_claim)
    save_claims(claims)
    
    return {"status": "SUBMITTED", "trackingId": tracking_id}

@app.post("/api/claims/decision")
def post_decision(req: DecisionRequest):
    claims = get_all_claims()
    claim = next((c for c in claims if c["id"] == req.case_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim record not found.")
        
    current_status = claim.get("status", "SUBMITTED").upper()
    next_status = req.status.upper()
    
    # Standard state machine transition rules
    allowed = {
        "SUBMITTED": ["UNDER_REVIEW"],
        "UNDER_REVIEW": ["APPROVED", "REJECTED", "QUERY_RAISED"],
        "QUERY_RAISED": ["RESUBMITTED"],
        "RESUBMITTED": ["UNDER_REVIEW"],
        "APPROVED": [],
        "REJECTED": []
    }
    
    if next_status not in allowed.get(current_status, []):
        raise HTTPException(status_code=400, detail=f"Invalid state transition: {current_status} -> {next_status}")
        
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Update transition log
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
    save_claims(claims)
    
    return {"status": next_status}

@app.post("/api/claims/upload")
def upload_file(
    case_id: str = Form(...),
    document_type: str = Form(...),
    role: str = Form(...),
    file: UploadFile = File(...)
):
    # Enforce role subfolder isolation
    if role not in ["claimant", "bank_employee", "insurer"]:
        raise HTTPException(status_code=400, detail="Invalid uploading role context.")
        
    filename = f"{case_id}_{document_type}_{file.filename}"
    
    # Generate SHA-256 for display integrity
    import hashlib
    file_bytes = file.file.read()
    sha = hashlib.sha256(file_bytes).hexdigest()
    
    # Save the file. Use GridFS if MongoDB is available, otherwise local file fallback.
    url = f"/api/claims/file/{role}/{filename}"
    
    if MONGO_AVAILABLE and grid_fs is not None:
        # Check if file already exists in GridFS, remove it to overwrite
        existing = grid_fs.find_one({"filename": filename})
        if existing:
            grid_fs.delete(existing._id)
        # Upload new file
        grid_fs.put(
            file_bytes,
            filename=filename,
            metadata={"case_id": case_id, "document_type": document_type, "role": role},
            content_type=file.content_type
        )
    else:
        # Fallback: Save to local assets/{role}
        role_dir = os.path.join(ASSETS_DIR, role)
        filepath = os.path.join(role_dir, filename)
        with open(filepath, "wb") as buffer:
            buffer.write(file_bytes)
            
        url = f"/static/assets/{role}/{filename}"
        
    # Update claim record in database
    claims = get_all_claims()
    claim = next((c for c in claims if c["id"] == case_id), None)
    if claim:
        # Add to submitted documents list
        if "submitted_documents" not in claim["claim"]:
            claim["claim"]["submitted_documents"] = []
            
        doc_key = document_type
        if doc_key not in claim["claim"]["submitted_documents"]:
            claim["claim"]["submitted_documents"].append(doc_key)
            
        # Update state history if it was resubmitted
        if claim["status"] == "QUERY_RAISED" and role == "bank_employee":
            # For accidental PMR / FIR uploads
            if "FIR" in claim["claim"]["submitted_documents"] and "Post_Mortem_Report" in claim["claim"]["submitted_documents"]:
                claim["claim"]["claim_forms"]["Form_C"] = True
                claim["claim"]["investigation"]["police_final_report_status"] = "SUBMITTED"
            
        save_claims(claims)
        
    return {"filename": filename, "sha256": sha, "url": url}

@app.get("/api/claims/file/{role}/{filename}")
def get_claim_file(role: str, filename: str):
    if MONGO_AVAILABLE and grid_fs is not None:
        grid_out = grid_fs.find_one({"filename": filename})
        if grid_out:
            return StreamingResponse(
                io.BytesIO(grid_out.read()),
                media_type=grid_out.content_type or "application/octet-stream",
                headers={"Content-Disposition": f"inline; filename={filename}"}
            )
            
    # Fallback to local files
    filepath = os.path.join(ASSETS_DIR, role, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
        
    raise HTTPException(status_code=404, detail="Requested dossier file not found.")

@app.post("/api/agents/simulate")
def simulate_agents(case_id: str = Query("CASE-002")):
    db_claims = get_all_claims()
    claim = next((c for c in db_claims if c["id"] == case_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail="Simulated Case not found.")
        
    logs = []
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    logs.append(f"[{now_str}] [Claimant Agent] Autopilot triggered for Case ID: {case_id}")
    
    # Simulate Claimant Agent submits claim
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
    
    # Simulate Insurer Agent evaluating rules and querying
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
        
        # Simulate Bank Agent pulling and resolving queries
        logs.append(f"[{now_str}] [Bank Agent] Scanning branch query queue. Found Case: {case_id} (Status: QUERY_RAISED).")
        logs.append(f"[{now_str}] [Bank Agent] Calling Simulated Municipal/Police Portal API to fetch missing documents...")
        
        # Add missing documents
        if "submitted_documents" not in claim["claim"]:
            claim["claim"]["submitted_documents"] = []
            
        # Simulate adding accidental police reports
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
            # Spelling name mismatch correction
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
        
        # Re-evaluate by Insurer Agent
        logs.append(f"[{now_str}] [Insurer Agent] Scanning resubmissions. Found Case: {case_id}.")
        logs.append(f"[{now_str}] [Insurer Agent] Claim transitioned to UNDER_REVIEW for final audit.")
        claim["status"] = "UNDER_REVIEW"
        claim["state_history"].append({
            "from": "RESUBMITTED",
            "to": "UNDER_REVIEW",
            "at": now_str,
            "by": "insurer_agent",
            "comment": "Triage evaluation start"
        })
        
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
        # Already clean case
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

    # Save changes to database
    save_claims(db_claims)
    return {"logs": logs}

# Serve static folders
app.mount("/static/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/app.js")
def read_js():
    return FileResponse(os.path.join(BASE_DIR, "app.js"))

@app.get("/style.css")
def read_css():
    return FileResponse(os.path.join(BASE_DIR, "style.css"))

if __name__ == "__main__":
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
