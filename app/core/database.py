import os
import json
import gridfs
from pymongo import MongoClient
from app.core.mongo_template import MongoTemplate
from app.utils.security import hash_password

# Setup environment loading
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # points to app/

def load_env_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

# Try loading .env from parent of app/ or app/
load_env_file(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_env_file(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "icats_db")
JSON_DB_PATH = os.path.join(BASE_DIR, "db.json")

mongo_client = None
db = None
users_col = None
claims_col = None
aadhaar_col = None
grid_fs = None
MONGO_AVAILABLE = False

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info() # verify connection
    db = mongo_client[MONGO_DB_NAME]
    users_col = db["users"]
    claims_col = db["claims"]
    aadhaar_col = db["aadhaar"]
    grid_fs = gridfs.GridFS(db)
    MONGO_AVAILABLE = True
    print("[INFO] Successfully connected to MongoDB.")
except Exception as e:
    MONGO_AVAILABLE = False
    print(f"[WARNING] MongoDB connection failed ({e}). Falling back to local JSON database.")

# Initialize the MongoTemplate wrapper
mongo_template = MongoTemplate(
    db_client=mongo_client if MONGO_AVAILABLE else None,
    db_name=MONGO_DB_NAME,
    fallback_json_path=JSON_DB_PATH
)

# Define mock data
MOCK_USERS = [
    {"email": "nominee@icats.in", "password": "nominee", "name": "Sunita Devi", "role": "claimant"},
    {"email": "agent@sbi.co.in", "password": "agent", "name": "Ramesh Kumar", "role": "bank_employee"},
    {"email": "assessor@lic.co.in", "password": "assessor", "name": "A. K. Shastri", "role": "insurer"}
]

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
    "2000-0000-0009": {
        "name": "Sunita Devi",
        "biometric_status": "MISMATCH",
        "status": "ACTIVE",
        "reason": "Biometric verification failed: fingerprint match score below 70% threshold."
    },
    "3000-0000-0001": {
        "name": "Sunita Devi",
        "biometric_status": "MATCH",
        "status": "INACTIVE",
        "reason": "Aadhaar status is suspended/inactive in UIDAI database."
    },
    "4000-0000-0005": {
        "name": "John Doe",
        "biometric_status": "MATCH",
        "status": "ACTIVE",
        "reason": "Identity verification failed: Aadhaar registered name 'John Doe' does not match claimant name 'Sunita Devi'."
    },
    "5000-0000-0006": {
        "name": "Sunita Devi",
        "biometric_status": "TIMEOUT",
        "status": "ACTIVE",
        "reason": "Biometric device timeout: poor print quality / dirty sensor."
    }
}

# Seed database logic
def seed_database():
    # Hash passwords in mock users for secure storage
    hashed_users = []
    for u in MOCK_USERS:
        hashed_user = u.copy()
        hashed_user["password"] = hash_password(u["password"])
        hashed_users.append(hashed_user)

    if MONGO_AVAILABLE:
        try:
            # Seed users using MongoTemplate
            if mongo_template.count("users") == 0:
                mongo_template.insert_many("users", hashed_users)
                print("[INFO] Seeded user directory to MongoDB.")
            # Seed claims using MongoTemplate
            if mongo_template.count("claims") == 0:
                mongo_template.insert_many("claims", MOCK_CLAIMS)
                print("[INFO] Seeded claims database to MongoDB.")
            # Seed aadhaar DB using MongoTemplate
            if mongo_template.count("aadhaar") == 0:
                seeded_aadhaar = []
                for num, val in MOCK_AADHAAR_DB.items():
                    item = val.copy()
                    item["aadhaar"] = num
                    seeded_aadhaar.append(item)
                mongo_template.insert_many("aadhaar", seeded_aadhaar)
                print("[INFO] Seeded Aadhaar profiles directory to MongoDB.")
        except Exception as e:
            print(f"[ERROR] Database seeding failed: {e}")
    else:
        # JSON fallback using MongoTemplate interface to keep fallback files synchronized
        if not os.path.exists(JSON_DB_PATH):
            seeded_aadhaar = []
            for num, val in MOCK_AADHAAR_DB.items():
                item = val.copy()
                item["aadhaar"] = num
                seeded_aadhaar.append(item)
            mongo_template.insert_many("users", hashed_users)
            mongo_template.insert_many("claims", MOCK_CLAIMS)
            mongo_template.insert_many("aadhaar", seeded_aadhaar)
            print("[INFO] Seeded local JSON database using MongoTemplate.")

# Seed on import
seed_database()
