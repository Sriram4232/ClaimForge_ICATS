from pydantic import BaseModel
from typing import List, Optional

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

class VerifyAadhaarRequest(BaseModel):
    case_id: str
