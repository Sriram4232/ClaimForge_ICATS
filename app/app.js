// ================= GLOBAL APP STATE =================
let loggedInUser = null;
let claimsList = [];
let activeClaimId = "CASE-001";
let activeWizardStep = 1;
let uploadedDocs = {};
let activeUploadCaseId = null;

// ================= APP INITIALIZATION =================
document.addEventListener("DOMContentLoaded", () => {
    // Check if user is already logged in
    const cached = localStorage.getItem("icats_user");
    if (cached) {
        loggedInUser = JSON.parse(cached);
        setupSession();
    } else {
        // Pre-fill Claimant credentials for convenience
        fillCredentials("nominee@icats.in", "nominee");
    }
});

// Helper to autofill credentials
function fillCredentials(email, password) {
    document.getElementById("login-email").value = email;
    document.getElementById("login-password").value = password;
}

// ================= AUTHENTICATION =================
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    
    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Authentication failed.");
            return;
        }
        
        loggedInUser = await response.json();
        localStorage.setItem("icats_user", JSON.stringify(loggedInUser));
        setupSession();
        
    } catch (err) {
        console.error("Login error:", err);
        alert("Failed to connect to authentication server.");
    }
}

function handleLogout() {
    loggedInUser = null;
    localStorage.removeItem("icats_user");
    
    // Reset view
    document.getElementById("auth-overlay").style.display = "flex";
    document.getElementById("app-view").style.display = "none";
    
    // Clear credentials form
    fillCredentials("nominee@icats.in", "nominee");
}

function setupSession() {
    // Hide login, show app
    document.getElementById("auth-overlay").style.display = "none";
    document.getElementById("app-view").style.display = "flex";
    
    // Configure user display
    document.getElementById("user-name").innerText = loggedInUser.name;
    document.getElementById("user-role").innerText = loggedInUser.role;
    
    // Configure role tag
    const roleTag = document.getElementById("role-tag");
    roleTag.innerText = loggedInUser.role.replace("_", " ");
    roleTag.className = "status-badge " + (loggedInUser.role === "insurer" ? "status-under_review" : (loggedInUser.role === "bank_employee" ? "status-submitted" : "status-ready"));
    
    // Configure role-based layout visibility
    configureRoleUI();
    
    // Load initial claims data
    loadClaims();
}

function configureRoleUI() {
    // Hide all role specific sections
    const claimantOnly = document.querySelectorAll(".claimant-only");
    const bankOnly = document.querySelectorAll(".bank-only");
    const insurerOnly = document.querySelectorAll(".insurer-only");
    
    claimantOnly.forEach(el => el.style.display = "none");
    bankOnly.forEach(el => el.style.display = "none");
    insurerOnly.forEach(el => el.style.display = "none");
    
    // Activate link and show section
    let firstMenu = null;
    if (loggedInUser.role === "claimant") {
        claimantOnly.forEach(el => el.style.display = "flex");
        // Trigger specific menus
        document.getElementById("menu-affidavit").style.display = "flex";
        firstMenu = document.querySelector(".claimant-only");
    } else if (loggedInUser.role === "bank_employee") {
        bankOnly.forEach(el => el.style.display = "flex");
        document.getElementById("menu-affidavit").style.display = "flex";
        firstMenu = document.querySelector(".bank-only");
    } else if (loggedInUser.role === "insurer") {
        insurerOnly.forEach(el => el.style.display = "flex");
        firstMenu = document.querySelector(".insurer-only");
    }
    
    // Reset active workspace section
    if (firstMenu) {
        firstMenu.click();
    }
}

