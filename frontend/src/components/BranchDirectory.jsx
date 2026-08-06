import React, { useState } from "react";

export default function BranchDirectory({ claims, reloadClaims, customFetch }) {
    const [scanModalOpen, setScanModalOpen] = useState(false);
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [activeCaseId, setActiveCaseId] = useState("");
    const [scanning, setScanning] = useState(false);
    const [scanResult, setScanResult] = useState(""); // "", "success", "failed"
    const [scanText, setScanText] = useState("Awaiting scanner fingerprint contact...");
    const [uploadDocs, setUploadDocs] = useState({});

    // Aadhaar scan popup handlers
    const openScanModal = (caseId) => {
        setActiveCaseId(caseId);
        setScanModalOpen(true);
        setScanning(false);
        setScanResult("");
        setScanText("Awaiting scanner fingerprint contact...");
    };

    const startScan = async () => {
        if (scanning || scanResult === "success") return;
        setScanning(true);
        setScanText("Scanning fingerprint biometric...");
        
        // Wait 2 seconds for visual laser scan
        await new Promise(r => setTimeout(r, 2000));
        
        try {
            const res = await customFetch("/api/claims/verify-aadhaar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ case_id: activeCaseId })
            });
            const data = await res.json();
            
            setScanning(false);
            if (data.success) {
                setScanResult("success");
                setScanText(data.message);
                await reloadClaims();
            } else {
                setScanResult("failed");
                setScanText(data.message || "Aadhaar verification failed.");
            }
        } catch (err) {
            console.error("Aadhaar verification error:", err);
            setScanning(false);
            setScanResult("failed");
            setScanText("Biometric transmission error. Please check server logs.");
        }
    };

    // Document uploads query resubmissions
    const openUploadModal = (caseId) => {
        setActiveCaseId(caseId);
        setUploadModalOpen(true);
        setUploadDocs({});
    };

    const triggerUpload = (docType) => {
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = ".pdf,.jpg,.png";
        fileInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const fd = new FormData();
            fd.append("case_id", activeCaseId);
            fd.append("document_type", docType);
            fd.append("role", "bank_employee");
            fd.append("file", file);
            
            try {
                const res = await customFetch("/api/claims/upload", {
                    method: "POST",
                    body: fd
                });
                if (res.ok) {
                    const info = await res.json();
                    setUploadDocs(prev => ({ ...prev, [docType]: info.url }));
                    alert(`File ${docType} uploaded successfully!`);
                }
            } catch (err) {
                console.error("Upload error:", err);
                alert("Upload failed.");
            }
        };
        fileInput.click();
    };

    const submitResubmission = async () => {
        try {
            const res = await customFetch("/api/claims/decision", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    case_id: activeCaseId,
                    status: "RESUBMITTED",
                    by: "bank_employee",
                    comment: "Uploaded certified police records (FIR & PMR) to clear underwriter query."
                })
            });
            if (res.ok) {
                alert("Dossier forwarded back to insurer review queue!");
                setUploadModalOpen(false);
                await reloadClaims();
            } else {
                const err = await res.json();
                alert(`Transition failed: ${err.detail}`);
            }
        } catch (err) {
            console.error("Resubmission error:", err);
        }
    };

    return (
        <section id="branch-section" className="workspace-section active">
            <div className="glass-card">
                <h3>Branch Claims Directory</h3>
                <p className="card-desc">Review and manage claims registered by depositors at State Bank of India branch levels.</p>
                
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Policy No</th>
                                <th>Claimant</th>
                                <th>Cause of Death</th>
                                <th>Calculated Payout</th>
                                <th>Status</th>
                                <th>Aadhaar KYC</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {claims.map((claim) => {
                                const evalRes = claim.evaluation || {};
                                const isVerified = claim.claim?.legal_status?.nominee_verified;
                                
                                return (
                                    <tr key={claim.id}>
                                        <td><strong>{claim.policy?.policy_number}</strong></td>
                                        <td>{claim.claim?.claimant?.name}</td>
                                        <td style={{ fontSize: "12px", color: "var(--text-muted)" }}>{claim.claim?.cause_of_death}</td>
                                        <td style={{ fontWeight: "700", color: "var(--color-success)" }}>
                                            INR {evalRes.payout ? evalRes.payout.amount.toLocaleString("en-IN") : "0"}
                                        </td>
                                        <td>
                                            <span className={`status-badge status-${claim.status ? claim.status.toLowerCase() : "submitted"}`}>
                                                {claim.status}
                                            </span>
                                        </td>
                                        <td>
                                            {isVerified ? (
                                                <span className="status-badge status-approved"><i className="fa-solid fa-circle-check"></i> VERIFIED</span>
                                            ) : (
                                                <button className="btn btn-secondary btn-sm" style={{ padding: "4px 8px", fontSize: "10px" }} onClick={() => openScanModal(claim.id)}>
                                                    <i className="fa-solid fa-fingerprint"></i> Scan Thumb
                                                </button>
                                            )}
                                        </td>
                                        <td>
                                            {claim.status === "QUERY_RAISED" && (
                                                <button className="btn btn-primary btn-sm" style={{ padding: "4px 8px", fontSize: "10px" }} onClick={() => openUploadModal(claim.id)}>
                                                    <i className="fa-solid fa-cloud-arrow-up"></i> Resolve Query
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                            {claims.length === 0 && (
                                <tr>
                                    <td colSpan="7" style={{ textAlign: "center", color: "var(--text-muted)" }}>No claims found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal: Biometric Scanner */}
            {scanModalOpen && (
                <div id="kyc-scan-modal" className="auth-overlay" style={{ display: "flex" }}>
                    <div className="auth-card" style={{ maxWidth: "380px" }}>
                        <h3>Simulate Aadhaar KYC</h3>
                        <p>Have the nominee place their thumb on the scanner to verify identity.</p>
                        
                        <div 
                            className={`fingerprint-container ${scanning ? "scanning" : ""} ${scanResult === "success" ? "scan-success" : ""} ${scanResult === "failed" ? "scan-failed" : ""}`}
                            onClick={startScan}
                        >
                            <i className="fa-solid fa-fingerprint fingerprint-icon"></i>
                            <div className="scanner-laser"></div>
                        </div>
                        
                        <div id="scan-status" style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "16px", textAlign: "center" }}>
                            {scanText}
                        </div>
                        <button className="btn btn-secondary btn-block" onClick={() => setScanModalOpen(false)}>Close Modal</button>
                    </div>
                </div>
            )}

            {/* Modal: Document resubmissions */}
            {uploadModalOpen && (
                <div id="upload-docs-modal" className="auth-overlay" style={{ display: "flex" }}>
                    <div className="auth-card" style={{ maxWidth: "420px", textAlign: "left" }}>
                        <h3>Upload Query Documents</h3>
                        <p style={{ marginBottom: "16px", fontSize: "12px", color: "var(--text-muted)" }}>
                            Retrieve police reports or autopsy certificates to resolve outstanding underwriting queries.
                        </p>
                        
                        <div className="form-group">
                            <label>Case ID</label>
                            <input type="text" value={activeCaseId} readOnly />
                        </div>
                        
                        <div className="upload-zone" onClick={() => triggerUpload('FIR')}>
                            <i className="fa-solid fa-file-shield upload-icon"></i>
                            <h4>Upload FIR (Accident report)</h4>
                            {uploadDocs.FIR && (
                                <div className="upload-file-info">
                                    <i className="fa-solid fa-circle-check"></i> <span>fir_certified.pdf</span>
                                </div>
                            )}
                        </div>
                        
                        <div className="upload-zone" onClick={() => triggerUpload('Post_Mortem_Report')}>
                            <i className="fa-solid fa-file-medical upload-icon"></i>
                            <h4>Upload PMR (Autopsy report)</h4>
                            {uploadDocs.Post_Mortem_Report && (
                                <div className="upload-file-info">
                                    <i className="fa-solid fa-circle-check"></i> <span>pmr_certified.pdf</span>
                                </div>
                            )}
                        </div>
                        
                        <div style={{ display: "flex", gap: "12px", marginTop: "20px" }}>
                            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setUploadModalOpen(false)}>Cancel</button>
                            <button className="btn btn-primary" style={{ flex: 1 }} onClick={submitResubmission}>Submit to Insurer</button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}
