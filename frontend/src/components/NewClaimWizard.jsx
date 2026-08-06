import React, { useState, useEffect } from "react";

export default function NewClaimWizard({ activeClaimId, onNavigateToTracker, reloadClaims, customFetch }) {
    const [step, setStep] = useState(1);
    
    // Form variables
    const [policyNo, setPolicyNo] = useState("502918273");
    const [lifeAssured, setLifeAssured] = useState("Harish Kumar");
    const [nomineeName, setNomineeName] = useState("Sunita Devi");
    const [sumAssured, setSumAssured] = useState(2500000);
    const [commencementDate, setCommencementDate] = useState("15/01/2024");
    const [premiumTerm, setPremiumTerm] = useState(15);
    const [premiumsPaid, setPremiumsPaid] = useState(1);
    const [policyStatus, setPolicyStatus] = useState("ACTIVE");
    const [lastPremiumDate, setLastPremiumDate] = useState("15/01/2024");
    const [exclusions, setExclusions] = useState("Suicide within 12 months");
    
    const [claimantName, setClaimantName] = useState("Sunita Devi");
    const [relation, setRelation] = useState("Wife");
    const [aadhaar, setAadhaar] = useState("1234-5678-9012");
    const [bankAcc, setBankAcc] = useState("1029384756");
    const [bankIfsc, setBankIfsc] = useState("SBIN0001029");
    const [chequeName, setChequeName] = useState("Sunita Devi");
    
    const [causeDeath, setCauseDeath] = useState("Chronic Kidney Disease (CKD) / Renal Failure");
    const [dateDeath, setDateDeath] = useState("20/10/2024");
    const [placeDeath, setPlaceDeath] = useState("Sir Ganga Ram Hospital, Delhi");
    
    const [medDoctor, setMedDoctor] = useState("Dr. Ashok Seth");
    const [medDisease, setMedDisease] = useState("Chronic Kidney Disease (CKD)");
    const [medIcd, setMedIcd] = useState("N18.9");
    const [medHistory, setMedHistory] = useState("Dialysis three times a week since October 2023.");

    const [uploadedDocs, setUploadedDocs] = useState({});
    const [checklistReport, setChecklistReport] = useState(null);
    const [payoutReport, setPayoutReport] = useState(null);

    // Helpers to build API payload
    const getPayload = () => ({
        id: activeClaimId,
        policy: {
            policy_number: policyNo,
            commencement_date: commencementDate,
            maturity_date: "15/01/2045",
            sum_assured: parseFloat(sumAssured),
            premium_paying_term_years: parseInt(premiumTerm),
            premiums_paid_years: parseInt(premiumsPaid),
            nominee_name: nomineeName,
            life_assured: lifeAssured,
            exclusions: [exclusions],
            last_premium_paid_date: lastPremiumDate,
            policy_status: policyStatus
        },
        claim: {
            date_of_death: dateDeath,
            cause_of_death: causeDeath,
            place_of_death: placeDeath,
            date_of_intimation: new Date().toLocaleDateString("en-GB"),
            submitted_documents: Object.keys(uploadedDocs),
            claimant: {
                name: claimantName,
                relationship: relation,
                aadhaar: aadhaar,
                phone: "9876543210",
                address: "Kochi, Kerala"
            },
            claim_forms: {
                Form_A: true,
                Form_B: true,
                Form_C: false
            },
            bank_details: {
                account_number: bankAcc,
                ifsc: bankIfsc,
                bank_name: "State Bank of India",
                name_on_cheque: chequeName
            },
            medical_details: {
                treating_doctor: medDoctor,
                underlying_disease: medDisease,
                icd_code: medIcd,
                hospitalization_history: medHistory
            },
            investigation: {
                investigation_status: "PENDING",
                police_final_report_status: "PENDING",
                accident_details: ""
            },
            legal_status: {
                nominee_verified: false,
                legal_heir_required: false,
                succession_certificate_status: "NOT_REQUIRED"
            }
        }
    });

    // Hook evaluations when navigating
    const goToStep = async (stepNum) => {
        if (stepNum === 2) {
            await runIntakeEvaluation();
        } else if (stepNum === 3 || stepNum === 4) {
            await runFullEvaluation();
        }
        setStep(stepNum);
    };

    const runIntakeEvaluation = async () => {
        try {
            const res = await customFetch("/api/claims/evaluate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(getPayload())
            });
            if (res.ok) {
                const report = await res.json();
                setChecklistReport(report);
            }
        } catch (err) {
            console.error("Intake evaluation error:", err);
        }
    };

    const runFullEvaluation = async () => {
        try {
            const res = await customFetch("/api/claims/evaluate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(getPayload())
            });
            if (res.ok) {
                const report = await res.json();
                setPayoutReport(report);
            }
        } catch (err) {
            console.error("Full evaluation error:", err);
        }
    };

    // Simulated PDF uploader
    const triggerUpload = (docType) => {
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = ".pdf,.jpg,.png";
        fileInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const fd = new FormData();
            fd.append("case_id", activeClaimId);
            fd.append("document_type", docType);
            fd.append("role", "claimant");
            fd.append("file", file);
            
            try {
                const res = await customFetch("/api/claims/upload", {
                    method: "POST",
                    body: fd
                });
                if (res.ok) {
                    const info = await res.json();
                    setUploadedDocs(prev => ({ ...prev, [docType]: info.url }));
                    alert(`Upload Complete!\nSHA-256 Hash:\n${info.sha256}`);
                }
            } catch (err) {
                console.error("Upload error:", err);
                alert("Upload failed.");
            }
        };
        fileInput.click();
    };

    const submitClaim = async () => {
        const payload = getPayload();
        try {
            const res = await customFetch("/api/claims/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: activeClaimId,
                    policy: payload.policy,
                    claim: payload.claim
                })
            });
            
            if (res.ok) {
                const result = await res.json();
                alert(`Claim submitted successfully!\nTracking ID: ${result.trackingId}`);
                await reloadClaims();
                onNavigateToTracker();
            }
        } catch (err) {
            console.error("Claim submission failed:", err);
        }
    };

    // Auto-fill listeners for simulator evaluations
    useEffect(() => {
        const handlePresetLoaded = (e) => {
            const preset = e.detail;
            if (preset.policy) {
                setPolicyNo(preset.policy.policy_number || "");
                setLifeAssured(preset.policy.life_assured || "");
                setNomineeName(preset.policy.nominee_name || "");
                setSumAssured(preset.policy.sum_assured || 2500000);
                setCommencementDate(preset.policy.commencement_date || "");
                setPremiumTerm(preset.policy.premium_paying_term_years || 15);
                setPremiumsPaid(preset.policy.premiums_paid_years || 1);
                setPolicyStatus(preset.policy.policy_status || "ACTIVE");
                setLastPremiumDate(preset.policy.last_premium_paid_date || "");
                setExclusions(preset.policy.exclusions?.[0] || "");
            }
            if (preset.claim) {
                setClaimantName(preset.claim.claimant?.name || "");
                setRelation(preset.claim.claimant?.relationship || "Wife");
                setAadhaar(preset.claim.claimant?.aadhaar || "");
                setBankAcc(preset.claim.bank_details?.account_number || "");
                setBankIfsc(preset.claim.bank_details?.ifsc || "");
                setChequeName(preset.claim.bank_details?.name_on_cheque || "");
                setCauseDeath(preset.claim.cause_of_death || "");
                setDateDeath(preset.claim.date_of_death || "");
                setPlaceDeath(preset.claim.place_of_death || "");
                if (preset.claim.medical_details) {
                    setMedDoctor(preset.claim.medical_details.treating_doctor || "");
                    setMedDisease(preset.claim.medical_details.underlying_disease || "");
                    setMedIcd(preset.claim.medical_details.icd_code || "");
                    setMedHistory(preset.claim.medical_details.hospitalization_history || "");
                }
            }
        };

        window.addEventListener("preset_loaded", handlePresetLoaded);
        return () => window.removeEventListener("preset_loaded", handlePresetLoaded);
    }, []);

    // Extraction indicators
    const showNameWarning = payoutReport && 
        (payoutReport.rules.find(r => r.rule_id === "RULE_02")?.result === "FAILED" ||
         payoutReport.rules.find(r => r.rule_id === "RULE_04")?.result === "FAILED");

    return (
        <section id="wizard-section" className="workspace-section active">
            {/* Stepper Wizard Progress */}
            <div className="stepper">
                {[
                    { id: 1, label: "Intake & Policy" },
                    { id: 2, label: "Checklist Audit" },
                    { id: 3, label: "KYC Matching" },
                    { id: 4, label: "Payout & Risk" },
                    { id: 5, label: "Final Submit" }
                ].map((s) => (
                    <div 
                        key={s.id} 
                        className={`step ${step === s.id ? "active" : ""} ${step > s.id ? "completed" : ""}`}
                        onClick={() => goToStep(s.id)}
                    >
                        <div className="step-number">{s.id}</div>
                        <span className="step-label">{s.label}</span>
                    </div>
                ))}
            </div>

            {/* Pane 1: Intake */}
            {step === 1 && (
                <div className="wizard-pane active" id="pane-1">
                    <div className="glass-card">
                        <h3><i className="fa-solid fa-file-signature text-primary"></i> Policy Specifications</h3>
                        <p className="card-desc">Provide policy metrics for validation. Load presets via Autopilot Simulator for automated case evaluations.</p>
                        
                        <div className="grid-2">
                            <div>
                                <div className="form-group">
                                    <label>Policy Number</label>
                                    <input type="text" value={policyNo} onChange={(e) => setPolicyNo(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Life Assured (Deceased)</label>
                                    <input type="text" value={lifeAssured} onChange={(e) => setLifeAssured(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Designated Nominee</label>
                                    <input type="text" value={nomineeName} onChange={(e) => setNomineeName(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Sum Assured (INR)</label>
                                    <input type="number" value={sumAssured} onChange={(e) => setSumAssured(parseFloat(e.target.value))} />
                                </div>
                                <div className="form-group">
                                    <label>Commencement Date</label>
                                    <input type="text" value={commencementDate} onChange={(e) => setCommencementDate(e.target.value)} />
                                </div>
                            </div>
                            <div>
                                <div className="form-group">
                                    <label>Premium Paying Term (Years)</label>
                                    <input type="number" value={premiumTerm} onChange={(e) => setPremiumTerm(parseInt(e.target.value))} />
                                </div>
                                <div className="form-group">
                                    <label>Premiums Paid (Years)</label>
                                    <input type="number" value={premiumsPaid} onChange={(e) => setPremiumsPaid(parseInt(e.target.value))} />
                                </div>
                                <div className="form-group">
                                    <label>Policy Status</label>
                                    <select value={policyStatus} onChange={(e) => setPolicyStatus(e.target.value)}>
                                        <option value="ACTIVE">ACTIVE</option>
                                        <option value="LAPSED">LAPSED</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Last Premium Paid Date</label>
                                    <input type="text" value={lastPremiumDate} onChange={(e) => setLastPremiumDate(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Exclusions Clause</label>
                                    <input type="text" value={exclusions} onChange={(e) => setExclusions(e.target.value)} />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="glass-card">
                            <h3><i className="fa-solid fa-user-tag text-primary"></i> Claimant Profile & Bank Account</h3>
                            <div className="form-group">
                                <label>Claimant Full Name</label>
                                <input type="text" value={claimantName} onChange={(e) => setClaimantName(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label>Relationship to Deceased</label>
                                <select value={relation} onChange={(e) => setRelation(e.target.value)}>
                                    <option value="Wife">Wife</option>
                                    <option value="Husband">Husband</option>
                                    <option value="Son">Son</option>
                                    <option value="Daughter">Daughter</option>
                                    <option value="Mother">Mother</option>
                                    <option value="Father">Father</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Aadhaar Card (KYC)</label>
                                <input type="text" value={aadhaar} onChange={(e) => setAadhaar(e.target.value)} />
                            </div>
                            <div className="grid-2">
                                <div className="form-group">
                                    <label>Account Number</label>
                                    <input type="text" value={bankAcc} onChange={(e) => setBankAcc(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>IFSC Code</label>
                                    <input type="text" value={bankIfsc} onChange={(e) => setBankIfsc(e.target.value)} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Name on Bank Cheque</label>
                                <input type="text" value={chequeName} onChange={(e) => setChequeName(e.target.value)} />
                            </div>
                        </div>

                        <div className="glass-card">
                            <h3><i className="fa-solid fa-hospital-user text-primary"></i> Death Details & Documents</h3>
                            <div className="form-group">
                                <label>Cause of Death</label>
                                <input type="text" value={causeDeath} onChange={(e) => setCauseDeath(e.target.value)} />
                            </div>
                            <div className="grid-2">
                                <div className="form-group">
                                    <label>Date of Death</label>
                                    <input type="text" value={dateDeath} onChange={(e) => setDateDeath(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Place of Death</label>
                                    <input type="text" value={placeDeath} onChange={(e) => setPlaceDeath(e.target.value)} />
                                </div>
                            </div>

                            <div className="upload-zone" onClick={() => triggerUpload('Death_Certificate')}>
                                <i className="fa-solid fa-file-pdf upload-icon"></i>
                                <h4>Death Certificate</h4>
                                <p style={{ fontSize: "11px", color: "var(--text-muted)" }}>Click to simulate file upload</p>
                                {uploadedDocs.Death_Certificate && (
                                    <div className="upload-file-info">
                                        <i className="fa-solid fa-circle-check"></i> <span>death_certificate.pdf</span>
                                    </div>
                                )}
                            </div>
                            
                            <div className="upload-zone" onClick={() => triggerUpload('Cancelled_Cheque')}>
                                <i className="fa-solid fa-file-invoice upload-icon"></i>
                                <h4>Cancelled Cheque Copy</h4>
                                <p style={{ fontSize: "11px", color: "var(--text-muted)" }}>Click to simulate file upload</p>
                                {uploadedDocs.Cancelled_Cheque && (
                                    <div className="upload-file-info">
                                        <i className="fa-solid fa-circle-check"></i> <span>cheque.pdf</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="glass-card">
                        <h3><i className="fa-solid fa-house-medical-flag text-primary"></i> Clinical Profile (Section 45 pre-existing checks)</h3>
                        <div className="grid-3">
                            <div className="form-group">
                                <label>Treating Doctor</label>
                                <input type="text" value={medDoctor} onChange={(e) => setMedDoctor(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label>Underlying Disease</label>
                                <input type="text" value={medDisease} onChange={(e) => setMedDisease(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label>ICD-10 Diagnostic Code</label>
                                <input type="text" value={medIcd} onChange={(e) => setMedIcd(e.target.value)} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Hospitalization History Description</label>
                            <input type="text" value={medHistory} onChange={(e) => setMedHistory(e.target.value)} />
                        </div>
                    </div>

                    <div className="wizard-actions">
                        <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Ensure all variables are populated before evaluating rules.</span>
                        <button className="btn btn-primary" onClick={() => goToStep(2)}>
                            Evaluate Rules & Next <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            )}

            {/* Pane 2: Checklist Audit */}
            {step === 2 && (
                <div className="wizard-pane active" id="pane-2">
                    <div className="glass-card">
                        <h3><i className="fa-solid fa-list-check text-primary"></i> Compliance Checklist Audit</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>
                            The checklist is dynamically configured based on standard regulatory requirements and the cause of death.
                        </p>
                        
                        <div>
                            <h4 style={{ marginBottom: "12px" }}>Required Checklist Verification Status</h4>
                            {checklistReport && checklistReport.rules ? (
                                checklistReport.rules.map((rule) => {
                                    const passed = rule.result === "PASSED";
                                    return (
                                        <div 
                                            key={rule.rule_id}
                                            style={{ padding: "10px 14px", border: "1px solid var(--border-glass)", borderRadius: "6px", marginBottom: "8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                                        >
                                            <div>
                                                <strong>{rule.name}</strong> ({rule.rule_id})
                                                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>{rule.message}</p>
                                            </div>
                                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                                <i className={`fa-solid ${passed ? "fa-circle-check text-success" : "fa-circle-xmark text-danger"}`}></i>
                                                <span style={{ fontSize: "12px", fontWeight: "700", color: passed ? "var(--color-success)" : "var(--color-danger)" }}>
                                                    {rule.result}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })
                            ) : (
                                <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>Running audit compliance rules...</p>
                            )}
                        </div>
                    </div>
                    
                    <div className="wizard-actions">
                        <button className="btn btn-secondary" onClick={() => goToStep(1)}>
                            <i className="fa-solid fa-arrow-left"></i> Intake Form
                        </button>
                        <button className="btn btn-primary" onClick={() => goToStep(3)}>
                            Nominee KYC Matching <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            )}

            {/* Pane 3: KYC Matching */}
            {step === 3 && (
                <div className="wizard-pane active" id="pane-3">
                    <div className="glass-card">
                        <h3><i className="fa-solid fa-arrows-spin text-primary"></i> Token-Sorted Levenshtein Matching</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "24px" }}>
                            Matches policy designated nominee name against claimant name and bank cheque payee details.
                        </p>
                        
                        <div className="grid-2">
                            <div className="glass-card" style={{ marginBottom: 0, background: "rgba(0,0,0,0.2)" }}>
                                <h4>Nominee Matching Matrix</h4>
                                <p style={{ fontSize: "13px", marginTop: "8px" }}>Policy Nominee: <strong>{nomineeName}</strong></p>
                                <p style={{ fontSize: "13px" }}>Claimant Name: <strong>{claimantName}</strong></p>
                                <p style={{ fontSize: "13px", marginTop: "8px" }}>
                                    Name Match:{" "}
                                    <span className={`status-badge ${payoutReport && payoutReport.rules.find(r => r.rule_id === "RULE_02")?.result === "PASSED" ? "status-approved" : "status-rejected"}`}>
                                        {payoutReport ? payoutReport.rules.find(r => r.rule_id === "RULE_02")?.result : "-"}
                                    </span>
                                </p>
                            </div>
                            
                            <div className="glass-card" style={{ marginBottom: 0, background: "rgba(0,0,0,0.2)" }}>
                                <h4>Cheque Holder Matching Matrix</h4>
                                <p style={{ fontSize: "13px", marginTop: "8px" }}>Claimant Name: <strong>{claimantName}</strong></p>
                                <p style={{ fontSize: "13px" }}>Cheque Name: <strong>{chequeName}</strong></p>
                                <p style={{ fontSize: "13px", marginTop: "8px" }}>
                                    Name Match:{" "}
                                    <span className={`status-badge ${payoutReport && payoutReport.rules.find(r => r.rule_id === "RULE_04")?.result === "PASSED" ? "status-approved" : "status-rejected"}`}>
                                        {payoutReport ? payoutReport.rules.find(r => r.rule_id === "RULE_04")?.result : "-"}
                                    </span>
                                </p>
                            </div>
                        </div>

                        {showNameWarning && (
                            <div id="name-warning-panel" className="alert-box">
                                <h4><i className="fa-solid fa-triangle-exclamation"></i> Nominee Name Spelling Discrepancy Flagged</h4>
                                <p style={{ fontSize: "13px", marginBottom: "12px" }}>
                                    The similarity score between the claimant's name and cheque name is below 90%. To proceed, you must execute a Name Affidavit.
                                </p>
                            </div>
                        )}
                    </div>
                    
                    <div className="wizard-actions">
                        <button className="btn btn-secondary" onClick={() => goToStep(2)}>
                            <i className="fa-solid fa-arrow-left"></i> Compliance Checklist
                        </button>
                        <button className="btn btn-primary" onClick={() => goToStep(4)}>
                            View Payout Computation <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            )}

            {/* Pane 4: Payout & Risk */}
            {step === 4 && (
                <div className="wizard-pane active" id="pane-4">
                    <div className="glass-card grid-2">
                        <div>
                            <h3><i className="fa-solid fa-calculator text-primary"></i> Payout Audit Details</h3>
                            <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: "8px", padding: "20px", marginTop: "16px", marginBottom: "16px", border: "1px solid var(--border-glass)" }}>
                                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>Payout Type</span>
                                <h4 style={{ marginBottom: "10px", fontWeight: "700" }}>
                                    {payoutReport ? payoutReport.payout.type.replace(/_/g, " ") : "-"}
                                </h4>
                                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>Calculated Value</span>
                                <h2 style={{ color: "var(--color-success)", fontWeight: "800" }}>
                                    <span className="data-glow">INR {payoutReport ? payoutReport.payout.amount.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0.00"}</span>
                                </h2>
                            </div>
                            <p style={{ fontSize: "13px" }}>
                                Computation Formula Used:{" "}
                                <code style={{ background: "#000", padding: "2px 6px", borderRadius: "4px" }}>
                                    {payoutReport ? payoutReport.payout.formula_used : "-"}
                                </code>
                            </p>
                        </div>
                        
                        <div>
                            <h3><i className="fa-solid fa-triangle-exclamation text-primary"></i> Fraud Risk Modifiers</h3>
                            <div className="risk-level-gauge">
                                <span style={{ fontSize: "13px", fontWeight: "700" }}>
                                    Risk Score: <span className="data-glow">{payoutReport ? payoutReport.risk.total_score : 0}</span>/100
                                </span>
                                <div className="gauge-bar-wrapper">
                                    <div 
                                        className="gauge-fill" 
                                        style={{ 
                                            width: `${payoutReport ? payoutReport.risk.total_score : 0}%`,
                                            background: payoutReport && payoutReport.risk.level === "MEDIUM" 
                                                ? "var(--color-warning)" 
                                                : (payoutReport && payoutReport.risk.level === "HIGH" ? "var(--color-danger)" : "var(--color-success)")
                                        }}
                                    ></div>
                                </div>
                                <span className={`status-badge ${payoutReport && payoutReport.risk.level === "LOW" ? "status-approved" : (payoutReport && payoutReport.risk.level === "MEDIUM" ? "status-under_review" : "status-rejected")}`}>
                                    {payoutReport ? payoutReport.risk.level : "-"}
                                </span>
                            </div>
                            
                            <div style={{ marginTop: "16px" }}>
                                {payoutReport && payoutReport.fraud_flags.length > 0 ? (
                                    payoutReport.fraud_flags.map((flag) => (
                                        <span 
                                            key={flag} 
                                            className="status-badge status-rejected"
                                            style={{ marginRight: "6px", marginBottom: "6px" }}
                                        >
                                            {flag.replace(/_/g, " ")}
                                        </span>
                                    ))
                                ) : (
                                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>No suspicious fraud triggers flagged.</span>
                                )}
                            </div>
                        </div>
                    </div>
                    
                    <div className="wizard-actions">
                        <button className="btn btn-secondary" onClick={() => goToStep(3)}>
                            <i className="fa-solid fa-arrow-left"></i> KYC Matching
                        </button>
                        <button className="btn btn-primary" onClick={() => goToStep(5)}>
                            Proceed to Submission <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            )}

            {/* Pane 5: Final Submit */}
            {step === 5 && (
                <div className="wizard-pane active" id="pane-5">
                    <div className="glass-card text-center" style={{ padding: "50px 20px", textAlign: "center" }}>
                        <i className="fa-solid fa-circle-check" style={{ fontSize: "64px", color: "var(--color-success)", marginBottom: "20px" }}></i>
                        <h3>Intake Rules Checked & Ready</h3>
                        <p style={{ color: "var(--text-muted)", maxWidth: "500px", margin: "8px auto 24px auto", fontSize: "14px" }}>
                            The claims engine has audited all submitted variables, calculated the non-forfeiture payout value, and validated the KYC. You can now finalize registration.
                        </p>
                        <button className="btn btn-primary btn-lg" onClick={submitClaim}>
                            <i className="fa-solid fa-paper-plane"></i> Submit to Underwriter Queue
                        </button>
                    </div>
                    <div className="wizard-actions">
                        <button className="btn btn-secondary" onClick={() => goToStep(4)}>
                            <i className="fa-solid fa-arrow-left"></i> Payout Result
                        </button>
                    </div>
                </div>
            )}
        </section>
    );
}