// ================= LOADER & SWITCHER =================
function showSection(sectionId, menuItemElement) {
    // Hide all sections
    const sections = document.querySelectorAll(".workspace-section");
    sections.forEach(sec => sec.classList.remove("active"));
    
    // Show active section
    const activeSec = document.getElementById(sectionId);
    if (activeSec) {
        activeSec.classList.add("active");
    }
    
    // Reset active tab states
    const items = document.querySelectorAll(".menu-item");
    items.forEach(it => it.classList.remove("active"));
    if (menuItemElement) {
        menuItemElement.classList.add("active");
    }
    
    // Update header texts
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");
    
    if (sectionId === "wizard-section") {
        pageTitle.innerText = "New Claim Assistance";
        pageSubtitle.innerText = "Follow the 5-step stepper to audit and submit death claim files.";
        goToStep(1);
    } else if (sectionId === "tracker-section") {
        pageTitle.innerText = "Claim Tracker";
        pageSubtitle.innerText = "Track your active claim workflow status and history trace.";
        loadTrackerView();
    } else if (sectionId === "branch-section") {
        pageTitle.innerText = "Branch Claims Directory";
        pageSubtitle.innerText = "Review and forward nominee claims registered at this branch.";
        renderBranchDirectory();
    } else if (sectionId === "inbox-section") {
        pageTitle.innerText = "Underwriting Inbox";
        pageSubtitle.innerText = "Review submitted claim dossiers and output decision directives.";
        renderInsurerInbox();
    } else if (sectionId === "certificate-section") {
        pageTitle.innerText = "Disbursal Clearance Certificate";
        pageSubtitle.innerText = "Official clearance certificate issued to the settlement bank.";
        renderApprovedCertificate();
    } else if (sectionId === "affidavit-section") {
        pageTitle.innerText = "One and the Same Person Affidavit";
        pageSubtitle.innerText = "Pre-filled identity declaration stamp for nominee name spelling differences.";
        renderSpellingAffidavit();
    } else if (sectionId === "autopilot-section") {
        pageTitle.innerText = "Autopilot Multi-Agent Simulator";
        pageSubtitle.innerText = "Launch automated agent flows to audit, query, and clear claims.";
    }
}

// ================= DATABASE LOADS =================
async function loadClaims() {
    try {
        const res = await fetch(`/api/claims?role=${loggedInUser.role}`);
        if (res.ok) {
            claimsList = await res.json();
            
            // Refresh dependent views
            const activeSection = document.querySelector(".workspace-section.active");
            if (activeSection) {
                const id = activeSection.id;
                if (id === "branch-section") renderBranchDirectory();
                if (id === "inbox-section") renderInsurerInbox();
            }
        }
    } catch (err) {
        console.error("Error loading claims:", err);
    }
}

// ================= CLAIMANT WIZARD STEPPER =================
function goToStep(stepNum) {
    // Hide all step panels
    for (let i = 1; i <= 5; i++) {
        const pane = document.getElementById(`pane-${i}`);
        const btn = document.getElementById(`step-btn-${i}`);
        if (pane) pane.classList.remove("active");
        if (btn) btn.classList.remove("active");
    }
    
    // Show active step panel
    document.getElementById(`pane-${stepNum}`).classList.add("active");
    document.getElementById(`step-btn-${stepNum}`).classList.add("active");
    activeWizardStep = stepNum;
    
    // Perform evaluations on steps
    if (stepNum === 2) {
        triggerIntakeEvaluation();
    } else if (stepNum === 3) {
        runFuzzyNameDetails();
    } else if (stepNum === 4) {
        runPayoutAndRiskPanel();
    }
}

async function triggerIntakeEvaluation() {
    const payload = getWizardPayload();
    try {
        const res = await fetch("/api/claims/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            const report = await res.json();
            renderDynamicChecklist(report);
        }
    } catch (err) {
        console.error("Intake evaluation error:", err);
    }
}

