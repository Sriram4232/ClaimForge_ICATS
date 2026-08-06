import React from "react";

export default function ClaimTracker({ claims, activeClaimId }) {
    const claimRecord = claims.find(c => c.id === activeClaimId) || claims[0];

    if (!claimRecord) {
        return (
            <section id="tracker-section" className="workspace-section active">
                <div className="glass-card">
                    <h3>No Active Claims Found</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Please register a new claim in the intake wizard first.</p>
                </div>
            </section>
        );
    }

    const currentStatus = claimRecord.status ? claimRecord.status.toLowerCase() : "submitted";

    // Stepper mapping
    const steps = [
        { key: "submitted", label: "Submitted", icon: "fa-paper-plane" },
        { key: "under_review", label: "Under Audit", icon: "fa-magnifying-glass-chart" },
        { key: "query_raised", label: "Query Raised", icon: "fa-circle-question" },
        { key: "approved", label: "Approved & Disbursed", icon: "fa-circle-check" }
    ];

    const getStepClass = (stepKey) => {
        if (currentStatus === "rejected" && stepKey === "approved") {
            return ""; // Don't highlight approved if rejected
        }
        if (currentStatus === stepKey || (currentStatus === "resubmitted" && stepKey === "under_review")) {
            return "active";
        }
        
        // Find index of current status and stepKey
        const statusIdx = steps.findIndex(s => s.key === (currentStatus === "resubmitted" ? "under_review" : currentStatus));
        const stepIdx = steps.findIndex(s => s.key === stepKey);
        
        if (statusIdx > stepIdx) {
            return "completed";
        }
        return "";
    };

    return (
        <section id="tracker-section" className="workspace-section active">
            <div className="glass-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                    <div>
                        <h3>Active Claim Progress</h3>
                        <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>Tracking File: <span>{claimRecord.trackingId || "Pending"}</span></p>
                    </div>
                    <span className={`status-badge status-${currentStatus}`}>
                        {claimRecord.status}
                    </span>
                </div>

                {/* Progress line */}
                <div className="stepper" style={{ marginTop: "40px", marginBottom: "40px" }}>
                    {steps.map((s) => (
                        <div key={s.key} className={`step ${getStepClass(s.key)}`} style={{ cursor: "default" }}>
                            <div className="step-number">
                                <i className={`fa-solid ${s.icon}`} style={{ fontSize: "12px" }}></i>
                            </div>
                            <span className="step-label">{s.label}</span>
                        </div>
                    ))}
                </div>

                <div className="glass-card" style={{ background: "rgba(0,0,0,0.2)", marginBottom: 0 }}>
                    <h4>Claim History Audit Trail</h4>
                    <div id="tracker-history-timeline" style={{ fontSize: "13px", lineHeight: "1.8", marginTop: "12px", color: "var(--text-muted)" }}>
                        {claimRecord.state_history && claimRecord.state_history.length > 0 ? (
                            claimRecord.state_history.map((hist, idx) => (
                                <div key={idx} style={{ marginBottom: "10px", paddingBottom: "10px", borderBottom: "1px solid rgba(255,255,255,0.02)" }}>
                                    <i className="fa-solid fa-clock-rotate-left" style={{ marginRight: "8px", color: "var(--color-primary)" }}></i>
                                    <strong>[{hist.at}]</strong> Transitioned from <span style={{ color: "var(--text-main)" }}>{hist.from}</span> to <span style={{ color: "var(--text-main)", fontWeight: "700" }}>{hist.to}</span> by <em>{hist.by}</em>
                                    {hist.comment && (
                                        <p style={{ fontSize: "12px", marginLeft: "22px", color: "var(--text-muted)", fontStyle: "italic" }}>
                                            &ldquo;{hist.comment}&rdquo;
                                        </p>
                                    )}
                                </div>
                            ))
                        ) : (
                            <p>No transactions registered for this claim.</p>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
