# ICATS Test Suite Summary

This directory contains the automated test suites used to verify the Insurance Claim Assistance and Tracking System (ICATS) FastAPI backend, rules engine, and security layer. 

In total, the test suites execute **290 test cases and scenarios** to ensure full coverage and correctness of features.

---

## 1. Test Suite Modules

### 📂 `test_app_mvc.py` (15 Test Cases)
Verifies the MVC controllers, database abstraction, and security configurations:
* **Authentication & Security:** Correct credentials validation, invalid login failures, token parsing, secure password hashing (`PBKDF2`), and role-based endpoint access control.
* **Database & MongoTemplate:** CRUD operations utilizing the `MongoTemplate` querying wrapper (covering database saving, counts, and deletions).
* **Negative Aadhaar KYC:** Verification scenarios handling biometric matches/mismatches, inactive account statuses, device timeouts, and name mismatches.
* **Negative State Transitions:** Strict validation of claim state transitions (e.g. rejecting illegal transitions such as moving from `DRAFT` directly to `APPROVED`).

### 📂 `test_icats.py` (158 Test Cases)
Verifies the custom rule-based Decision Intelligence engine and compliance math:
* **5 Real Test Cases:** Standard claimant dossiers representing baseline rules validation (e.g., suicide exclusions, normal natural claims).
* **150 Combinatorial Scenarios:** Combinations of policy age, cause of death, premium-payment histories, and medical codes to verify statutory paid-up value calculations (Section 113) and early death audits (Section 45).
* **3 Custom Edge Cases:** Advanced conditions covering conflicting medical signals, complex fraud modifiers, and aggregate risk-score decision override thresholds.

### 📂 `test_app.py` (117 Test Cases)
Verifies the API intake pipeline and web endpoints:
* **9 Core API Flow Tests:** Standard integration tests covering endpoint routing, static views mounting, and file uploading details.
* **108 Combinatorial Scenario Tests:** Validates compliance checklists and intake checks against an array of combined form states, cause of death parameters, and document sets.

---

## 2. How to Run the Tests

Ensure your virtual environment is active and run the tests using standard Python `unittest`:

### Run MVC & Security Tests
```bash
python app/tests/test_app_mvc.py
```

### Run Rules Engine Scenarios
```bash
python app/tests/test_icats.py
```

### Run API Intake Tests
```bash
python app/tests/test_app.py
```