function getWizardPayload() {
    return {
        id: activeClaimId,
        policy: {
            policy_number: document.getElementById("policy-no").value,
            commencement_date: document.getElementById("commencement-date").value,
            maturity_date: "15/01/2045", // Mock Maturity
            sum_assured: parseFloat(document.getElementById("sum-assured").value),
            premium_paying_term_years: parseInt(document.getElementById("premium-paying-term").value),
            premiums_paid_years: parseInt(document.getElementById("premiums-paid").value),
            nominee_name: document.getElementById("nominee-name").value,
            life_assured: document.getElementById("life-assured").value,
            exclusions: [document.getElementById("policy-exclusions").value],
            last_premium_paid_date: document.getElementById("last-premium-date").value,
            policy_status: document.getElementById("policy-status").value
        },
        claim: {
            date_of_death: document.getElementById("date-death").value,
            cause_of_death: document.getElementById("cause-death").value,
            place_of_death: document.getElementById("place-death").value,
            date_of_intimation: new Date().toLocaleDateString("en-GB"),
            submitted_documents: Object.keys(uploadedDocs),
            claimant: {
                name: document.getElementById("claimant-name").value,
                relationship: document.getElementById("claimant-relation").value,
                aadhaar: document.getElementById("claimant-aadhaar").value,
                phone: "9876543210",
                address: "Kochi, Kerala"
            },
            claim_forms: {
                Form_A: true,
                Form_B: true,
                Form_C: false // Will be flagged and toggled during reviews
            },
            bank_details: {
                account_number: document.getElementById("bank-acc").value,
                ifsc: document.getElementById("bank-ifsc").value,
                bank_name: "State Bank of India",
                name_on_cheque: document.getElementById("bank-cheque-name").value
            },
            medical_details: {
                treating_doctor: document.getElementById("med-doctor").value,
                underlying_disease: document.getElementById("med-disease").value,
                icd_code: document.getElementById("med-icd").value,
                hospitalization_history: document.getElementById("med-history").value
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
    };
}

function renderDynamicChecklist(report) {
    const container = document.getElementById("dynamic-checklist-container");
    container.innerHTML = "";
    
    // Render mandatory document audits
    const heading = document.createElement("h4");
    heading.style.marginBottom = "12px";
    heading.innerText = "Required Checklist Verification Status";
    container.appendChild(heading);
    
    // Render rules array
    report.rules.forEach(rule => {
        const item = document.createElement("div");
        item.style.padding = "10px 14px";
        item.style.border = "1px solid var(--border-glass)";
        item.style.borderRadius = "6px";
        item.style.marginBottom = "8px";
        item.style.display = "flex";
        item.style.justifyContent = "space-between";
        item.style.alignItems = "center";
        
        const passed = rule.result === "PASSED";
        const icon = passed ? '<i class="fa-solid fa-circle-check text-success"></i>' : '<i class="fa-solid fa-circle-xmark text-danger"></i>';
        
        item.innerHTML = `
            <div>
                <strong>${rule.name}</strong> (${rule.rule_id})
                <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">${rule.message}</p>
            </div>
            <div>
                ${icon} <span style="font-size:12px; font-weight:700; color:${passed ? "var(--color-success)" : "var(--color-danger)"};">${rule.result}</span>
            </div>
        `;
        container.appendChild(item);
    });
}

// Step 3: Run Fuzzy matching display details
async function runFuzzyNameDetails() {
    const payload = getWizardPayload();
    try {
        const res = await fetch("/api/claims/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            const report = await res.json();
            
            // Extract Rule 2 and Rule 4 results
            const r2 = report.rules.find(r => r.rule_id === "RULE_02");
            const r4 = report.rules.find(r => r.rule_id === "RULE_04");
            
            document.getElementById("val-policy-nominee").innerText = payload.policy.nominee_name;
            document.getElementById("val-claimant-name").innerText = payload.claim.claimant.name;
            document.getElementById("val-claimant-name2").innerText = payload.claim.claimant.name;
            document.getElementById("val-cheque-name").innerText = payload.claim.bank_details.name_on_cheque;
            
            // Set nominee badge
            const nomineeBadge = document.getElementById("badge-nominee-match");
            nomineeBadge.innerText = r2.result;
            nomineeBadge.className = `status-badge ${r2.result === "PASSED" ? "status-approved" : "status-rejected"}`;
            
            // Set cheque badge
            const chequeBadge = document.getElementById("badge-cheque-match");
            chequeBadge.innerText = r4.result;
            chequeBadge.className = `status-badge ${r4.result === "PASSED" ? "status-approved" : "status-rejected"}`;
            
            // Show alert box if mismatch exists
            const alertPanel = document.getElementById("name-warning-panel");
            if (r2.result === "FAILED" || r4.result === "FAILED" || r4.impact === "WARNING") {
                alertPanel.style.display = "block";
            } else {
                alertPanel.style.display = "none";
            }
        }
    } catch (err) {
        console.error("Fuzzy name mismatch check error:", err);
    }
}

// Step 4: Payout and Risk indicators
async function runPayoutAndRiskPanel() {
    const payload = getWizardPayload();
    try {
        const res = await fetch("/api/claims/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            const report = await res.json();
            
            // Populate Payout calculations
            document.getElementById("val-payout-type").innerText = report.payout.type.replace(/_/g, " ");
            document.getElementById("val-payout-amount").innerText = `INR ${report.payout.amount.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById("val-payout-formula").innerText = report.payout.formula_used;
            
            // Populate Risk Level
            document.getElementById("val-risk-score").innerText = report.risk.total_score;
            const gaugeFill = document.getElementById("risk-gauge-fill");
            gaugeFill.style.width = `${report.risk.total_score}%`;
            
            let color = "var(--color-success)";
            if (report.risk.level === "MEDIUM") color = "var(--color-warning)";
            if (report.risk.level === "HIGH") color = "var(--color-danger)";
            gaugeFill.style.background = color;
            
            const riskBadge = document.getElementById("badge-risk-level");
            riskBadge.innerText = report.risk.level;
            riskBadge.className = `status-badge ${report.risk.level === "LOW" ? "status-approved" : (report.risk.level === "MEDIUM" ? "status-under_review" : "status-rejected")}`;
            
            // List active fraud flags
            const flagsBox = document.getElementById("fraud-flags-box");
            flagsBox.innerHTML = "";
            if (report.fraud_flags.length > 0) {
                report.fraud_flags.forEach(flag => {
                    const tag = document.createElement("span");
                    tag.className = "status-badge status-rejected";
                    tag.style.marginRight = "6px";
                    tag.style.marginBottom = "6px";
                    tag.innerText = flag.replace(/_/g, " ");
                    flagsBox.appendChild(tag);
                });
            } else {
                flagsBox.innerHTML = '<span style="font-size:12px; color:var(--text-muted);">No suspicious fraud triggers flagged.</span>';
            }
        }
    } catch (err) {
        console.error("Payout and risk calculation error:", err);
    }
}

// File Upload simulation helper
function triggerFileUpload(docType) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".pdf,.jpg,.png";
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const fd = new FormData();
        fd.append("case_id", activeClaimId);
        fd.append("document_type", docType);
        fd.append("role", loggedInUser.role);
        fd.append("file", file);
        
        try {
            const res = await fetch("/api/claims/upload", {
                method: "POST",
                body: fd
            });
            if (res.ok) {
                const info = await res.json();
                uploadedDocs[docType] = info.url;
                
                // Show success block
                document.getElementById(`upload-status-${docType}`).style.display = "flex";
                document.getElementById(`filename-${docType}`).innerText = file.name;
                alert(`File Upload Complete!\nGenerated Display SHA-256 Hash:\n${info.sha256}`);
            }
        } catch (err) {
            console.error("Upload error:", err);
            alert("File upload failed.");
        }
    };
    fileInput.click();
}

// Final claim submission to database
async function simulateClaimSubmission() {
    const payload = getWizardPayload();
    try {
        const res = await fetch("/api/claims/submit", {
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
            alert(`Claim dossier submitted successfully!\nTracking ID: ${result.trackingId}`);
            
            // Refresh claims
            await loadClaims();
            
            // Switch to Claim Tracker
            showSection("tracker-section", document.querySelector('[onclick*="tracker-section"]'));
        }
    } catch (err) {
        console.error("Dossier submission failed:", err);
    }
}

// ================= CLAIM STATUS TRACKER =================
function loadTrackerView() {
    // Find active claim
    const activeClaim = claimsList.find(c => c.id === activeClaimId) || claimsList[0];
    if (!activeClaim) {
        document.getElementById("tracker-tracking-id").innerText = "None active";
        document.getElementById("tracker-status").innerText = "N/A";
        return;
    }
    
    document.getElementById("tracker-tracking-id").innerText = activeClaim.trackingId;
    
    const status = activeClaim.status.toUpperCase();
    const statusLabel = document.getElementById("tracker-status");
    statusLabel.innerText = status.replace(/_/g, " ");
    statusLabel.className = `status-badge ${status === "APPROVED" ? "status-approved" : (status === "REJECTED" ? "status-rejected" : "status-under_review")}`;
    
    // Set stepper nodes
    const steps = ["submitted", "under_review", "query_raised", "approved"];
    steps.forEach(st => {
        document.getElementById(`track-step-${st}`).classList.remove("active", "completed");
    });
    
    if (status === "SUBMITTED" || status === "RESUBMITTED") {
        document.getElementById("track-step-submitted").classList.add("active");
    } else if (status === "UNDER_REVIEW") {
        document.getElementById("track-step-submitted").classList.add("completed");
        document.getElementById("track-step-under_review").classList.add("active");
    } else if (status === "QUERY_RAISED") {
        document.getElementById("track-step-submitted").classList.add("completed");
        document.getElementById("track-step-under_review").classList.add("completed");
        document.getElementById("track-step-query_raised").classList.add("active");
    } else if (status === "APPROVED") {
        document.getElementById("track-step-submitted").classList.add("completed");
        document.getElementById("track-step-under_review").classList.add("completed");
        document.getElementById("track-step-query_raised").classList.add("completed");
        document.getElementById("track-step-approved").classList.add("completed");
    } else if (status === "REJECTED") {
        document.getElementById("track-step-submitted").classList.add("completed");
        document.getElementById("track-step-under_review").classList.add("completed");
        document.getElementById("track-step-query_raised").classList.add("completed");
        // Highlight reject status separately
        const node = document.getElementById("track-step-approved");
        node.classList.add("active");
        node.querySelector(".step-number").style.backgroundColor = "var(--color-danger)";
        node.querySelector(".step-number").style.borderColor = "var(--color-danger)";
        node.querySelector(".step-label").innerText = "Rejected / Closed";
    }
    
    // Populate transition audit trail
    const timeline = document.getElementById("tracker-history-timeline");
    timeline.innerHTML = "";
    if (activeClaim.state_history && activeClaim.state_history.length > 0) {
        activeClaim.state_history.forEach(log => {
            const line = document.createElement("div");
            line.style.marginBottom = "10px";
            line.innerHTML = `
                <span style="color:var(--color-primary); font-weight:700;">[${log.at}]</span> 
                Status changed from <strong>${log.from}</strong> to <strong>${log.to}</strong> 
                by <em>${log.by}</em>. 
                <span style="font-size:12px; display:block; color:var(--text-muted); padding-left:14px; margin-top:2px;">"${log.comment || "No comment provided."}"</span>
            `;
            timeline.appendChild(line);
        });
    } else {
        timeline.innerHTML = "<p>No transitions recorded.</p>";
    }
    
    if (status === "APPROVED") {
        const actionDiv = document.createElement("div");
        actionDiv.style.marginTop = "20px";
        actionDiv.style.paddingTop = "15px";
        actionDiv.style.borderTop = "1px solid var(--border-glass)";
        actionDiv.innerHTML = `
            <button class="btn btn-success" onclick="openDisbursalCertificateForCase('${activeClaim.id}')">
                <i class="fa-solid fa-stamp"></i> View & Print Disbursal Clearance Certificate
            </button>
        `;
        timeline.appendChild(actionDiv);
    }
}

// ================= BANK EMPLOYEE / BRANCH DIRECTORY =================
function renderBranchDirectory() {
    const tbody = document.getElementById("branch-claims-tbody");
    tbody.innerHTML = "";
    
    if (claimsList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No branch claims found.</td></tr>';
        return;
    }
    
    claimsList.forEach(c => {
        const row = document.createElement("tr");
        const status = c.status;
        const payout = c.evaluation ? c.evaluation.payout.amount : c.policy.sum_assured;
        const formatPayout = `INR ${payout.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
        
        let actionBtn = "";
        if (status === "SUBMITTED" || status === "RESUBMITTED") {
            actionBtn = `<button class="btn btn-primary btn-sm" onclick="openKycVerification('${c.id}')"><i class="fa-solid fa-fingerprint"></i> Biometric KYC</button>`;
        } else if (status === "QUERY_RAISED") {
            actionBtn = `<button class="btn btn-danger btn-sm" onclick="openUploadDocuments('${c.id}')"><i class="fa-solid fa-file-arrow-up"></i> Resolve Query</button>`;
        } else if (status === "APPROVED") {
            actionBtn = `<button class="btn btn-success btn-sm" onclick="openDisbursalCertificateForCase('${c.id}')"><i class="fa-solid fa-stamp"></i> View Clearance</button>`;
        } else {
            actionBtn = `<span style="font-size:12px; color:var(--text-muted);">No Actions Pending</span>`;
        }
        
        const kycStatus = c.claim.legal_status.nominee_verified ? '<span class="text-success"><i class="fa-solid fa-circle-check"></i> Verified</span>' : '<span class="text-muted"><i class="fa-solid fa-circle-notch"></i> Pending</span>';
        
        row.innerHTML = `
            <td><strong>${c.policy.policy_number}</strong></td>
            <td>${c.claim.claimant.name}</td>
            <td style="font-size:13px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${c.claim.cause_of_death}">${c.claim.cause_of_death}</td>
            <td>${formatPayout}</td>
            <td><span class="status-badge status-${status.toLowerCase()}">${status.replace(/_/g, " ")}</span></td>
            <td>${kycStatus}</td>
            <td>${actionBtn}</td>
        `;
        tbody.appendChild(row);
    });
}

function openKycVerification(caseId) {
    activeUploadCaseId = caseId;
    document.getElementById("kyc-scan-modal").style.display = "flex";
}

function closeKycModal() {
    document.getElementById("kyc-scan-modal").style.display = "none";
}

function startBiometricScan() {
    const scanner = document.getElementById("biometric-scanner-btn");
    const statusText = document.getElementById("scan-status");
    
    scanner.classList.add("scanning");
    statusText.innerText = "Scanning fingerprint. Comparing Aadhaar biometric database...";
    
    setTimeout(async () => {
        scanner.classList.remove("scanning");
        statusText.innerText = "Biometric verify successful! Aadhaar KYC matching is 100%.";
        
        // Push verification details to database
        try {
            // Update nominee verified to true, transition status to UNDER_REVIEW
            const res = await fetch("/api/claims/decision", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    case_id: activeUploadCaseId,
                    status: "UNDER_REVIEW",
                    comment: "Nominee biometric verification complete. Aadhaar KYC linked successfully.",
                    by: "bank_agent"
                })
            });
            
            if (res.ok) {
                alert("Nominee Aadhaar KYC Verification Complete! Claims forwarded to underwriters.");
                closeKycModal();
                await loadClaims();
            }
        } catch (err) {
            console.error("Biometric decision error:", err);
            alert("Failed to submit verification status.");
        }
    }, 2500);
}

