import React from "react";

export default function NameAffidavit({ claims, activeClaimId }) {
    const claimRecord = claims.find(c => c.id === activeClaimId) || claims[0];

    if (!claimRecord) {
        return (
            <section id="affidavit-section" className="workspace-section active">
                <div className="glass-card">
                    <h3>No Affidavit Record Active</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Affidavit details will prefill when claim spelling discrepancy warning triggers.</p>
                </div>
            </section>
        );
    }

    return (
        <section id="affidavit-section" className="workspace-section active">
            <div className="glass-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                    <div>
                        <h3>Name Spelling Discrepancy Affidavit</h3>
                        <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>Pre-filled legal template required by Indian insurers when nominee names differ slightly from KYC databases.</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => window.print()}><i className="fa-solid fa-print"></i> Print Affidavit</button>
                </div>

                <div className="affidavit-paper" id="affidavit-paper-print">
                    <div className="affidavit-stamp-header">
                        NON-JUDICIAL LEGAL STAMP PAPER - INDIA
                    </div>
                    <h3>AFFIDAVIT DECLARATION</h3>
                    <p>I, <strong>{claimRecord.claim?.claimant?.name || "Sunita Devi"}</strong>, residing at Delhi/Kochi/Pune, do hereby solemnly affirm and declare as follows:</p>
                    <ol>
                        <li>That my husband/father, Shri <strong>{claimRecord.policy?.life_assured || "Harish Kumar"}</strong>, who was holding Life Insurance Policy Number <strong>{claimRecord.policy?.policy_number || "502918273"}</strong>, passed away on <strong>{claimRecord.claim?.date_of_death || "20/10/2024"}</strong>.</li>
                        <li>That in the records of the Insurance Company, my name has been entered as <strong>{claimRecord.policy?.nominee_name || "Sunita Devi"}</strong>.</li>
                        <li>That in my Bank Account (Account Number: <strong>{claimRecord.claim?.bank_details?.account_number || "1029384756"}</strong>) and Aadhaar card, my name is recorded as <strong>{claimRecord.claim?.bank_details?.name_on_cheque || "Sunita Devi"}</strong>.</li>
                        <li>That <strong>{claimRecord.policy?.nominee_name}</strong> and <strong>{claimRecord.claim?.bank_details?.name_on_cheque}</strong> refer to the one and the same individual, which is myself.</li>
                        <li>That I make this solemn affirmation conscientiously believing the same to be true and correct, and to submit to the Insurance Company for settlement of the death claim.</li>
                    </ol>
                    <div className="affidavit-signatures">
                        <div>
                            <p>_______________________</p>
                            <strong>DEPONENT</strong>
                        </div>
                        <div style={{ textAlign: "right" }}>
                            <p>Verified before me,</p>
                            <strong>NOTARY PUBLIC / GAZETTED OFFICER</strong>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
