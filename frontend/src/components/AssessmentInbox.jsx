import React, { useState } from "react";

export default function AssessmentInbox({ claims, reloadClaims, customFetch, onNavigateToCert }) {
    const [selectedClaimId, setSelectedClaimId] = useState(null);

    const activeClaim = claims.find(c => c.id === selectedClaimId);

    const postDecision = async (status, caseId) => {
        const comment = prompt(`Enter underwriter comment for transitioning case to ${status}:`, `Forwarding claim state to ${status}`);
        if (comment === null) return; // cancelled
        
        try {
            const res = await customFetch("/api/claims/decision", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    case_id: caseId,
                    status: status,
                    by: "insurer",
                    comment: comment
                })
            });
            if (res.ok) {
                alert(`Case status updated to ${status}!`);
                await reloadClaims();
            } else {
                const err = await res.json();
                alert(`Error making decision: ${err.detail}`);
            }
        } catch (err) {
            console.error("Decision endpoint error:", err);
        }
    };

    return (
        <section id="inbox-section" className="workspace-section active">
            <div className="grid-2">
                {/* Left Queue Panel */}
                <div className="glass-card" style={{ maxHeight: "80vh", overflowY: "auto" }}>
                    <h3>Audit Triage Queue</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "12px", marginBottom: "16px" }}>
                        Claims needing assessor reviews and payment disbursements.
                    </p>
                    
                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {claims.map((claim) => (
                            <div 
                                key={claim.id}
                                className={`glass-card ${claim.id === selectedClaimId ? "active" : ""}`}
                                onClick={() => setSelectedClaimId(claim.id)}
                                style={{ 
                                    padding: "16px", 
                                    marginBottom: 0, 
                                    cursor: "pointer", 
                                    borderLeft: claim.id === selectedClaimId ? "4px solid var(--color-primary)" : "1px solid var(--border-glass)",
                                    background: claim.id === selectedClaimId ? "rgba(0, 245, 255, 0.04)" : "rgba(10, 15, 28, 0.4)" 
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <strong>{claim.policy?.life_assured}</strong>
                                    <span className={`status-badge status-${claim.status ? claim.status.toLowerCase() : "submitted"}`}>
                                        {claim.status}
                                    </span>
                                </div>
                                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", display: "flex", justifyContent: "space-between" }}>
                                    <span>Ref: {claim.trackingId}</span>
                                    <span>Payout: INR {claim.evaluation?.payout?.amount?.toLocaleString() || "0"}</span>
                                </div>
                            </div>
                        ))}
                        {claims.length === 0 && (
                            <p style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>Triage queue is empty.</p>
                        )}
                    </div>
                </div>

                {/* Right Workspace Dossier Panel */}
                <div className="glass-card" style={{ maxHeight: "80vh", overflowY: "auto" }}>
                    {!activeClaim ? (
                        <div style={{ textAlign: "center", padding: "100px 20px", color: "var(--text-muted)" }}>
                            <i className="fa-solid fa-file-signature" style={{ fontSize: "48px", marginBottom: "16px" }}></i>
                            <p>Select a claim dossier from the queue to start underwriting audit.</p>
                        </div>
                    ) : (
                        <div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                                <div>
                                    <h3>Dossier Review</h3>
                                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{activeClaim.trackingId}</span>
                                </div>
                                <span className={`status-badge status-${activeClaim.status ? activeClaim.status.toLowerCase() : "submitted"}`}>
                                    {activeClaim.status}
                                </span>
                            </div>

                            <hr style={{ border: 0, borderTop: "1px solid var(--border-glass)", marginBottom: "16px" }} />

                            <div className="grid-2" style={{ marginBottom: "16px" }}>
                                <div className="detail-list">
                                    <p>Life Assured: <strong>{activeClaim.policy?.life_assured}</strong></p>
                                    <p>Policy Commencement: <strong>{activeClaim.policy?.commencement_date}</strong></p>
                                    <p>Sum Assured: <strong>INR {activeClaim.policy?.sum_assured?.toLocaleString()}</strong></p>
                                    <p>Premiums Paid: <strong>{activeClaim.policy?.premiums_paid_years} Years</strong></p>
                                </div>
                                <div className="detail-list">
                                    <p>Claimant Nominee: <strong>{activeClaim.claim?.claimant?.name}</strong></p>
                                    <p>KYC Aadhaar: <strong>{activeClaim.claim?.claimant?.aadhaar}</strong></p>
                                    <p>IFSC Bank Code: <strong>{activeClaim.claim?.bank_details?.ifsc}</strong></p>
                                    <p>Account Number: <strong>{activeClaim.claim?.bank_details?.account_number}</strong></p>
                                </div>
                            </div>

                            <div className="glass-card" style={{ background: "rgba(0,0,0,0.2)", marginBottom: "16px", padding: "20px" }}>
                                <h4>Medical & Accident Details</h4>
                                <div className="grid-2" style={{ marginTop: "8px" }}>
                                    <div className="detail-list" style={{ marginBottom: 0 }}>
                                        <p style={{ margin: 0 }}>Primary Cause: <strong>{activeClaim.claim?.cause_of_death}</strong></p>
                                        <p style={{ margin: 0 }}>Treating Doctor: <strong>{activeClaim.claim?.medical_details?.treating_doctor}</strong></p>
                                    </div>
                                    <div className="detail-list" style={{ marginBottom: 0 }}>
                                        <p style={{ margin: 0 }}>ICD-10 Code: <strong>{activeClaim.claim?.medical_details?.icd_code}</strong></p>
                                        <p style={{ margin: 0, borderBottom: 0 }}>History: <strong>{activeClaim.claim?.medical_details?.hospitalization_history}</strong></p>
                                    </div>
                                </div>
                            </div>

                            {/* Rules Trace Log Console */}
                            <div className="glass-card" style={{ background: "rgba(0,0,0,0.2)", marginBottom: "16px", padding: "20px" }}>
                                <h4>Explainable Rules Engine Trace Log</h4>
                                <div className="console-trace mt-2" style={{ marginTop: "12px" }}>
                                    {activeClaim.evaluation?.explainability?.rules_trace ? (
                                        activeClaim.evaluation.explainability.rules_trace.map((trace, idx) => (
                                            <div key={idx} className="console-line">
                                                {trace}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="console-line">No trace records registered.</div>
                                    )}
                                </div>
                            </div>

                            {/* Risk Gauge Bar */}
                            <div className="glass-card" style={{ background: "rgba(0,0,0,0.2)", marginBottom: "20px", padding: "20px" }}>
                                <h4>Assessor Risk Level Audit</h4>
                                <div className="risk-level-gauge">
                                    <span style={{ fontSize: "13px", fontWeight: "700" }}>
                                        Score: <span>{activeClaim.evaluation?.risk?.total_score || 0}</span>
                                    </span>
                                    <div className="gauge-bar-wrapper">
                                        <div 
                                            className="gauge-fill" 
                                            style={{ 
                                                width: `${activeClaim.evaluation?.risk?.total_score || 0}%`,
                                                background: activeClaim.evaluation?.risk?.level === "MEDIUM" 
                                                    ? "var(--color-warning)" 
                                                    : (activeClaim.evaluation?.risk?.level === "HIGH" ? "var(--color-danger)" : "var(--color-success)")
                                            }}
                                        ></div>
                                    </div>
                                    <span className={`status-badge ${activeClaim.evaluation?.risk?.level === "LOW" ? "status-approved" : (activeClaim.evaluation?.risk?.level === "MEDIUM" ? "status-under_review" : "status-rejected")}`}>
                                        {activeClaim.evaluation?.risk?.level}
                                    </span>
                                </div>
                            </div>

                            {/* Action Decisions */}
                            <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: "8px", padding: "16px", border: "1px solid var(--border-glass)" }}>
                                <h4>Underwriting Decision & Payout Info</h4>
                                <p style={{ fontSize: "13px", marginTop: "8px" }}>
                                    Decided Payout: <strong style={{ color: "var(--color-success)" }}>
                                        INR {activeClaim.evaluation?.payout?.amount?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                    </strong>
                                </p>
                                <p style={{ fontSize: "13px" }}>
                                    Reasoning: <span style={{ color: "var(--text-muted)" }}>{activeClaim.evaluation?.explainability?.summary}</span>
                                </p>
                                
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "16px" }}>
                                    {activeClaim.status === "SUBMITTED" && (
                                        <button className="btn btn-secondary btn-sm" onClick={() => postDecision('UNDER_REVIEW', activeClaim.id)}>
                                            <i className="fa-solid fa-magnifying-glass-chart"></i> Move to Audit
                                        </button>
                                    )}
                                    {activeClaim.status === "UNDER_REVIEW" && (
                                        <>
                                            <button className="btn btn-secondary btn-sm" onClick={() => postDecision('QUERY_RAISED', activeClaim.id)}>
                                                <i className="fa-solid fa-circle-question"></i> Raise Query
                                            </button>
                                            <button className="btn btn-danger btn-sm" onClick={() => postDecision('REJECTED', activeClaim.id)}>
                                                <i className="fa-solid fa-circle-xmark"></i> Reject Claim
                                            </button>
                                            <button className="btn btn-primary btn-sm" onClick={() => postDecision('APPROVED', activeClaim.id)}>
                                                <i className="fa-solid fa-circle-check"></i> Approve Claim
                                            </button>
                                        </>
                                    )}
                                </div>

                                {activeClaim.status === "APPROVED" && (
                                    <div style={{ marginTop: "16px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px" }}>
                                        <button className="btn btn-success btn-block" onClick={onNavigateToCert}>
                                            <i className="fa-solid fa-stamp"></i> Issue Clearance Disbursal Certificate
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