function openUploadDocuments(caseId) {
    activeUploadCaseId = caseId;
    document.getElementById("upload-modal-case-id").value = caseId;
    document.getElementById("upload-docs-modal").style.display = "flex";
}

function closeUploadModal() {
    document.getElementById("upload-docs-modal").style.display = "none";
}

function triggerFileUploadModal(docType) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".pdf,.jpg,.png";
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const fd = new FormData();
        fd.append("case_id", activeUploadCaseId);
        fd.append("document_type", docType);
        fd.append("role", loggedInUser.role);
        fd.append("file", file);
        
        try {
            const res = await fetch("/api/claims/upload", {
                method: "POST",
                body: fd
            });
            if (res.ok) {
                const info = await res.json();
                document.getElementById(`upload-status-modal-${docType}`).style.display = "flex";
                document.getElementById(`filename-modal-${docType}`).innerText = file.name;
                alert(`File Upload Complete!\nGenerated SHA-256:\n${info.sha256}`);
            }
        } catch (err) {
            console.error("Upload error:", err);
            alert("File upload failed.");
        }
    };
    fileInput.click();
}

async function submitResubmittedClaim() {
    try {
        const res = await fetch("/api/claims/decision", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: activeUploadCaseId,
                status: "RESUBMITTED",
                comment: "Resubmitted requested documents to resolve outstanding compliance queries.",
                by: "bank_agent"
            })
        });
        
        if (res.ok) {
            alert("Discrepancies resolved. Claims resubmitted back to underwriters.");
            closeUploadModal();
            await loadClaims();
        }
    } catch (err) {
        console.error("Resubmission error:", err);
    }
}

