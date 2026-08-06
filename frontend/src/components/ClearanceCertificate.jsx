import React from "react";

export default function ClearanceCertificate({ claims, activeClaimId }) {
    const claimRecord = claims.find(c => c.id === activeClaimId) || claims[0];

    if (!claimRecord) {
        return (
            <section id="certificate-section" className="workspace-section active">
                <div className="glass-card">
                    <h3>No Clearance Record Active</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Approved claims will generate settlement disbursement certificates here.</p>
                </div>
            </section>
        );
    }

    const todayStr = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });

    return (
        <section id="certificate-section" className="workspace-section active">
            <div className="glass-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignSelf: "stretch", alignItems: "center", marginBottom: "20px" }}>
                    <div>
                        <h3>Disbursal Clearance Certificate</h3>
                        <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>Generated clearance seal issued for bank fund settlement.</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => window.print()}>
                        <i className="fa-solid fa-print"></i> Print Clearance
                    </button>
                </div>

                <div className="certificate-paper" id="cert-paper-print">
                    <div className="cert-header">
                        <div className="cert-seal"><i className="fa-solid fa-shield-halved"></i></div>
                        <div className="cert-title">ICATS CLEARANCE SYSTEM</div>
                    </div>
                    <div className="cert-body">
                        <p>
                            This document serves as formal clearance that the life insurance death claim listed below has passed all compliance checklists, statutory non-forfeiture rules under Section 113 of the Insurance Act 1938, and medical suppression checks.
                        </p>
                    </div>
                    <div className="cert-meta">
                        <p><strong>Approved Settled Sum:</strong> INR {claimRecord.evaluation?.payout?.amount?.toLocaleString("en-IN", { minimumFractionDigits: 2 }) || "0.00"}</p>
                        <p><strong>Beneficiary Nominee:</strong> {claimRecord.claim?.claimant?.name || "Sunita Devi"}</p>
                        <p><strong>Policy Number Reference:</strong> {claimRecord.policy?.policy_number || "502918273"}</p>
                        <p><strong>Verification Code:</strong> LIC-DISB-2026-SBI-K01</p>
                    </div>
                    <div className="cert-body">
                        <p>
                            The processing bank is hereby advised to clear and disburse funds to the beneficiary's registered settlement bank account. The claim has been marked closed on the insurer registry ledger.
                        </p>
                    </div>
                    <div className="cert-footer">
                        <span style={{ fontSize: "11px", color: "#555" }}>Clearance Date: {todayStr}</span>
                        <div style={{ textAlign: "center", width: "150px", borderTop: "1px solid #444", paddingTop: "4px", fontSize: "12px", fontWeight: "700" }}>
                            Underwriter Sign
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