// ================= INSURER CONSOLE & DECISIONS WORKSPACE =================
function renderInsurerInbox() {
    const list = document.getElementById("insurer-claims-list");
    list.innerHTML = "";
    
    const submitted = claimsList.filter(c => ["SUBMITTED", "UNDER_REVIEW", "RESUBMITTED", "QUERY_RAISED", "APPROVED", "REJECTED"].includes(c.status));
    
    if (submitted.length === 0) {
        list.innerHTML = '<p style="text-align:center; color:var(--text-muted);">No submitted claim files found.</p>';
        return;
    }
    
    submitted.forEach(c => {
        const item = document.createElement("div");
        item.style.padding = "16px";
        item.style.border = "1px solid var(--border-glass)";
        item.style.borderRadius = "8px";
        item.style.background = c.id === activeClaimId ? "rgba(99, 102, 241, 0.08)" : "rgba(0, 0, 0, 0.2)";
        item.style.borderColor = c.id === activeClaimId ? "var(--color-primary)" : "var(--border-glass)";
        item.style.cursor = "pointer";
        item.onclick = () => openDossier(c.id);
        
        item.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <strong>${c.policy.policy_number}</strong>
                <span class="status-badge status-${c.status.toLowerCase()}">${c.status.replace(/_/g, " ")}</span>
            </div>
            <p style="font-size:12px; color:var(--text-muted);">Insured: ${c.policy.life_assured}</p>
            <p style="font-size:12px; color:var(--text-muted);">Nominee: ${c.claim.claimant.name}</p>
        `;
        list.appendChild(item);
    });
    
    // Automatically load active claim if set
    if (activeClaimId) {
        openDossier(activeClaimId);
    }
}

function openDossier(caseId) {
    activeClaimId = caseId;
    
    // Re-highlight list items
    const listItems = document.getElementById("insurer-claims-list").children;
    for (let el of listItems) {
        el.style.background = "rgba(0, 0, 0, 0.2)";
        el.style.borderColor = "var(--border-glass)";
    }
    
    const claim = claimsList.find(c => c.id === caseId);
    if (!claim) return;
    
    document.getElementById("workspace-empty-view").style.display = "none";
    document.getElementById("workspace-active-view").style.display = "block";
    
    // Populate text details
    document.getElementById("w-case-title").innerText = `Dossier: ${claim.policy.life_assured}`;
    document.getElementById("w-tracking-id").innerText = claim.trackingId;
    
    const statusBadge = document.getElementById("w-status-badge");
    statusBadge.innerText = claim.status.replace(/_/g, " ");
    statusBadge.className = `status-badge status-${claim.status.toLowerCase()}`;
    
    document.getElementById("w-life-assured").innerText = claim.policy.life_assured;
    document.getElementById("w-policy-date").innerText = claim.policy.commencement_date;
    document.getElementById("w-sum-assured").innerText = `INR ${claim.policy.sum_assured.toLocaleString("en-IN")}`;
    document.getElementById("w-premiums-paid").innerText = `${claim.policy.premiums_paid_years} Years`;
    
    document.getElementById("w-nominee").innerText = claim.policy.nominee_name;
    document.getElementById("w-aadhaar").innerText = claim.claim.claimant.aadhaar;
    document.getElementById("w-ifsc").innerText = claim.claim.bank_details.ifsc;
    document.getElementById("w-acc-num").innerText = claim.claim.bank_details.account_number;
    
    document.getElementById("w-cause-death").innerText = claim.claim.cause_of_death;
    document.getElementById("w-doctor").innerText = claim.claim.medical_details.treating_doctor || "Not reported";
    document.getElementById("w-icd").innerText = claim.claim.medical_details.icd_code || "N/A";
    document.getElementById("w-history").innerText = claim.claim.medical_details.hospitalization_history || "No prior history";
    
    // Configure risk variables from cached evaluation
    const report = claim.evaluation;
    if (report) {
        document.getElementById("w-risk-score").innerText = `${report.risk.total_score}/100`;
        const fill = document.getElementById("w-gauge-fill");
        fill.style.width = `${report.risk.total_score}%`;
        
        let color = "var(--color-success)";
        if (report.risk.level === "MEDIUM") color = "var(--color-warning)";
        if (report.risk.level === "HIGH") color = "var(--color-danger)";
        fill.style.background = color;
        
        const rlvl = document.getElementById("w-risk-level-badge");
        rlvl.innerText = report.risk.level;
        rlvl.className = `status-badge ${report.risk.level === "LOW" ? "status-approved" : (report.risk.level === "MEDIUM" ? "status-under_review" : "status-rejected")}`;
        
        // Payout decision block
        document.getElementById("w-payout-amount").innerText = `INR ${report.payout.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
        document.getElementById("w-decision-reason").innerText = report.decision.reason;
        
        // Rules trace console
        const traceConsole = document.getElementById("w-console-trace");
        traceConsole.innerHTML = "";
        report.explainability.decision_path.forEach(pathLine => {
            const line = document.createElement("div");
            line.className = "console-line";
            line.innerText = `> ${pathLine}`;
            traceConsole.appendChild(line);
        });
    }
    
    // Display certification button for APPROVED claims
    const certAction = document.getElementById("cert-action-pane");
    if (claim.status === "APPROVED") {
        certAction.style.display = "block";
    } else {
        certAction.style.display = "none";
    }
}

async function postAssessorDecision(status) {
    const comment = prompt(`Provide audit comment for transitioning claim to ${status}:`, `Underwriter verification action: ${status}`);
    if (comment === null) return; // cancel click
    
    try {
        const res = await fetch("/api/claims/decision", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: activeClaimId,
                status,
                comment,
                by: "insurer_assessor"
            })
        });
        
        if (res.ok) {
            alert(`Claim updated successfully to ${status}!`);
            await loadClaims();
        } else {
            const err = await res.json();
            alert(err.detail || "Decision transition failed.");
        }
    } catch (err) {
        console.error("Decision transaction error:", err);
    }
}

// ================= CLEARANCE CERTIFICATE PREVIEWS =================
function renderApprovedCertificate() {
    const claim = claimsList.find(c => c.id === activeClaimId) || claimsList.find(c => c.status === "APPROVED") || claimsList[0];
    if (!claim) return;
    
    if (claim.status !== "APPROVED") {
        document.getElementById("cert-paper-print").innerHTML = `
            <div style="text-align:center; padding:100px 20px; color:var(--text-muted);">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:48px; margin-bottom:16px; color:var(--color-warning);"></i>
                <h3>Clearance Pending Approval</h3>
                <p>The Disbursal Clearance Certificate will be generated automatically once the insurer has audited and approved the death claim.</p>
            </div>
        `;
        return;
    }
    
    const payout = claim.evaluation ? claim.evaluation.payout.amount : claim.policy.sum_assured;
    const approvalLog = claim.state_history.find(h => h.to === "APPROVED");
    const approvalDate = approvalLog ? approvalLog.at.split(" ")[0] : new Date().toLocaleDateString("en-GB");
    
    document.getElementById("cert-paper-print").innerHTML = `
        <div class="cert-header">
            <div class="cert-seal"><i class="fa-solid fa-shield-halved"></i></div>
            <div class="cert-title">ICATS CLEARANCE SYSTEM</div>
        </div>
        <div class="cert-body">
            <p>This document serves as formal clearance that the life insurance death claim listed below has passed all compliance checklists, statutory non-forfeiture rules under Section 113 of the Insurance Act 1938, and medical suppression checks.</p>
        </div>
        <div class="cert-meta">
            <p><strong>Approved Settled Sum:</strong> INR <span id="c-sum-assured">${payout.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span></p>
            <p><strong>Beneficiary Nominee:</strong> <span id="c-nominee">${claim.policy.nominee_name}</span></p>
            <p><strong>Policy Number Reference:</strong> <span id="c-policy-no">${claim.policy.policy_number}</span></p>
            <p><strong>Verification Code:</strong> LIC-DISB-2026-SBI-K01</p>
        </div>
        <div class="cert-body">
            <p>The processing bank is hereby advised to clear and disburse funds to the beneficiary's registered settlement bank account. The claim has been marked closed on the insurer registry ledger.</p>
        </div>
        <div class="cert-footer">
            <span style="font-size:11px; color:#555;">Clearance Date: <span id="c-date">${approvalDate}</span></span>
            <div style="text-align:center; width:150px; border-top:1px solid #444; padding-top:4px; font-size:12px; font-weight:700;">
                Underwriter Sign
            </div>
        </div>
    `;
}

function openDisbursalCertificate() {
    renderApprovedCertificate();
    showSection("certificate-section", document.getElementById("menu-cert"));
}

function openDisbursalCertificateForCase(caseId) {
    activeClaimId = caseId;
    renderApprovedCertificate();
    showSection("certificate-section", document.getElementById("menu-cert"));
}

// ================= LEGAL AFFIDAVIT GENERATOR =================
function renderSpellingAffidavit() {
    const claim = claimsList.find(c => c.id === activeClaimId) || claimsList[0];
    if (!claim) return;
    
    document.getElementById("aff-nominee-full").innerText = claim.claim.claimant.name;
    document.getElementById("aff-life-assured").innerText = claim.policy.life_assured;
    document.getElementById("aff-policy-no").innerText = claim.policy.policy_number;
    document.getElementById("aff-date-death").innerText = claim.claim.date_of_death;
    document.getElementById("aff-nominee-policy").innerText = claim.policy.nominee_name;
    document.getElementById("aff-bank-account").innerText = claim.claim.bank_details.account_number;
    document.getElementById("aff-nominee-bank").innerText = claim.claim.bank_details.name_on_cheque;
}

function viewNameAffidavit() {
    showSection("affidavit-section", document.getElementById("menu-affidavit"));
}

// ================= AUTOPILOT SIMULATOR =================
async function runAutopilot() {
    const caseId = document.getElementById("sim-preset").value;
    const terminal = document.getElementById("autopilot-terminal");
    
    terminal.innerHTML = "[System] Autopilot simulator launched. Querying database APIs...";
    
    try {
        const res = await fetch(`/api/agents/simulate?case_id=${caseId}`, { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            
            // Print logs sequentially with typewriter delay to show microservices interaction
            terminal.innerHTML = "";
            let index = 0;
            
            function printNextLine() {
                if (index < data.logs.length) {
                    const line = document.createElement("div");
                    line.className = "terminal-line";
                    
                    // Highlight microservices color
                    let logText = data.logs[index];
                    logText = logText.replace("[Claimant Agent]", '<span style="color:#60a5fa; font-weight:700;">[Claimant Agent]</span>');
                    logText = logText.replace("[Bank Agent]", '<span style="color:#f59e0b; font-weight:700;">[Bank Agent]</span>');
                    logText = logText.replace("[Insurer Agent]", '<span style="color:#10b981; font-weight:700;">[Insurer Agent]</span>');
                    
                    line.innerHTML = logText;
                    terminal.appendChild(line);
                    terminal.scrollTop = terminal.scrollHeight;
                    index++;
                    setTimeout(printNextLine, 600); // 600ms typewriter delay
                } else {
                    const endLine = document.createElement("div");
                    endLine.className = "terminal-line";
                    endLine.style.color = "var(--color-success)";
                    endLine.style.fontWeight = "700";
                    endLine.innerHTML = `[System] Autopilot resolved Case ${caseId} cleanly. Database updated.`;
                    terminal.appendChild(endLine);
                    
                    // Reload data
                    loadClaims();
                }
            }
            printNextLine();
        }
    } catch (err) {
        console.error("Simulation failed:", err);
        terminal.innerHTML = '<span style="color:var(--color-danger);">[System Error] Autopilot connection broke. Try checking MongoDB connection logs.</span>';
    }
}
